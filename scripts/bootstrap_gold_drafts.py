#!/usr/bin/env python3
"""Bootstrap draft gold annotations from real PDFs using NLP + BOQ heuristics.

Output files are marked metadata.status='draft_review' — YOU must verify/correct
before counting as gold for F1 reporting or final retrain.

Usage:
    python scripts/bootstrap_gold_drafts.py
    python scripts/bootstrap_gold_drafts.py --limit 15
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest.pdf_extractor import PDFExtractor

REAL_SOURCE_DIRS = {"ireps", "cpwd", "delhi_pwd", "epi", "nhai", "odisha_pwd", "bims", "mes", "mh_publicworks"}
BOQ_LINE = re.compile(
    r"(?i).{0,80}(cement|concrete|steel|brick|mortar|plaster|paint|tile|pipe|cable|"
    r"excavat|earthwork|masonry|flooring|roofing|door|window|column|beam|slab).{0,120}"
    r"(\d+[\d.,]*)\s*(nos?|kg|mt|cum|sqm|sq\.?\s*m|rm|ltr|ls|each)\b"
)

# Simple token-level quantity+unit detector (fast; avoids loading NER model).
QTY_UNIT = re.compile(r"(?i)^\d[\d.,]*$")
UNIT = re.compile(r"(?i)^(nos?|kg|mt|cum|sqm|sq\.?m|rm|ltr|ls|each)$")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--raw-dir", type=Path, default=Path("data/real_rfqs/raw"))
    p.add_argument("--gold-dir", type=Path, default=Path("data/real_rfqs/gold"))
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--max-chars", type=int, default=8000)
    return p.parse_args()


def is_real_pdf(path: Path) -> bool:
    parts = {p.name for p in path.parents}
    if "synthetic_archive" in parts:
        return False
    name = path.name.lower()
    if name.startswith("rfq_"):
        return False
    if path.parent.name in REAL_SOURCE_DIRS:
        return True
    if any(x in name for x in ("ireps", "delhi_pwd", "delhi")):
        return True
    if "cpwd" in name and "guidelines" not in name:
        return True
    return False


def entities_to_bioes(tokens: list[str], entities: list[dict]) -> list[str]:
    tags = ["O"] * len(tokens)
    for ent in entities:
        start, end = ent["start"], ent["end"]
        et = ent["type"]
        if start < 0 or end >= len(tokens):
            continue
        if start == end:
            tags[start] = f"S-{et}"
        else:
            tags[start] = f"B-{et}"
            for i in range(start + 1, end):
                tags[i] = f"I-{et}"
            tags[end] = f"E-{et}"
    return tags


def char_span_to_token_span(tokens: list[str], start_char: int, end_char: int) -> tuple[int, int] | None:
    pos = 0
    token_starts: list[int] = []
    for tok in tokens:
        token_starts.append(pos)
        pos += len(tok) + 1
    t_start = t_end = None
    for i, ts in enumerate(token_starts):
        te = ts + len(tokens[i])
        if t_start is None and te > start_char:
            t_start = i
        if te >= end_char:
            t_end = i
            break
    if t_start is None or t_end is None:
        return None
    return t_start, t_end


def pick_boq_text(full_text: str, max_chars: int) -> str:
    lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]
    boq_lines = [ln for ln in lines if BOQ_LINE.search(ln)]
    if boq_lines:
        chunk = "\n".join(boq_lines[:80])
    else:
        chunk = full_text
    return chunk[:max_chars]


def _bootstrap_entities(tokens: list[str]) -> tuple[list[dict], list[dict]]:
    entities: list[dict] = []
    relations: list[dict] = []

    ent_i = 0
    for i in range(1, len(tokens)):
        if not QTY_UNIT.match(tokens[i - 1]):
            continue
        if not UNIT.match(tokens[i]):
            continue

        qty_start = i - 1
        qty_ent = {"text": tokens[qty_start], "type": "QUANTITY", "start": qty_start, "end": qty_start}
        unit_ent = {"text": tokens[i], "type": "UNIT", "start": i, "end": i}

        # Material = previous 2–6 tokens before quantity (heuristic).
        mat_end = max(0, qty_start - 1)
        mat_start = max(0, mat_end - 5)
        mat_tokens = [t for t in tokens[mat_start : mat_end + 1] if t.strip()]
        if not mat_tokens:
            continue
        mat_ent = {
            "text": " ".join(mat_tokens),
            "type": "MATERIAL",
            "start": mat_start,
            "end": mat_end,
        }

        mat_idx = len(entities)
        entities.extend([mat_ent, qty_ent, unit_ent])
        relations.extend(
            [
                {"head_idx": mat_idx, "tail_idx": mat_idx + 1, "type": "HAS_QUANTITY"},
                {"head_idx": mat_idx, "tail_idx": mat_idx + 2, "type": "HAS_UNIT"},
            ]
        )
        ent_i += 3

        if ent_i >= 60:
            break

    return entities, relations


def build_annotation(pdf_path: Path, extractor: PDFExtractor) -> dict | None:
    # Fast sampling: only read a few pages (avoid full-doc extraction).
    import pymupdf

    doc = pymupdf.open(str(pdf_path))
    try:
        page_count = int(getattr(doc, "page_count", 0) or 0)
        if page_count == 0:
            return None
        n_pages = min(3, page_count)
        full_text = "\n".join((doc.load_page(i).get_text("text") or "") for i in range(n_pages))
    finally:
        doc.close()

    if len(full_text.strip()) < 200:
        return None

    text = pick_boq_text(full_text, 8000)
    tokens = text.split()
    if len(tokens) < 20:
        return None

    entities, relations = _bootstrap_entities(tokens)
    ner_tags = entities_to_bioes(tokens, entities)

    return {
        "doc_id": pdf_path.stem,
        "source_file": pdf_path.name,
        "tokens": tokens,
        "ner_tags": ner_tags,
        "entities": entities,
        "relations": relations,
        "metadata": {
            "annotator": "bootstrap_nlp",
            "date": date.today().isoformat(),
            "status": "draft_review",
            "agreement": None,
            "notes": "Auto-draft from NLP; human must verify before gold eval/retrain.",
        },
    }


def main() -> None:
    args = parse_args()
    args.gold_dir.mkdir(parents=True, exist_ok=True)

    pdfs: list[Path] = []
    raw = args.raw_dir
    for sub in REAL_SOURCE_DIRS:
        d = raw / sub
        if d.is_dir():
            pdfs.extend(sorted(d.glob("*.pdf")))
    for p in sorted(raw.glob("*.pdf")):
        if "synthetic" in p.name or "rfq_" in p.name:
            continue
        if p not in pdfs:
            pdfs.append(p)

    pdfs = [p for p in pdfs if is_real_pdf(p)][: args.limit]
    print(f"Bootstrapping draft gold for {len(pdfs)} real PDFs...")

    extractor = PDFExtractor()
    written = 0
    for pdf in pdfs:
        out = args.gold_dir / f"{pdf.stem}.json"
        if out.exists():
            with out.open(encoding="utf-8") as f:
                meta = json.load(f).get("metadata", {})
            if meta.get("status") == "complete":
                print(f"  skip (complete): {out.name}")
                continue
        try:
            ann = build_annotation(pdf, extractor)
            if not ann or not ann["entities"]:
                print(f"  skip (no entities): {pdf.name}")
                continue
            with out.open("w", encoding="utf-8") as f:
                json.dump(ann, f, indent=2, ensure_ascii=False)
            n_ent = len(ann["entities"])
            print(f"  draft: {out.name} ({n_ent} entities)")
            written += 1
        except Exception as exc:
            print(f"  error {pdf.name}: {exc}")

    print(f"\nWrote {written} draft files to {args.gold_dir}")
    print("Human step: open ui/annotate.py or edit JSON; set metadata.status='complete' when verified.")


if __name__ == "__main__":
    main()
