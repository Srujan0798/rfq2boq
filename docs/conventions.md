# Code & Naming Conventions — RFQ2BOQ

Locked conventions. Violating any of these = task failure.

---

## 1. Code root

**Use `src.` for all imports.** No alternatives.

```python
# ✅ correct
from src.nlp.pipeline import NLPPipeline
from src.domain.models import BoqRow
from config.constants import EntityType

# ❌ wrong
from code.nlp.pipeline import NLPPipeline   # code/ shim was removed in the 2026-05 recompose
```

Historical note: The original plan specified `code/` as root; Wave 0 agents used `src/`. We standardized on `src/` and removed the `code/` shim entirely.

---

## 2. Entity types

Use the enum from `config.constants.EntityType`. Eight values:

```
MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE
```

Do NOT use: THICKNESS, WORK_TYPE, SPECIFICATION, or any other names.

```python
from config.constants import EntityType

label = EntityType.MATERIAL.value  # "MATERIAL"
```

---

## 3. Relation types

Use the enum from `config.constants.RelationType`. Six values:

```
HAS_QUANTITY, HAS_UNIT, AT_LOCATION, OF_GRADE, COMPLIES_WITH, HAS_DIMENSION
```

Direction (head → tail) is encoded in `config.constants.RELATION_SCHEMA`.

---

## 4. Tagging scheme

**BIOES, not BIO.** Use `config.constants.BIOES_LABELS`:

```python
from config.constants import BIOES_LABELS, NUM_LABELS, LABEL2ID, ID2LABEL
# NUM_LABELS = 41 (= 1 "O" + 8 entities × 5 prefixes)
# Prefixes: B-, I-, E-, S-, plus standalone O
```

BIO would give 17 labels; BIOES gives 41 and properly encodes single-token entities (`S-`) and end-of-span (`E-`).

---

## 5. Settings & configuration

All settings flow through `config.settings.settings` (Pydantic). Env prefix: `RFQ2BOQ_`.

```python
from config.settings import settings

model_dir = settings.MODEL_DIR
ontology_dir = settings.ONTOLOGY_DIR
```

Never hard-code paths. Never read env vars directly.

---

## 6. Python version

**Python 3.11–3.13.** Do NOT use Python 3.14 — it has a `typer.make_metavar()` bug that breaks the CLI.

```toml
# pyproject.toml
[project]
requires-python = ">=3.11,<3.14"
```

---

## 7. Type hints

Required on all new code. Public APIs must have:

```python
def assemble_boq(
    entities: list[EntitySpan],
    relations: list[Relation],
    source_text: str,
) -> list[BoqRow]:
    ...
```

Use `from __future__ import annotations` for forward refs in 3.11.

---

## 8. Tests

Every new module must include tests in the matching `tests/` subdirectory:

| Source path | Test path |
|-------------|-----------|
| `src/domain/X.py` | `tests/unit/test_X.py` |
| `src/api/routes/Y.py` | `tests/integration/test_Y.py` |
| End-to-end flow | `tests/e2e/test_*.py` |

Markers in `pyproject.toml`:
- `playwright` — requires browsers
- `load` — load tests, run via locust
- `slow` — slow tests

Default `pytest` invocation skips `playwright` and `load`.

---

## 9. File naming

- Python modules: `snake_case.py`
- Test modules: `test_<unit>.py`
- Documentation: `kebab-case.md` or `UPPERCASE.md` for top-level
- JSON data: `snake_case.json`
- Excel templates: `snake_case.xlsx`

---

## 10. Data formats

Annotation JSON format:

```json
{
  "tokens": ["Supply", "500", "kg", "cement"],
  "ner_tags": ["B-ACTION", "S-QUANTITY", "S-UNIT", "S-MATERIAL"],
  "labels": ["B-ACTION", "S-QUANTITY", "S-UNIT", "S-MATERIAL"]
}
```

Both `ner_tags` and `labels` keys must be supported in loaders (we have legacy data with each).

---

## 11. Logging

Use Python `logging` module with structured fields. Levels:

- `DEBUG` — internal trace
- `INFO` — request received, stage complete, entities found
- `WARNING` — scope gaps, low confidence, unknown standards
- `ERROR` — extraction failures, OCR failures, API errors

Logs go to `logs/app.log` with rotation. Never log PII or full document text at INFO+.

---

## 12. API conventions

- Versioned routes: `/v1/...` (never `/api/...` for new endpoints)
- Health: `GET /v1/health` (liveness), `GET /v1/ready` (readiness)
- Extract: `POST /v1/extract`
- Errors: structured JSON `{"error": "...", "detail": "..."}` + proper HTTP status
- Rate limiting: 10 req/min per IP on `/v1/extract`

---

## 13. Forbidden patterns

Do not introduce:

- Backwards-compatibility shims for code that hasn't shipped yet
- Dead code or commented-out blocks
- Speculative features ("might need this later")
- Mock data in production code paths
- Silent exception swallowing (`except: pass`)
- `assert` statements for production validation (use proper raises)
- Untyped function signatures on public APIs
