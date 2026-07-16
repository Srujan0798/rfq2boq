#!/usr/bin/env python3
"""Fair product evaluation — independent row-gold + entity-level scoring.

Single entry point that reports:
  1. Row-level match rate vs independent row-gold (for 4 XLSX enquiries)
  2. Entity-level precision/recall/F1 vs human entity-gold (for all gold enquiries)

All gold is produced independently of the prediction pipeline.
Row-gold: data/real_rfqs/gold/rows/<id>.rowgold.json (transcribed from XLSX by build_row_gold.py)
Entity-gold: data/real_rfqs/gold/swa_*.json (human annotations)

Usage:
    python3 scripts/eval_product.py --enquiry all --level all
    python3 scripts/eval_product.py --enquiry 08_sael --level row
    python3 scripts/eval_product.py --level entity
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.models import BoqRow, EntitySpan, EntityType
from src.eval.boq_row_matcher import BOQRowMatcher
from src.pipeline import Pipeline

GOLD_DIR = Path("data/real_rfqs/gold")
ENQUIRY_DIR = Path("data/real_rfqs/swa_enquiries")
ROW_GOLD_DIR = Path("data/real_rfqs/gold/rows")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

ENQUIRIES: dict[str, dict] = {
    "02_isro_vssc": {
        "gold": "swa_02_isro_vssc.json",
        "row_gold": "02_isro_vssc.rowgold.json",
        "source": "02_isro_vssc/VSSC_BOQ_with_qty.xlsx",
        "client": "ISRO VSSC",
        "description": "Incremental qty BOQ — aerospace facility",
        "has_row_gold": True,
    },
    "03_zydus_matoda_osd": {
        "gold": "swa_03_zydus_matoda_osd.json",
        "row_gold": "03_zydus_matoda_osd.rowgold.json",
        "source": "03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx",
        "client": "Zydus Pharma Matoda",
        "description": "OSD facility insulation",
        "has_row_gold": True,
    },
    "05_zydus_animal_pharmez": {
        "gold": "swa_05_zydus_animal_pharmez.json",
        "row_gold": "05_zydus_animal_pharmez.rowgold.json",
        "source": "05_zydus_animal_pharmez/Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx",
        "client": "Zydus Animal Health",
        "description": "Pharmez Ahmedabad expansion",
        "has_row_gold": True,
    },
    "08_sael": {
        "gold": "swa_08_sael.json",
        "row_gold": "08_sael.rowgold.json",
        "source": "08_sael/Copy of Insulation Enquiry - SAEL.xlsx",
        "client": "SAEL",
        "description": "Insulation enquiry",
        "has_row_gold": True,
    },
}


def _load_row_gold(enquiry_id: str) -> list[BoqRow]:
    path = ROW_GOLD_DIR / ENQUIRIES[enquiry_id]["row_gold"]
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


def _load_predicted_boq_rows(xlsx_path: Path) -> list[BoqRow]:
    result = Pipeline().run(str(xlsx_path))
    return result.boq_items


def _load_entity_gold(enquiry_id: str) -> tuple[list[EntitySpan], list]:
    gold_path = GOLD_DIR / ENQUIRIES[enquiry_id]["gold"]
    if not gold_path.exists():
        return [], []
    with open(gold_path) as fh:
        d = json.load(fh)
    entities: list[EntitySpan] = []
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
    relations: list = d.get("relations", [])
    return entities, relations


def _load_predicted_entities(xlsx_path: Path) -> tuple[list[EntitySpan], list]:
    result = Pipeline().run(str(xlsx_path))
    return result.entities, result.relations


def _micro_entity_metrics(
    predicted: list[EntitySpan],
    gold: list[EntitySpan],
) -> dict:
    types = list(EntityType)
    total_tp = total_fp = total_fn = 0
    type_details = {}
    for t in types:
        pred_of_type = [e for e in predicted if e.type == t]
        gold_of_type = [e for e in gold if e.type == t]
        tp = sum(1 for p in pred_of_type if any(p.text.strip() == g.text.strip() for g in gold_of_type))
        fp = len(pred_of_type) - tp
        fn = len(gold_of_type) - tp
        total_tp += tp
        total_fp += fp
        total_fn += fn
        type_details[t.value] = {"tp": tp, "fp": fp, "fn": fn, "pred_n": len(pred_of_type), "gold_n": len(gold_of_type)}
    micro_p = total_tp / (total_tp + total_fp) * 100 if (total_tp + total_fp) > 0 else 0.0
    micro_r = total_tp / (total_tp + total_fn) * 100 if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0.0
    return {
        "micro_precision": round(micro_p, 1),
        "micro_recall": round(micro_r, 1),
        "micro_f1": round(micro_f1, 1),
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "by_type": type_details,
    }


def _row_level_summary(report) -> dict:
    total = report.tp + report.fp + report.fn
    match_rate = report.tp / total * 100 if total > 0 else 0.0
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


def evaluate_row_level(enquiry_id: str) -> dict:
    info = ENQUIRIES[enquiry_id]
    source_path = ENQUIRY_DIR / info["source"]
    row_gold_path = ROW_GOLD_DIR / info["row_gold"]

    if not source_path.exists():
        return {"enquiry_id": enquiry_id, "error": f"XLSX not found: {source_path}"}
    if not row_gold_path.exists():
        return {"enquiry_id": enquiry_id, "error": f"Row gold not found: {row_gold_path}"}

    gold_rows = _load_row_gold(enquiry_id)
    pred_rows = _load_predicted_boq_rows(source_path)

    matcher = BOQRowMatcher(material_threshold=0.80, quantity_tolerance=0.05)
    report = matcher.match(pred_rows, gold_rows)
    summary = _row_level_summary(report)

    per_row = []
    for m in report.per_row_details:
        entry = {
            "material_score": round(m.material_score, 3),
            "quantity_diff_pct": round(float(m.quantity_diff_pct) * 100, 1),
            "unit_match": m.unit_match,
            "is_tp": m.is_tp,
            "reason": m.reason,
            "match_type": m.match_type,
        }
        if m.predicted_idx is not None and m.predicted_idx < len(pred_rows):
            entry["predicted_material"] = pred_rows[m.predicted_idx].material
            entry["predicted_quantity"] = float(pred_rows[m.predicted_idx].quantity)
            entry["predicted_unit"] = pred_rows[m.predicted_idx].unit
        if m.gold_idx is not None and m.gold_idx < len(gold_rows):
            entry["gold_material"] = gold_rows[m.gold_idx].material
            entry["gold_quantity"] = float(gold_rows[m.gold_idx].quantity)
            entry["gold_unit"] = gold_rows[m.gold_idx].unit
        per_row.append(entry)

    return {
        "enquiry_id": enquiry_id,
        "client": info["client"],
        "description": info["description"],
        "gold_count": len(gold_rows),
        "predicted_count": len(pred_rows),
        "summary": summary,
        "per_row": per_row,
    }


def evaluate_entity_level(enquiry_id: str) -> dict:
    info = ENQUIRIES[enquiry_id]
    source_path = ENQUIRY_DIR / info["source"]

    if not source_path.exists():
        return {"enquiry_id": enquiry_id, "error": f"XLSX not found: {source_path}"}

    gold_entities, _ = _load_entity_gold(enquiry_id)
    pred_entities, _ = _load_predicted_entities(source_path)

    metrics = _micro_entity_metrics(pred_entities, gold_entities)

    return {
        "enquiry_id": enquiry_id,
        "client": info["client"],
        "description": info["description"],
        "gold_entity_count": len(gold_entities),
        "predicted_entity_count": len(pred_entities),
        "micro_precision": metrics["micro_precision"],
        "micro_recall": metrics["micro_recall"],
        "micro_f1": metrics["micro_f1"],
        "total_tp": metrics["total_tp"],
        "total_fp": metrics["total_fp"],
        "total_fn": metrics["total_fn"],
        "by_type": metrics["by_type"],
    }


def generate_markdown(row_results: list[dict], entity_results: list[dict]) -> str:
    lines = [
        "# Product Evaluation Report — Fair Assessment",
        "",
        f"**Date:** {date.today().isoformat()}",
        "**Method:** Gold produced independently of prediction pipeline",
        "  - Row-gold: transcribed from XLSX by `scripts/build_row_gold.py` (no pipeline imports)",
        "  - Entity-gold: human-annotated `data/real_rfqs/gold/swa_*.json`",
        "  - Predicted: `Pipeline().run()` on source XLSX",
        "",
    ]

    if row_results:
        lines.append("## Row-Level Match Rate (vs independent row-gold)")
        for r in row_results:
            if "error" in r:
                lines.append(f"### {r['enquiry_id']} — ERROR: {r['error']}")
                continue
            sid = r["enquiry_id"]
            lines.append(f"### {sid} — {r['client']} ({r['description']})")
            lines.append(f"- Row-gold rows: {r['gold_count']}")
            lines.append(f"- Predicted rows: {r['predicted_count']}")
            lines.append(f"- Match rate: **{r['summary']['match_rate_pct']}%**")
            lines.append(f"  - TP: {r['summary']['tp']}, FP: {r['summary']['fp']}, FN: {r['summary']['fn']}")
            lines.append(f"  - Material precision: {r['summary']['material_precision_pct']}%")
            lines.append(f"  - Material recall: {r['summary']['material_recall_pct']}%")
            lines.append(f"  - Quantity within ±5%: {r['summary']['quantity_within_tolerance_pct']}%")
            lines.append(f"  - Unit match: {r['summary']['unit_match_pct']}%")
            lines.append("")

        row_aggs = [r for r in row_results if "summary" in r]
        if row_aggs:
            total_tp = sum(r["summary"]["tp"] for r in row_aggs)
            total_fp = sum(r["summary"]["fp"] for r in row_aggs)
            total_fn = sum(r["summary"]["fn"] for r in row_aggs)
            total = total_tp + total_fp + total_fn
            overall = total_tp / total * 100 if total > 0 else 0.0
            lines.append(f"**Overall row-level match rate: {overall:.1f}%** ({total_tp}/{total})")
            lines.append("")

    if entity_results:
        lines.append("## Entity-Level P/R/F1 (vs human entity-gold)")
        all_tp = sum(r["total_tp"] for r in entity_results)
        all_fp = sum(r["total_fp"] for r in entity_results)
        all_fn = sum(r["total_fn"] for r in entity_results)
        all_p = all_tp / (all_tp + all_fp) * 100 if (all_tp + all_fp) > 0 else 0.0
        all_r = all_tp / (all_tp + all_fn) * 100 if (all_tp + all_fn) > 0 else 0.0
        all_f1 = 2 * all_p * all_r / (all_p + all_r) if (all_p + all_r) > 0 else 0.0

        lines.append(f"**Micro-averaged across {len(entity_results)} enquiries:**")
        lines.append("| Metric | Value |")
        lines.append("|---|---|")
        lines.append(f"| Micro Precision | {all_p:.1f}% |")
        lines.append(f"| Micro Recall | {all_r:.1f}% |")
        lines.append(f"| **Micro F1** | **{all_f1:.1f}%** |")
        lines.append("")
        lines.append("| Enquiry | Gold | Predicted | Prec% | Rec% | F1 |")
        lines.append("|---|---|---|---|---|---|")
        for r in entity_results:
            lines.append(
                f"| {r['enquiry_id']} | {r['gold_entity_count']} | {r['predicted_entity_count']} "
                f"| {r['micro_precision']} | {r['micro_recall']} | {r['micro_f1']} |"
            )
        lines.append("")

        lines.append("### Per-entity-type micro F1 (aggregated)")
        type_rows = []
        for etype in EntityType:
            tp = sum(r.get("by_type", {}).get(etype.value, {}).get("tp", 0) for r in entity_results)
            fp = sum(r.get("by_type", {}).get(etype.value, {}).get("fp", 0) for r in entity_results)
            fn = sum(r.get("by_type", {}).get(etype.value, {}).get("fn", 0) for r in entity_results)
            p = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0.0
            f1 = 2 * p * rec / (p + rec) if (p + rec) > 0 else 0.0
            type_rows.append((etype.value, tp, fp, fn, p, rec, f1))
        lines.append("| Entity Type | TP | FP | FN | Prec% | Rec% | F1 |")
        lines.append("|---|---|---|---|---|---|---|")
        for etype, tp, fp, fn, p, rec, f1 in type_rows:
            if tp + fp + fn > 0:
                lines.append(f"| {etype} | {tp} | {fp} | {fn} | {p:.1f} | {rec:.1f} | {f1:.1f} |")
        lines.append("")

    lines.append("## Notes")
    lines.append("- Row matching: Levenshtein ratio ≥ 0.80 (material), ±5% tolerance (quantity), canonical unit match")
    lines.append(
        "- Row-gold is independent of Pipeline (build_row_gold.py does not import src.pipeline or BOQAssembler)"
    )
    lines.append("- Entity-gold is human-annotated; entity match = exact text equality (case-insensitive)")
    lines.append("- 05_zydus_animal_pharmez row-gold: quantity = SUM of all system qty columns (multi-column sheet)")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fair product evaluation")
    parser.add_argument(
        "--enquiry",
        default="all",
        choices=["all", "02_isro_vssc", "03_zydus_matoda_osd", "05_zydus_animal_pharmez", "08_sael"],
    )
    parser.add_argument("--level", default="all", choices=["all", "row", "entity"])
    args = parser.parse_args()

    enquiry_ids = list(ENQUIRIES.keys()) if args.enquiry == "all" else [args.enquiry]

    row_results: list[dict] = []
    entity_results: list[dict] = []

    if args.level in ("all", "row"):
        print("=== ROW-LEVEL EVALUATION ===")
        for eid in enquiry_ids:
            if not ENQUIRIES[eid].get("has_row_gold"):
                continue
            print(f"  Evaluating {eid}...")
            try:
                result = evaluate_row_level(eid)
                row_results.append(result)
                if "error" not in result:
                    print(
                        f"    gold={result['gold_count']} pred={result['predicted_count']} "
                        f"match_rate={result['summary']['match_rate_pct']}%"
                    )
            except Exception as e:
                print(f"    ERROR: {e}")
                row_results.append({"enquiry_id": eid, "error": str(e)})

    if args.level in ("all", "entity"):
        print("\n=== ENTITY-LEVEL EVALUATION ===")
        for eid in enquiry_ids:
            gold_path = GOLD_DIR / ENQUIRIES[eid]["gold"]
            if not gold_path.exists():
                print(f"  [SKIP] {eid}: no entity-gold")
                continue
            print(f"  Evaluating {eid}...")
            try:
                result = evaluate_entity_level(eid)
                entity_results.append(result)
                if "error" not in result:
                    print(
                        f"    gold={result['gold_entity_count']} pred={result['predicted_entity_count']} "
                        f"P={result['micro_precision']} R={result['micro_recall']} F1={result['micro_f1']}"
                    )
            except Exception as e:
                print(f"    ERROR: {e}")
                entity_results.append({"enquiry_id": eid, "error": str(e)})

    results_payload = {
        "date": str(date.today()),
        "row_level": row_results,
        "entity_level": entity_results,
    }
    results_path = RESULTS_DIR / "product_eval.json"
    with open(results_path, "w") as f:
        json.dump(results_payload, f, indent=2)
    print(f"\nWrote {results_path}")

    md = generate_markdown(row_results, entity_results)
    md_path = RESULTS_DIR / "PRODUCT_EVAL.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Wrote {md_path}")

    if row_results and all("error" not in r for r in row_results):
        total_tp = sum(r["summary"]["tp"] for r in row_results if "summary" in r)
        total_fp = sum(r["summary"]["fp"] for r in row_results if "summary" in r)
        total_fn = sum(r["summary"]["fn"] for r in row_results if "summary" in r)
        total = total_tp + total_fp + total_fn
        overall = total_tp / total * 100 if total > 0 else 0.0
        print(f"\n=== ROW-LEVEL SUMMARY: {overall:.1f}% ({total_tp}/{total}) ===")

    if entity_results and all("error" not in r for r in entity_results):
        all_tp = sum(r["total_tp"] for r in entity_results)
        all_fp = sum(r["total_fp"] for r in entity_results)
        all_fn = sum(r["total_fn"] for r in entity_results)
        p = all_tp / (all_tp + all_fp) * 100 if (all_tp + all_fp) > 0 else 0.0
        r = all_tp / (all_tp + all_fn) * 100 if (all_tp + all_fn) > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        print(f"\n=== ENTITY-LEVEL SUMMARY: P={p:.1f}% R={r:.1f}% F1={f1:.1f}% ===")


if __name__ == "__main__":
    main()
