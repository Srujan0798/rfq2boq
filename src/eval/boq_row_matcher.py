"""Row-level fuzzy matcher comparing predicted BoqRows against ground-truth BoqRows."""

from dataclasses import dataclass, field

from src.domain.models import BoqRow
from src.rules.units import normalize_unit as _normalize_unit

STOPWORDS = frozenset({"of", "for", "to", "and", "the", "a", "an", "in", "on", "at", "by"})


def _strip_stopwords(text: str) -> str:
    return " ".join(w for w in text.lower().split() if w not in STOPWORDS)


def _levenshtein_ratio(a: str, b: str) -> float:
    """Return 0..1 similarity ratio. 1.0 = identical."""
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    len_a, len_b = len(a), len(b)
    prev = list(range(len_b + 1))
    curr = [0] * (len_b + 1)
    for i in range(1, len_a + 1):
        curr[0] = i
        for j in range(1, len_b + 1):
            cost = 0 if a[i - 1].lower() == b[j - 1].lower() else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
        prev, curr = curr, prev
    distance = prev[len_b]
    max_len = max(len_a, len_b)
    return 1.0 - distance / max_len


@dataclass
class RowMatch:
    predicted_idx: int | None
    gold_idx: int | None
    material_score: float
    quantity_diff_pct: float
    unit_match: bool
    is_tp: bool
    reason: str
    match_type: str = "1:1"  # "1:1", "1:N", "N:1"


@dataclass
class MatchReport:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    material_precision: float = 0.0
    material_recall: float = 0.0
    quantity_within_tolerance_pct: float = 0.0
    unit_match_pct: float = 0.0
    per_row_details: list[RowMatch] = field(default_factory=list)


class BOQRowMatcher:
    def __init__(
        self,
        material_threshold: float = 0.80,
        quantity_tolerance: float = 0.05,
    ):
        self.material_threshold = material_threshold
        self.quantity_tolerance = quantity_tolerance

    def match(
        self,
        predicted: list[BoqRow],
        ground_truth: list[BoqRow],
    ) -> MatchReport:
        """
        Match predicted BOQ rows against ground truth using 1:1, 1:N, and N:1 strategies.

        Strategy:
        - N:1: Multiple consecutive predicted rows combine to match one gold row.
          Used when gold row has composite material like "50mm thick mineral wool"
          but predicted splits it into MATERIAL + DIMENSION rows.
        - 1:N: One predicted row matches multiple consecutive gold rows.
          Used when gold has separate rows but predicted combines them.
        - 1:1: Standard best-bid matching when N:1/1:N don't apply.
        """
        report = MatchReport()
        used_pred: set[int] = set()
        used_gold: set[int] = set()

        # --- Phase 1: N:1 detection ---
        # Multiple predicted rows combine to match one gold row
        for g_idx, gold_row in enumerate(ground_truth):
            if g_idx in used_gold:
                continue

            gold_tokens = set(_strip_stopwords(gold_row.material).split())
            gold_unit_norm = _normalize_unit(gold_row.unit or "")
            gold_qty = float(gold_row.quantity or 0)

            # Skip N:1 if any single unused predicted row already matches well.
            # Prevents greedy merges when an exact 1:1 match exists elsewhere.
            single_match_exists = False
            for p_idx, pred_row in enumerate(predicted):
                if p_idx in used_pred:
                    continue
                if _normalize_unit(pred_row.unit or "") != gold_unit_norm:
                    continue
                pred_tokens_single = set(_strip_stopwords(pred_row.material).split())
                o = len(gold_tokens & pred_tokens_single)
                u = len(gold_tokens | pred_tokens_single)
                s = o / u if u > 0 else 0.0
                if s >= self.material_threshold and o >= len(gold_tokens) * 0.8:
                    single_match_exists = True
                    break

            best_n1_score = 0.0
            best_n1_pred_indices: list[int] = []

            if single_match_exists:
                # Let 1:1 matching handle this gold row
                continue

            for start_p in range(len(predicted)):
                if start_p in used_pred:
                    continue

                for end_p in range(start_p, min(start_p + 3, len(predicted))):
                    if end_p in used_pred:
                        continue

                    seq = predicted[start_p : end_p + 1]
                    seq_units = [_normalize_unit(r.unit or "") for r in seq]
                    if len(set(seq_units)) != 1 or seq_units[0] != gold_unit_norm:
                        continue

                    seq_mat_tokens = set()
                    for r in seq:
                        seq_mat_tokens.update(_strip_stopwords(r.material).split())

                    overlap = len(gold_tokens & seq_mat_tokens)
                    union = len(gold_tokens | seq_mat_tokens)
                    token_jaccard = overlap / union if union > 0 else 0.0

                    # Guard: if any single row in the sequence already covers
                    # the gold row nearly as well, prefer 1:1 matching instead
                    # of forcing an N:1 merge.
                    best_single_score = 0.0
                    for r in seq:
                        r_tokens = set(_strip_stopwords(r.material).split())
                        o = len(gold_tokens & r_tokens)
                        u = len(gold_tokens | r_tokens)
                        s = o / u if u > 0 else 0.0
                        if s > best_single_score:
                            best_single_score = s

                    if token_jaccard > best_n1_score and overlap >= len(gold_tokens) * 0.6:
                        best_n1_score = token_jaccard
                        best_n1_pred_indices = list(range(start_p, end_p + 1))
                        # Mark if a single row is good enough; we'll skip N:1
                        if best_single_score >= self.material_threshold:
                            best_n1_pred_indices = []

            if best_n1_pred_indices and len(best_n1_pred_indices) >= 2 and best_n1_score >= 0.6:
                combined_qty = sum(float(predicted[i].quantity or 0) for i in best_n1_pred_indices)
                qty_diff = (
                    abs(combined_qty - gold_qty) / gold_qty
                    if gold_qty != 0.0
                    else (0.0 if combined_qty == 0.0 else 1.0)
                )
                is_tp = qty_diff <= self.quantity_tolerance

                for p_idx in best_n1_pred_indices:
                    used_pred.add(p_idx)
                used_gold.add(g_idx)

                report.per_row_details.append(
                    RowMatch(
                        predicted_idx=best_n1_pred_indices[0],
                        gold_idx=g_idx,
                        material_score=best_n1_score,
                        quantity_diff_pct=qty_diff,
                        unit_match=True,
                        is_tp=is_tp,
                        reason=f"N:1 merge ({len(best_n1_pred_indices)} rows), token_jaccard={best_n1_score:.2f}",
                        match_type="N:1",
                    )
                )
                if is_tp:
                    report.tp += 1
                else:
                    report.fp += 1
                    report.fn += 1
                continue

        # --- Phase 2: 1:N detection ---
        # One predicted row matches multiple consecutive gold rows
        for p_idx, pred_row in enumerate(predicted):
            if p_idx in used_pred:
                continue

            pred_tokens = set(_strip_stopwords(pred_row.material).split())
            pred_unit_norm = _normalize_unit(pred_row.unit or "")
            pred_qty = float(pred_row.quantity or 0)

            # Skip 1:N if any single unused gold row already matches well.
            single_match_exists = False
            for g_idx, gold_row in enumerate(ground_truth):
                if g_idx in used_gold:
                    continue
                if _normalize_unit(gold_row.unit or "") != pred_unit_norm:
                    continue
                gold_tokens_single = set(_strip_stopwords(gold_row.material).split())
                o = len(pred_tokens & gold_tokens_single)
                u = len(pred_tokens | gold_tokens_single)
                s = o / u if u > 0 else 0.0
                if s >= self.material_threshold and o >= len(pred_tokens) * 0.8:
                    single_match_exists = True
                    break

            best_1n_score = 0.0
            best_1n_gold_indices: list[int] = []

            if single_match_exists:
                # Let 1:1 matching handle this predicted row
                continue

            for start_g in range(len(ground_truth)):
                if start_g in used_gold:
                    continue

                for end_g in range(start_g, min(start_g + 3, len(ground_truth))):
                    if end_g in used_gold:
                        continue

                    seq = ground_truth[start_g : end_g + 1]
                    seq_units = [_normalize_unit(r.unit or "") for r in seq]
                    if len(set(seq_units)) != 1 or seq_units[0] != pred_unit_norm:
                        continue

                    seq_mat_tokens = set()
                    for r in seq:
                        seq_mat_tokens.update(_strip_stopwords(r.material).split())

                    overlap = len(pred_tokens & seq_mat_tokens)
                    union = len(pred_tokens | seq_mat_tokens)
                    token_jaccard = overlap / union if union > 0 else 0.0

                    if token_jaccard > best_1n_score and overlap >= len(seq_mat_tokens) * 0.6:
                        best_1n_score = token_jaccard
                        best_1n_gold_indices = list(range(start_g, end_g + 1))

            if best_1n_gold_indices and len(best_1n_gold_indices) >= 2 and best_1n_score >= 0.5:
                combined_qty = sum(float(ground_truth[i].quantity or 0) for i in best_1n_gold_indices)
                qty_diff = (
                    abs(float(pred_qty) - combined_qty) / combined_qty
                    if combined_qty != 0.0
                    else (0.0 if pred_qty == 0.0 else 1.0)
                )
                is_tp = qty_diff <= self.quantity_tolerance

                used_pred.add(p_idx)
                for g_idx in best_1n_gold_indices:
                    used_gold.add(g_idx)

                report.per_row_details.append(
                    RowMatch(
                        predicted_idx=p_idx,
                        gold_idx=best_1n_gold_indices[0],
                        material_score=best_1n_score,
                        quantity_diff_pct=qty_diff,
                        unit_match=True,
                        is_tp=is_tp,
                        reason=f"1:N expand ({len(best_1n_gold_indices)} rows), token_jaccard={best_1n_score:.2f}",
                        match_type="1:N",
                    )
                )
                if is_tp:
                    report.tp += 1
                else:
                    report.fp += 1
                    report.fn += 1
                continue

        # --- Phase 3: Standard 1:1 matching ---
        for g_idx, gold_row in enumerate(ground_truth):
            if g_idx in used_gold:
                continue

            best_pred_idx: int | None = None
            best_score = 0.0
            best_reason = ""

            for p_idx, pred_row in enumerate(predicted):
                if p_idx in used_pred:
                    continue

                mat_score = _levenshtein_ratio(
                    _strip_stopwords(pred_row.material),
                    _strip_stopwords(gold_row.material),
                )
                if mat_score < best_score:
                    continue

                qty_gold = float(gold_row.quantity or 0.0)
                qty_pred = float(pred_row.quantity or 0.0)
                if qty_gold != 0.0:
                    qty_diff_pct = abs(qty_pred - qty_gold) / abs(qty_gold)
                else:
                    qty_diff_pct = 0.0 if qty_pred == 0.0 else 1.0

                unit_match = _normalize_unit(pred_row.unit or "") == _normalize_unit(gold_row.unit or "")

                reasons: list[str] = []
                if mat_score >= self.material_threshold:
                    reasons.append(f"material={mat_score:.2f}")
                if qty_diff_pct <= self.quantity_tolerance:
                    reasons.append("qty_ok")
                else:
                    reasons.append(f"qty_off={qty_diff_pct:.0%}")
                if unit_match:
                    reasons.append("unit_ok")

                is_tp = mat_score >= self.material_threshold and qty_diff_pct <= self.quantity_tolerance and unit_match
                reason = "; ".join(reasons)

                if mat_score > best_score:
                    best_score = mat_score
                    best_pred_idx = p_idx
                    best_reason = reason

            if best_pred_idx is not None and best_score >= self.material_threshold:
                g_qty = float(gold_row.quantity or 0)
                p_qty = float(predicted[best_pred_idx].quantity or 0)
                qty_diff = abs(p_qty - g_qty) / g_qty if g_qty != 0.0 else (0.0 if p_qty == 0.0 else 1.0)
                unit_ok = _normalize_unit(predicted[best_pred_idx].unit or "") == _normalize_unit(gold_row.unit or "")
                is_tp = qty_diff <= self.quantity_tolerance and unit_ok

                report.per_row_details.append(
                    RowMatch(
                        predicted_idx=best_pred_idx,
                        gold_idx=g_idx,
                        material_score=best_score,
                        quantity_diff_pct=qty_diff,
                        unit_match=unit_ok,
                        is_tp=is_tp,
                        reason=best_reason,
                        match_type="1:1",
                    )
                )
                used_pred.add(best_pred_idx)
                used_gold.add(g_idx)
                if is_tp:
                    report.tp += 1
                else:
                    report.fp += 1
                    report.fn += 1
            else:
                report.per_row_details.append(
                    RowMatch(
                        predicted_idx=None,
                        gold_idx=g_idx,
                        material_score=best_score,
                        quantity_diff_pct=1.0,
                        unit_match=False,
                        is_tp=False,
                        reason=f"no_match (best_mat={best_score:.2f}, {best_reason})",
                        match_type="1:1",
                    )
                )
                used_gold.add(g_idx)
                report.fn += 1

        # --- Phase 4: Remaining predicted rows are FP ---
        remaining_preds = [(i, r) for i, r in enumerate(predicted) if i not in used_pred]
        for p_idx, _pred_row in remaining_preds:
            report.per_row_details.append(
                RowMatch(
                    predicted_idx=p_idx,
                    gold_idx=None,
                    material_score=0.0,
                    quantity_diff_pct=1.0,
                    unit_match=False,
                    is_tp=False,
                    reason="extra_row",
                    match_type="1:1",
                )
            )
            report.fp += 1

        total_gold = len(ground_truth)

        tp_qty_ok = sum(
            1
            for m in report.per_row_details
            if m.predicted_idx is not None and m.quantity_diff_pct <= self.quantity_tolerance
        )
        tp_unit_ok = sum(1 for m in report.per_row_details if m.predicted_idx is not None and m.unit_match)

        report.quantity_within_tolerance_pct = tp_qty_ok / report.tp * 100 if report.tp > 0 else 0.0
        report.unit_match_pct = tp_unit_ok / report.tp * 100 if report.tp > 0 else 0.0

        total_matched = report.tp + report.fp
        report.material_precision = report.tp / total_matched * 100 if total_matched > 0 else 0.0
        report.material_recall = report.tp / total_gold * 100 if total_gold > 0 else 0.0

        return report
