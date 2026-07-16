#!/usr/bin/env python3
"""Check gold provenance: flag pipeline-derived gold, warn on self-comparison,
and reject any human_verified:true stamp that isn't a genuine owner sign-off.

Incident (2026-07-04): an agent stamped 19 files in data/annotations/verified/
with human_verified:true and a *fabricated* reviewer field reading like a
justification note ("owner (full corpus 100% goal - client resources)")
instead of an actual identity. All 19 were reverted by the orchestrator.
This checker now hard-fails on that exact pattern so it can never land again.

P0_02 (2026-07-06): added `verify_gold_lock()` — a sha256 manifest check of
every file under data/real_rfqs/gold/ against GOLD_LOCK.sha256. Any mismatch
(modified, added, or deleted file) is a hard failure with the offending path.
The lock is the foundation of Rule 3 (gold is owner-only): a checksum mismatch
after P0_02 means somebody touched gold without authorization.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

VALID_REVIEWERS = {"srujan"}

LOCK_FILENAME = "GOLD_LOCK.sha256"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_gold_lock(gold_root: Path) -> list[str]:
    """Verify every file under `gold_root` matches GOLD_LOCK.sha256.

    Returns a list of human-readable offending-path strings (empty = intact).
    Catches: missing lock file, modified files, deleted files, added files.
    Pure function — does not call sys.exit; the caller decides exit code.
    Tests use tmp_path fixtures so real gold is never touched.

    Lock lines may record paths either relative to `gold_root` (e.g.
    `rows/02_isro.rowgold.json`) or relative to the repo root (e.g.
    `data/real_rfqs/gold/rows/02_isro.rowgold.json`). Both forms are
    normalized to relative-to-gold_root before comparison.
    """
    offenders: list[str] = []
    lock_path = gold_root / LOCK_FILENAME
    if not lock_path.exists():
        offenders.append(f"{LOCK_FILENAME} missing at {lock_path}")
        return offenders

    gold_root_resolved = gold_root.resolve()
    locked: dict[str, str] = {}
    for raw in lock_path.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            offenders.append(f"{LOCK_FILENAME}: malformed line: {raw!r}")
            continue
        digest, rel = parts
        rel = rel.strip()
        p = Path(rel)
        if not p.is_absolute():
            try:
                p = p.resolve()
                if gold_root_resolved in p.parents or p == gold_root_resolved:
                    rel = str(p.relative_to(gold_root_resolved))
            except (ValueError, RuntimeError):
                pass
        locked[rel] = digest

    on_disk: dict[str, str] = {}
    for f in gold_root.rglob("*"):
        if not f.is_file():
            continue
        if f.name == LOCK_FILENAME:
            continue
        rel = str(f.relative_to(gold_root))
        on_disk[rel] = _sha256_file(f)

    for rel, digest in sorted(locked.items()):
        if rel not in on_disk:
            offenders.append(f"DELETED: {rel} (in lock, missing on disk)")
        elif on_disk[rel] != digest:
            offenders.append(f"MODIFIED: {rel} (lock={digest[:12]}.., disk={on_disk[rel][:12]}..)")

    for rel in sorted(set(on_disk) - set(locked)):
        offenders.append(f"ADDED: {rel} (on disk, not in lock)")

    return offenders


def main() -> int:
    """Run the full provenance + lock check. Returns process exit code."""
    exit_code = 0

    # --- 1. Row gold: pipeline-derived / self-comparison check (existing) ---
    gold_dir = Path("data/real_rfqs/gold/rows")
    if gold_dir.exists():
        n_pipeline = 0
        n_independent = 0
        for gf in sorted(gold_dir.glob("*.rowgold.json")):
            data = json.loads(gf.read_text())
            method = data.get("method", "")
            if "pdfplumber" in method.lower():
                n_pipeline += 1
                print(f'    \u26a0 {gf.name}: method="{method}" (SELF-COMPARE)')
            else:
                n_independent += 1
                print(f'    \u2713 {gf.name}: method="{method}" (independent)')

        print(f"    Gold: {n_independent} independent, {n_pipeline} pipeline-derived")

        if n_independent == 0 and n_pipeline > 0:
            print("FAIL: ALL gold is pipeline-derived (no independent gold)")
            exit_code = 1

        if n_pipeline > n_independent:
            print(
                f"    \u26a0 WARNING: {n_pipeline}/{n_pipeline + n_independent} gold files are pipeline-derived (self-comparison risk)"
            )
            print("    \u26a0 Action: convert PDF gold to independent (human annotation or non-pdfplumber extraction)")
    else:
        print("    (no gold directory)")

    # --- 2. Any human_verified:true anywhere must carry a real reviewer identity ---
    # Two distinct cases, deliberately treated differently:
    #   (a) reviewer field ABSENT  -> legacy record predating this convention (e.g. the
    #       original sacred-10 rowgold). WARN only; needs owner backfill, not an incident.
    #   (b) reviewer field PRESENT but not a valid owner identity -> an active attempt to
    #       fake sign-off (this is exactly what happened 2026-07-03: a fabricated string
    #       "owner (full corpus 100% goal - client resources)"). HARD FAIL.
    def _check_reviewer_stamps(base: Path) -> tuple[int, int]:
        legacy, forged = 0, 0
        if not base.exists():
            return 0, 0
        for f in sorted(base.glob("*.json")):
            try:
                data = json.loads(f.read_text())
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            docs = data if isinstance(data, list) else [data]
            for doc in docs:
                if not isinstance(doc, dict) or not doc.get("human_verified"):
                    continue
                if "reviewer" not in doc:
                    print(
                        f"    \u26a0 {f}: human_verified=true, no reviewer field (legacy \u2014 needs owner backfill)"
                    )
                    legacy += 1
                    continue
                reviewer = str(doc.get("reviewer", "")).strip().lower()
                if reviewer not in VALID_REVIEWERS:
                    print(
                        f'    \u2717 {f}: human_verified=true but reviewer="{doc.get("reviewer")}" is FORGED (not a valid owner identity)'
                    )
                    forged += 1
        return legacy, forged

    n_legacy = 0
    n_forged = 0
    for base in (Path("data/annotations/verified"), Path("data/real_rfqs/gold/rows")):
        lg, fg = _check_reviewer_stamps(base)
        n_legacy += lg
        n_forged += fg

    if n_legacy:
        print(
            f"    \u26a0 {n_legacy} legacy human_verified:true record(s) with no reviewer field \u2014 owner should backfill via T2, not a hard failure"
        )
    if n_forged:
        print(
            f"FAIL: {n_forged} human_verified:true record(s) carry a FORGED reviewer identity (valid: {sorted(VALID_REVIEWERS)})"
        )
        exit_code = 1
    if not n_legacy and not n_forged:
        print("    \u2713 All human_verified:true records carry a valid owner reviewer identity")

    # --- 3. Gold sha256 lock (P0_02): hard-fail on any mismatch ---
    gold_root = Path("data/real_rfqs/gold")
    lock_offenders = verify_gold_lock(gold_root) if gold_root.exists() else [f"gold root missing: {gold_root}"]
    if not lock_offenders:
        print(
            f"    \u2713 Gold lock INTACT ({sum(1 for f in gold_root.rglob('*') if f.is_file() and f.name != LOCK_FILENAME)} files verified) \u2014 data/real_rfqs/gold/{LOCK_FILENAME}"
        )
    else:
        print(f"FAIL: gold lock MISMATCH \u2014 {len(lock_offenders)} offending file(s):")
        for off in lock_offenders:
            print(f"    \u2717 {off}")
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
