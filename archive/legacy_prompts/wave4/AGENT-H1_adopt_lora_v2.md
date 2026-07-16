# TASK: Adopt LoRA v2 as Production Default NER — Agent-H1

## 1. GOAL
Wire the trained LoRA v2 adapter (models/rfq2boq-ner-lora-v2/, F1 0.856 on real SWA held-out) as the default NER in production NLPPipeline so that the product stops using the broken rfq2boq-ner-final (real F1 0.000) and immediately benefits from the only working ML model. This is the single biggest lever to move product match rate from ~32% toward ~75%+ on the 10 SWA enquiries.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/nlp/pipeline.py` — the NLPPipeline._init_ner and load methods (current priority, LoRA detection, _load_lora_ner).
- `src/nlp/ner/lora_adapter.py` — LoRANERAdapter.load and is_available.
- `models/rfq2boq-ner-lora-v2/README.md` and adapter_config.json — confirm it is a valid adapter and what base it expects.
- `src/pipeline.py` — how the main Pipeline wires NLPPipeline (ner_enabled etc).

Current state:
- LoRA v2 dir exists with adapter_config.json + adapter_model.safetensors + checkpoints.
- NLPPipeline has full support for loading LoRA adapters (if adapter_config present) and _load_lora_ner.
- Default _init_ner priority is real-only-v2 → final (broken) → fallback. No hard-coded path to lora-v2 in the default branch.
- The "0.43 F1" numbers in old docs are synthetic or outdated; real prod NER on SWA data is 0.000 because the loaded model is broken (base_model mismatch).
- Pipeline falls back to regex + dictionary + assembler, which is why it "works" at all.
- UI and core are already unpriced (S1) and real-only (S2/S3).

## 3. DELIVERABLES
Create or modify EXACTLY these files:
- [ ] `src/nlp/pipeline.py` — in _init_ner, add explicit top-priority load of lora-v2 dir (adapter_config present → _resolve_base + _load_lora_ner).
- [ ] `prompts/wave4/AGENT-H1_adopt_lora_v2.md` — this prompt (self-documenting).
- [ ] `tests/unit/test_lora_v2_adoption.py` (new) — 4-6 tests: default load uses LoRA adapter, process() returns entities on real text, no crash on 03 Zydus Matoda, falls back gracefully if adapter missing.
- [ ] `docs/CORE_UNDERSTANDING.md` and `HANDOFF_FINAL_BRUTAL.md` (or main handoff) — one-line update: "Production default NER is now rfq2boq-ner-lora-v2 (F1 0.856)".
- [ ] `results/PROD_LORA_V2_ADOPTION.md` — short before/after: which model is loaded by default, sample entity count on 03, confirmation that 03 still works well.

## 4. STEPS
1. Read the context files in Section 2.
2. Run the current default load test to capture "before":
   ```bash
   python3 -c "
   from src.nlp.pipeline import NLPPipeline
   p = NLPPipeline()
   print('ner type:', type(p.ner).__name__ if p.ner else None)
   r = p.process('Supply 500 kg cement as per IS 456 M20 at ground floor')
   print('entities count:', len(r.entities))
   "
   ```
3. Edit `src/nlp/pipeline.py` _init_ner:
   - Right after `base_path = ...`
   - Add the lora-v2 block as top priority (before the real-only-v2 check):
     ```python
     lora_v2_dir = base_path / "models/rfq2boq-ner-lora-v2"
     if (lora_v2_dir / "adapter_config.json").exists():
         base = self._resolve_base_model(str(lora_v2_dir))
         self._load_lora_ner(base, str(lora_v2_dir))
         return
     ```
   - Update the priority comment to mention "lora-v2 (0.856) first".
4. Create `tests/unit/test_lora_v2_adoption.py` with tests that:
   - Default NLPPipeline() loads something whose type name contains "LoRA" or "Adapter".
   - process() on a simple construction sentence returns >=1 entity.
   - Running on the 03 Zydus Matoda XLSX (via main Pipeline) still produces the expected ~33 rows (no regression).
   - Graceful fallback if adapter dir is renamed (simulate by temp move or mock).
5. Update the two docs with one-sentence note about the new default.
6. Run all verification in Section 5.
7. Create the results/PROD_...md with the numbers from the verif run.

## 5. VERIFICATION
Run these commands in order. Each must succeed with the expected output.

```bash
# 1. Default load now uses LoRA v2 adapter
python3 -c "
from src.nlp.pipeline import NLPPipeline
p = NLPPipeline()
print('ner type:', type(p.ner).__name__ if p.ner else None)
assert 'LoRA' in type(p.ner).__name__ or 'Adapter' in type(p.ner).__name__ or hasattr(p.ner, 'adapter'), 'LoRA v2 not loaded as default ner'
print('✓ LoRA v2 is the default ner')
r = p.process('Supply 500 kg cement as per IS 456 M20 grade at ground floor')
print('entities:', len(r.entities))
assert len(r.entities) > 0
"

# 2. End-to-end on a real SWA file still works (use 03 which is strong)
python3 -c "
from src.pipeline import Pipeline
p = Pipeline()
r = p.run('data/real_rfqs/swa_enquiries/03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx')
print('03 rows:', len(r.boq_items))
assert len(r.boq_items) >= 20, '03 extraction regressed after LoRA wiring'
print('✓ 03 still extracts reasonable BOQ')
"

# 3. Unit tests for the adoption
python3 -m pytest tests/unit/test_lora_v2_adoption.py -q --tb=short
EXPECT: 4-6 passed, 0 failed

# 4. No regressions on core tests
python3 -m pytest tests/unit/test_section_classifier.py tests/unit/test_table_extractor.py -q --tb=no
EXPECT: previously passing tests still pass

# 5. Lint
python3 -m ruff check src/nlp/pipeline.py tests/unit/test_lora_v2_adoption.py
EXPECT: All checks passed!

# 6. Document the adoption
cat results/PROD_LORA_V2_ADOPTION.md | head -20
EXPECT: contains "LoRA v2 now default", before/after model names, entity counts on 03, date.
```

## 6. ACCEPTANCE CRITERIA
ALL must be true:
- Default NLPPipeline() loads a LoRA/Adapter ner (not the pure final or lazy broken model).
- process() on construction text returns >0 entities.
- End-to-end on 03 Zydus Matoda XLSX produces >=20 items (no regression).
- New test file has ≥4 tests, all pass.
- ruff clean on changed files.
- Docs and results/ report updated with the adoption.
- The change is a one-screen diff that only touches the default priority in _init_ner + adds tests + docs.

## 7. CONSTRAINTS
- Only change the default load priority and add the minimal test/docs. Do not rewrite the whole NER stack.
- Keep the existing if model_dir: adapter detection and all fallbacks.
- Do not touch config/constants.py or any gold files.
- Python 3.11-3.13 syntax, type hints.
- The lora-v2 dir must remain the source of truth; do not copy weights.
- If adapter fails to load, fall back exactly as the existing _load_lora_ner does.

## 8. DEPENDENCIES
- Blocked by: S1 (unpriced), S2 (real-only), S3 (corpus locked) — already done.
- Blocks: Honest handover refresh (S6 / Priority 3) — numbers will improve once wired.
- Parallel-safe with: S4 (PDF section) and owner gold annotation (S5).
- Shared files: src/nlp/pipeline.py (the load logic); be careful not to conflict with any concurrent LoRA experiments.

## 9. GOTCHAS
- The lora-v2 adapter_config.json points to a base_model_name_or_path — _resolve_base_model already handles this and falls back to rfq2boq-ner-final if needed.
- Loading LoRA requires the LoRANERAdapter (already in src/nlp/ner/lora_adapter.py).
- MPS only on this hardware — the existing code already sets CUDA_VISIBLE_DEVICES="" and lets torch choose.
- After this change the "0.43 F1" / "0.000 F1" comments in old docs become even more misleading — the adoption note in CORE + handoff is mandatory.
- Do not claim "now 100%" — still rely on regex/assembler for full quality; this is the ML upgrade only.
- Test on a real SWA file (03 is the strongest) so you can show the before/after entity count in the report.

---

## End-of-task report format
When done, produce exactly:

```
## REPORT: Adopt LoRA v2 as Production Default NER — Agent-H1

Deliverables:
- src/nlp/pipeline.py — added lora-v2 top priority in _init_ner
- tests/unit/test_lora_v2_adoption.py — new (X passed)
- docs/CORE_UNDERSTANDING.md — one-line adoption note
- results/PROD_LORA_V2_ADOPTION.md — before/after numbers

Verification:
- pytest: X passed, 0 failed (new tests + no regression)
- ruff: clean
- Default ner is now LoRA/Adapter
- 03 extraction still >=20 items
- Pipeline on real XLSX/PDF works

Blockers encountered: [none]
Deviations from spec: [none]
Files modified outside spec: [none]
```

This unblocks the biggest lever (Task 1). The prompt for Task 2 (G5) already exists on disk. Owner still owns the gold sign-off for full S5.
