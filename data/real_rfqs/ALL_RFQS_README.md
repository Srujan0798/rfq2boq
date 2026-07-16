# ALL 127 REAL RFQs — the master index. READ THIS FIRST.

**If you are an agent working on this project: the RFQ corpus is 127 real documents, not 10.**
Every prior agent that scoped fidelity/training/testing work to only the 10 SWA enquiries was wrong.
Fixed 2026-07-05 after the owner caught this exact mistake being repeated across sessions.

## See every real RFQ in one place

`data/real_rfqs/ALL_RFQS/` contains a symlink to every one of the 127 real documents this project has,
named `<source_batch>__<original filename>` so you can `ls` one folder and see everything:

```
ls data/real_rfqs/ALL_RFQS/    # 127 symlinks, zero duplication, originals untouched
```

Symlinks point back to the real files in their original locations — nothing was moved, copied, or renamed.
Regenerate this folder any time with the manifest (see bottom of this file).

## Where the 127 actually live

| Source | Path | Count | Role |
|---|---|---|---|
| Sacred 10 enquiries | `data/real_rfqs/swa_enquiries/` | 19 | **Frozen TEST anchor** — never trained on, never mined for gazetteer terms |
| Specifications batch 1 | `data/specifications/Specifications/` | 50 | TRAIN/DEV pool |
| Specification 2 batch | `data/specifications/Specification 2/` | 41 | TRAIN/DEV pool |
| Email enquiry bundles | `data/specifications/*` (Grew/SAEL/AVANTE/Adani/Zydus) | 14 | Origin docs of the sacred-10 gold |
| Extracted from `resources/Specifications.rar` | `data/specifications/rar_extra/` | 3 | TRAIN/DEV pool (net-new after de-dup) |
| **TOTAL** | | **127** | |

## By document type

- `boq_bearing` (33): has an actual line-item table — these matter for fidelity + row-gold
- `spec_only` (78): prose specification, no BOQ table — usable for NER sentence gold
- `non_training` (16): make-lists, GCC annexures, prebid queries — not training material

## Governing documents

- `data/real_rfqs/corpus_manifest.json` — machine-readable, all 127, sha256 + classification
- `data/real_rfqs/split_test.json` — frozen TRAIN/DEV/TEST split (42 test / 15 dev / 70 train)
- `data/real_rfqs/CORPUS.md` — detail on the sacred-10 TEST subset specifically
- `tasks/sonnet/00_START_HERE.md` §CORPUS, `docs/CORPUS_DEFINITION.md` — the scope statement for agents

## Regenerate this folder

```python
import json; from pathlib import Path
m = json.load(open('data/real_rfqs/corpus_manifest.json'))
d = Path('data/real_rfqs/ALL_RFQS'); d.mkdir(exist_ok=True)
for f in m['files']:
    src = Path(f['path']).resolve()
    link = d / f"{f['source_batch'].replace(':','_')}__{src.name}"
    if not link.exists(): link.symlink_to(src)
```
