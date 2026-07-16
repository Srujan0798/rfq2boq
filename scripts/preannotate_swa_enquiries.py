#!/usr/bin/env python3
"""Pre-annotate the 10 SWA enquiries using the NLP pipeline to produce BIOES seed sentences.

Usage:
    python3 scripts/preannotate_swa_enquiries.py [--dry-run]

Reads ingested JSON files from data/real_rfqs/swa_enquiries/ingested/,
runs the NLPPipeline on each sentence, and writes draft BIOES annotation
files to data/annotations/draft/swa_draft_{enquiry_id}.json.

HELD-OUT RULE: SWA enquiry sentences must NEVER be written to
data/annotations/train/ or data/annotations/val/.  A hard assertion
enforces this at the start of the script.

Output format per file (list of sentence records):
    {
      "text": "...",
      "tokens": ["Supply", "500", "kg", ...],
      "ner_tags": ["S-ACTION", "S-QUANTITY", "S-UNIT", ...],
      "entities": [...],   # raw entity dicts from pipeline
      "status": "draft-needs-review",
      "source": "swa_enquiries/01_gsecl_wanakbori_tmd8",
      "doc_id": "swa_draft_01_gsecl_wanakbori_tmd8"
    }
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# ── project root on sys.path ──────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.nlp.pipeline import NLPPipeline  # noqa: E402

# ── paths ─────────────────────────────────────────────────────────────────────
INGESTED_DIR = ROOT / "data" / "real_rfqs" / "swa_enquiries" / "ingested"
DRAFT_DIR = ROOT / "data" / "annotations" / "draft"
TRAIN_DIR = ROOT / "data" / "annotations" / "train"
VAL_DIR = ROOT / "data" / "annotations" / "val"

# ── minimum sentence length (tokens) to consider ─────────────────────────────
MIN_TOKENS = 3
MAX_SENTENCE_CHARS = 500  # skip abnormally long "sentences"


# ── held-out guard ────────────────────────────────────────────────────────────
def assert_no_swa_in_train_val() -> None:
    """Hard assert: SWA enquiry files must not exist in train/ or val/."""
    violations: list[str] = []
    for directory in (TRAIN_DIR, VAL_DIR):
        if not directory.exists():
            continue
        for f in directory.glob("swa_draft_*.json"):
            violations.append(str(f))
    if violations:
        raise AssertionError(
            "HELD-OUT VIOLATION: SWA draft files found in train/val directories:\n"
            + "\n".join(violations)
        )


# ── text → sentences ──────────────────────────────────────────────────────────
_SENT_SPLITTER = re.compile(r"(?<=[.?!;:\n])\s+|\n{2,}")


def split_sentences(text: str) -> list[str]:
    """Rough sentence splitter suitable for tender text."""
    raw = _SENT_SPLITTER.split(text)
    cleaned: list[str] = []
    for s in raw:
        s = s.strip()
        if not s or len(s) > MAX_SENTENCE_CHARS:
            continue
        cleaned.append(s)
    return cleaned


# ── entity spans → BIOES tags ─────────────────────────────────────────────────
def _tokenise(text: str) -> list[str]:
    """Simple whitespace tokeniser."""
    return text.split()


def _char_offsets(tokens: list[str], text: str) -> list[tuple[int, int]]:
    """Compute (start, end) char offsets for each token."""
    offsets: list[tuple[int, int]] = []
    pos = 0
    for tok in tokens:
        start = text.find(tok, pos)
        if start == -1:
            start = pos
        end = start + len(tok)
        offsets.append((start, end))
        pos = end
    return offsets


def entities_to_bioes(
    tokens: list[str],
    offsets: list[tuple[int, int]],
    entities: list[dict],
) -> list[str]:
    """Convert entity span dicts to BIOES token tags.

    Entity dict format (from NLPPipeline):
        {"text": "...", "type": "MATERIAL", "start": <char>, "end": <char>, ...}
    """
    tags = ["O"] * len(tokens)

    for ent in entities:
        e_start = ent["start"]
        e_end = ent["end"]
        e_type = ent["type"]

        # Find token indices that overlap with this entity span
        matched: list[int] = []
        for i, (t_start, t_end) in enumerate(offsets):
            if t_end > e_start and t_start < e_end:
                matched.append(i)

        if not matched:
            continue

        if len(matched) == 1:
            tags[matched[0]] = f"S-{e_type}"
        else:
            tags[matched[0]] = f"B-{e_type}"
            for mid in matched[1:-1]:
                tags[mid] = f"I-{e_type}"
            tags[matched[-1]] = f"E-{e_type}"

    return tags


# ── main processing ───────────────────────────────────────────────────────────
def process_enquiry(
    enquiry_id: str,
    ingested_path: Path,
    pipeline: NLPPipeline,
) -> tuple[list[dict], Counter]:
    """Process one enquiry; return (sentence_records, entity_type_counter)."""
    with open(ingested_path) as f:
        data = json.load(f)

    # Collect all text from all files in the ingested manifest
    all_texts: list[str] = []
    for file_entry in data.get("files", []):
        text = file_entry.get("text", "").strip()
        if text:
            all_texts.append(text)

    if not all_texts:
        return [], Counter()

    combined_text = "\n\n".join(all_texts)
    sentences = split_sentences(combined_text)

    records: list[dict] = []
    entity_counts: Counter = Counter()

    for sent in sentences:
        tokens = _tokenise(sent)
        if len(tokens) < MIN_TOKENS:
            continue

        result = pipeline.process(sent)
        if not result.entities:
            continue  # skip sentences with no entity hits

        offsets = _char_offsets(tokens, sent)
        tags = entities_to_bioes(tokens, offsets, result.entities)

        for ent in result.entities:
            entity_counts[ent["type"]] += 1

        records.append(
            {
                "text": sent,
                "tokens": tokens,
                "ner_tags": tags,
                "entities": result.entities,
                "status": "draft-needs-review",
                "source": f"swa_enquiries/{enquiry_id}",
                "doc_id": f"swa_draft_{enquiry_id}",
            }
        )

    return records, entity_counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-annotate SWA enquiries with NLP pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Print stats without writing files")
    args = parser.parse_args()

    # Hard guard: SWA data must never be in train/val
    assert_no_swa_in_train_val()

    if not INGESTED_DIR.exists():
        print(f"ERROR: ingested dir not found: {INGESTED_DIR}", file=sys.stderr)
        return 1

    if not args.dry_run:
        DRAFT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading NLP pipeline...")
    pipeline = NLPPipeline()
    print("Pipeline ready.\n")

    ingested_files = sorted(INGESTED_DIR.glob("*.json"))
    if not ingested_files:
        print("No ingested files found.")
        return 1

    grand_total_sentences = 0
    grand_entity_counts: Counter = Counter()
    per_enquiry_stats: list[dict] = []

    for ingested_path in ingested_files:
        enquiry_id = ingested_path.stem
        records, entity_counts = process_enquiry(enquiry_id, ingested_path, pipeline)

        grand_total_sentences += len(records)
        grand_entity_counts.update(entity_counts)

        per_enquiry_stats.append(
            {
                "enquiry_id": enquiry_id,
                "sentences": len(records),
                "entity_counts": dict(entity_counts),
            }
        )

        if not args.dry_run and records:
            out_path = DRAFT_DIR / f"swa_draft_{enquiry_id}.json"
            with open(out_path, "w") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            print(f"  [{enquiry_id}]  {len(records):4d} sentences  -> {out_path.name}")
        else:
            print(f"  [{enquiry_id}]  {len(records):4d} sentences (dry-run, not written)")

    # ── print summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total enquiries processed : {len(ingested_files)}")
    print(f"Total sentences generated : {grand_total_sentences}")
    print("\nPer-enquiry breakdown:")
    for stat in per_enquiry_stats:
        eid = stat["enquiry_id"]
        n = stat["sentences"]
        types_str = ", ".join(
            f"{k}:{v}" for k, v in sorted(stat["entity_counts"].items(), key=lambda x: -x[1])
        )
        print(f"  {eid:<40s}  {n:4d} sents  [{types_str or 'none'}]")

    print("\nGlobal entity type counts:")
    for etype, count in sorted(grand_entity_counts.items(), key=lambda x: -x[1]):
        print(f"  {etype:<15s}  {count:5d}")

    if not args.dry_run:
        print(f"\nDraft files written to: {DRAFT_DIR}")
        print("STATUS: draft-needs-review (human review required before training)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
