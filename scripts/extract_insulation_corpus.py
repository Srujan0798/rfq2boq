#!/usr/bin/env python3
"""Extract text + tables from the insulation_hvac tender PDF corpus.

This is a REUSABLE ingestion helper for the new insulation/HVAC training
corpus (separate from src.pipeline so it does NOT contaminate downstream
evaluation). It only writes plain-text and table-JSON dumps plus a manifest.

Inputs:  data/real_rfqs/raw/insulation_hvac/*.pdf  (tenders, NOT boq_references/)
Outputs: data/real_rfqs/extracted/insulation_hvac/<stem>.txt
         data/real_rfqs/extracted/insulation_hvac/tables/<stem>_tables.json
         data/real_rfqs/extracted/insulation_hvac/manifest.json

Anti-cheat: this script NEVER imports src.pipeline or anything that runs
the NER model. It is pure text + table extraction, intended for human
annotation downstream (B2).
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pdfplumber
import pymupdf  # PyMuPDF

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_DIR = REPO_ROOT / "data" / "real_rfqs" / "raw" / "insulation_hvac"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "real_rfqs" / "extracted" / "insulation_hvac"
DEFAULT_TABLES_DIR = DEFAULT_OUTPUT_DIR / "tables"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("extract_insulation_corpus")

_WS_RE = re.compile(r"[ \t]+")
_BLANK_LINE_RE = re.compile(r"\n{3,}")


def _clean_text(raw: str) -> str:
    cleaned = raw.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = _WS_RE.sub(" ", cleaned)
    cleaned = _BLANK_LINE_RE.sub("\n\n", cleaned)
    return cleaned.strip() + "\n"


def _extract_text_pdfplumber(pdf_path: Path) -> tuple[str, int]:
    pages_text: list[str] = []
    page_count = 0
    with pdfplumber.open(str(pdf_path)) as pdf:
        page_count = len(pdf.pages)
        for idx, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            pages_text.append(f"\n----- PAGE {idx} -----\n{text}")
    return _clean_text("\n".join(pages_text)), page_count


def _extract_text_pymupdf(pdf_path: Path) -> tuple[str, int]:
    pages_text: list[str] = []
    with pymupdf.open(str(pdf_path)) as doc:
        page_count = doc.page_count
        for idx, page in enumerate(doc, 1):
            text = page.get_text("text") or ""
            pages_text.append(f"\n----- PAGE {idx} -----\n{text}")
    return _clean_text("\n".join(pages_text)), page_count


def _extract_text_ocr(pdf_path: Path, page_count: int, max_pages: int) -> str:
    """OCR fallback for image-only PDFs. Uses tesseract via subprocess.

    Slow: ~5-10s per page. Capped to ``max_pages`` so compliance sheets
    (e.g. Tender (2).pdf, Tender (4) (1).pdf) don't block the run.
    """
    pages_to_ocr = min(page_count, max_pages)
    out_parts: list[str] = []
    with pymupdf.open(str(pdf_path)) as doc:
        for idx in range(pages_to_ocr):
            page = doc[idx]
            pix = page.get_pixmap(dpi=200)
            png_path = pdf_path.with_suffix(f".__ocr_{idx}.png")
            pix.save(str(png_path))
            try:
                result = subprocess.run(
                    ["tesseract", str(png_path), "-", "-l", "eng"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                text = result.stdout if result.returncode == 0 else ""
            except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
                log.warning("OCR failed on %s page %d: %s", pdf_path.name, idx + 1, exc)
                text = ""
            finally:
                if png_path.exists():
                    png_path.unlink()
            out_parts.append(f"\n----- PAGE {idx + 1} (OCR) -----\n{text}")
    if page_count > pages_to_ocr:
        out_parts.append(
            f"\n[OCR SKIPPED {page_count - pages_to_ocr} additional page(s) — over max_pages={max_pages}]\n"
        )
    return _clean_text("\n".join(out_parts))


def _extract_tables(pdf_path: Path) -> list[dict]:
    """Extract all tables per page using pdfplumber (camelot is unavailable)."""
    tables_out: list[dict] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_idx, page in enumerate(pdf.pages, 1):
            try:
                tables = page.extract_tables() or []
            except Exception as exc:
                log.warning("extract_tables() failed on %s p%d: %s", pdf_path.name, page_idx, exc)
                tables = []
            for ti, table in enumerate(tables):
                cleaned = [
                    [(cell.strip() if isinstance(cell, str) else "") for cell in row]
                    for row in table
                ]
                tables_out.append(
                    {
                        "page": page_idx,
                        "table_index": ti,
                        "rows": len(cleaned),
                        "cols": max((len(r) for r in cleaned), default=0),
                        "data": cleaned,
                    }
                )
    return tables_out


def _stable_stem(pdf_path: Path) -> str:
    s = pdf_path.stem
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s)
    return s.strip("_") or "doc"


@dataclass
class FileRecord:
    pdf_file: str
    pdf_size_bytes: int
    pdf_path: str
    stem: str
    page_count: int
    chars_text: int
    table_count: int
    extraction_methods: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    seconds: float = 0.0


def process_pdf(pdf_path: Path, *, ocr_fallback: bool, ocr_max_pages: int) -> FileRecord:
    rec = FileRecord(
        pdf_file=pdf_path.name,
        pdf_size_bytes=pdf_path.stat().st_size,
        pdf_path=str(pdf_path),
        stem=_stable_stem(pdf_path),
        page_count=0,
        chars_text=0,
        table_count=0,
    )
    t0 = time.time()

    text_pp = ""
    page_count_pp = 0
    try:
        text_pp, page_count_pp = _extract_text_pdfplumber(pdf_path)
    except Exception as exc:
        rec.warnings.append(f"pdfplumber text error: {exc}")

    rec.page_count = page_count_pp

    if text_pp.strip():
        final_text = text_pp
        rec.extraction_methods.append("pdfplumber")
    else:
        log.info("pdfplumber returned empty text for %s — trying PyMuPDF", pdf_path.name)
        text_mu = ""
        page_count_mu = 0
        try:
            text_mu, page_count_mu = _extract_text_pymupdf(pdf_path)
            if page_count_mu:
                rec.page_count = page_count_mu
        except Exception as exc:
            rec.warnings.append(f"pymupdf text error: {exc}")

        if text_mu.strip():
            final_text = text_mu
            rec.extraction_methods.append("pymupdf")
        elif ocr_fallback:
            log.info("Both text extractors empty — running OCR on %s", pdf_path.name)
            try:
                final_text = _extract_text_ocr(pdf_path, rec.page_count, ocr_max_pages)
                if final_text.strip():
                    rec.extraction_methods.append("tesseract-ocr")
                else:
                    rec.warnings.append("ocr returned empty")
            except Exception as exc:
                rec.warnings.append(f"ocr error: {exc}")
                final_text = text_pp or text_mu
        else:
            final_text = text_pp or text_mu
            rec.warnings.append("no text extracted (image PDF, OCR disabled)")

    rec.chars_text = len(final_text)

    tables: list[dict] = []
    try:
        tables = _extract_tables(pdf_path)
    except Exception as exc:
        rec.warnings.append(f"tables error: {exc}")
    rec.table_count = len(tables)
    if tables:
        rec.extraction_methods.append("pdfplumber-tables")

    rec.seconds = round(time.time() - t0, 2)

    out_txt = DEFAULT_OUTPUT_DIR / f"{rec.stem}.txt"
    out_txt.write_text(final_text, encoding="utf-8")

    out_tables = DEFAULT_TABLES_DIR / f"{rec.stem}_tables.json"
    out_tables.write_text(json.dumps(tables, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info(
        "  -> %s  pages=%d  chars=%d  tables=%d  methods=%s  %.1fs",
        pdf_path.name,
        rec.page_count,
        rec.chars_text,
        rec.table_count,
        ",".join(rec.extraction_methods) or "(none)",
        rec.seconds,
    )
    return rec


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--ocr-fallback", action="store_true", help="Enable Tesseract OCR for image PDFs")
    parser.add_argument("--ocr-max-pages", type=int, default=3)
    parser.add_argument("--limit", type=int, default=0, help="Process only first N PDFs (debug)")
    args = parser.parse_args()

    in_dir: Path = args.input_dir
    out_dir: Path = args.output_dir
    tables_dir = out_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(p for p in in_dir.glob("*.pdf") if p.is_file())
    if args.limit:
        pdfs = pdfs[: args.limit]

    if not pdfs:
        log.error("No PDFs found in %s", in_dir)
        return 2

    log.info("Extracting %d PDFs from %s", len(pdfs), in_dir)
    log.info("Output dir: %s", out_dir)

    manifest: list[dict] = []
    overall_t0 = time.time()
    for i, pdf_path in enumerate(pdfs, 1):
        log.info("[%d/%d] %s", i, len(pdfs), pdf_path.name)
        try:
            rec = process_pdf(
                pdf_path,
                ocr_fallback=args.ocr_fallback,
                ocr_max_pages=args.ocr_max_pages,
            )
        except Exception as exc:
            log.error("FAILED %s: %s", pdf_path.name, exc)
            rec = FileRecord(
                pdf_file=pdf_path.name,
                pdf_size_bytes=pdf_path.stat().st_size,
                pdf_path=str(pdf_path),
                stem=_stable_stem(pdf_path),
                page_count=0,
                chars_text=0,
                table_count=0,
                extraction_methods=[],
                warnings=[f"unhandled error: {exc}"],
            )
        manifest.append(rec.__dict__)

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_dir": str(in_dir),
        "output_dir": str(out_dir),
        "file_count": len(manifest),
        "total_chars": sum(r["chars_text"] for r in manifest),
        "total_tables": sum(r["table_count"] for r in manifest),
        "ocr_fallback_enabled": args.ocr_fallback,
        "ocr_max_pages": args.ocr_max_pages,
        "files": manifest,
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Wrote %s", manifest_path)
    log.info(
        "DONE: %d files, %d chars, %d tables, %.1fs total",
        payload["file_count"],
        payload["total_chars"],
        payload["total_tables"],
        time.time() - overall_t0,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
