# Expanded BIOES Training Data — Summary

**Generated:** 2026-07-05
**Script:** `scripts/generate_all_bioes_training.py`
**Output:** `data/annotations/expanded/training_sentences.json`

## Coverage

| Metric | Value |
|--------|-------|
| Total training sentences | 468 |
| Unique documents covered | 65 |
| Entity types (BIOES tags) | 29 |
| Sources merged | 6 |

## Source Contributions (after dedup)

| Source | Sentences | Description |
|--------|-----------|-------------|
| `batch_extractions` | 295 | Per-entry BIOES from 38 extracted JSONs (batch pipeline) |
| `batch_v2` | 199 | BOQ items from 26 alternate extraction pipeline files |
| `cli_drafts` | 295 | Previously generated draft BIOES (claude/sonnet pipeline) |
| `draft_from_rfqs` | 241 | RFQ pipeline draft BIOES |
| `verified_from_rowgold` | 0 | All 178 human-verified sentences were from sacred SWA docs — correctly excluded |
| `intake_drafts` | 44 | Intake pipeline draft annotations (1 per spec-only doc) |

Note: Sources overlap heavily (same docs processed by different pipelines). Dedup by tokens+tags fingerprint removed 606 duplicates from 1074 raw sentences.

## TEST Split Exclusion

**42 documents excluded** from the frozen TEST split:
- 19 sacred10 SWA enquiries in `data/real_rfqs/swa_enquiries/`
- 14 bundle duplicates (byte-identical to sacred10)
- 4 client-name carry-alongs (Adani/SAEL from spec2)
- 5 new spec2 picks

**427 sentences skipped** as sacred/TEST across all sources.

## Entity Distribution

| Tag | Count |
|-----|-------|
| O | 3,948 |
| S-MATERIAL | 4,166 |
| S-QUANTITY | 2,032 |
| S-UNIT | 1,456 |
| I-MATERIAL | 493 |
| B-MATERIAL | 455 |
| E-MATERIAL | 436 |
| S-ACTION | 353 |
| S-DIMENSION | 197 |
| S-LOCATION | 53 |
| S-GRADE | 32 |
| (other) | ~200 |

## Top Documents by Sentence Count

| Document | Sentences | Sources |
|----------|-----------|---------|
| BOQ_-_INSULATION | 78 | draft_rfq, batch_extraction |
| boq_insulation_xlsx | 48 | batch_v2 |
| BOQ | 41 | draft_rfq, batch_extraction |
| SWPL-MPL-GPVC-CAC2-HVAC-RFQ-10 | 31 | intake_draft, draft_rfq, batch_extraction |
| BOQ PAGE | 30 | batch_extraction |
| Copy of UBS_Hyderabad_Project_BOQ(1) | 20 | batch_extraction |
| insulation_xlsx | 18 | batch_v2 |
| insulation_medical | 16 | batch_v2 |
| BOQ_PAGE | 16 | intake_draft, draft_rfq |
| boq_page | 15 | batch_v2 |

## Quality Notes

1. **All sentences are machine-generated drafts** with `human_verified: false`. No human has reviewed them.
2. Tagging quality reflects the simple rule-based entity detector in `gen_annotation_drafts.py` — function words are frequently over-tagged as MATERIAL, and multi-token entities use mostly S- prefix instead of proper B/I/E sequences.
3. The 178 verified sentences from `verified_from_rowgold` are entirely from sacred SWA docs and correctly excluded from training data.
4. 44 spec-only docs each contribute 1 long BIOES sequence (all tokens concatenated), which provides minimal training signal.
5. The data is suitable for **initial training** of an NER model with the understanding that quality is limited. For production use, human review of all sentences is strongly recommended.

## Next Steps for Improved Coverage

1. Run the entity extraction pipeline on spec-only PDFs (78 docs currently with no BOQ extraction)
2. Add human-reviewed correction passes on the generated drafts
3. Convert `data/real_rfqs/extracted/` entity-level data to token-level BIOES (requires source text reconstruction)
4. Consider adding synthetic data from the 42 TEST docs for validation
