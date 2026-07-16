# Wave Gotchas — Common pitfalls across Waves 2–5

Cross-cutting gotchas encoded from real agent failures in this project. Every wave prompt should cite the relevant ones in its Section 9. Maintain this file as the single source.

---

## Architecture

- **`src/` is canonical**; the `code/` package was removed in the 2026-05 recompose. Never re-introduce a `code/` shim.
- **Do NOT create `templates/`, `static/`, `bench/`, or `notebooks/` directories.** They were removed as dead clutter. The only top-level `templates`-flavored content lives inside `src/export/excel_templates.py` (a module, not a dir).
- **Do NOT create top-level `report/`, `slides/`, `paper/`, `patent/`, `plan/`, `resources/`.** All deliverables go under `deliverables/`. Historical specs go under `docs/historical/`.
- **All imports use `src.` prefix.** No `code.`, no `from src import` without subpath.

## ML / training

- **MPS available on this hardware, CUDA not.** Always use `torch.device("mps" if torch.backends.mps.is_available() else "cpu")`.
- **Synthetic F1 is inflated** (~99.6%) because synthetic templates overlap train/val/test. Real-world F1 is ~67%. Always report both honestly.
- **Tokenizers must be saved alongside model weights.** Loading a checkpoint without its tokenizer is a common bug.
- **Model files (`.pt`, `.bin`, `.onnx`, `.safetensors`) are gitignored.** Use Git LFS or external object storage for distribution.
- **`bert-base-cased`** is the English NER base. `xlm-roberta-base` is the bilingual (en+hi) base. `microsoft/layoutlmv3-base` is the layout-aware base.

## NLP / data

- **BIOES tagging** (not BIO). Use `config.constants.BIOES_LABELS` (41 labels: 1 `O` + 8 entities × 5 prefixes).
- **Entity types are fixed**: MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE. Never THICKNESS, WORK_TYPE, SPECIFICATION.
- **Relation types are fixed**: HAS_QUANTITY, HAS_UNIT, AT_LOCATION, OF_GRADE, COMPLIES_WITH, HAS_DIMENSION.
- **Annotation key drift**: `data/annotations/*.json` uses `ner_tags`; some loaders expect `labels`. Loaders must handle both keys.
- **Method name mismatches** found in past agent output:
  - Validator: `validate_boq` (current) vs `validate_result` (older); both should be supported during transition.
  - Confidence: `score_item` (current) vs `score_boq_item` (older); keep alias.
- **Ontology API**: `ConstructionOntology` class with `lookup_material`, `lookup_standard`, `validate_material_standard`, `get_default_unit`, `normalize_unit`. There is NO `.load()` method — Codex generated tests against this stale API once.

## Testing

- **Hypothesis `@st.composite`** requires `draw` as the first positional argument. Define strategies as `def my_strategy(draw): return draw(...)`.
- **Locust + gevent** monkey-patches on import; if pytest imports `tests/load/*` first, you get a `RecursionError`. Tests under `tests/load/` carry `pytestmark = pytest.mark.skip(reason="locust load tests run via locust CLI")` at module level.
- **Playwright** needs explicit `@pytest.mark.playwright` marker AND `playwright install chromium` before runs.
- **Python 3.14 typer/click bug** — `make_metavar()` is missing the `ctx` argument. Pin Python to 3.11–3.13.
- **Codex wrong-API tests** — before writing tests against an existing module, read the actual implementation. Do NOT assume signatures.

## Project conventions

- **Settings** flow through `config.settings.settings` (Pydantic). Env prefix `RFQ2BOQ_`.
- **API routes** versioned under `/v1/...`. Health: `GET /v1/health`. Extract: `POST /v1/extract`. Errors: `{"error", "detail"}` JSON.
- **Logging**: structured JSON, never log PII or full extraction text at INFO+.
- **Forbidden in production**: backwards-compat shims for unshipped code, dead code, speculative features, silent `except: pass`, `assert` for production validation.

## Path references (current canonical layout)

| Old / wrong | Current canonical |
|-------------|-------------------|
| `code/...` | `src/...` |
| `report/figures/` | `deliverables/report/figures/` |
| `paper/draft.tex` | `deliverables/paper/draft.tex` |
| `patent/contributions.md` | `deliverables/patent/contributions.md` |
| `slides/presentation.md` | `deliverables/slides/presentation.md` |
| `plan/` | `docs/historical/plan/` |
| `docs/agent-tasks/` | `docs/historical/agent-tasks/` |
| `resources/` | `docs/historical/research/` |
| `requirements.txt` | (deleted — use `pyproject.toml`) |
| `templates/` (root) | (deleted — never recreate) |
| `static/` (root) | (deleted — never recreate) |
| `bench/` (root) | (deleted — load tests live under `tests/load/`) |
| `notebooks/` (root) | (deleted — re-create only if actually using) |
| `__pycache__/`, `*.pyc`, `.DS_Store`, `.coverage` | (gitignored — never commit) |

## How to use this file in a task prompt

Cite the specific gotchas relevant to your task. For example, an NER training task adds:

> See `docs/WAVE_GOTCHAS.md` § ML/training (MPS device, synthetic F1 inflation, tokenizer saving) and § Path references.

Then in Section 9 (Gotchas), list the task-specific pitfalls beyond what's in this file.
