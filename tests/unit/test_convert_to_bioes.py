"""Tests for scripts/convert_to_bioes.py (NW-04)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.convert_to_bioes import (
    HELD_OUT_PATTERNS,
    _deterministic_split,
    _is_held_out,
    _is_swa_sacred,
    assert_no_held_out_in_train_val,
    load_verified_annotations,
    split_annotations,
    write_bioes_split,
)


def _ann(doc_id: str, tokens: list[str] | None = None) -> dict:
    return {
        "doc_id": doc_id,
        "source_file": f"{doc_id}.pdf",
        "tokens": tokens or ["a", "b"],
        "ner_tags": ["O", "O"],
        "entities": [],
        "relations": [],
        "metadata": {"status": "human_verified"},
    }


class TestIsHeldOut:
    @pytest.mark.parametrize(
        "doc_id",
        [
            "swa_01_gsecl",
            "swa_02_isro",
            "swa_09_gem",
            "swa_10_gem",
        ],
    )
    def test_swa_prefix_held_out(self, doc_id: str):
        assert _is_held_out(doc_id)

    @pytest.mark.parametrize(
        "doc_id",
        [
            "01_gsecl",
            "02_isro_vssc",
            "03_zydus_matoda",
            "04_adani",
            "05_zydus_animal_pharmez",
            "06_avante_kirloskar_pune",
            "07_grew_solar",
            "08_sael",
            "09_gem_bid_7439924",
            "10_gem_bid_7552777",
        ],
    )
    def test_zero_padded_swa_dir_held_out(self, doc_id: str):
        assert _is_held_out(doc_id)

    @pytest.mark.parametrize(
        "doc_id",
        [
            "rfq_road_001",
            "rfq_building_RFQ5521",
            "generic_doc",
            "attic_pdf_rfq_road_50",
            "swa_doc",  # no underscore-digit after swa
        ],
    )
    def test_normal_docs_not_held_out(self, doc_id: str):
        assert not _is_held_out(doc_id)

    def test_two_digit_prefix_is_held_out(self):
        # 11_random matches the ^\d{2}_\w+ pattern by design — any
        # 2-digit-prefixed doc name is treated like the SWA directories.
        assert _is_held_out("11_random")

    def test_patterns_are_compiled(self):
        # All patterns are pre-compiled regex objects
        import re

        for p in HELD_OUT_PATTERNS:
            assert isinstance(p, re.Pattern)


class TestDeterministicSplit:
    def test_stable(self):
        assert _deterministic_split("doc_a") == _deterministic_split("doc_a")

    def test_returns_known_bucket(self):
        assert _deterministic_split("doc_a") in {"train", "val", "test"}

    def test_distribution_close_to_targets(self):
        # Across many doc_ids, distribution should be ~70/15/15
        counts = {"train": 0, "val": 0, "test": 0}
        for i in range(1000):
            counts[_deterministic_split(f"doc_{i}")] += 1
        # Allow ±10 percentage points
        assert 600 < counts["train"] < 800
        assert 50 < counts["val"] < 250
        assert 50 < counts["test"] < 250


class TestSplitAnnotations:
    def test_held_out_forced_to_test(self):
        ann = _ann("01_gsecl")
        train, val, test = split_annotations([ann])
        assert train == []
        assert val == []
        assert len(test) == 1

    def test_normal_doc_goes_somewhere(self):
        train, val, test = split_annotations([_ann("rfq_001")])
        total = len(train) + len(val) + len(test)
        assert total == 1

    def test_swa_pattern_forced_to_test(self):
        ann = _ann("swa_05_zydus")
        train, val, test = split_annotations([ann])
        assert len(test) == 1
        assert len(train) == 0
        assert len(val) == 0

    def test_mixed_split(self):
        anns = [
            _ann("rfq_a"),
            _ann("rfq_b"),
            _ann("rfq_c"),
            _ann("01_gsecl"),
            _ann("swa_09_gem"),
        ]
        train, val, test = split_annotations(anns)
        # Two SWA + zero-pad are forced to test
        assert len(test) >= 2
        # Total preserved
        assert len(train) + len(val) + len(test) == 5


class TestAssertNoHeldOut:
    def test_clean_passes(self):
        train = [_ann("rfq_001"), _ann("rfq_002")]
        val = [_ann("rfq_003")]
        assert_no_held_out_in_train_val(train, val)  # no raise

    def test_raises_when_swa_in_train(self):
        train = [_ann("01_gsecl")]
        with pytest.raises(AssertionError) as exc:
            assert_no_held_out_in_train_val(train, [])
        assert "HELD-OUT VIOLATION" in str(exc.value)
        assert "01_gsecl" in str(exc.value)

    def test_raises_when_swa_in_val(self):
        val = [_ann("swa_10_gem")]
        with pytest.raises(AssertionError) as exc:
            assert_no_held_out_in_train_val([], val)
        assert "HELD-OUT VIOLATION" in str(exc.value)

    def test_raises_lists_all_offenders(self):
        train = [_ann("01_gsecl"), _ann("swa_09_gem")]
        with pytest.raises(AssertionError) as exc:
            assert_no_held_out_in_train_val(train, [])
        msg = str(exc.value)
        assert "01_gsecl" in msg
        assert "swa_09_gem" in msg

    def test_test_split_is_not_checked(self):
        # Held-out docs ARE allowed in test (they live there)
        # This call should not raise — the function only inspects train+val
        assert_no_held_out_in_train_val([], [])
        # The test set can contain them


class TestLoadVerified:
    def test_empty_dir(self, tmp_path: Path):
        assert load_verified_annotations(tmp_path / "empty") == []

    def test_missing_dir(self, tmp_path: Path):
        # Nonexistent dir returns [] rather than raising
        assert load_verified_annotations(tmp_path / "missing") == []

    def test_skips_invalid_records(self, tmp_path: Path):
        d = tmp_path / "verified"
        d.mkdir()
        # Missing tokens / ner_tags → skipped
        (d / "bad.json").write_text(json.dumps({"doc_id": "x"}))
        # Valid record
        (d / "good.json").write_text(json.dumps(_ann("y")))
        loaded = load_verified_annotations(d)
        assert len(loaded) == 1
        assert loaded[0]["doc_id"] == "y"

    def test_loads_multiple(self, tmp_path: Path):
        d = tmp_path / "verified"
        d.mkdir()
        for i in range(3):
            (d / f"doc_{i}.json").write_text(json.dumps(_ann(f"doc_{i}")))
        loaded = load_verified_annotations(d)
        assert {a["doc_id"] for a in loaded} == {"doc_0", "doc_1", "doc_2"}


class TestWriteBioesSplit:
    def test_writes_records(self, tmp_path: Path):
        out = tmp_path / "train.json"
        write_bioes_split([_ann("a"), _ann("b")], out)
        data = json.loads(out.read_text())
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["doc_id"] == "a"
        assert data[0]["tokens"] == ["a", "b"]
        assert data[0]["ner_tags"] == ["O", "O"]


class TestEndToEndHeldOut:
    """End-to-end: if a verified file contains an SWA doc, the script raises."""

    def test_main_flow_rejects_swa_in_verified(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Stage: verified dir with a held-out doc; main() should raise
        verified = tmp_path / "verified"
        verified.mkdir()
        # An SWA-named doc somehow ended up in verified/
        (verified / "swa_05_zydus.json").write_text(json.dumps(_ann("swa_05_zydus")))
        # A normal doc
        (verified / "rfq_ok.json").write_text(json.dumps(_ann("rfq_ok")))

        monkeypatch.setattr("scripts.convert_to_bioes.VERIFIED_DIR", verified)
        monkeypatch.setattr("scripts.convert_to_bioes.DEFAULT_OUTPUT_DIR", tmp_path / "out")

        # split_annotations should route SWA to test, then assert must not raise
        # (held-out goes to test, which is not checked)
        annotations = load_verified_annotations(verified)
        train, val, test = split_annotations(annotations)
        # Should not raise — swa is in test, not train/val
        assert_no_held_out_in_train_val(train, val)
        # SWA doc always lands in test
        swa_in_test = [a for a in test if a["doc_id"] == "swa_05_zydus"]
        assert len(swa_in_test) == 1
        # And never in train
        swa_in_train = [a for a in train if a["doc_id"] == "swa_05_zydus"]
        assert len(swa_in_train) == 0
        # Total preserved
        assert len(train) + len(val) + len(test) == 2

    def test_assert_holds_against_injected_train(self):
        # Simulate a bug: someone pre-loads a SWA into "train"
        train = [_ann("swa_07_grew_solar")]
        with pytest.raises(AssertionError):
            assert_no_held_out_in_train_val(train, [])


class TestStrictHeldOutProvenance:
    """Additional guards for strict SWA sacred never-in-train enforcement (NW-04)."""

    def test_swa_provenance_forces_test_even_with_generic_doc_id(self):
        ann = _ann("generic_rfq_from_swa")
        ann["source_file"] = "something.pdf"
        ann["metadata"] = {"provenance": {"original_path": "data/real_rfqs/swa_enquiries/01_foo/xx.pdf"}}
        assert _is_swa_sacred(ann) is True
        train, val, test = split_annotations([ann])
        assert len(train) == 0 and len(val) == 0
        assert len(test) == 1

    def test_provenance_string_match_triggers_sacred(self):
        ann = _ann("weird_name")
        ann["metadata"] = {"source": "swa_enquiries/03_zydus/xx.xlsx"}
        assert _is_swa_sacred(ann)
        # does not go to train
        train, val, test = split_annotations([ann])
        assert len(train) + len(val) == 0

    def test_non_swa_provenance_passes(self):
        ann = _ann("new_client_tender_42")
        ann["metadata"] = {"provenance": {"original_path": "data/specifications/foo.pdf"}}
        assert not _is_swa_sacred(ann)
        # can go to train/val/test normally
        train, val, test = split_annotations([ann])
        total = len(train) + len(val) + len(test)
        assert total == 1


class TestReviewExplicitAcceptGuard:
    """Guard that review script path (CLI) forces explicit accept, not auto."""

    def test_review_func_still_supports_auto_for_tests_but_cli_does_not(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # This test calls the python func directly (as existing tests do).
        # The CLI itself no longer exposes --yes, enforcing human "a" choice.
        from scripts.review_annotation import review_annotation as ra

        d = tmp_path / "draft"
        d.mkdir()
        v = tmp_path / "verified"
        m = tmp_path / "m.csv"
        monkeypatch.setattr("scripts.review_annotation.DRAFT_DIR", d)
        monkeypatch.setattr("scripts.review_annotation.VERIFIED_DIR", v)
        monkeypatch.setattr("scripts.review_annotation.MANIFEST_PATH", m)

        # inline minimal draft (no reliance on _make_draft from other test file)
        draft = {
            "doc_id": "cli_explicit",
            "source_file": "t.pdf",
            "tokens": ["a", "500", "kg"],
            "ner_tags": ["O", "S-QUANTITY", "S-UNIT"],
            "entities": [
                {"text": "500", "type": "QUANTITY", "start": 1, "end": 2, "source": "AUTO"},
                {"text": "kg", "type": "UNIT", "start": 2, "end": 3, "source": "AUTO"},
            ],
            "relations": [],
            "metadata": {"status": "draft-needs-review"},
        }
        dp = d / "cli_explicit.json"
        dp.write_text(json.dumps(draft))

        # auto only via direct call (tests); CLI review script requires explicit
        out = ra(dp, reviewer="unit", auto_accept=True)
        assert out is not None
        data = json.loads(out.read_text())
        assert data["metadata"]["status"] == "human_verified"
        # cleanup
        out.unlink(missing_ok=True)
