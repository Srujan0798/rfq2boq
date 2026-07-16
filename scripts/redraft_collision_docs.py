"""P2_03 helper: re-draft specific TRAIN docs and save with unique doc_ids.

Background: the macOS APFS default is case-insensitive, so a doc with the
literal filename "BOQ.pdf" (→ doc_id "BOQ") and a doc with the literal
filename "boq.pdf" (→ doc_id "boq") collide on disk (the second write
overwrites the first). The same applies to "Insulation.xlsx" (doc_id
"Insulation") vs "INSULATION.pdf" (doc_id "INSULATION") on a case-insensitive
volume. The factory's _safe_doc_id does not lowercase, so the case difference
is preserved in the doc_id, but not in the on-disk filename.

This script re-drafts the docs whose files were lost to case-insensitive
collisions and writes them with source_batch-prefixed doc_ids (so the queue
can be regenerated deterministically).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import annotation_factory as af  # noqa: E402

DRAFTS_DIR = af.DRAFTS_DIR


def main() -> int:
    manifest = af._load_manifest()
    split = af._load_split()
    train_paths = set(split["train"]["all_paths"])

    # The two collisions we need to recover:
    # - "data/specifications/Specification 2/INSULATION.pdf" (lost, overwritten by Insulation.xlsx)
    # - "data/specifications/Specifications/BOQ.pdf" (lost, overwritten by boq.pdf)
    targets = [
        "data/specifications/Specification 2/INSULATION.pdf",
        "data/specifications/Specifications/BOQ.pdf",
    ]

    for path in targets:
        entry = next((e for e in manifest["files"] if e["path"] == path), None)
        if entry is None:
            print(f"NOT IN MANIFEST: {path}")
            continue
        if path not in train_paths:
            print(f"NOT IN TRAIN SPLIT (refusing): {path}")
            continue
        if af._is_test_split(path, split):
            print(f"REFUSED (TEST): {path}")
            return 2

        record = af._draft_one_doc(entry)
        if record["n_sentences"] == 0:
            print(f"  {record['doc_id']}: 0 sentences (skipping write)")
            continue

        # Add a source_batch prefix to make the doc_id unique
        batch = record.get("source_batch", "unknown")
        # Sanitize batch
        batch_safe = batch.replace(":", "_").replace("/", "_")
        record["doc_id"] = f"{batch_safe}__{record['doc_id']}"
        out_path = DRAFTS_DIR / f"{record['doc_id']}.draft.json"
        if out_path.exists():
            print(f"  {record['doc_id']}: already exists at {out_path.name}; leaving as-is")
            continue
        out_path.write_text(json.dumps(record, indent=2, ensure_ascii=False))
        print(
            f"  {record['doc_id']}: {record['n_sentences']} sentences, {record['n_entities_total']} entities -> {out_path.name}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
