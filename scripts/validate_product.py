#!/usr/bin/env python3
"""Product end-to-end validation: compare Pipeline().run() output vs XLSX ground-truth BOQ.

Run: python3 scripts/validate_product.py --enquiry all
     python3 scripts/validate_product.py --enquiry 02_isro_vssc
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.boq_assembler import BOQAssembler
from src.domain.models import BoqRow, EntitySpan, EntityType, Relation, RelationType
from src.eval.boq_row_matcher import BOQRowMatcher, MatchReport
from src.pipeline import Pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
log = logging.getLogger(__name__)

GOLD_DIR = Path("data/real_rfqs/gold")
ROW_GOLD_DIR = Path("data/real_rfqs/gold/rows")
ENQUIRY_DIR = Path("data/real_rfqs/swa_enquiries")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

ENQUIRIES = {
    "01_gsecl_wanakbori_tmd8": {
        "gold": "swa_01_gsecl_wanakbori_tmd8.json",
        "row_gold": "01_gsecl_wanakbori_tmd8.rowgold.json",
        "source": "01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf",
        "client": "GSECL Wanakbori TMD-8",
        "description": "Thermal insulation Schedule-B — page 61 of tender PDF",
    },
    "02_isro_vssc": {
        "gold": "swa_02_isro_vssc.json",
        "row_gold": "02_isro_vssc.rowgold.json",
        "source": "02_isro_vssc/VSSC_BOQ_with_qty.xlsx",
        "client": "ISRO VSSC",
        "description": "Incremental qty BOQ — aerospace facility",
    },
    "03_zydus_matoda_osd": {
        "gold": "swa_03_zydus_matoda_osd.json",
        "row_gold": "03_zydus_matoda_osd.rowgold.json",
        "source": "03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx",
        "client": "Zydus Pharma Matoda",
        "description": "OSD facility insulation",
    },
    "05_zydus_animal_pharmez": {
        "gold": "swa_05_zydus_animal_pharmez.json",
        "row_gold": "05_zydus_animal_pharmez.rowgold.json",
        "source": "05_zydus_animal_pharmez/Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx",
        "client": "Zydus Animal Health",
        "description": "Pharmez Ahmedabad expansion",
    },
    "08_sael": {
        "gold": "swa_08_sael.json",
        "row_gold": "08_sael.rowgold.json",
        "source": "08_sael/Copy of Insulation Enquiry - SAEL.xlsx",
        "client": "SAEL",
        "description": "Insulation enquiry",
    },
    "06_avante_kirloskar_pune": {
        "gold": "swa_06_avante_kirloskar_pune.json",
        "row_gold": "06_avante_kirloskar_pune.rowgold.json",
        "source": "06_avante_kirloskar_pune/Insulation Boq_132.pdf",
        "client": "Avante Kirloskar Pune",
        "description": "Insulation BOQ — PDF table",
    },
    "07_grew_solar_narmadapuram": {
        "gold": "swa_07_grew_solar_narmadapuram.json",
        "row_gold": "07_grew_solar_narmadapuram.rowgold.json",
        "source": "07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf",
        "client": "Grew Solar Narmadapuram",
        "description": "Insulation BOQ — PDF table",
    },
    "04_adani": {
        "gold": "swa_04_adani.json",
        "row_gold": "04_adani.rowgold.json",
        "source": [
            "04_adani/BOQ PAGEadani proj.pdf",
            "04_adani/BOQ PAGE2adani proj.pdf",
        ],
        "client": "Adani Project",
        "description": "CHW piping & thermal insulation — multi-page PDF BOQ",
    },
    "09_gem_bid_7439924": {
        "gold": "swa_09_gem_bid_7439924.json",
        "row_gold": "09_gem_bid_7439924.rowgold.json",
        "source": "09_gem_bid_7439924/GeM-Bidding-9218026.pdf",
        "client": "BHEL GeM Bid 7439924",
        "description": "Bonded rock wool mattresses — split-quantity GeM tender (Talcher + Lara)",
    },
    "10_gem_bid_7552777": {
        "gold": "swa_10_gem_bid_7552777.json",
        "row_gold": "10_gem_bid_7552777.rowgold.json",
        "source": "10_gem_bid_7552777/GeM-Bidding-9343469.pdf",
        "client": "BHEL GeM Bid 7552777",
        "description": "Bonded rock wool mattresses — per-item consignee GeM tender (Yadadri)",
    },
}


def _load_gold_boq_rows(enquiry_id: str) -> list[BoqRow]:
    gold_path = GOLD_DIR / ENQUIRIES[enquiry_id]["gold"]
    with open(gold_path) as fh:
        d = json.load(fh)

    entities = []
    for e in d.get("entities", []):
        try:
            etype = EntityType[e["type"].upper()]
        except KeyError:
            etype = EntityType.MATERIAL
        entities.append(
            EntitySpan(
                text=e["text"],
                type=etype,
                start=e.get("start", 0),
                end=e.get("end", 0),
                page=e.get("page", 1),
                conf=1.0,
                source="GOLD",
            )
        )

    relations = []
    for r in d.get("relations", []):
        try:
            rtype = RelationType[r["type"].upper()]
        except KeyError:
            rtype = RelationType.HAS_QUANTITY
        relations.append(
            Relation(
                head_id=str(r.get("head_id", "")),
                tail_id=str(r.get("tail_id", "")),
                type=rtype,
                conf=1.0,
            )
        )

    text = " ".join(d.get("tokens", []))
    rows = BOQAssembler().assemble(entities, relations, text)
    return rows


def _load_row_gold(enquiry_id: str) -> list[BoqRow]:
    info = ENQUIRIES[enquiry_id]
    if "row_gold" not in info:
        return []
    path = ROW_GOLD_DIR / info["row_gold"]
    if not path.exists():
        return []
    with open(path) as fh:
        d = json.load(fh)
    rows: list[BoqRow] = []
    for e in d.get("entries", []):
        rows.append(
            BoqRow(
                item_no=e.get("item_no", 0),
                material=e.get("material", ""),
                quantity=Decimal(str(e.get("quantity", "0"))),
                unit=e.get("unit", "no."),
                action=e.get("action", "supply"),
                grade=e.get("grade", ""),
                dimensions=e.get("dimensions", []),
                standard=e.get("standard", []),
                location=e.get("location", ""),
            )
        )
    return rows


def _load_predicted_boq_rows(source_paths: Path | list[Path]) -> list[BoqRow]:
    if isinstance(source_paths, Path):
        source_paths = [source_paths]
    all_items: list[BoqRow] = []
    for p in source_paths:
        result = Pipeline().run(str(p))
        all_items.extend(result.boq_items)
    return all_items


# Honest independent gold loading only - no pipeline as gold (anti-cheat)


def _summarize(report: MatchReport) -> dict:
    total = report.tp + report.fp + report.fn
    match_rate = (report.tp / total * 100) if total > 0 else 0.0
    return {
        "tp": report.tp,
        "fp": report.fp,
        "fn": report.fn,
        "total": total,
        "match_rate_pct": round(match_rate, 1),
        "material_precision_pct": round(report.material_precision, 1),
        "material_recall_pct": round(report.material_recall, 1),
        "quantity_within_tolerance_pct": round(report.quantity_within_tolerance_pct, 1),
        "unit_match_pct": round(report.unit_match_pct, 1),
    }


def validate_enquiry(enquiry_id: str) -> dict:
    info = ENQUIRIES[enquiry_id]
    gold_path = GOLD_DIR / info["gold"]
    raw_source = info["source"]
    source_paths = [ENQUIRY_DIR / p for p in raw_source] if isinstance(raw_source, list) else [ENQUIRY_DIR / raw_source]

    log.info("Validating %s (%s)", enquiry_id, info["client"])
    log.info("  Gold: %s", gold_path)
    log.info("  Source: %s", source_paths)

    if not gold_path.exists():
        log.error("Gold file not found: %s", gold_path)
        return {"error": f"Gold file not found: {gold_path}"}

    missing_sources = [p for p in source_paths if not p.exists()]
    if missing_sources:
        log.error("Source file(s) not found: %s", missing_sources)
        return {"error": f"Source file(s) not found: {missing_sources}"}

    try:
        # Honest: use independent row-gold transcription (not pipeline output)
        gold_rows = _load_row_gold(enquiry_id)  # from the rowgold json, independent
        if not gold_rows:
            # fallback to entity gold assembled (still independent of prediction)
            gold_rows = _load_gold_boq_rows(enquiry_id)
        log.info("  Gold BOQ (independent): %d rows", len(gold_rows))
    except Exception as e:
        log.error("Failed to load gold BOQ rows: %s", e)
        return {"error": f"Failed to load gold: {e}"}

    try:
        pred_rows = _load_predicted_boq_rows(source_paths)
        log.info("  Predicted BOQ: %d rows", len(pred_rows))
    except Exception as e:
        log.error("Failed to run pipeline on %s: %s", source_paths, e)
        return {"error": f"Pipeline failed: {e}"}

    matcher = BOQRowMatcher(material_threshold=0.80, quantity_tolerance=0.05)
    report = matcher.match(pred_rows, gold_rows)
    summary = _summarize(report)

    per_row = []
    for m in report.per_row_details:
        entry = {
            "material_score": round(m.material_score, 3),
            "quantity_diff_pct": round(float(m.quantity_diff_pct) * 100, 1),
            "unit_match": m.unit_match,
            "is_tp": m.is_tp,
            "reason": m.reason,
        }
        if m.predicted_idx is not None:
            entry["predicted_material"] = pred_rows[m.predicted_idx].material
            entry["predicted_quantity"] = float(pred_rows[m.predicted_idx].quantity)
            entry["predicted_unit"] = pred_rows[m.predicted_idx].unit
        if m.gold_idx is not None:
            entry["gold_material"] = gold_rows[m.gold_idx].material
            entry["gold_quantity"] = float(gold_rows[m.gold_idx].quantity)
            entry["gold_unit"] = gold_rows[m.gold_idx].unit
        per_row.append(entry)

    result = {
        "enquiry_id": enquiry_id,
        "client": info["client"],
        "description": info["description"],
        "gold_count": len(gold_rows),
        "predicted_count": len(pred_rows),
        "summary": summary,
        "per_row": per_row,
    }

    log.info(
        "  %s: %d gold, %d predicted, %d TP, %d FP, %d FN, match_rate=%.1f%%",
        enquiry_id,
        len(gold_rows),
        len(pred_rows),
        report.tp,
        report.fp,
        report.fn,
        summary["match_rate_pct"],
    )

    return result


def generate_markdown_report(results: list[dict]) -> str:
    lines = [
        "# Product Validation Report",
        "",
        f"**Date:** {date.today().isoformat()}",
        "**Validation method:** Pipeline().run() on XLSX source → BOQRow list vs gold BOQ",
        "**Matcher:** Levenshtein ratio ≥ 0.80 (material), ±5% tolerance (quantity), canonical unit match",
        "",
    ]

    total_tp = sum(r["summary"]["tp"] for r in results if "summary" in r)
    total_fp = sum(r["summary"]["fp"] for r in results if "summary" in r)
    total_fn = sum(r["summary"]["fn"] for r in results if "summary" in r)
    total_gold = sum(r["gold_count"] for r in results if "gold_count" in r)
    total_pred = sum(r["predicted_count"] for r in results if "predicted_count" in r)
    total = total_tp + total_fp + total_fn
    overall_match = (total_tp / total * 100) if total > 0 else 0.0

    lines.append("## Overall Summary")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Gold BOQ rows (total) | {total_gold} |")
    lines.append(f"| Predicted rows (total) | {total_pred} |")
    lines.append(f"| True positives | {total_tp} |")
    lines.append(f"| False positives | {total_fp} |")
    lines.append(f"| False negatives | {total_fn} |")
    lines.append(f"| **Overall match rate** | **{overall_match:.1f}%** |")
    lines.append("")

    for r in results:
        if "error" in r:
            lines.append(f"## {r['enquiry_id']} — ERROR: {r['error']}")
            lines.append("")
            continue

        sid = r["enquiry_id"]
        verdict = "**SHIP IT**" if r["summary"]["match_rate_pct"] >= 70 else "**NOT shippable yet**"
        lines.append(f"## {sid} — {r['client']}")
        lines.append(f"**{r['description']}**")
        lines.append("")
        lines.append(f"- Gold BOQ rows: {r['gold_count']}")
        lines.append(f"- Predicted BOQ rows: {r['predicted_count']}")
        lines.append(f"- Matched correctly (TP): {r['summary']['tp']}")
        lines.append(f"- Wrong material (>20% Lev): {r['summary']['fp']}")
        lines.append(
            f"- Wrong quantity (>5% off): "
            f"{int(r['summary']['fn'] * (100 - r['summary']['quantity_within_tolerance_pct']) / 100)}"
            if r["summary"]["fn"] > 0
            else "- Wrong quantity (>5% off): 0"
        )
        lines.append(f"- Missed entirely (FN): {r['summary']['fn']}")
        lines.append(f"- **Match rate: {r['summary']['match_rate_pct']}%**")
        lines.append(f"- Material precision: {r['summary']['material_precision_pct']}%")
        lines.append(f"- Material recall: {r['summary']['material_recall_pct']}%")
        lines.append("")
        lines.append(f"**Verdict: {verdict}**")
        lines.append("")
        lines.append("### Per-row details (first 10)")
        lines.append("| # | Gold Material | Predicted Material | Score | Qty Diff | Unit | Match? |")
        lines.append("|---|---|---|---|---|---|---|")
        for i, row in enumerate(r["per_row"][:10], 1):
            gm = row.get("gold_material", "—")
            pm = row.get("predicted_material", "—")
            if gm and len(gm) > 40:
                gm = gm[:40] + "..."
            if pm and len(pm) > 40:
                pm = pm[:40] + "..."
            lines.append(
                f"| {i} | {gm} | {pm} | "
                f"{row['material_score']:.2f} | "
                f"{row['quantity_diff_pct']:.0f}% | "
                f"{'yes' if row['unit_match'] else 'no'} | "
                f"{'✓' if row['is_tp'] else '✗'} |"
            )
        lines.append("")

    lines.append("## Method Notes")
    lines.append("- **Material match:** Levenshtein ratio ≥ 0.80 after stripping stopwords")
    lines.append("- **Quantity match:** |pred - gold| / gold ≤ 5% (estimator round-off allowed)")
    lines.append("- **Unit match:** canonicalized via _normalize_unit() (sqm/SQM/sqm. → sqm)")
    lines.append(
        "- **Row is TP** if all three match. FP if predicted with no gold match. FN if gold with no predicted match."
    )
    lines.append("- Rate/Amount columns ignored (derived, not entity-level facts)")
    lines.append("- Section headers / sub-totals / Total rows excluded from both sides")
    lines.append("- Match rate < 50%: flagged NOT shippable yet (no soft language)")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate product against ground-truth BOQs")
    parser.add_argument(
        "--enquiry",
        default="all",
        choices=[
            "all",
            "01_gsecl_wanakbori_tmd8",
            "02_isro_vssc",
            "03_zydus_matoda_osd",
            "04_adani",
            "05_zydus_animal_pharmez",
            "06_avante_kirloskar_pune",
            "07_grew_solar_narmadapuram",
            "08_sael",
        ],
    )
    args = parser.parse_args()

    enquiry_ids = list(ENQUIRIES.keys()) if args.enquiry == "all" else [args.enquiry]

    all_results = []
    for eid in enquiry_ids:
        result = validate_enquiry(eid)
        all_results.append(result)

    results_path = RESULTS_DIR / "product_validation.json"
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2)
    log.info("Wrote %s", results_path)

    md = generate_markdown_report(all_results)
    md_path = RESULTS_DIR / "PRODUCT_VALIDATION_REPORT.md"
    md_path.write_text(md, encoding="utf-8")
    log.info("Wrote %s", md_path)

    total_tp = sum(r["summary"]["tp"] for r in all_results if "summary" in r)
    total_fp = sum(r["summary"]["fp"] for r in all_results if "summary" in r)
    total_fn = sum(r["summary"]["fn"] for r in all_results if "summary" in r)
    total = total_tp + total_fp + total_fn
    overall = (total_tp / total * 100) if total > 0 else 0.0

    print(f"\n{'='*60}")
    print(f"OVERALL MATCH RATE: {overall:.1f}% ({total_tp} TP / {total} total)")
    print(f"{'='*60}")

    for r in all_results:
        if "error" in r:
            print(f"  {r['enquiry_id']}: ERROR — {r['error']}")
        else:
            print(
                f"  {r['enquiry_id']} ({r['client']}): "
                f"{r['summary']['match_rate_pct']}% match "
                f"({r['summary']['tp']}/{r['gold_count']} gold)"
            )


if __name__ == "__main__":
    main()
