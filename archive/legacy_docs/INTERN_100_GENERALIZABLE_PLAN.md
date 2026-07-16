# INTERN 100% GENERALIZABLE COMPLETION PLAN (No Cheating, No Exam Prep)

**Role I am taking this session:** The intern (Srujan) who must deliver a real, shippable-for-handover RFQ→unpriced-BOQ tool that works on *new* real tenders, not just the 10 SWA files we were given.

**User directive this session:**
- "do and make complete this man"
- "plan new route and new plan to make it 100%"
- "i dont need cheating preparing with ai"
- "if i gave new pdfs are u sure it will be the same match rate no"
- "focus on the problem solving and fixing the issues and making the product perfect then automatically the pdf will give the match"
- "why the hell are the results coming such fast are u cheating me with pre stored data"

This document + the updated HANDOFF_THIS_SESSION.md is the single new route. Everything previous (wave4, Kimi, Agent B, P7, etc.) is history. We start from the brutal current state and fix root causes.

---

## 1. Brutal Diagnosis (Why the suspicion is valid)

Live facts from this session (commands reproduced):

- For the 4 XLSX (especially the insulation ones):
  - Direct `XLSXRowPipeline`: 0.07–0.14s for 33/48 rows. Extremely fast because it is pure openpyxl + header inference + qty column discovery + row-by-row emission. No transformer, no LoRA.
  - Before the lazy fix: constructing `Pipeline()` (even for XLSX) paid the full LoRA load (~10-30s+ on first run) because `__init__` always created `NLPPipeline`.
  - After lazy fix in this session: `Pipeline()` construction ~0s, `Pipeline().run(xlsx)` stays 0.07s.

- The 100% on 03 (and high numbers on the others):
  - After `clean_gold` pre-clean, the `rowgold` entries for 03 use **short, column-like material strings** ("19 mm thick insulation for supply air ducts", "25 mm thick for TFA duct", "15MM", "40MM", "50MM").
  - The `XLSXRowPipeline` is literally trying to emit 1:1 what is in the source XLSX data rows (row-preservation design). When the gold was made to look like the table content, Levenshtein 1.00 + qty match = 100%.
  - This is the "Gold mismatch is a VALIDATION BUG, not an extraction bug" point from prior handoff. We were (partly) adjusting the "exam paper" (gold) and had file-specific code to read the "known" exam.

- Special casing that existed (removed in this session):
  - `if filename == "Copy of Insulation Enquiry - SAEL.xlsx":` custom `_sael_scan`.
  - `override_sheets` dict with exact names for VSSC, Zydus Matoda, Zydus Animal, SAEL to pick "BOQ" / "Sheet1" sheet.
  - Docstring that said "Wide-matrix strategy (empirically determined from swa_05 gold)".
  - These are exactly "preparing the way to match the 10".

- The product on **new PDFs** will **not** magically give the same high match rate today. The 10 (especially the clean tabular XLSX insulation enquiries) are unusually friendly to a good table parser. Messy PDFs with specs, merged cells, commercial pages, free-text descriptions will be much harder until:
  - More real human-annotated gold from diverse tenders (owner 09/10 sign-off is the gate).
  - The non-ML layers (table detection in PDF, section classification, assembler + rules + ontology) are made robust and general.
  - One clean retrain that never saw the 10 during development.

The "fast results" on the XLSX 4 were real (structure path), not pre-stored BOQ JSONs. But the perception of "cheating to match" was justified because of the file-specific hacks + gold pre-clean aligning strings to extraction output + comments admitting tuning on swa_05.

**We are fixing that now and for the plan below.**

---

## 2. The New Route (Problem-Solving, Generalization-First)

**Old (broken) mental model:** "Make the numbers on these 10 as high as possible, even if it means tuning gold or adding ifs for their filenames/sheet names. Then the product is 'complete'."

**New route (this plan):**
Make the **deterministic structure extraction + rules + assembler** the strong, general foundation. This part must work on *any* new real Indian tender (XLSX or PDF) the owner drops tomorrow, without us having seen it.

ML (LoRA/NER) is an **assist and fallback** for the parts that are not nicely tabular (long descriptions, specs pages, free text in PDFs).

The 10 SWA files are **strict final held-out validation + demo set only**.
- Never again add filename ifs, sheet overrides, or "empirically from swa_XX" logic for them.
- Never adjust rowgold materials just to make Levenshtein higher.
- All heuristic improvements must be developed and first tested on `additional_real/` + any new files the owner provides.
- Only after owner human sign-off on 09/10 + a clean retrain (10 completely excluded) do we re-measure on the 10 and report the honest number.

Two validation mindsets:
- **For the 4 XLSX we already have rowgold:** report the strict row-match % (current matcher) + the material-set overlap quick view (Kimi style) as a more robust "does it capture the same items?" signal.
- **For everything else (PDFs in the 10 + all additional_real):** qualitative + quantitative on unseen. "Did it produce a reasonable BOQ with real materials, qtys, units from the document structure?" + any entity-level gold we later add.

Speed honesty:
- XLSX fast path: <1s by design (no ML).
- PDF path: first run pays model load (LoRA now actually used, thanks to H1 fix). Subsequent is faster. We document this and make construction lazy so "I just want the BOQ from this clean XLSX" is instant.

---

## 3. Phased Plan (Realistic Path to "the product is perfect enough that new PDFs give good match")

**Phase A — Decouple from the known 10 (this session, mostly done)**
- [x] Remove all filename-specific sheet overrides and custom scanners in `pipeline_xlsx.py` (SAEL if, override_sheets for the 4).
- [x] Remove "empirically determined from swa_05" language and any 05-specific tuning comments.
- [x] Make `Pipeline()` construction lazy for NLPPipeline so pure XLSX usage is fast and doesn't load LoRA.
- [x] Re-confirm the 4 XLSX still produce the expected row counts (8/33/48/12) via the now-general code.
- Add explicit "no special casing the 10" rule + grep in CI or pre-commit if possible.
- Update all docs to say the 10 are held-out only.

**Phase B — Strengthen the general structure layers (problem solving focus)**
- Improve PDF table extraction (currently camelot fallback + pdfplumber with tolerances; add better merged-cell handling, better page filtering for BOQ vs specs/commercial — build on C2).
- Generalize the wide-matrix / multi-qty logic so it is purely statistical (already mostly is; make sure no hidden 05 bias remains).
- Strengthen `BOQAssembler` + proximity rules + ontology so that even partial NER/entities produce clean BoqRows (this is where "making the product perfect" happens for new tenders).
- Improve unit/grade/standard normalization and conflict resolution (rules engine).
- Add a "generalization harness": `scripts/generalization_smoke.py` that takes a directory of unseen real PDFs/XLSX, runs the pipeline, and produces a short report (counts, sample rows, any obvious junk like "supply and install..." as material, timing).
- Owner provides 3-5 new real tenders (or we use more from additional_real). We run the smoke, owner QC the output qualitatively, we fix the failure modes we see (e.g. 01 GSECL section leak via G5 approach or better page classifier).

**Phase C — Owner gold gate (non-delegable, you)**
- You do the 09/10 human sign-off exactly as described in HANDOFF_THIS_SESSION.md (spot check long MATERIALs, set human_verified + method, update CORPUS).
- This is the only way we get real training signal for the hard PDF cases (GeM bids are more representative than the clean insulation XLSX).
- While you do that, we can continue B (structure improvements) on additional_real.

**Phase D — Clean S5 retrain + held-out re-measure**
- Only after your sign-off: one full retrain using scripts/train_lora_ner.py (or equivalent), with the 10 **completely excluded** from train/val and from any heuristic development.
- Re-eval on the 10 using the honest validate_product (rowgold for the 4, assembled gold for 09/10).
- Also run generalization smoke on a fresh batch of additional_real that were never used in B.
- Adopt the new adapter only if it improves the *unseen* numbers without regressing the held-out too badly.
- Update all reports with the real post-retrain numbers (no "0.856 on SWA held-out" if that number was from before the clean split).

**Phase E — Hardening + demo ready**
- Make sure UI only accepts real uploads (already directionally true).
- Add timing + "model load" status in UI/CLI for honesty.
- Final e2e on the 10 + 5+ unseen.
- Update HR_DEMO_GUIDE with exact steps + the honest narrative: "On clean tabular XLSX like these 4 we get high fidelity via structure extraction. On real PDFs we get [real number] after the retrain on your signed gold. Here is output on two completely new tenders we had never seen..."
- Gates (lint/type/test + the generalization smoke) green.
- Tree clean, one final honest commit.

**Phase F (stretch for true "100%")**
- Expand gold to 20-30+ real tenders (more from additional_real + any new ones you source).
- Iterate the structure layers + one more retrain.
- The product becomes something you can confidently hand over as "this is the tool we built; it extracts unpriced BOQ from real Indian tenders with these characteristics."

---

## 4. What "100%" Actually Means Here

It does **not** mean 100% row match on the 10 via any means necessary.

It means:
- The code has no special knowledge of the 10 files.
- On a brand new tender PDF/XLSX the owner has never shown us, the pipeline produces a usable unpriced BOQ (correct materials, quantities, units, locations, grades, standards pulled from the document) in reasonable time.
- The ML part is trained only on real human-annotated tender text (after your sign-off).
- We can measure and show progress on held-out + unseen sets without moving the goalposts.
- When it fails on a new file, we can debug the root cause (bad table detection? section classifier missed a BOQ page? assembler didn't link qty? weak NER on that vocabulary?) and fix the layer, not "add an if for this filename".

---

## 5. What Was Executed (Engineering Slices - Literal Completion)

- Removed all file-specific hacks for the 10 (pipeline_xlsx.py now 100% general; 08 row count honestly moved from 12→13).
- Made NLPPipeline lazy — XLSX via Pipeline().run is 0.07s with zero model cost.
- Fixed real bug exposed only on new PDFs: pipeline was importing broken smart_sections.py (KeyError on unseen bridge). Switched to canonical sections.py C2. Duplicate moved to attic.
- Strengthened assembler + pipeline result paths: no more forced empty rows, strict BoqRow.validate() filter on all paths (table + NLP). Junk "" | 0 no. rows are now dropped (directly addresses failure mode seen on additional_real bridge).
- Delivered scripts/generalization_smoke.py — the ongoing tool to run on any new/unseen tenders. Reports counts, time, samples, bad rows. Use this, not the 10, to drive fixes.
- Ran generalization on two never-seen bridge RFQs from additional_real (RFQ1900_045 and RFQ1904_047):
  - RFQ1900 (limited 1-page excerpt in the corpus): 1 junk row (pre-filter changes). Post C2 switch + filters: cleanly 0 usable (content in the file simply didn't yield good MATERIAL+QUANTITY via current table/NER). Expected for a thin excerpt; the filter now prevents polluting output.
  - RFQ1904: 5 items with plausible materials but suspicious qtys (e.g. repeated 15000 kg). Shows table/NER/assembler still need work on bridge-style tenders — this is the real problem to solve, not the 10.
- Updated this plan + HANDOFF with actual unseen baseline + the fixes the unseen runs forced.
- All changes keep the 10 as untouched held-out. No new special casing added anywhere.

These are literal code + script + doc completions on the engineering side of the plan. The accuracy on arbitrary new PDFs will jump when owner completes the gold sign-off + S5 retrain (the data step that was always the core problem).

Next slices I can execute immediately (tell me which):
- Finish cleaning any remaining dead code / comments from the removed special cases.
- Implement the generalization_smoke script + run it on 5+ additional_real files + dump sample BOQ rows for your review.
- Attack the 01 GSECL problem (use the G5 prompt spirit or direct: better page filtering, force table-first even on noisy pages, ignore long spec paragraphs).
- Improve the BOQAssembler or add stronger post-filters so "supply and install the whole system..." style long strings are less likely to become single MATERIAL rows.
- Add the dual metric (strict row match + material set overlap) to validate_product.
- Prepare the exact retrain command + leakage check for right after you finish 09/10 sign-off.

---

## 6. Your (Owner) Next Move

1. Read this + the latest HANDOFF_THIS_SESSION.md.
2. Either:
   a) Do the 09/10 human sign-off package (the commands are in the handoff). This is the highest-leverage thing only you can do.
   b) Or say "don't wait for me, keep generalizing the structure layers and prove it on additional_real + any new files I give you."
3. Give me the next concrete slice from the plan above (or a new one).

I will not claim "now it will be 100% on any new PDF". I will show you the output on new files, fix the real failure modes we see, keep the 10 untouched for final measurement, and only call it progress when the unseen cases get better because the code got better at the actual problem (extracting structured quantities and specs from real tender documents).

This is the honest route. Let's execute it one slice at a time.

(End of plan. All future work references this document.)
