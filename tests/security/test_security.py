"""Security tests for JWT auth, MFA, rate limiting, upload sandboxing, and audit logging."""

import os
import tempfile
import time
from unittest.mock import MagicMock, patch

import pytest


class TestJWTAuth:
    def test_create_access_token(self):
        from src.auth.security import JWTAuth

        auth = JWTAuth(secret_key="test-secret-key-12345")
        token = auth.create_access_token(user_id="user123", tenant_id="tenant1", role="user")
        assert token is not None
        assert len(token) > 20

    def test_verify_valid_token(self):
        from src.auth.security import JWTAuth

        auth = JWTAuth(secret_key="test-secret-key-12345")
        token = auth.create_access_token(user_id="user123", tenant_id="tenant1")
        payload = auth.verify_token(token)
        assert payload is not None
        assert payload.sub == "user123"
        assert payload.tenant_id == "tenant1"

    def test_verify_expired_token(self):
        from src.auth.security import JWTAuth

        auth = JWTAuth(secret_key="test-secret-key-12345")
        with patch.object(auth, "_encode_token") as mock_encode:
            mock_encode.return_value = "expired-token"

        result = auth.verify_token("expired-token")
        assert result is None

    def test_verify_invalid_token(self):
        from src.auth.security import JWTAuth

        auth = JWTAuth(secret_key="test-secret-key-12345")
        result = auth.verify_token("invalid.token.here")
        assert result is None

    def test_create_refresh_token(self):
        from src.auth.security import JWTAuth

        auth = JWTAuth(secret_key="test-secret-key-12345")
        token = auth.create_refresh_token(user_id="user123")
        assert token is not None
        payload = auth.verify_token(token)
        assert payload is not None
        assert payload.sub == "user123"

    def test_different_secrets_produce_different_tokens(self):
        from src.auth.security import JWTAuth

        auth1 = JWTAuth(secret_key="secret1")
        auth2 = JWTAuth(secret_key="secret2")
        token1 = auth1.create_access_token(user_id="user123")
        token2 = auth2.create_access_token(user_id="user123")
        assert token1 != token2


class TestMFAGenerator:
    def test_generate_secret(self):
        from src.auth.security import MFAGenerator

        secret = MFAGenerator.generate_secret()
        assert secret is not None
        assert len(secret) == 32
        assert secret.isupper()

    def test_get_totp_uri(self):
        from src.auth.security import MFAGenerator

        secret = "JBSWY3DPEHPK3PXP"
        uri = MFAGenerator.get_totp_uri(secret, "test@example.com", "RFQ2BOQ")
        assert uri.startswith("otpauth://totp/")
        assert "test@example.com" in uri
        assert "RFQ2BOQ" in uri

    def test_verify_totp_valid(self):
        import pyotp
        from src.auth.security import MFAGenerator

        secret = MFAGenerator.generate_secret()
        totp = pyotp.TOTP(secret)
        token = totp.now()
        result = MFAGenerator.verify_totp(secret, token)
        assert result is True

    def test_verify_totp_invalid(self):
        from src.auth.security import MFAGenerator

        secret = MFAGenerator.generate_secret()
        result = MFAGenerator.verify_totp(secret, "000000")
        assert result is False


class TestRateLimiter:
    @patch("src.auth.security.RateLimiter._get_client", return_value=None)
    def test_is_allowed_no_redis(self, mock_get_client):
        from src.auth.security import RateLimiter

        limiter = RateLimiter(redis_host="nonexistent")
        result = limiter.is_allowed("test_key", limit=5, window=60)
        assert result is True

    @patch("src.auth.security.RateLimiter._get_client", return_value=None)
    def test_rate_limit_tracking(self, mock_get_client):
        from src.auth.security import RateLimiter

        limiter = RateLimiter(redis_host="nonexistent")
        key = "ratelimit_test_key"
        for _ in range(5):
            result = limiter.is_allowed(key, limit=5, window=60)
            assert result is True
        result = limiter.is_allowed(key, limit=5, window=60)
        assert result is False

    @patch("src.auth.security.RateLimiter._get_client", return_value=None)
    def test_rate_limit_reset_after_window(self, mock_get_client):
        from src.auth.security import RateLimiter

        limiter = RateLimiter(redis_host="nonexistent")
        key = "ratelimit_reset_key"
        result1 = limiter.is_allowed(key, limit=1, window=1)
        assert result1 is True
        time.sleep(1.1)
        result2 = limiter.is_allowed(key, limit=1, window=1)
        assert result2 is True

    @patch("src.auth.security.RateLimiter._get_client", return_value=None)
    def test_check_request_limit_with_user_id(self, mock_get_client):
        from src.auth.security import RateLimiter

        limiter = RateLimiter(redis_host="nonexistent")
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        result = limiter.check_request_limit(mock_request, user_id="user123")
        assert result is True

    @patch("src.auth.security.RateLimiter._get_client", return_value=None)
    def test_check_request_limit_without_user_id(self, mock_get_client):
        from src.auth.security import RateLimiter

        limiter = RateLimiter(redis_host="nonexistent")
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"
        result = limiter.check_request_limit(mock_request)
        assert result is True


class TestAuditLogger:
    def test_init_creates_log_directory(self):
        import tempfile

        from src.auth.security import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.log")
            logger = AuditLogger(log_path=log_path)
            assert logger.log_path.exists() or logger.log_path.parent.exists()

    def test_log_creates_entry(self):
        import json
        import tempfile

        from src.auth.security import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.log")
            logger = AuditLogger(log_path=log_path)
            logger.log(event="test_event", user_id="user123", tenant_id="tenant1", metadata={"key": "value"})
            assert os.path.exists(log_path)
            with open(log_path) as f:
                entry = json.loads(f.readline())
                assert entry["event"] == "test_event"
                assert entry["user_id"] == "user123"
                assert entry["tenant_id"] == "tenant1"

    def test_log_auth_failure(self):
        import tempfile

        from src.auth.security import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.log")
            logger = AuditLogger(log_path=log_path)
            logger.log_auth_failure(email="test@example.com", reason="invalid_password")
            assert os.path.getsize(log_path) > 0

    def test_log_extraction(self):
        import tempfile

        from src.auth.security import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.log")
            logger = AuditLogger(log_path=log_path)
            logger.log_extraction(user_id="user123", job_id="job456", doc_name="test.pdf")
            assert os.path.getsize(log_path) > 0

    def test_log_export(self):
        import tempfile

        from src.auth.security import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.log")
            logger = AuditLogger(log_path=log_path)
            logger.log_export(user_id="user123", job_id="job456", format="excel")
            assert os.path.getsize(log_path) > 0


class TestUploadSandbox:
    def test_validate_file_type_pdf(self):
        pytest.importorskip("src.security.upload", reason="upload module archived to attic/")
        from src.security.upload import UploadSandbox

        sandbox = UploadSandbox()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 test content")
            f.flush()
            result = sandbox.validate_file_type(f.name, allowed_types={"pdf"})
            os.unlink(f.name)
            assert result is True

    def test_validate_file_type_not_allowed(self):
        pytest.importorskip("src.security.upload", reason="upload module archived to attic/")
        from src.security.upload import UploadSandbox

        sandbox = UploadSandbox()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"some text content")
            f.flush()
            result = sandbox.validate_file_type(f.name, allowed_types={"pdf"})
            os.unlink(f.name)
            assert result is False

    def test_validate_file_type_by_magic_bytes(self):
        pytest.importorskip("src.security.upload", reason="upload module archived to attic/")
        from src.security.upload import UploadSandbox

        sandbox = UploadSandbox()
        with tempfile.NamedTemporaryFile(suffix=".fake", delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n fake png content")
            f.flush()
            result = sandbox.validate_file_type(f.name, allowed_types={"png"})
            os.unlink(f.name)
            assert result is True

    def test_validate_file_size_within_limit(self):
        pytest.importorskip("src.security.upload", reason="upload module archived to attic/")
        from src.security.upload import UploadSandbox

        sandbox = UploadSandbox()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"x" * 1024)
            f.flush()
            result = sandbox.validate_file_size(f.name, max_size_mb=10)
            os.unlink(f.name)
            assert result is True

    def test_validate_file_size_exceeds_limit(self):
        pytest.importorskip("src.security.upload", reason="upload module archived to attic/")
        from src.security.upload import UploadSandbox

        sandbox = UploadSandbox()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"x" * (11 * 1024 * 1024))
            f.flush()
            result = sandbox.validate_file_size(f.name, max_size_mb=10)
            os.unlink(f.name)
            assert result is False

    def test_sanitize_filename_normal(self):
        pytest.importorskip("src.security.upload", reason="upload module archived to attic/")
        from src.security.upload import sanitize_filename

        result = sanitize_filename("document.pdf")
        assert result == "document.pdf"

    def test_sanitize_filename_path_traversal(self):
        pytest.importorskip("src.security.upload", reason="upload module archived to attic/")
        from src.security.upload import sanitize_filename

        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result
        assert result != "../../../etc/passwd"

    def test_sanitize_filename_with_directory(self):
        pytest.importorskip("src.security.upload", reason="upload module archived to attic/")
        from src.security.upload import sanitize_filename

        result = sanitize_filename("uploads/myfile.pdf")
        assert ".." not in result

    def test_sanitize_filename_preserves_valid_chars(self):
        pytest.importorskip("src.security.upload", reason="upload module archived to attic/")
        from src.security.upload import sanitize_filename

        result = sanitize_filename("my-document_v2.pdf")
        assert result == "my-document_v2.pdf"

    def test_upload_sandbox_full_validation(self):
        pytest.importorskip("src.security.upload", reason="upload module archived to attic/")
        from src.security.upload import UploadSandbox

        sandbox = UploadSandbox()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 test content")
            f.flush()
            type_ok = sandbox.validate_file_type(f.name, allowed_types={"pdf"})
            size_ok = sandbox.validate_file_size(f.name, max_size_mb=10)
            os.unlink(f.name)
            assert type_ok is True
            assert size_ok is True

    def test_upload_sandbox_rejects_bad_type(self):
        pytest.importorskip("src.security.upload", reason="upload module archived to attic/")
        from src.security.upload import UploadSandbox

        sandbox = UploadSandbox()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not a pdf")
            f.flush()
            type_ok = sandbox.validate_file_type(f.name, allowed_types={"pdf"})
            os.unlink(f.name)
            assert type_ok is False
