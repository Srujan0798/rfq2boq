#!/usr/bin/env python3
"""Audit and quarantine contaminated/unvalidated model checkpoints.

Usage:
    python scripts/quarantine_contaminated_models.py              # dry-run (default)
    python scripts/quarantine_contaminated_models.py --execute    # actually move dirs
"""

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
QUARANTINE_DIR = MODELS_DIR / "quarantine"

# Classification table: (model_dir_name, classification, reason)
MODEL_CLASSIFICATIONS = [
    (
        "rfq2boq-ner-lora-cli",
        "CONTAMINATED",
        (
            "Trained on leaked test data (data/annotations/cli_training/ was deleted "
            "for TEST-set leakage). PID 88948 crashed at step 23/345 (epoch 1 of 15). "
            "Best eval F1: 9.36%. Unusable and contaminated."
        ),
    ),
    (
        "rfq2boq-ner-lora-real",
        "BROKEN",
        (
            "PID 6877 dead. Completed 5 epochs but eval F1 collapsed from 7.68% "
            "(epoch 2, checkpoint-46) to 0.0% (epochs 4-5). Only ~39 short docs "
            "after train/val split caused severe overfitting. Not usable."
        ),
    ),
    (
        "rfq2boq-ner-lora-swa10",
        "BROKEN",
        (
            "Experimental checkpoint. Only 3 training steps (3 epochs on tiny data). "
            "Eval F1: 0.0% at every evaluation. Never learned anything. "
            "Unknown training data provenance."
        ),
    ),
    (
        "rfq2boq-ner-lora-v2",
        "UNKNOWN",
        (
            "Un-audited provenance. Base model references "
            "models/rfq2boq-ner-real-only-v2/final_model (non-existent path). "
            "Best eval F1: 4.26% after 20 epochs. No documented training data source."
        ),
    ),
    (
        "rfq2boq-ner-lora-v3",
        "UNKNOWN",
        (
            "Un-audited provenance. Best eval F1: 14.75% after 10 epochs. "
            "No documented training data source or README provenance."
        ),
    ),
    (
        "rfq2boq-ner-lora-v4",
        "BROKEN",
        (
            "Empty final_model/ directory — no adapter weights, no checkpoint files. "
            "Training never produced a usable output."
        ),
    ),
    (
        "rfq2boq-ner-lora-v5",
        "CONTAMINATED",
        (
            "Trained on pseudo-labeled (silver) data. Best eval F1: 64.68% on "
            "contaminated synthetic eval set, but only 18.8% on held-out real docs "
            "(per AGENTS.md). Overfits to synthetic noise. Violates anti-cheat rule: "
            "machine labels must never enter training."
        ),
    ),
]


def build_manifest_entry(model_name: str, classification: str, reason: str) -> dict:
    return {
        "model_dir": model_name,
        "classification": classification,
        "reason": reason,
        "original_path": str(MODELS_DIR / model_name),
        "quarantine_path": str(QUARANTINE_DIR / model_name),
        "timestamp": datetime.now(UTC).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Quarantine contaminated model checkpoints")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually move directories (default is dry-run)",
    )
    args = parser.parse_args()

    dry_run = not args.execute

    print("=" * 72)
    print(f"MODEL QUARANTINE {'(DRY RUN)' if dry_run else '(EXECUTE)'}")
    print(f"Models dir:   {MODELS_DIR}")
    print(f"Quarantine:   {QUARANTINE_DIR}")
    print("=" * 72)
    print()

    # Verify models dir exists
    if not MODELS_DIR.is_dir():
        print(f"ERROR: models directory not found at {MODELS_DIR}", file=sys.stderr)
        sys.exit(1)

    # Collect results for manifest
    manifest_entries: list[dict] = []
    skipped: list[str] = []

    for model_name, classification, reason in MODEL_CLASSIFICATIONS:
        src = MODELS_DIR / model_name
        dst = QUARANTINE_DIR / model_name

        print(f"[{classification:12s}] {model_name}")
        print(f"  Reason: {reason}")
        print(f"  Source: {src}")

        if not src.is_dir():
            print("  Status: SKIP (directory does not exist)")
            skipped.append(model_name)
            print()
            continue

        if dst.exists():
            print(f"  Status: SKIP (already in quarantine at {dst})")
            skipped.append(model_name)
            print()
            continue

        if dry_run:
            print(f"  Action: WOULD MOVE -> {dst}")
        else:
            print(f"  Action: MOVING -> {dst}")
            QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            print("  Status: MOVED")

        manifest_entries.append(build_manifest_entry(model_name, classification, reason))
        print()

    # Summary
    print("-" * 72)
    print(f"Total models audited:  {len(MODEL_CLASSIFICATIONS)}")
    print(f"To quarantine:         {len(manifest_entries)}")
    print(f"Skipped:               {len(skipped)}")
    if skipped:
        print(f"  Skipped dirs:        {', '.join(skipped)}")
    print()

    # Classifications breakdown
    from collections import Counter

    class_counts = Counter()
    for _, c, _ in MODEL_CLASSIFICATIONS:
        class_counts[c] += 1
    print("Classification breakdown:")
    for cls in ["CONTAMINATED", "BROKEN", "UNKNOWN", "SAFE"]:
        if class_counts[cls] > 0:
            print(f"  {cls:15s}: {class_counts[cls]}")
    print()

    # Write manifest
    if manifest_entries:
        manifest_path = QUARANTINE_DIR / "MANIFEST.json"
        if dry_run:
            print(f"Would write manifest to: {manifest_path}")
        else:
            QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
            # Load existing manifest if present
            existing: list[dict] = []
            if manifest_path.exists():
                with open(manifest_path) as f:
                    existing = json.load(f)
            existing.extend(manifest_entries)
            with open(manifest_path, "w") as f:
                json.dump(existing, f, indent=2)
            print(f"Manifest written to: {manifest_path}")

    print()
    if dry_run:
        print("DRY RUN complete. Re-run with --execute to move directories.")
    else:
        print("EXECUTE complete. Directories moved to quarantine.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
