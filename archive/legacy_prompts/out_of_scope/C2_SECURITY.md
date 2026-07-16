# TASK: Security Hardening — Agent-4

**Wave:** 4 | **Tier:** C | **Priority:** P1

## 1. GOAL
Production security: OWASP audit pass, dependency scanning, secrets management, JWT auth with MFA, file upload sandboxing, audit logging, penetration test report.

## 2. CONTEXT
Read first:
- `src/api/` — all endpoints
- `src/auth/` — current auth (if any)
- `.env.example` — current secrets
- [docs/conventions.md](../../../docs/conventions.md)

Current state: Basic file size limits, no auth, no rate limiting per user, secrets in .env file.

## 3. DELIVERABLES
- [ ] `src/auth/__init__.py`
- [ ] `src/auth/security.py` — JWT, refresh tokens, MFA TOTP
- [ ] `src/auth/middleware.py` — auth middleware
- [ ] `src/auth/audit_log.py` — audit logging
- [ ] `src/security/upload.py` — file upload validation + sandboxing
- [ ] `scripts/security_audit.py` — automated security scan
- [ ] `.github/dependabot.yml` — dependency scanning
- [ ] `.github/workflows/security.yml` — pip-audit + trivy + semgrep
- [ ] `docs/security.md` — security model + runbook
- [ ] `tests/security/test_security.py` — ≥15 security tests

## 4. STEPS
1. JWT auth: short-lived access (15min) + refresh (7day)
2. MFA TOTP via `pyotp`
3. Rate limiting per user (not IP) via Redis token bucket
4. File upload: validate by content (magic bytes), not extension
5. ClamAV scan on uploads
6. Path traversal prevention
7. SSRF prevention in URL handlers
8. Audit log: every state-changing action → signed log entry
9. Dependabot config for weekly updates
10. CI security workflow: pip-audit, trivy, semgrep
11. Penetration test report via zap-cli

## 5. VERIFICATION
```bash
$ python3 -m pytest tests/security/ -v
EXPECT: ≥15 passed

$ python3 scripts/security_audit.py
EXPECT: prints scan results, no critical findings

$ python3 -c "from src.auth.security import create_token, verify_token; t = create_token({'sub':'test'}); p = verify_token(t); assert p['sub'] == 'test'"
EXPECT: no AssertionError

$ pip-audit
EXPECT: no high/critical vulnerabilities

# Manual penetration test results
$ test -f docs/security_pentest.md
EXPECT: exit 0
```

## 6. ACCEPTANCE CRITERIA
- [ ] OWASP Top 10 audit: all addressed
- [ ] pip-audit: 0 high/critical
- [ ] Trivy scan on Docker image: 0 high/critical
- [ ] semgrep: 0 high findings
- [ ] Rate limiting enforced per user
- [ ] Audit log captures all auth + state changes
- [ ] Coverage ≥85% on auth code
- [ ] Penetration test report exists with remediations

## 7. CONSTRAINTS
- All imports `src.` prefix
- Secrets ONLY via env vars
- Never log credentials, tokens, or PII
- HTTPS-only in production (TLS via reverse proxy)
- Session cookies: HttpOnly, Secure, SameSite=Strict

## 8. DEPENDENCIES
- **Blocked by:** C1 (uses Redis + PostgreSQL)
- **Blocks:** C4 (multi-tenancy needs auth)
- **Parallel-safe with:** C3, C5

## 9. GOTCHAS
- JWT secret rotation: support multiple valid signing keys for graceful rotation
- ClamAV: install in Docker image, signature update via cron
- Path traversal: use `pathlib.Path.resolve()` and check it stays in allowed dir
- Audit log integrity: HMAC-sign each entry, separate from app log
- Dependabot can churn PRs — set group strategy
- zap-cli requires Docker; document the scan command
