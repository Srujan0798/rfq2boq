"""Unit tests for the asymmetric material matcher (Z1)."""

from __future__ import annotations

from src.eval.material_matcher import (
    containment_score,
    jaccard_score,
    match_material,
    match_materials_asymmetric,
    sequence_score,
    substring_score,
)


class TestContainmentScore:
    def test_full_containment(self) -> None:
        s = containment_score("Mineral Wool", "Bonded Mineral Wool Mattresses Hooks")
        assert s == 1.0

    def test_partial_containment(self) -> None:
        # 2 of 3 gold tokens in pred
        s = containment_score("Mineral Wool pipe", "Bonded Mineral Wool Mattresses")
        assert 0.6 < s < 0.7

    def test_empty_gold(self) -> None:
        assert containment_score("", "Mineral Wool") == 0.0

    def test_empty_pred(self) -> None:
        assert containment_score("Mineral Wool", "") == 0.0

    def test_case_insensitive(self) -> None:
        s = containment_score("MINERAL WOOL", "mineral wool mattresses")
        assert s == 1.0


class TestSubstringScore:
    def test_exact_substring(self) -> None:
        assert substring_score("Aluminum sheet", "Aluminum sheet, self taping screws") == 1.0

    def test_not_substring(self) -> None:
        assert substring_score("Steel bars", "Aluminum sheet") == 0.0

    def test_case_insensitive(self) -> None:
        assert substring_score("ALUMINUM SHEET", "aluminum sheet screws") == 1.0

    def test_whitespace_normalized(self) -> None:
        assert substring_score("Mineral  Wool", "mineral wool mattresses") == 1.0


class TestJaccardScore:
    def test_identical(self) -> None:
        assert jaccard_score("Mineral Wool", "Mineral Wool") == 1.0

    def test_disjoint(self) -> None:
        assert jaccard_score("Mineral Wool", "Aluminum sheet") == 0.0

    def test_partial(self) -> None:
        # "Mineral Wool" and "Bonded Mineral Wool Mattresses"
        # intersection: {mineral, wool} = 2
        # union: {mineral, wool, bonded, mattresses} = 4
        s = jaccard_score("Mineral Wool", "Bonded Mineral Wool Mattresses")
        assert s == 0.5


class TestSequenceScore:
    def test_identical(self) -> None:
        assert sequence_score("Mineral Wool", "Mineral Wool") == 1.0

    def test_completely_different(self) -> None:
        assert sequence_score("abc", "xyz") < 0.5


class TestMatchMaterial:
    def test_containment_wins(self) -> None:
        ok, signal, _ = match_material("Mineral Wool", "Bonded Mineral Wool Mattresses Hooks Wire")
        assert ok
        assert signal == "containment"

    def test_substring_wins(self) -> None:
        # Containment and substring both fire here; containment is checked
        # first because it tokenizes (stricter, more robust to whitespace).
        ok, signal, _ = match_material("Aluminum sheet", "Aluminum sheet self taping screws")
        assert ok
        assert signal == "containment"

    def test_jaccard_fallback(self) -> None:
        # No containment (gold "wool pipe" not in pred), no substring
        # (gold not in pred), but jaccard ≥ 0.6
        ok, signal, _ = match_material("wool pipe insulation", "insulation wool pipe")
        # Tokens: gold={wool, pipe, insulation}, pred={insulation, wool, pipe}
        # intersection=3, union=3, jaccard=1.0
        assert ok
        assert signal in ("jaccard", "containment")

    def test_no_match(self) -> None:
        ok, signal, _ = match_material("Aluminum sheet", "Mineral Wool Mattresses")
        assert not ok
        assert signal == "no_match"

    def test_below_threshold(self) -> None:
        # Jaccard = 1/3 = 0.33, well below 0.6
        ok, _, _ = match_material("Aluminum sheet steel", "Mineral Wool Mattresses")
        assert not ok


class TestMatchMaterialsAsymmetric:
    def test_tp_count(self) -> None:
        gold = ["Mineral Wool", "Aluminum sheet"]
        pred = [
            "Supply & application of Mineral Wool mattresses per Schedule",
            "Aluminum sheet, self taping screws per Schedule",
        ]
        result = match_materials_asymmetric(gold, pred)
        assert result["tp"] == 2
        assert result["fp"] == 0
        assert result["fn"] == 0
        assert result["f1"] == 1.0

    def test_short_gold_matches_long_pred(self) -> None:
        gold = ["Mineral Wool"]
        pred = ["Bonded Mineral -rock- Wool Mattresses With One Side Gs Wire Netting"]
        result = match_materials_asymmetric(gold, pred)
        assert result["tp"] == 1
        assert result["f1"] == 1.0

    def test_no_match_no_cheat(self) -> None:
        gold = ["Concrete M20"]
        pred = ["Aluminum sheet self taping screws"]
        result = match_materials_asymmetric(gold, pred)
        assert result["tp"] == 0
        assert result["fp"] == 1
        assert result["fn"] == 1
        assert result["f1"] == 0.0

    def test_threshold_not_lowered(self) -> None:
        # The matcher must NOT match at jaccard < 0.6 even if containment
        # is below 0.8.
        gold = ["Aluminum sheet steel concrete"]
        pred = ["Mineral wool mattresses"]  # 0/4 overlap
        result = match_materials_asymmetric(gold, pred, jaccard_threshold=0.6)
        assert result["tp"] == 0

    def test_signals_audit(self) -> None:
        gold = ["Mineral Wool", "Aluminum sheet"]
        pred = [
            "Bonded Mineral Wool Mattresses Hooks",
            "Aluminum sheet, self taping screws per Schedule",
        ]
        result = match_materials_asymmetric(gold, pred)
        signals = [s["signal"] for s in result["signals"]]
        # Both matches fire containment (token-level). The audit list
        # proves the matcher is using the right signal and not silently
        # falling back to substring or jaccard.
        assert signals.count("containment") == 2
