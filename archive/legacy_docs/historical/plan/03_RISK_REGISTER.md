# RISK REGISTER + REVERSE-ROLE SELF-ATTACK
## "What can fail, and how do we catch it before it ships?"

Severity: **P0** = blocks shipping · **P1** = degrades quality target · **P2** = causes maintenance pain

---

## TOP 14 RISKS

### R1 [P0] OCR collapses on poor scans
**Failure mode.** Photographed-then-printed-then-rescanned RFQs (common in Indian/MENA tenders) drop OCR confidence to ~0.5 and bleed garbage tokens into NER.
**Mitigation.** (a) Quality gate routes < 0.80 mean conf to manual review queue. (b) PaddleOCR alternative with stronger Asian-language support. (c) Deskew + denoise preprocessing.
**Detection signal.** `ingest.quality.ocr_conf` percentile per batch in CI; alarm if p50 drops.
**Owner.** A-1.

### R2 [P0] Cross-sentence relations missed
**Failure mode.** "The wall shall be 230 mm thick. It must use M20 concrete." — three relations span sentences. Sentence-level RE misses them.
**Mitigation.** PURE within ±3 sentences as default; Longformer-based doc-level RE for cases flagged by section detector.
**Detection signal.** Relation recall stratified by intra-/cross-sentence; gap > 0.10 triggers review.
**Owner.** A-2.

### R3 [P0] Hallucinated entities if any LLM is used as fallback
**Failure mode.** A generative model invents a material spec that isn't in the document; BOQ is contractually wrong; legal exposure (AEC Contracts ref).
**Mitigation.** No LLM in critical path. If used (annotation assist, retrieval), the rule-validator must approve every entity; un-approved entities are dropped with audit log.
**Detection signal.** `rule_validated == false` rate; CI fails if > 2% on golden set.
**Owner.** A-2 + A-4.

### R4 [P1] Unit ambiguity (m vs m² vs m³ vs mm)
**Failure mode.** "Brick masonry 1.5 m" — m³? m²? Wrong unit → wrong quantity → wrong cost by 100×.
**Mitigation.** Unit-grammar parser with context window; co-occurrence model (`brick masonry` ⇒ m³ prior 0.85); ambiguous cases tagged `UNIT_AMBIGUOUS` warning.
**Detection signal.** Confusion matrix on UNIT entity; ambiguity warnings per RFQ.
**Owner.** A-2.

### R5 [P1] Annotator drift / inconsistency
**Failure mode.** Annotators disagree on whether "RCC" is a MATERIAL or a composite of (CEMENT + STEEL + AGGREGATE).
**Mitigation.** Annotation guide (`docs/annotation_guide.md`) with 50+ adjudicated examples; Cohen's κ enforced ≥ 0.75 per batch; weekly calibration session.
**Detection signal.** κ trend per batch; per-annotator F1 on held-out gold.
**Owner.** A-2.

### R6 [P1] Quantity tables not detected
**Failure mode.** Scope-of-work tables in scanned PDFs are read as flat text, losing column→row associations.
**Mitigation.** LayoutParser table detector + PaddleOCR table recognition; cell-level extraction; fallback to bbox heuristics on regular grids.
**Detection signal.** % rows with `quantity` matched to `material` from same row; CI golden set check.
**Owner.** A-1.

### R7 [P1] Domain shift across geographies
**Failure mode.** Standards differ (IS vs BS vs ASTM); units differ (cum/cubic-metre/m³); slang differs.
**Mitigation.** Per-region config (`config/regions/`) with allowed standards list + unit dictionaries; corpus split sampled to cover regions.
**Detection signal.** Per-region F1; regression alert on region with weakest F1.
**Owner.** A-2 + A-3.

### R8 [P1] Scope omission missed
**Failure mode.** RFQ has 47 items, we extract 41 → 6 missing → contractor sues later (the exact AEC-Contracts risk).
**Mitigation.** Co-occurrence rules: every numbered list item must produce ≥1 BOQ row, else `SCOPE_GAP_WARNING`. Sectional coverage report shipped with every output.
**Detection signal.** % items in numbered lists with no extracted row; alarm > 5%.
**Owner.** A-2 + A-3.

### R9 [P2] Data licensing / privacy
**Failure mode.** Training corpus contains restricted government tenders that can't be redistributed.
**Mitigation.** License audit per source; public-only corpus shared in repo; private corpus referenced by URL + checksum, not bundled.
**Detection signal.** Pre-merge license check script.
**Owner.** A-4.

### R10 [P2] Dependency hell / version drift
**Failure mode.** PyTorch / Transformers minor releases break training script weeks before submission.
**Mitigation.** Pinned `pyproject.toml`; Docker image tag-locked; `uv.lock` committed; weekly dependabot review.
**Detection signal.** CI build break.
**Owner.** A-4.

### R11 [P2] Compute budget overrun
**Failure mode.** Fine-tuning BERT-large hits free-tier limits; experiments stall.
**Mitigation.** Default to BERT-base (110M); only try DeBERTa-v3-small if budget allows; use mixed precision; sweep on dev subset, not full set.
**Detection signal.** GPU-hours log per week.
**Owner.** A-2.

### R12 [P2] Schema drift between stages
**Failure mode.** NER updates change span format; downstream RE crashes.
**Mitigation.** Pydantic models for every inter-stage payload; schema version on every artifact; integration test on every PR.
**Detection signal.** Pydantic `ValidationError` count.
**Owner.** A-4.

### R13 [P2] Demo failure on mentor's machine
**Failure mode.** Docker version mismatch, port conflict, missing model files.
**Mitigation.** `make demo` runs entirely from a fresh clone; healthcheck endpoints; small bundled model for demo.
**Detection signal.** Cold-clone CI job (weekly).
**Owner.** A-4.

### R14 [P2] Documentation rots
**Failure mode.** Code changes; README claims a flag that no longer exists.
**Mitigation.** Examples in README are doctests (`pytest --doctest-modules`); architecture diagrams generated from code (`pylint` graph) where possible.
**Detection signal.** Doc-test CI step.
**Owner.** A-3.

---

## REVERSE-ROLE SELF-ATTACK (orchestrator wearing red-team hat)

### Q1. What did the plan miss?
- **Confidence calibration** — model "confidence" is uncalibrated softmax. Add temperature scaling on dev set so ≥0.9 means truly ≥90% precision.
- **Active learning loop** — review queue corrections should feed back into training; without it, the model never improves post-deploy. Added to Step 9 stretch.
- **Multi-language** — Indian RFQs mix English + Hindi/regional terms. Sentence-level lang-id + per-lang tokenizer required if corpus shows >5% non-English. Added test in Step 2 EDA.
- **PDF passwords / signed PDFs** — `pikepdf` step with password prompt + audit. Added to Step 3.

### Q2. Where is the design fragile?
- The **rule-vs-ML conflict policy** is the most opinionated decision and has no test until Step 5. Push to W4 a "rules sandbox" notebook so we can argue with data, not vibes.
- **Sentence segmentation in tables** — spaCy senter doesn't know tables exist. We hand sentences from the layout module, not the raw text. Make that an interface contract.

### Q3. Is this excellent or "good enough"?
A/A+ checklist:
- Reproducible from scratch in ≤ 10 min — **yes** (`make demo`).
- Hits all three target metrics — **planned** (eval gate in CI).
- Catches the exact failure the literature warns about (scope omission) — **yes** (R8 + SCOPE_GAP_WARNING).
- Could ship to a real estimator — **MVP yes**, with the review queue as the safety net.
- Defendable in a technical interview — **yes**: every architectural choice is grounded in either a cited paper or a failure mode in this register.

### Q4. What if we have to cut?
Priority of cuts (cut bottom first):
9. UI React app → swap to Jupyter `ipywidgets` review.
8. Longformer doc-level RE → keep PURE-only, accept R2 cost.
7. ifcOWL integration → custom CTO only.
6. Load tests → keep perf benchmark only.
5. CSV/JSON exporter → Excel only.
4. Annotator κ enforcement → single-annotator pilot.
3. NER+RE → NER only with hand-crafted relation rules.
2. BERT-CRF → spaCy custom NER only.
1. Custom training → off-the-shelf spaCy + heavy rules (graceful degradation).
**Never cut** Steps 1, 2, 3, 6, 7, 8, 9.

---

## P0 / P1 closure tracker

| ID | Sev | Status | Closed-by-week | Evidence |
|---|---|---|---|---|
| R1 | P0 | open | W3 | ingest CI test |
| R2 | P0 | open | W6 | RE eval report |
| R3 | P0 | open | W6 | validator coverage |
| R4 | P1 | open | W5 | unit-grammar tests |
| R5 | P1 | open | W4 | κ ≥ 0.75 |
| R6 | P1 | open | W3 | golden table test |
| R7 | P1 | open | W6 | per-region F1 |
| R8 | P1 | open | W6 | scope-gap test |
| R9–R14 | P2 | open | W8 | various |

---

**Verdict.** With these mitigations in place, the failure modes documented across the 10 references in the PDF are either prevented or detected. No silent failures remain on the critical path.
