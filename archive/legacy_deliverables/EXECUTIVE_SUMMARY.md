# RFQ2BOQ Executive Summary (S6 honest handover)

**Status (post S1-S6):** One focused NLP tool for real Indian construction tenders (10 SWA sacred held-out) → unpriced structured BOQ (Excel/JSON). All 10 process no crash. XLSX exact to user table (02=8, 03=33, 05=48, 08=12) via robust table/section. Honest metrics: ~32.3% row-level vs independent rowgold (XLSX); Kimi material overlap 73-100% fair view; PDF partial (S4 improved section/table for weak ones like 01). NER ~0.43 F1 real (synthetic misleading; real gold is fix per CORE). No pricing (S1), no demo/syn (S2/S3), corpus locked, gold pre-cleaned (09/10 owner sign-off pending S5), LoRA v2 wired as default (H1/A done, F1 0.856 potential).

**Scope (locked per CLAUDE + STEPs):** Extraction only. Unpriced BOQ (material/quantity/unit + dim/grade/standard/location/action). Real data only. Honest numbers (no 100%/self-gold; ~100% = red flag).

**Demo:** Lead with strong XLSX (03 Zydus Matoda 100% honest rowgold, 05/08/02). PDFs variable (04/06/07 human gold better post-S4; 01/09/10 weak/slow — pre-run only). Use ui/app.py (upload real from swa_enquiries/), scripts/final_integration_test.py, validate_product.py (honest).

**What's Next:** Owner 09/10 human review/sign-off (S5). Full real-gold retrain + honest head-to-head (adopt if > current on frozen test). Refresh artifacts if needed.

**Integrity:** All prior cheats (self-gold 100%, synthetic in train, etc.) caught/fixed. Resources/ sacred. 10 held-out.

Numbers trace to results/ + verifs (e.g. final_integration, validate --enquiry all, Kimi overlap). See HANDOFF_FINAL_BRUTAL.md, CORE_UNDERSTANDING.md, PHASE8_UNIFIED.
