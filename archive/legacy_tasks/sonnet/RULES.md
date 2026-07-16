# RULES — read before every task. Violating any = stop, report, revert.

This project has **6 documented cheating incidents** by prior agents (fake model metrics, harness monkey-patch, validator self-comparison, gold-file poisoning, dishonest handoff rewrite, circular silver-training + log spam). You are being verified against all of them.

## Absolute prohibitions
1. **Never train on machine labels.** Silver/pseudo/auto-generated annotations are drafts for human review ONLY. The `RFQ2BOQ_ALLOW_SILVER` env path gets DELETED in T6; until then never set it.
2. **Never edit gold, source-truth counts, or thresholds to make a number pass.** Gold changes belong to Srujan alone, with provenance to the source page/cell.
3. **Never grade the pipeline against its own output.** Gold and source counts come from the source document + human eyes.
4. **Never write `if filename == ...` logic, per-file thresholds, or caches keyed to input names.**
5. **Never claim ~100% correctness on held-out data.** If you see it, you broke something — investigate, don't celebrate. (100% *capture-or-flag fidelity* per doc against frozen source truth is the legitimate target.)
6. **Never touch `resources/`** (sacred, read-only), `data/real_rfqs/swa_enquiries/` (restore from git if damaged, never regenerate), or the frozen TEST split (no training, no mining, no tuning on it).
7. **Never mark your own task CLOSED.** You mark READY FOR VERIFICATION; orchestrator/owner closes after re-running your commands.
8. **One ledger entry per real action** with date + command + stdout excerpt + commit. Duplicate/no-evidence entries auto-revoke the task.

## Fidelity definition (per document, no exceptions)
PASS = `captured + flagged == source_truth AND dropped == 0 AND over_capture == 0`. No aggregate netting across documents. Over-capture is a FAIL, not "fuller capture."

## Engineering constants
- Branch `phase8-clean-slate` only. No new branches.
- Imports `src.` prefix; entities/relations from `config.constants` (8 entities, 6 relations, BIOES — LOCKED); settings via `config.settings.settings`.
- Python 3.11–3.13 (`.venv` is 3.12). MPS not CUDA. Type hints on new code. Tests in matching `tests/` subdir.
- Unpriced BOQ only — no Rate/Amount/cost columns anywhere.
- Verify gate: `make verify` (tests + lint + anti-cheat) must be green before READY FOR VERIFICATION.

## REPORT format (end of every task)
```
## REPORT: [Task ID]
Deliverables: [path — created/modified]
Verification: [each command + real output excerpt]
Numbers: [every metric produced, verbatim]
Blockers: [none / list]
Deviations: [none / list]
Outside-spec edits: [none / list]
```
