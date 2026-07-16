#!/usr/bin/env python3
"""Convert verified annotations to BIOES train/val/test splits.

Usage:
    python3 scripts/convert_to_bioes.py [--output-dir data/annotations] [--dry-run]

Reads all verified annotations from data/annotations/verified/,
splits 70/15/15 (deterministic via hash of doc_id), and writes
bioes_train.json, bioes_val.json, bioes_test.json.

HARD ASSERT: no SWA document (matching swa_\\d+ or 0\\d_\\w+) may appear
in train or val.  The 10 SWA enquiries are held-out for final evaluation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

VERIFIED_DIR = Path("data/annotations/verified")
DEFAULT_OUTPUT_DIR = Path("data/annotations")

# Doc IDs that must NEVER appear in train or val.
HELD_OUT_PATTERNS = [
    re.compile(r"^swa_\d+"),
    re.compile(r"^0\d_\w+"),
    re.compile(r"^\d{2}_\w+"),  # e.g. 01_gsecl, 04_adani
]


def _is_held_out(doc_id: str) -> bool:
    """Check if a doc_id belongs to the held-out SWA set."""
    return any(p.match(doc_id) for p in HELD_OUT_PATTERNS)


def _is_swa_sacred(ann: dict) -> bool:
    """Strict held-out check: doc_id pattern OR provenance mentions swa_enquiries.

    The 10 SWA enquiries (sacred gold) must never enter train or val splits,
    even if doc_id was altered.
    """
    doc_id = ann.get("doc_id", "") or ""
    if _is_held_out(doc_id):
        return True
    # Check source_file, metadata, provenance for sacred origin
    src = str(ann.get("source_file", "") or "")
    meta = ann.get("metadata", {}) or {}
    prov = str(meta.get("provenance", "") or "")
    source_hint = str(meta.get("source", "") or "")
    return any("swa_enquiries" in s or "/swa_enquiries/" in s for s in (src, prov, source_hint, str(ann)))


def _deterministic_split(doc_id: str, train_frac: float = 0.70, val_frac: float = 0.15) -> str:
    """Deterministic split based on hash of doc_id."""
    h = int(hashlib.sha256(doc_id.encode()).hexdigest(), 16)
    r = (h % 1000) / 1000.0
    if r < train_frac:
        return "train"
    elif r < train_frac + val_frac:
        return "val"
    return "test"


def load_verified_annotations(directory: Path) -> list[dict]:
    """Load all verified annotation JSONs."""
    annotations: list[dict] = []
    if not directory.exists():
        return annotations
    for path in sorted(directory.glob("*.json")):
        with open(path) as f:
            data = json.load(f)
            # Ensure required fields
            if "tokens" in data and "ner_tags" in data:
                annotations.append(data)
    return annotations


def split_annotations(annotations: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Split annotations into train/val/test with held-out enforcement."""
    train: list[dict] = []
    val: list[dict] = []
    test: list[dict] = []

    for ann in annotations:
        doc_id = ann.get("doc_id", "")
        split = _deterministic_split(doc_id)

        # Force held-out docs into test (STRICT: use provenance-aware check)
        if _is_swa_sacred(ann) or _is_held_out(doc_id):
            split = "test"

        if split == "train":
            train.append(ann)
        elif split == "val":
            val.append(ann)
        else:
            test.append(ann)

    return train, val, test


def assert_no_held_out_in_train_val(train: list[dict], val: list[dict]) -> None:
    """Hard assert that no held-out docs leak into train or val.

    Uses strict _is_swa_sacred check so the 10 SWA sacred enquiries
    (and any with swa_enquiries provenance) NEVER enter train splits.
    """
    offenders: list[str] = []
    for ann in train + val:
        doc_id = ann.get("doc_id", "")
        if _is_swa_sacred(ann) or _is_held_out(doc_id):
            offenders.append(doc_id)
    if offenders:
        raise AssertionError(
            f"HELD-OUT VIOLATION: {len(offenders)} SWA doc(s) found in train/val: {', '.join(offenders)}"
        )


def write_bioes_split(annotations: list[dict], output_path: Path) -> None:
    """Write annotations in BIOES list format."""
    records = []
    for ann in annotations:
        record = {
            "doc_id": ann.get("doc_id", ""),
            "source_file": ann.get("source_file", ""),
            "tokens": ann["tokens"],
            "ner_tags": ann["ner_tags"],
            "entities": ann.get("entities", []),
            "relations": ann.get("relations", []),
            "metadata": ann.get("metadata", {}),
        }
        records.append(record)
    with open(output_path, "w") as f:
        json.dump(records, f, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert verified annotations to BIOES splits")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Print stats without writing files")
    args = parser.parse_args()

    print("Loading verified annotations...")
    annotations = load_verified_annotations(VERIFIED_DIR)
    print(f"  Found {len(annotations)} verified annotation(s)")

    train, val, test = split_annotations(annotations)

    print("\nSplit (before held-out enforcement):")
    print(f"  Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

    # Hard assert - always run so --dry-run prints the assertion line even with 0 verified
    try:
        assert_no_held_out_in_train_val(train, val)
        print("  ✓ Held-out assert passed: no SWA docs in train/val")
    except AssertionError as e:
        print(f"  ✗ {e}")
        return 1

    if not annotations:
        print("No verified annotations to convert.")
        return 0

    if args.dry_run:
        print("\nDRY RUN — no files written.")
        print(f"  Would write {len(train)} records to bioes_train.json")
        print(f"  Would write {len(val)} records to bioes_val.json")
        print(f"  Would write {len(test)} records to bioes_test.json")
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_bioes_split(train, args.output_dir / "bioes_train.json")
    write_bioes_split(val, args.output_dir / "bioes_val.json")
    write_bioes_split(test, args.output_dir / "bioes_test.json")

    print(f"\n✓ Written to {args.output_dir}:")
    print(f"  bioes_train.json: {len(train)} docs")
    print(f"  bioes_val.json:   {len(val)} docs")
    print(f"  bioes_test.json:  {len(test)} docs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
