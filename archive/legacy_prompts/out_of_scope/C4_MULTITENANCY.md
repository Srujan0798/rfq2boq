# TASK: Multi-Tenancy & SaaS Features — Agent-4

**Wave:** 4 | **Tier:** C | **Priority:** P2

## 1. GOAL
Transform the system into a SaaS product: tenant isolation, per-tenant ontology customization, usage tracking, Stripe billing, team roles, tenant dashboard.

## 2. CONTEXT
Read first:
- `src/auth/security.py` — JWT auth from C2
- `src/db/postgres.py` — DB layer from C1
- `src/api/` — endpoints to scope by tenant
- [docs/conventions.md](../../../docs/conventions.md)

Current state: Single-tenant. No billing. No user management beyond basic auth.

## 3. DELIVERABLES
- [ ] `src/db/migrations/` — tenant tables migration
- [ ] `src/auth/tenant.py` — tenant model + RLS policies
- [ ] `src/auth/teams.py` — team roles (owner, admin, editor, viewer)
- [ ] `src/billing/__init__.py`
- [ ] `src/billing/stripe.py` — Stripe integration (plans, subscriptions, webhooks)
- [ ] `src/billing/usage.py` — usage metering
- [ ] `src/billing/limits.py` — quota enforcement
- [ ] `src/api/routes/tenants.py` — tenant CRUD
- [ ] `src/api/routes/billing.py` — billing endpoints
- [ ] `web/app/tenant/` — tenant dashboard pages
- [ ] `tests/integration/test_multitenancy.py` — ≥15 tests

## 4. STEPS
1. Add tenants, memberships, plans, usage, invoices tables
2. Row-level security policies in PostgreSQL: every query scoped by `tenant_id`
3. JWT extended with `tenant_id` claim
4. Plans: Free (10 docs/mo), Pro ($99 — 500 docs), Enterprise (custom)
5. Stripe Checkout for subscriptions, webhooks for status updates
6. Usage tracking: increment on every extraction
7. Quota enforcement: reject extraction if over limit
8. Team roles enforced via decorators
9. Tenant dashboard: usage stats, billing, team, API keys
10. Tests cover isolation, billing, quota

## 5. VERIFICATION
```bash
$ python3 -m pytest tests/integration/test_multitenancy.py -v
EXPECT: ≥15 passed

# Tenant isolation
$ python3 -c "
from src.auth.tenant import TenantService
t1 = TenantService.create('Tenant1')
t2 = TenantService.create('Tenant2')
# Create job in t1, verify t2 cannot read
assert True  # full test in test file
"
EXPECT: no AssertionError

$ curl -X POST http://localhost:8000/v1/tenants -H "Authorization: Bearer ADMIN_TOKEN" -d '{"name":"Test"}'
EXPECT: 201 Created with tenant id
```

## 6. ACCEPTANCE CRITERIA
- [ ] Tenant A cannot access tenant B's data (verified by integration test)
- [ ] Stripe webhooks update subscription state correctly
- [ ] Quota enforcement returns 429 when exceeded
- [ ] Team role permissions enforced (admin can invite, viewer cannot)
- [ ] Tenant dashboard renders usage stats
- [ ] Coverage ≥85% on new code

## 7. CONSTRAINTS
- All imports `src.` prefix
- Stripe keys ONLY from env
- Use Stripe test keys in dev
- Migration must be reversible
- Backwards compat: single-tenant mode still works if `RFQ2BOQ_MULTITENANT=false`

## 8. DEPENDENCIES
- **Blocked by:** C1 (PostgreSQL), C2 (auth)
- **Blocks:** None
- **Parallel-safe with:** C3, C5

## 9. GOTCHAS
- RLS policies in PostgreSQL must be enabled per table — easy to miss
- Stripe webhook signature verification: must use stripe-python SDK's `Webhook.construct_event`
- Usage metering: aggregate at query time, not write time (avoid race conditions)
- Free tier abuse: rate limit on signups, email verification required
- Test Stripe via their CLI: `stripe listen --forward-to localhost:8000/v1/billing/webhook`
