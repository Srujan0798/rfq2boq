# TASK: C2 Security — Tests, Middleware, Docs, CI Workflow

**Wave:** 4 | **Tier:** C | **Priority:** P1

## 1. GOAL

Complete the security implementation by adding: test file, auth middleware, upload sandboxing, security docs, and GitHub Actions CI workflow.

## 2. CONTEXT

Files to read first:
- `src/auth/security.py` — existing JWTAuth, MFAGenerator, RateLimiter, AuditLogger
- `src/api/main.py` — existing app entry point
- `src/api/dependencies.py` — existing dependencies
- `tests/unit/test_llm_assistant.py` — example test structure
- `pyproject.toml` — pytest configuration

## 3. DELIVERABLES

Exact paths to create/modify:
1. `tests/security/test_security.py` — test file
2. `src/auth/middleware.py` — auth middleware (JWT validation, tenant context)
3. `src/security/upload.py` — upload sandboxing (file type validation, size limits, path traversal prevention)
4. `docs/security.md` — security documentation
5. `docs/security_pentest.md` — penetration testing guide
6. `.github/workflows/security.yml` — GitHub security scanning workflow
7. `.github/dependabot.yml` — (already exists, verify it is correct)

## 4. STEPS

1. **Create `tests/security/test_security.py`:**
   - `TestJWTAuth` — test token creation, validation, expiry
   - `TestMFAGenerator` — test TOTP generation and verification
   - `TestRateLimiter` — test rate limit tracking and reset
   - `TestAuditLogger` — test audit log entry creation
   - `TestUploadSandbox` — test file type validation, size limit, path traversal
   - Use pytest, MagicMock where needed

2. **Create `src/auth/middleware.py`:**
   - `JWTBearer` — FastAPI dependency for JWT validation
   - `TenantContextMiddleware` — inject tenant ID from JWT into request state
   - `RateLimitMiddleware` — apply rate limiting per tenant/user

3. **Create `src/security/upload.py`:**
   - `validate_file_type(file_path, allowed_types)` — check magic bytes, not just extension
   - `validate_file_size(file_path, max_size_mb=10)` — reject oversized uploads
   - `sanitize_filename(filename)` — prevent path traversal (../ attacks)
   - `UploadSandbox` class wrapping all three

4. **Create `docs/security.md`:**
   - Authentication (JWT, MFA)
   - Rate limiting
   - Audit logging
   - Upload security
   - Secret management (.env)
   - API key scopes

5. **Create `docs/security_pentest.md`:**
   - OWASP Top 10 alignment
   - Test cases for each vulnerability
   - Remediation steps

6. **Create `.github/workflows/security.yml`:**
   - Run `pip-audit` for dependency vulnerabilities
   - Run `bandit` for code security issues
   - Run `safety` check
   - Run new `pytest tests/security/` in CI

## 5. VERIFICATION

```bash
# Run new security tests
python3 -m pytest tests/security/test_security.py -v --tb=short

# Verify middleware imports
python3 -c "from src.auth.middleware import JWTBearer, TenantContextMiddleware; print('OK')"

# Verify upload sandbox
python3 -c "from src.security.upload import UploadSandbox; s = UploadSandbox(); print('OK')"

# Verify docs exist
ls docs/security.md docs/security_pentest.md

# Verify workflow exists
ls .github/workflows/security.yml

# ruff check
ruff check src/auth/middleware.py src/security/upload.py tests/security/test_security.py
```

## 6. ACCEPTANCE CRITERIA

- [ ] `tests/security/test_security.py` exists with ≥20 passing tests
- [ ] `src/auth/middleware.py` has JWTBearer and TenantContextMiddleware
- [ ] `src/security/upload.py` has UploadSandbox with type/size/path validation
- [ ] `docs/security.md` and `docs/security_pentest.md` exist and are non-empty (>100 lines each)
- [ ] `.github/workflows/security.yml` triggers on push/PR for security scanning
- [ ] All new files pass `ruff check`
- [ ] `pytest tests/security/` passes with no failures

## 7. CONSTRAINTS

- Python 3.11–3.13 only
- Type hints required on all new code
- Use `src.` import prefix, not `code.`
- Follow existing test patterns from `tests/unit/test_llm_assistant.py`
- Do NOT modify existing auth logic — only add missing pieces

## 8. DEPENDENCIES

- Blocks: C3 Observability (shares auth context), C4 Multitenancy (shares tenant middleware)
- Blocked by: A0_FIX_BROKEN_TESTS (DONE)

## 9. GOTCHAS

- JWT secret must come from environment variable `JWT_SECRET`, not hardcoded
- File type validation must check magic bytes, not just extensions (security)
- Rate limiter must be thread-safe (use dict with threading.Lock or use Redis if available)
- GitHub workflow must use `ubuntu-latest` runner
