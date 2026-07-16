"""P2_02 unit tests for the annotation factory.

Coverage:
  1. test_draft_is_deterministic          — same input, same draft output
  2. test_draft_bioes_valid                — every emitted draft is BIOES-clean
  3. test_draft_sets_human_verified_false  — drafts never stamp verified
  4. test_draft_refuses_test_split         — TEST-split docs are hard-refused
  5. test_review_refuses_non_tty           — non-interactive session never stamps
  6. test_review_refuses_non_srujan        — only the owner can stamp
  7. test_review_sets_reviewer_when_tty    — interactive tty + non-srujan = refuse
                                            (use a forged stdin via fake tty)
  8. test_validate_catches_each_corruption — B->E-type-mismatch, I-without-B, E-followed-by-I, length-mismatch, unknown label
  9. test_validate_accepts_clean           — a clean draft passes
 10. test_stats_no_verified_files          — stats is safe when no verified yet
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

import annotation_factory as af  # noqa: E402


@pytest.fixture
def clean_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """Redirect drafts/verified/stats to tmp_path so tests never touch real data."""
    drafts = tmp_path / "drafts"
    verified = tmp_path / "verified"
    stats = tmp_path / "owner_minutes.jsonl"
    monkeypatch.setattr(af, "DRAFTS_DIR", drafts)
    monkeypatch.setattr(af, "VERIFIED_DIR", verified)
    monkeypatch.setattr(af, "STATS_PATH", stats)
    return {"drafts": drafts, "verified": verified, "stats": stats}


def _fake_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make sys.stdin appear interactive."""

    class _FakeTty(io.StringIO):
        def isatty(self) -> bool:  # type: ignore[override]
            return True

    monkeypatch.setattr(sys, "stdin", _FakeTty(""))


def _fake_non_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeNonTty(io.StringIO):
        def isatty(self) -> bool:  # type: ignore[override]
            return False

    monkeypatch.setattr(sys, "stdin", _FakeNonTty(""))


# ── 1. Drafting ──────────────────────────────────────────────────────────────


def test_draft_is_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_dirs: dict) -> None:
    """Same input -> same draft output (excluding timestamp)."""
    monkeypatch.setattr(af, "_now_iso", lambda: "2026-07-06T00:00:00+00:00")
    af._reset_gem_cache()

    def _fake_process(self, text: str):  # noqa: ARG001
        class _R:
            entities = []

        return _R()

    monkeypatch.setattr(af, "_make_pipeline", lambda: type("P", (), {"process": _fake_process})())

    # Use a real fixture file we can resolve via _resolve_on_disk
    fixed_entry = {
        "path": "data/specifications/Specifications/BOQ.pdf",
        "format": "pdf",
        "client": "TEST",
        "source_batch": "spec1",
    }

    a = af._draft_one_doc(fixed_entry)
    b = af._draft_one_doc(fixed_entry)
    assert a["n_sentences"] == b["n_sentences"]
    a_sents = a.get("sentences", [])
    b_sents = b.get("sentences", [])
    assert a_sents and b_sents, f"expected non-empty sentences; got {len(a_sents)}/{len(b_sents)}"
    for sa, sb in zip(a_sents, b_sents, strict=False):
        assert sa["tokens"] == sb["tokens"]
        assert sa["ner_tags"] == sb["ner_tags"]


def test_draft_bioes_valid(clean_dirs: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every draft emitted via cmd_draft is BIOES-clean."""
    monkeypatch.setattr(af, "_now_iso", lambda: "2026-07-06T00:00:00+00:00")
    af._reset_gem_cache()

    # Stub the heavy NLPPipeline: speed up the test (production usage is slow
    # but correctness-focused). The factory contract is what we test here.
    def _fake_process(self, text: str):  # noqa: ARG001
        class _R:
            entities = []

        return _R()

    monkeypatch.setattr(af, "_make_pipeline", lambda: type("P", (), {"process": _fake_process})())

    # Use a higher --docs so the first few (alphabetically) might be spec2 with no
    # on-disk text — we want at least 2 spec1 docs to land.
    args = type("Args", (), {"split": "train", "docs": 50})()
    rc = af.cmd_draft(args)
    assert rc == 0

    drafts = list(clean_dirs["drafts"].glob("*.draft.json"))
    assert len(drafts) >= 2, f"expected >= 2 draft files written, got {len(drafts)}"
    for d in drafts:
        errors = af.collect_errors_for_file(d)
        assert errors == [], f"BIOES errors in {d.name}: {errors}"


def test_draft_sets_human_verified_false(clean_dirs: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """A draft is never human_verified:true, never reviewer-set, never reviewed_at-set."""
    monkeypatch.setattr(af, "_now_iso", lambda: "2026-07-06T00:00:00+00:00")
    af._reset_gem_cache()

    def _fake_process(self, text: str):  # noqa: ARG001
        class _R:
            entities = []

        return _R()

    monkeypatch.setattr(af, "_make_pipeline", lambda: type("P", (), {"process": _fake_process})())

    args = type("Args", (), {"split": "train", "docs": 50})()
    rc = af.cmd_draft(args)
    assert rc == 0
    drafts = list(clean_dirs["drafts"].glob("*.draft.json"))
    assert drafts, "no drafts written (skipping)"
    for d in drafts:
        rec = json.loads(d.read_text())
        assert rec["human_verified"] is False
        assert rec.get("reviewer") is None
        assert rec.get("reviewed_at") is None


def test_draft_refuses_test_split(clean_dirs: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-split docs are hard-refused at draft time (Rule 8)."""
    split = af._load_split()
    test_path = next(iter(split["test"]["all_paths"]))
    assert af._is_test_split(test_path, split) is True

    # A non-TRAIN split argument is refused too
    args = type("Args", (), {"split": "test", "docs": 2})()
    assert af.cmd_draft(args) == 2


# ── 2. Review path (fence) ───────────────────────────────────────────────────


def test_review_refuses_non_tty(clean_dirs: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-interactive session MUST never stamp human_verified:true."""
    # Plant a draft so the file-existence check would pass
    clean_dirs["drafts"].mkdir(parents=True, exist_ok=True)
    (clean_dirs["drafts"] / "test.draft.json").write_text(
        json.dumps(
            {
                "doc_id": "test",
                "source_file": "x.pdf",
                "human_verified": False,
                "reviewer": None,
                "reviewed_at": None,
                "sentences": [],
            }
        )
    )
    _fake_non_tty(monkeypatch)
    args = type("Args", (), {"file": str(clean_dirs["drafts"] / "test.draft.json"), "reviewer": "srujan"})()
    rc = af.cmd_review(args)
    assert rc == 3, "expected fence to refuse (exit 3); non-tty must not stamp"
    assert not (clean_dirs["verified"]).exists() or not list((clean_dirs["verified"]).glob("*.json"))


def test_review_refuses_non_srujan_reviewer(clean_dirs: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """Only the owner is permitted to stamp human_verified:true."""
    _fake_tty(monkeypatch)
    clean_dirs["drafts"].mkdir(parents=True, exist_ok=True)
    (clean_dirs["drafts"] / "test.draft.json").write_text(
        json.dumps(
            {
                "doc_id": "test",
                "source_file": "x.pdf",
                "human_verified": False,
                "reviewer": None,
                "reviewed_at": None,
                "sentences": [],
            }
        )
    )
    args = type("Args", (), {"file": str(clean_dirs["drafts"] / "test.draft.json"), "reviewer": "dryrun-agent"})()
    rc = af.cmd_review(args)
    assert rc == 2, "forged reviewer identity must be refused"
    assert not (clean_dirs["verified"]).exists() or not list((clean_dirs["verified"]).glob("*.json"))


def test_review_already_verified_skips(clean_dirs: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reviewing a file that is already verified should not double-stamp."""
    _fake_tty(monkeypatch)
    clean_dirs["drafts"].mkdir(parents=True, exist_ok=True)
    draft = {
        "doc_id": "test",
        "source_file": "x.pdf",
        "human_verified": True,
        "reviewer": "srujan",
        "reviewed_at": "2026-07-06T00:00:00+00:00",
        "sentences": [],
    }
    (clean_dirs["drafts"] / "test.draft.json").write_text(json.dumps(draft))
    args = type("Args", (), {"file": str(clean_dirs["drafts"] / "test.draft.json"), "reviewer": "srujan"})()
    rc = af.cmd_review(args)
    assert rc == 1


def test_review_writes_only_on_accept(clean_dirs: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """If the owner types 'q' immediately, no verified file is written."""
    _fake_tty(monkeypatch)
    clean_dirs["drafts"].mkdir(parents=True, exist_ok=True)
    draft = {
        "doc_id": "test",
        "source_file": "x.pdf",
        "human_verified": False,
        "reviewer": None,
        "reviewed_at": None,
        "sentences": [{"text": "x", "tokens": ["x"], "ner_tags": ["S-MATERIAL"]}],
    }
    (clean_dirs["drafts"] / "test.draft.json").write_text(json.dumps(draft))
    monkeypatch.setattr("builtins.input", lambda *a, **k: "q")
    args = type("Args", (), {"file": str(clean_dirs["drafts"] / "test.draft.json"), "reviewer": "srujan"})()
    rc = af.cmd_review(args)
    assert rc == 0
    assert not (clean_dirs["verified"]).exists() or not list((clean_dirs["verified"]).glob("*.json"))


def test_review_writes_when_owner_accepts(clean_dirs: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """If the owner types 'a' on a sentence, the verified file is written with the right provenance."""
    _fake_tty(monkeypatch)
    clean_dirs["drafts"].mkdir(parents=True, exist_ok=True)
    draft = {
        "doc_id": "test",
        "source_file": "x.pdf",
        "human_verified": False,
        "reviewer": None,
        "reviewed_at": None,
        "sentences": [
            {
                "text": "Supply 500 kg cement",
                "tokens": ["Supply", "500", "kg", "cement"],
                "ner_tags": ["S-ACTION", "S-QUANTITY", "S-UNIT", "S-MATERIAL"],
            },
            {"text": "second", "tokens": ["second"], "ner_tags": ["O"]},
        ],
    }
    (clean_dirs["drafts"] / "test.draft.json").write_text(json.dumps(draft))
    inputs = iter(["a", "q"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(inputs))
    args = type("Args", (), {"file": str(clean_dirs["drafts"] / "test.draft.json"), "reviewer": "srujan"})()
    rc = af.cmd_review(args)
    assert rc == 0
    verified_files = list(clean_dirs["verified"].glob("*.json"))
    assert len(verified_files) == 1
    rec = json.loads(verified_files[0].read_text())
    assert rec["human_verified"] is True
    assert rec["reviewer"] == "srujan"
    assert rec["reviewed_at"]
    assert rec["review_stats"]["accepted"] == 1


# ── 3. Validate ──────────────────────────────────────────────────────────────


def _write_bad_draft(path: Path, kind: str) -> None:
    if kind == "I-no-B":
        rec = {
            "doc_id": "x",
            "source_file": "x.pdf",
            "human_verified": False,
            "sentences": [{"text": "x", "tokens": ["x"], "ner_tags": ["I-MATERIAL"]}],
        }
    elif kind == "E-followed-by-I":
        rec = {
            "doc_id": "x",
            "source_file": "x.pdf",
            "human_verified": False,
            "sentences": [
                {"text": "x y", "tokens": ["x", "y"], "ner_tags": ["B-MATERIAL", "E-MATERIAL"]},
            ],
        }
    elif kind == "E-followed-by-I-actual":
        rec = {
            "doc_id": "x",
            "source_file": "x.pdf",
            "human_verified": False,
            "sentences": [
                {"text": "x y z", "tokens": ["x", "y", "z"], "ner_tags": ["B-MATERIAL", "E-MATERIAL", "I-MATERIAL"]},
            ],
        }
    elif kind == "unknown-label":
        rec = {
            "doc_id": "x",
            "source_file": "x.pdf",
            "human_verified": False,
            "sentences": [{"text": "x", "tokens": ["x"], "ner_tags": ["B-FAKE"]}],
        }
    elif kind == "length-mismatch":
        rec = {
            "doc_id": "x",
            "source_file": "x.pdf",
            "human_verified": False,
            "sentences": [{"text": "x y", "tokens": ["x", "y"], "ner_tags": ["S-MATERIAL"]}],
        }
    elif kind == "labels-key":
        rec = {
            "doc_id": "x",
            "source_file": "x.pdf",
            "human_verified": False,
            "sentences": [{"text": "x", "tokens": ["x"], "labels": ["I-MATERIAL"]}],
        }
    else:  # noqa
        raise ValueError(kind)
    path.write_text(json.dumps(rec))


def test_validate_catches_each_corruption(tmp_path: Path) -> None:
    for kind in ("I-no-B", "E-followed-by-I-actual", "unknown-label", "length-mismatch", "labels-key"):
        f = tmp_path / f"{kind}.draft.json"
        _write_bad_draft(f, kind)
        errs = af.collect_errors_for_file(f)
        assert errs, f"expected errors for kind={kind}, got none"


def test_validate_accepts_clean(tmp_path: Path) -> None:
    f = tmp_path / "clean.draft.json"
    rec = {
        "doc_id": "x",
        "source_file": "x.pdf",
        "human_verified": False,
        "sentences": [
            {"text": "x y", "tokens": ["x", "y"], "ner_tags": ["B-MATERIAL", "E-MATERIAL"]},
            {"text": "z", "tokens": ["z"], "ner_tags": ["O"]},
        ],
    }
    f.write_text(json.dumps(rec))
    errs = af.collect_errors_for_file(f)
    assert errs == []


# ── 4. Stats ─────────────────────────────────────────────────────────────────


def test_stats_no_verified_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(af, "VERIFIED_DIR", tmp_path / "verified")
    args = type("Args", (), {})()
    rc = af.cmd_stats(args)
    assert rc == 0


# ── 5. Token / segment / bioes helpers ──────────────────────────────────────


def test_segment_keeps_table_row_atomic() -> None:
    """Table cells with a number+unit pair stay as one sentence (Rule: not prose)."""
    text = "Header line.\n9 mm thick 600.0 sqm supply\nNext prose sentence."
    sents = af._segment_into_sentences(text)
    assert any("9 mm thick 600.0 sqm supply" in s for s in sents)


def test_entities_to_bioes_round_trip() -> None:
    text = "Supply 500 kg cement"
    tokens = af._tokenize(text)
    offsets = af._char_offsets(tokens, text)
    ents = [{"text": "500", "type": "QUANTITY", "start": 7, "end": 10, "source": "pattern"}]
    tags = af._entities_to_bioes(tokens, offsets, ents)
    assert tags == ["O", "S-QUANTITY", "O", "O"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
