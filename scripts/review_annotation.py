#!/usr/bin/env python3
"""Terminal review loop for draft annotations.

Usage:
    python3 scripts/review_annotation.py data/annotations/draft/<doc_id>.json
    python3 scripts/review_annotation.py --all  # Review all pending drafts

Shows each draft entity span in context. Owner accepts / edits / rejects.
Writes status: human_verified ONLY on explicit accept (interactive "a").
The --yes auto flag has been removed; CLI review always requires explicit human input.
Logs reviewer + timestamp.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.constants import ENTITY_LABELS

DRAFT_DIR = Path("data/annotations/draft")
VERIFIED_DIR = Path("data/annotations/verified")
MANIFEST_PATH = Path("data/real_rfqs/INTAKE_MANIFEST.csv")


def _load_manifest_rows() -> list[dict]:
    """Load manifest as list of dicts."""
    if not MANIFEST_PATH.exists():
        return []
    import csv

    with open(MANIFEST_PATH, newline="") as f:
        return list(csv.DictReader(f))


def _update_manifest_status(doc_id: str, status: str, annotator: str) -> None:
    """Update manifest row for doc_id with new status and review date."""
    if not MANIFEST_PATH.exists():
        return
    import csv

    rows = _load_manifest_rows()
    fieldnames = (
        list(rows[0].keys())
        if rows
        else [
            "sha256",
            "filename",
            "doc_id",
            "source",
            "client",
            "date",
            "pages",
            "draft_entities",
            "status",
            "annotator",
            "review_date",
        ]
    )
    updated = False
    for row in rows:
        if row.get("doc_id") == doc_id:
            row["status"] = status
            row["annotator"] = annotator
            row["review_date"] = datetime.now(UTC).isoformat()
            updated = True
    if updated:
        with open(MANIFEST_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def _show_context(tokens: list[str], start: int, end: int, window: int = 8) -> str:
    """Render entity in context with surrounding tokens."""
    ctx_start = max(0, start - window)
    ctx_end = min(len(tokens), end + window)
    left = " ".join(tokens[ctx_start:start])
    entity = " ".join(tokens[start:end])
    right = " ".join(tokens[end:ctx_end])
    return f"… {left}  >>{entity}<<  {right} …"


def _edit_entity(tokens: list[str], entity: dict) -> dict | None:
    """Interactive edit of an entity span."""
    print(f"\n  Current: {entity['type']} | {' '.join(tokens[entity['start'] : entity['end']])}")
    print(f"  Start: {entity['start']}, End: {entity['end']}")
    print("  Commands: s <start> | e <end> | t <type> | q (quit edit)")
    ent = copy.deepcopy(entity)
    while True:
        cmd = input("  edit> ").strip()
        if not cmd:
            continue
        if cmd == "q":
            break
        if cmd.startswith("s "):
            try:
                ent["start"] = int(cmd.split()[1])
            except (ValueError, IndexError):
                print("    Invalid start")
        elif cmd.startswith("e "):
            try:
                ent["end"] = int(cmd.split()[1])
            except (ValueError, IndexError):
                print("    Invalid end")
        elif cmd.startswith("t "):
            typ = cmd.split()[1].upper()
            if typ in ENTITY_LABELS:
                ent["type"] = typ
            else:
                print(f"    Invalid type. Use: {', '.join(ENTITY_LABELS)}")
        else:
            print("    Unknown command")
        # Update text
        if 0 <= ent["start"] < ent["end"] <= len(tokens):
            ent["text"] = " ".join(tokens[ent["start"] : ent["end"]])
        print(f"    Now: {ent['type']} | {ent['text']}")
    return ent


def review_annotation(draft_path: Path, reviewer: str, auto_accept: bool = False) -> Path | None:
    """Review a single draft annotation interactively."""
    with open(draft_path) as f:
        annotation = json.load(f)

    doc_id = annotation["doc_id"]
    tokens = annotation["tokens"]
    entities = list(annotation.get("entities", []))
    print(f"\n{'=' * 70}")
    print(f"REVIEW: {doc_id} ({len(entities)} draft entities)")
    print(f"Source: {annotation.get('source_file', 'unknown')}")
    print(f"{'=' * 70}")

    if not entities:
        print("No draft entities to review.")
        return None

    accepted: list[dict] = []
    for idx, ent in enumerate(entities):
        context = _show_context(tokens, ent["start"], ent["end"])
        print(f"\n[{idx + 1}/{len(entities)}] {ent['type']} (auto)")
        print(f"  {context}")
        choice = "a" if auto_accept else input("  [a]ccept / [e]dit / [r]eject / [q]uit review> ").strip().lower()
        if choice == "q":
            print("  Quitting review — progress NOT saved.")
            return None
        elif choice == "a":
            ent["source"] = "HUMAN"
            accepted.append(ent)
            print("  ✓ Accepted")
        elif choice == "e":
            edited = _edit_entity(tokens, ent)
            if edited:
                edited["source"] = "HUMAN"
                accepted.append(edited)
                print("  ✓ Accepted (edited)")
        else:
            print("  ✗ Rejected")

    if not accepted:
        print("\nNo entities accepted. Skipping save.")
        return None

    # Rebuild ner_tags from accepted entities
    from scripts.intake_tender import _entities_to_bioes

    ner_tags = _entities_to_bioes(tokens, accepted)

    verified = copy.deepcopy(annotation)
    verified["entities"] = accepted
    verified["ner_tags"] = ner_tags
    verified["metadata"]["status"] = "human_verified"
    verified["metadata"]["annotator"] = reviewer
    verified["metadata"]["review_date"] = datetime.now(UTC).isoformat()
    verified["metadata"]["original_draft"] = str(draft_path)
    verified["metadata"]["reviewed_entities"] = len(accepted)
    verified["metadata"]["rejected_entities"] = len(entities) - len(accepted)

    VERIFIED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = VERIFIED_DIR / f"{doc_id}.json"
    with open(out_path, "w") as f:
        json.dump(verified, f, indent=2)

    # Update manifest
    _update_manifest_status(doc_id, "human_verified", reviewer)

    print(f"\n✓ Verified annotation saved: {out_path}")
    print(f"  Accepted: {len(accepted)}, Rejected: {len(entities) - len(accepted)}")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Review draft annotations")
    parser.add_argument("file", nargs="?", help="Draft annotation JSON to review")
    parser.add_argument("--all", action="store_true", help="Review all pending drafts")
    parser.add_argument("--reviewer", default="srujan", help="Reviewer name")
    # NOTE: No --yes / auto-accept in CLI. Review script REQUIRES explicit interactive human accept ("a"/"e")
    # to set human_verified. Auto mode is only for unit tests calling the function directly.
    args = parser.parse_args()

    if args.all:
        drafts = sorted(DRAFT_DIR.glob("*.json"))
        if not drafts:
            print("No draft annotations found.")
            return 0
        print(f"Found {len(drafts)} draft(s) to review")
        for draft_path in drafts:
            review_annotation(draft_path, args.reviewer, auto_accept=False)
        return 0

    if not args.file:
        print("Usage: review_annotation.py <file> | --all")
        return 1

    draft_path = Path(args.file)
    if not draft_path.exists():
        print(f"File not found: {draft_path}")
        return 1

    result = review_annotation(draft_path, args.reviewer, auto_accept=False)
    return 0 if result else 1


if __name__ == "__main__":
    raise SystemExit(main())
