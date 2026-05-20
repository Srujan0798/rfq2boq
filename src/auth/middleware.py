"""Auth middleware - JWT validation, tenant context, rate limiting."""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from src.auth.security import JWTAuth, TokenPayload
from starlette.middleware.base import BaseHTTPMiddleware

_jwt_secret: str | None = None


def get_jwt_secret() -> str:
    global _jwt_secret
    if _jwt_secret is None:
        _jwt_secret = os.environ.get("JWT_SECRET", "dev-secret-do-not-use-in-production")
    return _jwt_secret


class JWTBearer:
    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error
        self._auth = JWTAuth(secret_key=get_jwt_secret())

    async def __call__(self, request: Request) -> TokenPayload:
        credentials: HTTPAuthorizationCredentials | None = await self._get_credentials(request)
        if credentials is None:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authorization header",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        token = credentials.credentials
        payload = self._auth.verify_token(token)
        if payload is None:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        return payload

    async def _get_credentials(self, request: Request) -> HTTPAuthorizationCredentials | None:
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=authorization[7:])


class TenantContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exclude_paths: list[str] | None = None):
        super().__init__(app)
        self._auth = JWTAuth(secret_key=get_jwt_secret())
        self._exclude_paths = exclude_paths or ["/", "/api/health", "/v1/health", "/metrics"]

    async def dispatch(self, request: Request, call_next: Callable):
        if request.url.path in self._exclude_paths:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        tenant_id: str | None = None
        user_id: str | None = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = self._auth.verify_token(token)
            if payload:
                tenant_id = payload.tenant_id
                user_id = payload.sub

        request.state.tenant_id = tenant_id
        request.state.user_id = user_id

        response = await call_next(request)
        return response


_rate_limit_lock = threading.Lock()
_rate_limit_cache: dict[str, tuple[int, float]] = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self._requests_per_minute = requests_per_minute
        self._requests_per_hour = requests_per_hour
        self._exclude_paths = exclude_paths or ["/", "/api/health", "/v1/health", "/metrics"]

    async def dispatch(self, request: Request, call_next: Callable):
        if request.url.path in self._exclude_paths:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", None)
        identifier = f"user:{user_id}" if user_id else f"ip:{client_ip}"

        if not self._check_rate_limit(identifier):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        return response

    def _check_rate_limit(self, identifier: str) -> bool:
        now = time.time()
        with _rate_limit_lock:
            last_request = _rate_limit_cache.get(identifier)
            if last_request:
                elapsed = now - last_request[1]
                if elapsed < 60:
                    if last_request[0] >= self._requests_per_minute:
                        return False
                    _rate_limit_cache[identifier] = (last_request[0] + 1, now)
                else:
                    _rate_limit_cache[identifier] = (1, now)
            else:
                _rate_limit_cache[identifier] = (1, now)
            return True
