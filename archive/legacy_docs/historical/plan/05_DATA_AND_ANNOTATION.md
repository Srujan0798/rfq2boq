# DATA + ANNOTATION PLAN
## Corpus, sources, splits, tooling, IAA, ethics

---

## A. CORPUS COMPOSITION (target n=200 RFQs)

| Stratum | Target n | Notes |
|---|---|---|
| Born-digital, English, Indian RFQs (CPWD, NHAI, GeM) | 80 | publicly available |
| Born-digital, English, EU TED | 40 | open data dump |
| Scanned PDFs (mixed quality) | 40 | older govt + private |
| Mixed-language (English + Indian regional) | 20 | edge case |
| Tiny / pathological (1 page, password, image-only) | 20 | stress / fuzz |

Of 200, **30 carry paired BOQs** = our gold ground truth for end-to-end eval.

---

## B. SPLITS

| Split | n | Use | Frozen? |
|---|---|---|---|
| train | 140 | model fitting | re-shuffles per run |
| dev   | 30  | hyperparams, early stop | seeded |
| test (hidden gold) | 30 | final report only, no peeking | **frozen** until W8 |

Within each split, stratify by source + scanned% so distribution holds.

---

## C. ANNOTATION PROCESS

1. **Pre-segmentation.** Run `ingest + preproc` to produce sentence-level units (~10k sentences).
2. **Pre-labeling.** Apply gazetteer + regex baselines to seed annotations (≥40% recall acceptable; annotators correct).
3. **Tool.** Label Studio (or doccano) self-hosted in dev container; JSON export.
4. **Roles.**
   - 2 primary annotators (interns / RAs)
   - 1 adjudicator (project lead = orchestrator)
5. **Cadence.** 5-doc batches per annotator per day; weekly κ calibration.
6. **IAA target.** Cohen's κ ≥ 0.75; below → calibrate, re-train, redo batch.
7. **Tracking.** annotations live in `data/annotations/` (jsonl); versioned by git LFS.

---

## D. ANNOTATION GUIDE (lives at `docs/annotation_guide.md`)

Contents (~25 pages):
1. Entity definitions (from `04_ENTITY_ONTOLOGY.md`)
2. 50 worked examples (positive + negative)
3. Tricky-case decisions (composite materials, abbreviations, multi-language)
4. Relation pairs — when to annotate, when to skip
5. Quality bar — when to flag for adjudication

---

## E. ETHICS / LICENSING

- All public-source RFQs retained with original URL + retrieval date.
- Private RFQs (if any) are not redistributed; only feature hashes stored.
- Annotators sign NDA for private data.
- Cohen's κ matrix + per-annotator F1 published in `data/IAA_report.md`.
- No personal data extracted; if PII (names, phone, email) appears in a doc, redact before training.
- License audit script `scripts/license_audit.py` runs in CI.

---

## F. SYNTHETIC DATA AUGMENTATION (optional, post-MVP)

If real corpus is under 100, augment via:
- Template-based generation from public BOQ templates → RFQ-style paraphrase
- Back-translation (English → Hindi → English) for paraphrase
- Replace materials / quantities / standards from registries; preserve structure

Synthetic data goes to `data/synthetic/` and is **never** mixed into test set.

---

## G. CORPUS HEALTH METRICS (computed weekly in EDA notebook)

| Metric | Target |
|---|---|
| Mean pages per doc | report only |
| % scanned | ≥ 20% |
| % English-only | ≥ 80% |
| Entity-tag density (entities/100 tokens) | ≥ 4 |
| Class-balance ratio (most/least common entity) | ≤ 20× |
| Train/test source overlap | 0 |

Imbalance fixes: oversample minority types in training; report per-type F1 always.

---

**Status:** Plan ready. Step 2 of execution kicks off corpus acquisition.
