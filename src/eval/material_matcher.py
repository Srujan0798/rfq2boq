"""Entity-level material matcher for the honest PDF eval (Z1).

Replaces the default `SequenceMatcher.ratio()` in `scripts/eval_honest.py`
with a three-signal matcher that tolerates the real-world asymmetry between
human gold (short canonical material phrase) and pipeline output (long BOQ
row sentence with action prefix, spec prefix, and reference suffix).

Three signals, evaluated in order:
  1. **Containment** — if ≥80% of the gold's tokens appear in the pred's
     tokens, count as match. Handles the "Mineral Wool" ⊂ "Bonded Mineral
     Wool Mattresses..." case.
  2. **Substring** — if the literal gold phrase (case-insensitive,
     whitespace-normalized) appears anywhere inside the pred string.
     Handles "Aluminum sheet" ⊂ "Aluminum sheet, self taping screws...".
  3. **Symmetric Jaccard ≥ 0.6** — token-level overlap ≥ 0.6. Final
     fallback. Same threshold as the original SequenceMatcher fallback in
     the boq_matcher module, which is the threshold we promised not to
     lower in Z1 constraints.

The matcher is asymmetric by design: a short gold can match a long pred
("gold ⊂ pred") but a long gold cannot match a short pred by the same
rule. This is correct — human gold for the SWA corpus is always short.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower().strip())


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", _normalize(text)) if len(t) > 1}


def containment_score(gold: str, pred: str) -> float:
    """Fraction of gold tokens (with length > 1) that appear in pred tokens.

    Returns 0.0 if either side is empty. Returns 1.0 if all gold tokens
    are present in pred tokens. Always ≤ 1.0.
    """
    g_tokens = _tokens(gold)
    p_tokens = _tokens(pred)
    if not g_tokens or not p_tokens:
        return 0.0
    return len(g_tokens & p_tokens) / len(g_tokens)


def substring_score(gold: str, pred: str) -> float:
    """1.0 if the normalized gold phrase appears as a substring of pred, else 0.0."""
    g = _normalize(gold)
    p = _normalize(pred)
    if not g or not p:
        return 0.0
    if g in p:
        return 1.0
    return 0.0


def jaccard_score(gold: str, pred: str) -> float:
    """Token-level Jaccard similarity (|A ∩ B| / |A ∪ B|)."""
    g_tokens = _tokens(gold)
    p_tokens = _tokens(pred)
    if not g_tokens or not p_tokens:
        return 0.0
    return len(g_tokens & p_tokens) / len(g_tokens | p_tokens)


def sequence_score(gold: str, pred: str) -> float:
    """Character-level SequenceMatcher ratio. Symmetric in length."""
    return SequenceMatcher(None, _normalize(gold), _normalize(pred)).ratio()


def match_material(
    gold: str,
    pred: str,
    containment_threshold: float = 0.8,
    substring_required: bool = True,
    jaccard_threshold: float = 0.6,
) -> tuple[bool, str, float]:
    """Decide whether a single gold matches a single pred.

    Returns (matched: bool, signal: str, score: float).
    signal is one of: "containment", "substring", "jaccard", "sequence",
    "no_match".
    """
    g = _normalize(gold)
    p = _normalize(pred)
    if not g or not p:
        return False, "no_match", 0.0

    cs = containment_score(g, p)
    if cs >= containment_threshold:
        return True, "containment", cs

    if substring_required and substring_score(g, p) == 1.0:
        return True, "substring", 1.0

    js = jaccard_score(g, p)
    if js >= jaccard_threshold:
        return True, "jaccard", js

    ss = sequence_score(g, p)
    if ss >= jaccard_threshold:
        return True, "sequence", ss

    return False, "no_match", max(cs, js, ss)


def match_materials_asymmetric(
    gold_mats: list[str],
    pred_mats: list[str],
    containment_threshold: float = 0.8,
    jaccard_threshold: float = 0.6,
) -> dict:
    """Match gold materials against predicted materials, allowing short gold
    to match long pred.

    Returns a dict compatible with the eval_honest.match_materials() output:
    tp, fp, fn, precision, recall, f1, pairs, unmatched_gold, unmatched_pred,
    plus a `signals` list for audit.
    """
    matched_gold: set[int] = set()
    matched_pred: set[int] = set()
    pairs: list[tuple[str, str, str, float]] = []
    signals: list[dict] = []

    for i, g in enumerate(gold_mats):
        best_j = -1
        best_signal = "no_match"
        best_score = 0.0
        for j, p in enumerate(pred_mats):
            if j in matched_pred:
                continue
            ok, signal, score = match_material(
                g,
                p,
                containment_threshold=containment_threshold,
                jaccard_threshold=jaccard_threshold,
            )
            if ok and score > best_score:
                best_j = j
                best_signal = signal
                best_score = score
        if best_j >= 0:
            matched_gold.add(i)
            matched_pred.add(best_j)
            pairs.append((g, pred_mats[best_j], best_signal, best_score))
            signals.append({"gold": g, "pred": pred_mats[best_j], "signal": best_signal, "score": best_score})

    tp = len(matched_gold)
    fp = len(pred_mats) - len(matched_pred)
    fn = len(gold_mats) - len(matched_gold)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "pairs": pairs,
        "signals": signals,
        "unmatched_gold": [g for i, g in enumerate(gold_mats) if i not in matched_gold],
        "unmatched_pred": [p for j, p in enumerate(pred_mats) if j not in matched_pred],
    }
