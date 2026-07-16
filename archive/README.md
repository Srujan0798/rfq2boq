# Archive — RFQ2BOQ Phase 9

This archive was created in P5_05 to keep full git history while cleaning up the repo root and active folders for SWA review. Nothing was deleted; every file here can be restored from git history if needed.

## Layout

- `legacy_root_docs/` — 8 superseded root-level handoff/plan docs from earlier project history
- `legacy_tasks/` — superseded task files/folders predating `tasks/phase9/`, including `NW*`, `TASK_*`, `lane_*`, `sonnet/`, and related execution plan/checklist docs
- `legacy_prompts/` — older or superseded prompt assets, including `wave4/` which was replaced by `tasks/phase9/` as the dispatch source of truth
- `legacy_docs/` — dated one-off operational/plan docs, wave notes, and status artifacts that are superseded by current docs (includes the former `docs/historical/`)
- `legacy_results/` — one-off dated reports and eval snapshots from earlier waves that are replaced by current `results/` outputs
- `legacy_prompts/` — older or superseded prompt assets, including `wave4/` and the former `prompts/archive/` (hybrid, out_of_scope, phase8, superseded, wave2, wave3)

## How to read a specific archive item

1. Check `archive/README.md` for the broad category.
2. Use `git log --` with the file path to see when it was archived and its history before that commit.
3. If an old doc refers to a path, check whether that successor path already exists in `CLAUDE.md`, `tasks/phase9/00_README.md`, or `HANDOFF.md`.

## Replaced by

| Legacy category | Current replacement |
|---|---|
| Superseded task files | `tasks/phase9/00_README.md` + numbered phase-9 task files |
| `prompts/wave4/` | `tasks/phase9/` dispatch |
| `docs/PHASE8_UNIFIED_TIMELINE_AND_FLOW.md` | `tasks/phase9/00_README.md` |
| `docs/wave_status.md` | `tasks/phase9/04_LEDGER.md` |
| `HANDOFF.md` variants | root `HANDOFF.md` |

For canonical current repo structure, see root `HANDOFF.md` and `CLAUDE.md`.

## legacy_results_2026-07
Intermediate eval dumps moved out of results/ during final closeout cleanup. See that folder README.
