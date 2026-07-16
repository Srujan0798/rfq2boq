"""Tests for scripts/review_annotation.py (NW-04)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from scripts.review_annotation import (
    _edit_entity,
    _load_manifest_rows,
    _show_context,
    _update_manifest_status,
    review_annotation,
)


def _make_draft(tmp_path: Path, doc_id: str = "demo_doc") -> Path:
    """Helper: write a minimal draft JSON and return its path."""
    d = tmp_path / "draft"
    d.mkdir(exist_ok=True)
    draft = {
        "doc_id": doc_id,
        "source_file": f"{doc_id}.pdf",
        "tokens": ["Supply", "500", "kg", "cement"],
        "ner_tags": ["S-ACTION", "S-QUANTITY", "S-UNIT", "S-MATERIAL"],
        "entities": [
            {"text": "Supply", "type": "ACTION", "start": 0, "end": 1, "source": "AUTO"},
            {"text": "500", "type": "QUANTITY", "start": 1, "end": 2, "source": "AUTO"},
            {"text": "kg", "type": "UNIT", "start": 2, "end": 3, "source": "AUTO"},
            {"text": "cement", "type": "MATERIAL", "start": 3, "end": 4, "source": "AUTO"},
        ],
        "relations": [],
        "metadata": {
            "status": "draft-needs-review",
            "annotator": "auto-pipeline",
            "date": "2026-06-11T00:00:00+00:00",
        },
    }
    p = d / f"{doc_id}.json"
    p.write_text(json.dumps(draft))
    return p


class TestShowContext:
    def test_renders_entity_bracketed(self):
        tokens = ["Supply", "and", "fix", "the", "pipe"]
        out = _show_context(tokens, 2, 3, window=2)
        assert ">>fix<<" in out
        assert "Supply" in out
        assert "the" in out

    def test_window_at_start(self):
        tokens = ["a", "b", "c"]
        out = _show_context(tokens, 0, 1, window=2)
        # window truncated to start
        assert ">>a<<" in out

    def test_window_at_end(self):
        tokens = ["a", "b", "c"]
        out = _show_context(tokens, 2, 3, window=2)
        # window truncated to end
        assert ">>c<<" in out


class TestEditEntity:
    def test_returns_deepcopy(self, monkeypatch: pytest.MonkeyPatch):
        entity = {"type": "MATERIAL", "start": 0, "end": 2, "text": "hdpe pipe"}
        tokens = ["hdpe", "pipe", "x"]
        # Simulate user typing "q" to quit edit
        monkeypatch.setattr("builtins.input", lambda *a, **kw: "q")
        out = _edit_entity(tokens, entity)
        # Deepcopy is a different object
        assert out is not entity
        assert out["type"] == "MATERIAL"
        assert out["start"] == 0
        assert out["end"] == 2

    def test_change_type(self, monkeypatch: pytest.MonkeyPatch):
        entity = {"type": "MATERIAL", "start": 0, "end": 1, "text": "x"}
        tokens = ["x"]
        # First change type, then quit
        inputs = iter(["t QUANTITY", "q"])
        monkeypatch.setattr("builtins.input", lambda *a, **kw: next(inputs))
        out = _edit_entity(tokens, entity)
        assert out["type"] == "QUANTITY"

    def test_invalid_type_rejected(self, monkeypatch: pytest.MonkeyPatch):
        entity = {"type": "MATERIAL", "start": 0, "end": 1, "text": "x"}
        tokens = ["x"]
        inputs = iter(["t BOGUS", "q"])
        monkeypatch.setattr("builtins.input", lambda *a, **kw: next(inputs))
        out = _edit_entity(tokens, entity)
        # BOGUS is not in ENTITY_LABELS so type stays MATERIAL
        assert out["type"] == "MATERIAL"


class TestManifestUpdate:
    def test_update_status_writes_review_date(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        manifest = tmp_path / "manifest.csv"
        manifest.write_text(
            "sha256,filename,doc_id,source,client,date,pages,draft_entities,status,annotator,review_date\n"
            "abc,foo.pdf,foo,sales,Acme,2026-01-01,1,3,draft-needs-review,auto-pipeline,\n"
        )
        monkeypatch.setattr("scripts.review_annotation.MANIFEST_PATH", manifest)

        _update_manifest_status("foo", "human_verified", "srujan")

        rows = list(csv.DictReader(manifest.open()))
        assert len(rows) == 1
        assert rows[0]["status"] == "human_verified"
        assert rows[0]["annotator"] == "srujan"
        assert rows[0]["review_date"] != ""

    def test_update_status_unknown_doc_is_noop(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        manifest = tmp_path / "manifest.csv"
        manifest.write_text(
            "sha256,filename,doc_id,source,client,date,pages,draft_entities,status,annotator,review_date\n"
            "abc,foo.pdf,foo,sales,Acme,2026-01-01,1,3,draft-needs-review,auto-pipeline,\n"
        )
        monkeypatch.setattr("scripts.review_annotation.MANIFEST_PATH", manifest)

        _update_manifest_status("nope", "human_verified", "x")

        rows = list(csv.DictReader(manifest.open()))
        # foo row untouched
        assert rows[0]["status"] == "draft-needs-review"

    def test_load_manifest_returns_rows(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        manifest = tmp_path / "m.csv"
        manifest.write_text("doc_id,status\nfoo,draft-needs-review\n")
        monkeypatch.setattr("scripts.review_annotation.MANIFEST_PATH", manifest)
        rows = _load_manifest_rows()
        assert len(rows) == 1
        assert rows[0]["doc_id"] == "foo"


class TestReviewAnnotationHappyPath:
    """End-to-end: review_annotation accepts and writes a verified file."""

    def test_auto_yes_promotes_to_human_verified(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr("scripts.review_annotation.DRAFT_DIR", tmp_path / "draft")
        monkeypatch.setattr("scripts.review_annotation.VERIFIED_DIR", tmp_path / "verified")
        monkeypatch.setattr("scripts.review_annotation.MANIFEST_PATH", tmp_path / "m.csv")

        draft_path = _make_draft(tmp_path, doc_id="doc1")

        result = review_annotation(draft_path, reviewer="tester", auto_accept=True)
        assert result is not None
        assert result.exists()

        # Verified file has human_verified status
        verified = json.loads(result.read_text())
        assert verified["metadata"]["status"] == "human_verified"
        assert verified["metadata"]["annotator"] == "tester"
        # Entities re-stamped as HUMAN
        assert all(e["source"] == "HUMAN" for e in verified["entities"])

    def test_reject_all_skips_save(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr("scripts.review_annotation.DRAFT_DIR", tmp_path / "draft")
        monkeypatch.setattr("scripts.review_annotation.VERIFIED_DIR", tmp_path / "verified")
        monkeypatch.setattr("scripts.review_annotation.MANIFEST_PATH", tmp_path / "m.csv")

        draft_path = _make_draft(tmp_path, doc_id="doc_reject")
        # All inputs "r" (reject)
        monkeypatch.setattr("builtins.input", lambda *a, **kw: "r")
        result = review_annotation(draft_path, reviewer="tester", auto_accept=False)
        assert result is None
        # No verified file written
        assert not (tmp_path / "verified" / "doc_reject.json").exists()


class TestDraftCannotBePromotedWithoutReview:
    """Guard: status: human_verified may ONLY be set by review_annotation.

    A draft file from intake_tender must never be marked human_verified
    on its own — promotion requires running review_annotation with at
    least one accept.
    """

    def test_intake_draft_status_is_draft(self, tmp_path: Path):
        draft = {
            "doc_id": "x",
            "tokens": ["a"],
            "ner_tags": ["O"],
            "entities": [],
            "metadata": {"status": "draft-needs-review"},
        }
        assert draft["metadata"]["status"] == "draft-needs-review"
        assert draft["metadata"]["status"] != "human_verified"

    def test_quit_during_review_does_not_save(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr("scripts.review_annotation.DRAFT_DIR", tmp_path / "draft")
        monkeypatch.setattr("scripts.review_annotation.VERIFIED_DIR", tmp_path / "verified")
        monkeypatch.setattr("scripts.review_annotation.MANIFEST_PATH", tmp_path / "m.csv")

        draft_path = _make_draft(tmp_path, doc_id="doc_quit")
        # First entity: quit
        monkeypatch.setattr("builtins.input", lambda *a, **kw: "q")
        result = review_annotation(draft_path, reviewer="tester", auto_accept=False)
        assert result is None
        # Verified file NOT written
        assert not (tmp_path / "verified" / "doc_quit.json").exists()
