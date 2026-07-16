#!/usr/bin/env python3
"""Verify sha256 of the frozen measurement/eval set against config/FROZEN_HASHES.sha256.

Frozen set (Rule 5): eval scripts, regression tests, constants, corpus manifest,
frozen split, and the gold lock. After P0_03 pins these, any implementation task
that edits one of them trips Gate 1 by design — only the orchestrator re-pins
hashes (documented manual command below).

A mismatch (modified / missing / extra file) is a hard failure (exit 1) with the
offending path printed. Re-pinning is a deliberate, logged action:

    # WARNING: re-pin ONLY after the orchestrator rules an edit legitimate.
    python3 scripts/check_frozen_hashes.py --pin

The manifest format is one `<sha256>  <path>` line per file, paths relative to
the repo root, sorted. The manifest file itself is excluded from its own set.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

LOCK_FILENAME = "FROZEN_HASHES.sha256"

# Files whose integrity guards the measurement system (Rule 5). Order is stable
# so the manifest is reproducible; tests/fixtures mirror this list.
FROZEN_PATHS: tuple[str, ...] = (
    "scripts/measure_fidelity.py",
    "scripts/fidelity_audit.py",
    "scripts/eval_honest_rows.py",
    "scripts/eval_ner.py",
    "scripts/check_gold_provenance.py",
    "scripts/check_eval_hacks.py",
    "scripts/check_split_leakage.py",
    "tests/regression/__init__.py",
    "tests/regression/test_combinations.py",
    "tests/regression/test_corpus_exact.py",
    "config/constants.py",
    "data/real_rfqs/corpus_manifest.json",
    "data/real_rfqs/split_test.json",
    "data/real_rfqs/source_truth.json",
    "data/real_rfqs/gold/GOLD_LOCK.sha256",
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def frozen_files(repo_root: Path) -> list[Path]:
    """Absolute paths of the frozen set that exist on disk."""
    return [repo_root / p for p in FROZEN_PATHS if (repo_root / p).exists()]


def verify_frozen_hashes(repo_root: Path, manifest_path: Path | None = None) -> list[str]:
    """Verify the frozen set against the manifest.

    Returns a list of human-readable offending-path strings (empty = intact).
    Catches: missing manifest, missing file, modified file, extra file in manifest.
    Pure function — does not call sys.exit; the caller decides the exit code.
    Tests pass a tmp `repo_root` and tmp `manifest_path` so no real file is touched.
    """
    offenders: list[str] = []
    if manifest_path is None:
        manifest_path = repo_root / "config" / LOCK_FILENAME
    if not manifest_path.exists():
        offenders.append(f"manifest missing: {manifest_path}")
        return offenders

    locked: dict[str, str] = {}
    for raw in manifest_path.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            offenders.append(f"manifest malformed line: {raw!r}")
            continue
        digest, rel = parts
        locked[rel.strip()] = digest

    for rel in FROZEN_PATHS:
        p = repo_root / rel
        if not p.exists():
            if rel in locked:
                offenders.append(f"MISSING: {rel} (in manifest, absent on disk)")
            else:
                offenders.append(f"MISSING: {rel} (frozen-set member not in manifest and not on disk)")
            continue
        disk = _sha256_file(p)
        if rel not in locked:
            offenders.append(f"UNPINNED: {rel} (on disk, not in manifest)")
        elif locked[rel] != disk:
            offenders.append(f"MODIFIED: {rel} (manifest={locked[rel][:12]}.., disk={disk[:12]}..)")

    for rel in sorted(set(locked) - set(FROZEN_PATHS)):
        offenders.append(f"EXTRA: {rel} (in manifest, not in frozen set)")

    return offenders


def pin_manifest(repo_root: Path, manifest_path: Path | None = None) -> int:
    """Regenerate the manifest from the on-disk frozen set."""
    if manifest_path is None:
        manifest_path = repo_root / "config" / LOCK_FILENAME
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for rel in FROZEN_PATHS:
        p = repo_root / rel
        if not p.exists():
            print(f"  WARN: frozen-set member missing, skipped: {rel}")
            continue
        lines.append(f"{_sha256_file(p)}  {rel}")
    manifest_path.write_text("\n".join(lines) + "\n")
    print(f"Pinned {len(lines)} files to {manifest_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--pin", action="store_true", help="Re-generate the manifest from on-disk files (orchestrator-only)"
    )
    parser.add_argument("--manifest", help="Override manifest path (for tests)")
    parser.add_argument("--repo-root", help="Override repo root (for tests)")
    args = parser.parse_args()

    repo_root = Path(args.repo_root) if args.repo_root else Path.cwd()
    manifest_path = Path(args.manifest) if args.manifest else (repo_root / "config" / LOCK_FILENAME)

    if args.pin:
        print(
            "WARNING: re-pinning frozen hashes — only the orchestrator does this, and only after ruling an edit legitimate."
        )
        return pin_manifest(repo_root, manifest_path)

    offenders = verify_frozen_hashes(repo_root, manifest_path)
    if not offenders:
        n = sum(1 for p in FROZEN_PATHS if (repo_root / p).exists())
        print(f"ALL FROZEN FILES INTACT ({n}/{len(FROZEN_PATHS)} verified) — {manifest_path}")
        return 0

    print(f"FAIL: frozen-hash mismatch — {len(offenders)} offending file(s):")
    for off in offenders:
        print(f"  \u2717 {off}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
