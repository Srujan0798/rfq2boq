# Security Documentation

## Overview

RFQ2BOQ implements defense-in-depth security across all layers. This document covers authentication, rate limiting, audit logging, upload security, secret management, and API key scopes.

## Authentication

### JWT Configuration

JWT tokens are configured via environment variables:

- `JWT_SECRET` — Required for production. Must be at least 32 characters of cryptographically secure random data.
- If `JWT_SECRET` is not set, a development fallback is used (not suitable for production).

Token configuration:

- **Algorithm:** HS256
- **Access token expiry:** 30 minutes
- **Refresh token expiry:** 7 days

Token payload structure:

```python
@dataclass
class TokenPayload:
    sub: str          # user_id
    tenant_id: str | None
    exp: int          # expiration timestamp
    iat: int          # issued at timestamp
    role: str = "user"
```

### Multi-Factor Authentication (MFA)

TOTP-based MFA is supported via the `MFAGenerator` class:

- **Secret generation:** `MFAGenerator.generate_secret()` produces a base32-encoded secret
- **URI generation:** `MFAGenerator.get_totp_uri(secret, email, issuer)` creates an `otpauth://` URI for authenticator apps
- **Verification:** `MFAGenerator.verify_totp(secret, token, window=1)` validates tokens with a 1-window tolerance

MFA is enforced via `src.auth.middleware.JWTBearer` dependency in protected endpoints.

## Rate Limiting

Rate limiting operates at two levels:

### Application-Level (RateLimiter)

The `RateLimiter` class in `src.auth.security` supports Redis-backed or local-memory fallback:

- Default limits: 60 requests/minute, 1000 requests/hour, 10000 requests/day
- Redis keys: `ratelimit:{key}:{window}`
- Local fallback uses an in-memory dict when Redis is unavailable

### Middleware-Level (RateLimitMiddleware)

`src.auth.middleware.RateLimitMiddleware` applies per-tenant/user rate limiting:

- Default: 60 requests/minute, 1000 requests/hour
- Returns HTTP 429 with `Retry-After: 60` header when exceeded
- Excludes health and metrics endpoints

Configuration via environment:

- `RATE_LIMIT_PER_MINUTE` — requests per minute (default: 60)
- `RATE_LIMIT_PER_HOUR` — requests per hour (default: 1000)

## Audit Logging

The `AuditLogger` class in `src.auth.security` records security-relevant events:

```
logs/audit.log
```

Log entry format:

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "event": "event_type",
  "user_id": "user123",
  "tenant_id": "tenant1",
  "metadata": {}
}
```

Tracked events:

- `auth_failure` — failed authentication attempts (email + reason)
- `extraction` — document extraction jobs (user_id, job_id, doc)
- `export` — BOQ export operations (user_id, job_id, format)

## Upload Security

### UploadSandbox (`src.security.upload`)

All uploaded files pass through the `UploadSandbox` class which enforces:

### File Type Validation

Magic byte verification (not just extension):

| Type | Magic Bytes |
|------|-------------|
| PDF  | `%PDF` |
| PNG  | `\x89PNG\r\n\x1a\n` |
| JPG/JPEG | `\xff\xd8\xff` |
| GIF  | `GIF87a`, `GIF89a` |
| BMP  | `BM` |
| TIFF | `II\x2a\x00`, `MM\x00\x2a` |
| WebP | `RIFF` |
| ZIP/DOCX/XLSX | `PK\x03\x04` |

### File Size Limits

- Default maximum: 10MB
- Configurable via constructor: `UploadSandbox(max_size_mb=10)`

### Filename Sanitization

Prevents path traversal attacks:

- `sanitize_filename()` removes `..`, `/`, `\`, `://`, null bytes
- Basename extraction ensures no directory components
- Only alphanumeric, `.`, `_`, `-` allowed (others replaced with `_`)

## Secret Management

### Environment Variables

All secrets must be provided via environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `JWT_SECRET` | JWT signing secret (32+ chars) | Production: Yes |
| `REDIS_HOST` | Redis hostname | No (local fallback) |
| `REDIS_PORT` | Redis port | No (default: 6379) |
| `CORS_ORIGINS` | Comma-separated allowed origins | No (default: `*`) |
| `LOG_LEVEL` | Logging level | No (default: INFO) |

### .env File

Use `.env.example` as a template. Never commit `.env` files containing real secrets.

### Secret Rotation

- JWT secrets should be rotated every 90 days
- Audit logs track when tokens were issued to help identify affected sessions

## API Key Scopes

API key scopes control access to specific features:

| Scope | Description |
|-------|-------------|
| `boq:read` | Read BOQ data |
| `boq:write` | Create/modify BOQ data |
| `boq:export` | Export BOQ to formats |
| `extraction:read` | Read extraction results |
| `extraction:write` | Submit new extraction jobs |
| `admin` | Full administrative access |

Implemented via JWT `role` field in token payload.

## Tenant Isolation

Multi-tenancy is enforced via `TenantContextMiddleware`:

- Tenant ID extracted from JWT `tenant_id` claim
- Stored in `request.state.tenant_id`
- All data operations scoped to tenant via ORM/Neo4j queries

## OWASP Top 10 Alignment

| OWASP Category | Implementation |
|----------------|----------------|
| A01 Broken Access Control | JWT validation + tenant context middleware |
| A02 Cryptographic Failures | JWT with HS256, password hashing with PBKDF2-SHA256 |
| A03 Injection | Parameterized queries, sanitized filenames |
| A04 Insecure Design | Rate limiting, audit logging, upload sandboxing |
| A05 Security Misconfiguration | CORS policy, security headers, minimal error messages |
| A06 Vulnerable Components | pip-audit + dependabot + safety checks in CI |
| A07 Auth Failures | MFA support, failed auth logging, token expiry |
| A08 Data Integrity | Audit logs track all mutations |
| A09 Logging Failures | Structured JSON logging to dedicated audit log |
| A10 SSRF | URL validation in any outbound requests |

## Security Testing

See [security_pentest.md](security_pentest.md) for penetration testing procedures and remediation guidelines.

## Reporting Security Issues

Security vulnerabilities should be reported to the maintainer via the project issue tracker with the label `security`.