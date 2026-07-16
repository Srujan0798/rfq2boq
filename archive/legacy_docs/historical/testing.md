# Testing

## Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Specific test directory
python3 -m pytest tests/unit -v
```

## Test Suite Layout

| Directory | Purpose | Run Time |
|-----------|---------|----------|
| `tests/unit/` | Unit tests for individual modules | ~10s |
| `tests/integration/` | API and pipeline integration tests | ~15s |
| `tests/golden/` | Tests against frozen ground truth examples | ~5s |
| `tests/fuzz/` | Property-based / random input tests | ~10s |
| `tests/e2e/` | Smoke test (full PDF → BOQ flow) | ~5s |

**Total runtime: ~45 seconds**

## What Was Archived

The following test suites were moved to `attic/tests/` because they were over-engineering for our current scale:

- `tests/property/` — Property-based tests (moved to attic)
- `tests/chaos/` — Chaos engineering tests (moved to attic)
- `tests/load/` — Load/stress tests (moved to attic)
- `tests/e2e/test_playwright*.py` — Playwright browser tests (moved to attic)

## Coverage Target

- Active code coverage: ≥80%
- Some archived code may reduce overall coverage slightly

## CI/CD

Tests run automatically on every push via `.github/workflows/ci.yml`:
- Lint (ruff)
- Type check (mypy)
- Unit + Integration + Golden + Fuzz tests
