# TASK: C4 Multi-tenancy — Routes, Team Management, Billing, Tests

**Wave:** 4 | **Tier:** C | **Priority:** P2

## 1. GOAL

Complete the multi-tenancy implementation by adding: tenant API routes, team management, usage metering, quota enforcement, billing routes, and integration test.

## 2. CONTEXT

Files to read first:
- `src/db/tenant_manager.py` — existing Tenant, TenantManager, StripeBilling
- `src/api/main.py` — existing app entry point
- `src/api/schemas.py` — existing Pydantic schemas
- `src/billing/stripe.py` — existing StripeBilling
- `tests/integration/test_pipeline.py` — example integration test structure
- `pyproject.toml` — pytest configuration

## 3. DELIVERABLES

Exact paths to create/modify:
1. `src/auth/tenant.py` — tenant context extraction from JWT
2. `src/auth/teams.py` — team roles (Admin, Member, Viewer)
3. `src/billing/usage.py` — usage tracking (API calls, storage, compute)
4. `src/billing/limits.py` — quota limits enforcement
5. `src/api/routes/tenants.py` — CRUD endpoints for tenants
6. `src/api/routes/billing.py` — billing and usage endpoints
7. `tests/integration/test_multitenancy.py` — integration test

Also update:
- `src/api/main.py` — register tenant and billing routes
- `src/api/dependencies.py` — add `get_current_tenant` dependency

## 4. STEPS

1. **Create `src/auth/tenant.py`:**
   - `TenantContext` — dataclass with tenant_id, user_id, plan, limits
   - `get_current_tenant()` — FastAPI dependency that extracts tenant from JWT
   - `require_plan(min_plan: str)` — dependency to check plan level
   - `TenantPlan` enum: FREE, STARTER, PROFESSIONAL, ENTERPRISE

2. **Create `src/auth/teams.py`:**
   - `TeamRole` enum: ADMIN, MEMBER, VIEWER
   - `TeamMember` — dataclass: user_id, email, role, joined_at
   - `TeamManager` class: add_member, remove_member, update_role, list_members
   - `require_role(min_role: TeamRole)` — dependency to check role

3. **Create `src/billing/usage.py`:**
   - `UsageRecord` — dataclass: tenant_id, month, api_calls, storage_mb, compute_hours
   - `UsageTracker` class: record_api_call, record_storage, record_compute, get_usage
   - `get_usage_summary(tenant_id)` — returns current month usage and limits
   - Store usage in PostgreSQL `usage_tracking` table

4. **Create `src/billing/limits.py`:**
   - `PlanLimits` — dataclass: api_calls/month, storage_mb, max_users, model_access
   - `PLAN_LIMITS` dict: FREE=1000 calls, STARTER=10000, PROFESSIONAL=100000, ENTERPRISE=unlimited
   - `QuotaEnforcer` class: check_quota(tenant_id, resource) → bool
   - `enforce_quota(tenant_id, resource)` — raises HTTP 429 if exceeded

5. **Create `src/api/routes/tenants.py`:**
   - `GET /v1/tenants/me` — return current tenant info
   - `PUT /v1/tenants/me` — update tenant settings (name, plan)
   - `GET /v1/tenants/me/members` — list team members
   - `POST /v1/tenants/me/members` — invite team member
   - `DELETE /v1/tenants/me/members/{user_id}` — remove team member
   - `PUT /v1/tenants/me/members/{user_id}` — update member role

6. **Create `src/api/routes/billing.py`:**
   - `GET /v1/billing/usage` — current month usage summary
   - `GET /v1/billing/invoices` — list invoices from Stripe
   - `POST /v1/billing/upgrade` — upgrade plan
   - `POST /v1/billing/downgrade` — downgrade plan
   - `DELETE /v1/billing/cancel` — cancel subscription

7. **Create `tests/integration/test_multitenancy.py`:**
   - `TestTenantRoutes` — test CRUD on tenants
   - `TestTeamManagement` — test add/remove/update roles
   - `TestUsageTracking` — test recording and querying usage
   - `TestQuotaEnforcement` — test 429 response when quota exceeded
   - Use `fixtures/conftest.py` for tenant fixtures

8. **Update `src/api/dependencies.py`:**
   - Add `get_current_tenant` dependency
   - Add `get_current_user` dependency (reuse from existing auth)

9. **Update `src/api/main.py`:**
   - Register routers: `from src.api.routes import tenants, billing`
   - `app.include_router(tenants.router, prefix="/v1", tags=["tenants"])`
   - `app.include_router(billing.router, prefix="/v1", tags=["billing"])`

## 5. VERIFICATION

```bash
# Verify imports
python3 -c "from src.auth.tenant import get_current_tenant; print('OK')"
python3 -c "from src.auth.teams import TeamManager; print('OK')"
python3 -c "from src.billing.usage import UsageTracker; print('OK')"
python3 -c "from src.billing.limits import QuotaEnforcer; print('OK')"

# Verify routes
python3 -c "from src.api.routes import tenants, billing; print('OK')"

# Run integration tests (may need DB)
python3 -m pytest tests/integration/test_multitenancy.py -v --tb=short 2>&1 | head -50

# ruff check
ruff check src/auth/tenant.py src/auth/teams.py src/billing/usage.py src/billing/limits.py src/api/routes/tenants.py src/api/routes/billing.py tests/integration/test_multitenancy.py
```

## 6. ACCEPTANCE CRITERIA

- [ ] `src/auth/tenant.py` has TenantContext, get_current_tenant, require_plan
- [ ] `src/auth/teams.py` has TeamRole, TeamMember, TeamManager
- [ ] `src/billing/usage.py` has UsageTracker with record and query methods
- [ ] `src/billing/limits.py` has PLAN_LIMITS and QuotaEnforcer
- [ ] `src/api/routes/tenants.py` has all 5 CRUD endpoints (me, members)
- [ ] `src/api/routes/billing.py` has all 5 billing endpoints
- [ ] `tests/integration/test_multitenancy.py` exists with ≥15 tests
- [ ] All new files pass `ruff check`
- [ ] Routes registered in `src/api/main.py`

## 7. CONSTRAINTS

- Python 3.11–3.13 only
- Type hints required on all new code
- Use `src.` import prefix
- Do NOT modify existing auth logic — only add tenant context
- All tenant routes must validate tenant_id from JWT (not from request body)
- Stripe integration in billing routes should be mocked in tests

## 8. DEPENDENCIES

- Blocks: None
- Blocked by: C2 Security (uses JWT validation from middleware)

## 9. GOTCHAS

- Tenant isolation is critical — never trust tenant_id from request body, always from JWT
- Usage tracking should be non-blocking (async/background) to avoid adding latency to every API call
- Stripe webhook handling needs to verify signature (but can be mocked in tests)
- Team member invitation can send email (mock in tests, don't actually send)