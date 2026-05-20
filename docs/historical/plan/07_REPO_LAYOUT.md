# REPOSITORY LAYOUT
## File-level structure with module responsibilities

```
rfq2boq/
├── README.md                       # quickstart + screenshots
├── LICENSE                          # MIT
├── pyproject.toml                   # uv/poetry; deps pinned
├── uv.lock                          # locked
├── Makefile                         # demo, test, lint, train, eval, docker
├── docker-compose.yml               # api + worker + ui + postgres
├── docker-compose.prod.yml          # prod variant
├── Dockerfile                       # multi-stage
├── .pre-commit-config.yaml
├── .github/
│   └── workflows/
│       ├── ci.yml                   # lint → type → test → build
│       └── eval.yml                 # weekly eval on dev set
│
├── plan/                            # this folder (specs that govern build)
│
├── docs/
│   ├── architecture.md
│   ├── annotation_guide.md
│   ├── api_reference.md             # auto from OpenAPI
│   ├── runbook.md
│   ├── adr/                         # architectural decision records
│   │   ├── 0001-bert-bilstm-crf-stack.md
│   │   ├── 0002-bioes-tagging.md
│   │   └── ...
│   └── model_card.md
│
├── code/
│   ├── ingest/
│   │   ├── pdf_parser.py            # pdfplumber wrapper
│   │   ├── ocr.py                   # tesseract + paddle
│   │   ├── layout.py                # layoutparser
│   │   └── quality_gate.py
│   ├── preproc/
│   │   ├── normalize.py
│   │   ├── sentence.py              # construction-aware tokenizer
│   │   └── sections.py
│   ├── models/
│   │   ├── ner/
│   │   │   ├── model.py             # BERT-BiLSTM-CRF
│   │   │   ├── dataset.py
│   │   │   ├── train.py
│   │   │   ├── eval.py
│   │   │   └── infer.py
│   │   ├── re/
│   │   │   ├── model.py             # PURE-style
│   │   │   ├── dataset.py
│   │   │   ├── train.py
│   │   │   └── infer.py
│   │   ├── baselines/
│   │   │   ├── gazetteer.py
│   │   │   ├── spacy_cnn.py
│   │   │   └── bert_linear.py
│   │   └── infer_pipeline.py
│   ├── rules/
│   │   ├── units.py
│   │   ├── standards.py
│   │   ├── scope_gap.py
│   │   ├── conflict.py
│   │   └── units_table.csv
│   ├── ontology/
│   │   ├── cto.ttl
│   │   ├── ifcOWL_subset.ttl
│   │   ├── mappings.yaml
│   │   └── resolver.py
│   ├── normalize/
│   │   ├── canonical.py
│   │   └── dedup.py
│   ├── export/
│   │   ├── excel.py
│   │   ├── csv.py
│   │   └── json.py
│   ├── api/
│   │   ├── main.py                  # FastAPI app
│   │   ├── routes/
│   │   │   ├── extract.py
│   │   │   ├── jobs.py
│   │   │   ├── review.py
│   │   │   └── ontology.py
│   │   ├── workers/
│   │   │   └── tasks.py             # RQ tasks
│   │   └── schemas.py               # Pydantic
│   ├── pipeline.py                  # Pipeline() — shared by api + CLI + batch
│   └── cli.py                       # `rfq2boq extract path/to.pdf -o out.xlsx`
│
├── ui/                              # React+Vite, minimal review UI
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│
├── data/
│   ├── raw/                         # original PDFs (git-LFS or external)
│   ├── interim/                     # ingest outputs (gitignored)
│   ├── processed/                   # ML-ready (gitignored)
│   ├── annotations/                 # label-studio export jsonl (git-LFS)
│   ├── gold/
│   │   └── golden_30.json           # frozen test set
│   ├── synthetic/                   # optional augmentation
│   └── IAA_report.md                # κ + per-annotator F1
│
├── models/                          # trained checkpoints (git-LFS)
│   ├── ner-bert-bilstm-crf-v1/
│   │   ├── config.json
│   │   ├── model.safetensors
│   │   ├── tokenizer/
│   │   └── eval_report.json
│   ├── re-pure-v1/
│   └── MODEL_CARD.md
│
├── schema/
│   ├── boq.v1.json                  # JSON Schema for canonical BOQ
│   └── boq.v1.example.json
│
├── templates/
│   └── boq_template.xlsx            # default output template
│
├── tests/
│   ├── unit/
│   │   ├── test_units.py
│   │   ├── test_standards.py
│   │   ├── test_canonical.py
│   │   └── ...
│   ├── integration/
│   │   ├── test_pipeline_e2e.py
│   │   └── ...
│   ├── golden/
│   │   ├── conftest.py
│   │   └── test_golden_30.py
│   ├── fuzz/
│   │   └── test_pdf_fuzz.py
│   └── load/
│       └── locustfile.py
│
├── bench/
│   ├── perf.py                      # pytest-benchmark
│   └── perf_history.csv
│
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_annotation_review.ipynb
│   ├── 03_baselines.ipynb
│   ├── 04_errors.ipynb
│   ├── 05_ablations.ipynb
│   └── 06_demo.ipynb
│
├── scripts/
│   ├── fetch_corpus.py
│   ├── train_ner.sh
│   ├── train_re.sh
│   ├── eval.py
│   ├── export_onnx.py
│   ├── license_audit.py
│   └── make_report.py
│
├── report/                          # final internship report (LaTeX or md→pdf)
│   ├── main.md
│   ├── results.md                   # auto-generated weekly
│   ├── figures/
│   └── refs.bib
│
└── slides/
    └── deck.pptx                    # 12-15 slides
```

---

## MODULE OWNERSHIP

- `ingest/`, `preproc/`, `data/` → Agent-1
- `models/`, `rules/`, `ontology/`, `notebooks/` → Agent-2
- `normalize/`, `export/`, `api/`, `ui/`, `templates/`, `schema/` → Agent-3
- `tests/`, `bench/`, `scripts/`, `.github/`, `docker*`, `Makefile` → Agent-4
- `plan/`, `docs/adr/`, `report/`, `slides/` → Orchestrator

---

## MAKEFILE TARGETS (frozen)

```makefile
make setup        # uv sync + pre-commit install + download models
make lint         # ruff + black --check
make type         # mypy
make test         # pytest -q
make test-cov     # pytest with coverage report
make train-ner    # scripts/train_ner.sh
make train-re     # scripts/train_re.sh
make eval         # scripts/eval.py --split dev --metrics all
make demo         # docker compose up; open browser; show sample RFQ → BOQ
make report       # scripts/make_report.py → report/main.pdf
make docker       # build prod image
make clean
```

---

**Status:** Layout ratified. Step 1 creates every empty file with a header comment so imports always resolve.
