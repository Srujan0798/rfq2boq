# Contributing to RFQ2BOQ

## Code Style

### Tools

- **Ruff** for linting and formatting: `ruff check . && ruff format .`
- **mypy** for type checking: `mypy src/`
- Pre-commit hooks run automatically on commit

### Configuration

```toml
# pyproject.toml (ruff section)
[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = true
```

### Pre-commit Setup

```bash
pip install pre-commit
pre-commit install
```

## Type Annotations

All new code must use type hints:

```python
from typing import Optional

def process_text(text: str) -> dict[str, list[dict]]:
    ...
```

No `Any` except for truly unknown types.

## Test Requirements

- All new features must have unit tests
- All bug fixes must have regression tests
- Run: `pytest tests/ -v --tb=short`
- Target: 100% coverage for new modules

### Test Structure

```python
# tests/unit/test_new_module.py
import pytest

class TestNewModule:
    def test_basic_case(self):
        from src.new_module import process
        result = process("input")
        assert result == expected

    def test_edge_case(self):
        with pytest.raises(ValueError):
            process("invalid")
```

## PR Process

1. Create branch: `git checkout -b feat/description` or `fix/description`
2. Make changes with tests
3. Run linting: `ruff check . && ruff format .`
4. Run tests: `pytest tests/ -v --tb=short`
5. Commit: `git add . && git commit -m "feat: add new feature"`
6. Push: `git push origin feat/description`
7. Open PR, request review
8. After approval, merge to main

## Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feat/<short-description>` | `feat/add-hindi-support` |
| Bug fix | `fix/<short-description>` | `fix/entity-overlap-crf` |
| Documentation | `docs/<short-description>` | `docs/update-api-ref` |
| Refactor | `refactor/<short-description>` | `refactor/ontology-loader` |
| Experiment | `exp/<short-description>` | `exp/distilbert-small` |

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new entity type for electrical works
fix: correct quantity extraction for "500 nos" format
docs: update README with real-world F1 results
refactor: simplify pipeline initialization
test: add golden set for waterproofing cases
```

## Review Checklist

- [ ] Tests added for new functionality
- [ ] Type hints on all function signatures
- [ ] No `TODO` or `FIXME` left in code
- [ ] Documentation updated (if needed)
- [ ] Linting passes (`ruff check .`)
- [ ] All tests pass (`pytest`)

## Documentation Standards

- Docstrings for all public functions:

```python
def extract_entities(text: str, mats: dict) -> list[dict]:
    """Extract construction entities from RFQ text.

    Args:
        text: Raw RFQ text
        mats: Materials dictionary from ontology

    Returns:
        List of entity dicts with type, text, start, end, conf.

    Raises:
        ValueError: If text is empty.
    """
```

- Inline comments only when code is complex (prefer readable code over comments)
