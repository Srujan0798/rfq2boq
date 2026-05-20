"""Security module - JWT, MFA, rate limiting, OWASP compliance."""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
from base64 import b32encode, b64decode, b64encode
from dataclasses import dataclass
from pathlib import Path

from fastapi import Request
from fastapi.security import HTTPBearer

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MIN = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


@dataclass
class TokenPayload:
    sub: str
    tenant_id: str | None
    exp: int
    iat: int
    role: str = "user"


class JWTAuth:
    def __init__(self, secret_key: str | None = None):
        self.secret = secret_key or secrets.token_urlsafe(32)

    def create_access_token(self, user_id: str, tenant_id: str | None = None, role: str = "user") -> str:
        from datetime import UTC, datetime, timedelta
        now = datetime.now(UTC)
        payload = TokenPayload(
            sub=user_id,
            tenant_id=tenant_id,
            exp=int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)).timestamp()),
            iat=int(now.timestamp()),
            role=role,
        )
        return self._encode_token(payload)

    def create_refresh_token(self, user_id: str) -> str:
        from datetime import UTC, datetime, timedelta
        now = datetime.now(UTC)
        payload = TokenPayload(
            sub=user_id,
            tenant_id=None,
            exp=int((now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).timestamp()),
            iat=int(now.timestamp()),
        )
        return self._encode_token(payload)

    def verify_token(self, token: str) -> TokenPayload | None:
        try:
            from jwt import ExpiredSignatureError, InvalidTokenError, decode
        except ImportError:
            return None

        try:
            data = decode(token, self.secret, algorithms=[ALGORITHM])
            return TokenPayload(**data)
        except (ExpiredSignatureError, InvalidTokenError):
            return None

    def _encode_token(self, payload: TokenPayload) -> str:
        try:
            from jwt import encode
        except ImportError:
            return ""

        return encode(payload.__dict__, self.secret, algorithm=ALGORITHM)


class MFAGenerator:
    @staticmethod
    def generate_secret() -> str:
        return b32encode(secrets.token_bytes(20)).decode().rstrip("=")

    @staticmethod
    def get_totp_uri(secret: str, email: str, issuer: str = "RFQ2BOQ") -> str:
        return f"otpauth://totp/{issuer}:{email}?secret={secret}&issuer={issuer}"

    @staticmethod
    def verify_totp(secret: str, token: str, window: int = 1) -> bool:
        try:
            import pyotp
        except ImportError:
            logger.warning("pyotp not installed")
            return False

        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=window)


class RateLimiter:
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self._client = None
        self._local_cache: dict[str, tuple[int, float]] = {}
        self.default_limits = {"minute": 60, "hour": 1000, "day": 10000}

    def _get_client(self):
        if self._client is None:
            try:
                import redis
                self._client = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True, socket_connect_timeout=1)
                self._client.ping()
            except Exception:
                self._client = None
        return self._client

    def is_allowed(self, key: str, limit: int, window: int = 60) -> bool:
        now = time.time()
        client = self._get_client()

        if client is None:
            last_time = self._local_cache.get(key)
            if last_time and now - last_time[1] < window:
                if last_time[0] >= limit:
                    return False
                self._local_cache[key] = (last_time[0] + 1, now)
            else:
                self._local_cache[key] = (1, now)
            return True

        redis_key = f"ratelimit:{key}:{window}"
        try:
            count = client.incr(redis_key)
            if count == 1:
                client.expire(redis_key, window)
            return count <= limit
        except Exception:
            return True

    def check_request_limit(self, request: Request, user_id: str | None = None) -> bool:
        key = f"user:{user_id}" if user_id else f"ip:{request.client.host}"
        return self.is_allowed(key, self.default_limits["minute"], 60)


security = HTTPBearer(auto_error=False)


async def verify_jwt(request: Request) -> TokenPayload | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    jwt_auth = JWTAuth()
    return jwt_auth.verify_token(token)


class AuditLogger:
    def __init__(self, log_path: str = "logs/audit.log"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, user_id: str | None = None, tenant_id: str | None = None, metadata: dict | None = None):
        import json
        from datetime import UTC, datetime

        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": event,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "metadata": metadata or {},
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def log_auth_failure(self, email: str, reason: str):
        self.log("auth_failure", metadata={"email": email, "reason": reason})

    def log_extraction(self, user_id: str, job_id: str, doc_name: str):
        self.log("extraction", user_id=user_id, metadata={"job_id": job_id, "doc": doc_name})

    def log_export(self, user_id: str, job_id: str, format: str):
        self.log("export", user_id=user_id, metadata={"job_id": job_id, "format": format})


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, bytes]:
    if salt is None:
        salt = secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return b64encode(hashed).decode(), b64encode(salt).decode()


def verify_password(password: str, hashed: str, salt: str) -> bool:
    try:
        salt_bytes = b64decode(salt)
        expected, _ = hash_password(password, salt_bytes)
        return hmac.compare_digest(expected, hashed)
    except Exception:
        return False
