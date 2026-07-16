"""BOQ row-level matcher for ground-truth validation.

Compares predicted BOQ rows against ground-truth XLSX rows.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class MatchResult:
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int
    matched_pairs: list[tuple[dict, dict, float]]
    unmatched_predicted: list[dict]
    unmatched_truth: list[dict]


def _normalize_text(text: str | None) -> str:
    return (text or "").lower().strip().replace("  ", " ")


def _quantity_match(q1: Decimal | float | None, q2: Decimal | float | None) -> bool:
    if q1 is None or q2 is None:
        return False
    try:
        return abs(float(q1) - float(q2)) < 0.01
    except (ValueError, TypeError):
        return False


def _unit_match(u1: str | None, u2: str | None) -> bool:
    n1 = _normalize_text(u1)
    n2 = _normalize_text(u2)
    if n1 == n2:
        return True
    # Common aliases
    aliases = {
        "nos": {"nos", "no.", "no", "nr", "number", "numbers"},
        "kg": {"kg", "kgs", "kilogram", "kilograms"},
        "m": {"m", "meter", "metre", "meters", "metres", "rm", "r.m", "lm"},
        "m²": {"m²", "m2", "sqm", "sq.m", "sq.m.", "square meter", "square metre"},
        "m³": {"m³", "m3", "cum", "cu.m", "cu.m.", "cubic meter", "cubic metre"},
        "ltr": {"ltr", "liter", "litre", "liters", "litres", "l"},
        "t": {"t", "ton", "tonne", "tonnes", "mt", "metric ton"},
    }
    return any(n1 in alias_set and n2 in alias_set for _canonical, alias_set in aliases.items())


def _material_similarity(m1: str | None, m2: str | None) -> float:
    """Return 0-1 similarity between material descriptions."""
    s1 = _normalize_text(m1)
    s2 = _normalize_text(m2)
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0
    # Check if one contains the other
    if s1 in s2 or s2 in s1:
        return 0.85
    # Token overlap (Jaccard)
    tokens1 = set(s1.split())
    tokens2 = set(s2.split())
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    jaccard = len(intersection) / len(union)
    return jaccard


def match_boq_rows(
    predicted: list[dict],
    ground_truth: list[dict],
    material_threshold: float = 0.6,
) -> MatchResult:
    """Match predicted BOQ rows against ground truth.

    predicted/ground_truth items are dicts with keys:
        material (str), quantity (float/Decimal), unit (str)
    """
    matched_pairs: list[tuple[dict, dict, float]] = []
    used_truth: set[int] = set()
    used_pred: set[int] = set()

    # First pass: exact quantity + unit + high material similarity
    for pi, pred in enumerate(predicted):
        if pi in used_pred:
            continue
        best_match: tuple[int, float] | None = None
        for ti, truth in enumerate(ground_truth):
            if ti in used_truth:
                continue
            if not _quantity_match(pred.get("quantity"), truth.get("quantity")):
                continue
            if not _unit_match(pred.get("unit"), truth.get("unit")):
                continue
            sim = _material_similarity(pred.get("material"), truth.get("material"))
            if sim >= material_threshold and (best_match is None or sim > best_match[1]):
                best_match = (ti, sim)
        if best_match:
            ti, sim = best_match
            matched_pairs.append((pred, ground_truth[ti], sim))
            used_pred.add(pi)
            used_truth.add(ti)

    tp = len(matched_pairs)
    fp = len(predicted) - len(used_pred)
    fn = len(ground_truth) - len(used_truth)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    unmatched_predicted = [predicted[i] for i in range(len(predicted)) if i not in used_pred]
    unmatched_truth = [ground_truth[i] for i in range(len(ground_truth)) if i not in used_truth]

    return MatchResult(
        precision=precision,
        recall=recall,
        f1=f1,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        matched_pairs=matched_pairs,
        unmatched_predicted=unmatched_predicted,
        unmatched_truth=unmatched_truth,
    )


def format_match_report(result: MatchResult) -> str:
    lines = [
        "=" * 50,
        "BOQ Row-Match Report",
        "=" * 50,
        f"Precision: {result.precision:.2%}",
        f"Recall:    {result.recall:.2%}",
        f"F1:        {result.f1:.2%}",
        "",
        f"True Positives:  {result.true_positives}",
        f"False Positives: {result.false_positives}",
        f"False Negatives: {result.false_negatives}",
        "",
    ]
    if result.matched_pairs:
        lines.append("Matched pairs:")
        for pred, truth, sim in result.matched_pairs:
            lines.append(f"  [sim={sim:.2f}] {pred.get('material', '')} = {truth.get('material', '')}")
    if result.unmatched_predicted:
        lines.append("Predicted but not in ground truth:")
        for p in result.unmatched_predicted:
            lines.append(f"  - {p.get('material', '')} | qty={p.get('quantity', '')} {p.get('unit', '')}")
    if result.unmatched_truth:
        lines.append("Ground truth but not predicted:")
        for t in result.unmatched_truth:
            lines.append(f"  - {t.get('material', '')} | qty={t.get('quantity', '')} {t.get('unit', '')}")
    return "\n".join(lines)


if __name__ == "__main__":
    # Quick sanity test
    pred = [
        {"material": "M20 concrete", "quantity": 100.0, "unit": "m³"},
        {"material": "TMT steel bars", "quantity": 500.0, "unit": "kg"},
    ]
    truth = [
        {"material": "Concrete M20 grade", "quantity": 100.0, "unit": "m³"},
        {"material": "Steel TMT Fe500", "quantity": 500.0, "unit": "kg"},
        {"material": "Brickwork", "quantity": 1000.0, "unit": "nos"},
    ]
    result = match_boq_rows(pred, truth)
    print(format_match_report(result))
