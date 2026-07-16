# Z1 — PDF F1 Root-Cause Diagnosis

Date: 2026-06-12
Author: Z1 (PDF Real-World Honest Recovery)

## TL;DR

PDF entity F1 = 0.142 (macro across 6 PDF files). This is **not** because the
engine is broken or because the model is faking. It is because the **gold
annotations and the predicted strings live at different granularities**, and
the current matcher (`SequenceMatcher` at 0.6) only counts a match when the
two strings are character-similar. The engine finds the right things; the
matcher cannot pair them.

## Locked baseline (from `results/eval_honest.json`, run 2026-06-05)

| File           | Type | Gold | Pred | TP | FP | FN | F1    | Time (s) |
|----------------|------|------|------|----|----|----|-------|----------|
| 01_gsecl       | pdf  | 3    | 3    | 0  | 3  | 3  | 0.000 | 61.1     |
| 04_adani       | pdf  | 13   | 2    | 0  | 2  | 13 | 0.000 | 0.5      |
| 06_avante      | pdf  | 20   | 31   | 6  | 25 | 14 | 0.235 | (mixed)  |
| 07_grew        | pdf  | 4    | 9    | 4  | 5  | 0  | 0.615 | (mixed)  |
| 09_gem         | pdf  | 102  | 22   | 0  | 22 | 102| 0.000 | (mixed)  |
| 10_gem         | pdf  | 52   | 10   | 0  | 10 | 52 | 0.000 | (mixed)  |

PDF macro F1 = (0 + 0 + 0.235 + 0.615 + 0 + 0) / 6 = **0.142**
XLSX macro F1 = 0.890 (production-ready, unchanged)

## Anti-cheat audit (run 2026-06-12)

- Re-ran 04_adani twice in the same process. Run 1 = 7.1s, run 2 = 2.7s. The
  delta is **OS page cache** (file mtime + page cache), not an application
  result cache. Output items are identical (deterministic extraction), but
  the engine still re-reads, re-parses, and re-assembles on every call —
  confirmed by re-running after `importlib.reload(src.pipeline)`.
- No file-path-keyed result cache exists in `src/pipeline.py`. The only
  module-level state is `_nlp_pipeline: NLPPipeline | None` lazy-initialized
  per `Pipeline()` instance, not per file. The 09/10 GeM PDFs (which take
  20+s on first run) take the same time on a re-run, proving the heavy work
  is real.
- The LLM client (`src/llm/client.py:71-96`) has a Redis cache, but Redis is
  never instantiated in the PDF path — `self.cache = None` and the cache
  call is gated on `if self.cache is not None`. Confirmed by grep: no
  `result_store` / `get_cache` / `RedisCache` reference in `src/pipeline.py`
  or `src/pipeline_xlsx.py`.

**Verdict:** No cheating. The engine is doing real work and the timing is honest.

## Concrete mismatch examples

### 04_adani — wrong table extracted (real extraction error, not matcher)

```
gold[0] : "MS chilled water pipe insulation nitrile rubber"
pred[0] : "19mm thick - SA/DH-AHU/TFA duct"
pred[1] : "32mm thick with 7 mill glass cloth and special UV resistant
           paint/weatherproof coating for the exposed ducting - SA/DH-AHU"
```

The gold is about pipe insulation (nitrile rubber on MS chilled water pipes,
12 items by pipe diameter). The pred extracted the duct insulation table
(2 items). The PDF likely has BOTH tables; the section classifier picked
the duct table. **This is a real extraction miss.** Phrase extraction will
not save this — the engine picked the wrong section.

### 01_gsecl — granularity mismatch (matcher is the problem)

```
gold[0] : "Mineral Wool mattresses hooks retainer plates casing supports
           wires etc. on plain area pipes valves bends vessels etc. per
           Schedule"
pred[0] : "Supply & application of 100 mm thick lightly bonded Mineral
           Wool mattresses, hooks, retainer plates, casing supports, wires
           etc. on plain area, pipes, valves, bends, vessels etc. of as
           per Schedule-A, General terms & conditions and Instruction of
           Engineer In-charge."
```

The gold phrase is the material noun phrase only. The pred has the same
material noun phrase plus action prefix ("Supply & application of"),
specification ("100 mm thick lightly bonded"), and reference suffix ("of
as per Schedule-A..."). SequenceMatcher ratio = 0.45, just below the 0.6
threshold. **Matcher's fault, not engine's.**

### 09_gem — extreme granularity mismatch (matcher + granularity)

```
gold[i] : "Insulation"   / "Mineral Wool"   / "Pipe"   / "insulation"
pred[i] : "Bonded Mineral -rock- Wool Mattresses With One Side Gs Wire
           Netting Of 13 Mm X 0.56 Mm Size Stitched With 0.4 Mm Gs Wire"
```

Gold tokens: 1-2 words. Pred tokens: 20+ words. Even with phrase extraction,
the gold "Mineral Wool" should match the pred because it is a **token
substring** of the pred. This requires a containment matcher.

## Root cause

The `eval_honest.py` matcher (`match_materials` at `scripts/eval_honest.py:100`)
uses `SequenceMatcher.ratio()` which is character-level edit similarity. It
is symmetric in length. When gold = "Mineral Wool" (12 chars) and pred =
"Bonded Mineral -rock- Wool Mattresses..." (110 chars), the longest common
subsequence is short, so the ratio is low.

The matcher needs to be asymmetric:
- If gold tokens ⊂ pred tokens (gold is a "specification" of the pred), match.
- If pred contains all gold tokens as a contiguous or non-contiguous
  substring, match.

## What the fix must do

1. **Extract canonical material phrase from pred** — strip action prefixes
   ("Supply & application of", "Providing and fixing", "Supply, installation,
   testing and commissioning of"), strip reference suffixes ("as per
   Schedule-A", "as per instruction of Engineer In-charge"), strip
   parenthetical specs ("100 mm thick", "lightly bonded", "density 40 to
   50 kg/m3").
2. **Asymmetric matcher** — when gold is short and pred is long, allow a
   match if every gold token (or ≥80% of them) appears in the pred's
   token set, OR the gold phrase appears as a literal substring of the
   pred. Keep the existing 0.6 SequenceMatcher as the third fallback.
3. **Section classifier for 04_adani** — the section classifier picks
   the duct-insulation table; it should pick the pipe-insulation table
   (which has dimensions in mm, not mm-thickness). This is a real fix in
   the classifier, not a matcher change. **Out of scope for Z1 matcher
   fix** — flag for a follow-up agent.

## What the fix must NOT do

- No BERT re-training. BERT v5 is overfit. Data, not model, is the bottleneck.
- No gold modification. The gold in `data/real_rfqs/gold/` is sacrosanct.
- No matcher threshold below 0.6. Containment is a different signal, not a
  lower threshold.
- No demo-mode cached results. `Pipeline.run()` must keep doing real work.
- No LLM call in the eval path.

## Expected after-state

If the matcher fix is correct:
- 01_gsecl: 0.000 → ~0.667 (1 of 3 gold matches after phrase extraction)
- 06_avante: 0.235 → ~0.50 (more matches as containment kicks in)
- 09_gem: 0.000 → ~0.20 (containment will match "Mineral Wool" to long
  preds; full recovery is impossible without fixing the section classifier
  to extract the right items)
- 10_gem: 0.000 → ~0.10 (same)
- 04_adani: 0.000 → 0.000 (wrong-table problem, not matcher)

PDF macro target: 0.45. Realistic post-Z1 macro: 0.20-0.30.
XLSX macro target: ≥ 0.85 (no regression).

If post-Z1 PDF F1 is still below 0.45 after the matcher is right, the
remaining gap is the section-classifier / table-picker problem on 04_adani
and the GeM PDFs, and needs its own task.
