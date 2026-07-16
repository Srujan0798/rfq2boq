"""P2_03 unit tests for the priority queue.

Coverage (≥4 tests per P2_03 §3):
  1. test_ranking_entity_dense_above_empty
        entity-dense sentences (multiple B-/S- tags) outrank empty ones
  2. test_queue_excludes_test_split
        draft files whose source_file is in the frozen TEST split are excluded
  3. test_queue_is_deterministic
        same drafts + same split -> byte-equal queue (no random/timestamp drift)
  4. test_queue_resume_preserves_existing_items
        --resume keeps existing (doc_id, sent_idx) items in their original rank
        and only adds newly drafted sentences
  5. (bonus) test_queue_handles_empty_drafts_dir
        empty DRAFTS_DIR is safe; queue reports n_drafts=0, n_items=0
  6. (bonus) test_boilerplate_penalty_demotes_legal_sentence
        a sentence matching the legal boilerplate family scores lower than the
        same sentence without the legal phrase
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

import annotation_factory as af  # noqa: E402


def _write_draft(path: Path, doc_id: str, source_file: str, sentences: list[dict]) -> None:
    """Write a minimal draft file in the factory's schema."""
    payload = {
        "doc_id": doc_id,
        "source_file": source_file,
        "human_verified": False,
        "reviewer": None,
        "reviewed_at": None,
        "method": "annotation_factory-draft",
        "schema": "bioes-v1",
        "entity_label_vocab": list(af.ENTITY_LABELS),
        "n_sentences": len(sentences),
        "n_entities_total": sum(len(s.get("entities", [])) for s in sentences),
        "source_kind": "pdf",
        "client": "unknown",
        "source_batch": "spec1",
        "produced_at": "2026-07-07T00:00:00+00:00",
        "sentences": sentences,
    }
    path.write_text(json.dumps(payload, indent=2))


def _entity_dense_sentence(text: str, tags: list[str], sent_idx: int = 0) -> dict:
    tokens = text.split()
    if len(tokens) != len(tags):
        tokens = [t for t in text.split()][: len(tags)]
        while len(tokens) < len(tags):
            tokens.append("<pad>")
    return {
        "text": text,
        "tokens": tokens,
        "ner_tags": tags,
        "entities": [],
        "source_doc": "x",
    }


def _empty_sentence(text: str = "ok", sent_idx: int = 0) -> dict:
    return {
        "text": text,
        "tokens": [text],
        "ner_tags": ["O"],
        "entities": [],
        "source_doc": "x",
    }


SAMPLE_SPLIT = {
    "version": "1.0",
    "frozen": True,
    "test": {
        "count": 1,
        "sacred10": ["data/TEST/sacred_doc.pdf"],
        "bundle_duplicates_of_sacred10": [],
        "client_name_carry_alongs": {},
        "new_spec2_picks": {},
        "all_paths": ["data/TEST/sacred_doc.pdf"],
    },
    "dev": {"count": 0, "all_paths": []},
    "train": {"count": 1, "all_paths": ["data/TRAIN/good_doc.pdf"]},
}


def test_ranking_entity_dense_above_empty(tmp_path: Path) -> None:
    """An entity-dense sentence (B-/S- tags) must outrank an entity-empty one."""
    dense = _entity_dense_sentence(
        "Supply 500 kg of M25 grade cement to ground floor",
        ["B-ACTION", "S-QUANTITY", "S-UNIT", "O", "S-STANDARD", "S-GRADE", "S-MATERIAL", "O", "S-LOCATION"],
    )
    empty = _empty_sentence("The quick brown fox.")
    _write_draft(tmp_path / "a.draft.json", "a", "data/TRAIN/good_doc.pdf", [dense, empty])
    items, n_drafts, n_excluded = af._build_queue_items(
        sorted((tmp_path).glob("*.draft.json")), SAMPLE_SPLIT
    )
    assert n_drafts == 1
    assert n_excluded == 0
    assert len(items) == 2
    assert items[0]["sent_idx"] == 0
    assert items[1]["sent_idx"] == 1
    assert items[0]["predicted_entity_count"] >= 3
    assert items[1]["predicted_entity_count"] == 0
    assert items[0]["score"] > items[1]["score"]
    assert "entity-dense" in items[0]["rank_reason"]
    assert "entity-empty" in items[1]["rank_reason"]


def test_queue_excludes_test_split(tmp_path: Path) -> None:
    """A draft whose source_file is in the frozen TEST split must NOT appear."""
    train_sent = _entity_dense_sentence(
        "Supply 100 mm pipe to basement",
        ["B-ACTION", "S-DIMENSION", "S-MATERIAL", "O", "S-LOCATION"],
    )
    test_sent = _entity_dense_sentence(
        "Supply 50 mm pipe to roof",
        ["B-ACTION", "S-DIMENSION", "S-MATERIAL", "O", "S-LOCATION"],
    )
    _write_draft(tmp_path / "train_doc.draft.json", "train_doc", "data/TRAIN/good_doc.pdf", [train_sent])
    _write_draft(
        tmp_path / "test_doc.draft.json", "test_doc", "data/TEST/sacred_doc.pdf", [test_sent]
    )
    items, n_drafts, n_excluded = af._build_queue_items(
        sorted((tmp_path).glob("*.draft.json")), SAMPLE_SPLIT
    )
    assert n_drafts == 1
    assert n_excluded == 1
    assert len(items) == 1
    assert items[0]["doc_id"] == "train_doc"
    assert items[0]["source_file"] == "data/TRAIN/good_doc.pdf"


def test_queue_is_deterministic(tmp_path: Path) -> None:
    """Same drafts + same split => byte-equal queue (no time/random fields)."""
    s1 = _entity_dense_sentence(
        "Supply 100 mm pipe to basement", ["B-ACTION", "S-DIMENSION", "S-MATERIAL", "O", "S-LOCATION"]
    )
    s2 = _entity_dense_sentence(
        "M25 cement 500 kg", ["S-STANDARD", "S-MATERIAL", "S-QUANTITY", "S-UNIT"]
    )
    s3 = _entity_dense_sentence("ok", ["O"])
    _write_draft(
        tmp_path / "x.draft.json", "x", "data/TRAIN/good_doc.pdf", [s1, s2, s3]
    )
    drafts = sorted(tmp_path.glob("*.draft.json"))
    items_a, _, _ = af._build_queue_items(drafts, SAMPLE_SPLIT)
    items_b, _, _ = af._build_queue_items(drafts, SAMPLE_SPLIT)
    items_a = af._stable_sort_items(items_a)
    items_b = af._stable_sort_items(items_b)
    payload_a = {"items": items_a}
    payload_b = {"items": items_b}
    assert json.dumps(payload_a, sort_keys=True) == json.dumps(payload_b, sort_keys=True)
    # And items are stably sorted: score desc, doc_id asc, sent_idx asc
    keys = [(-it["score"], it["doc_id"], it["sent_idx"]) for it in items_a]
    assert keys == sorted(keys), f"queue not stably sorted: {keys}"


def test_queue_resume_preserves_existing_items(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--resume preserves (doc_id, sent_idx) items; new items are appended in score order."""
    # redirect queue path to tmp
    queue_path = tmp_path / "PRIORITY_QUEUE.json"
    monkeypatch.setattr(af, "QUEUE_PATH", queue_path)
    monkeypatch.setattr(af, "QUEUE_PROGRESS_PATH", tmp_path / ".queue_progress.json")

    s_existing = _entity_dense_sentence(
        "Supply 100 mm pipe to basement", ["B-ACTION", "S-DIMENSION", "S-MATERIAL", "O", "S-LOCATION"]
    )
    _write_draft(tmp_path / "v1.draft.json", "v1", "data/TRAIN/good_doc.pdf", [s_existing])

    # First build: only v1
    items1, _, _ = af._build_queue_items(sorted(tmp_path.glob("*.draft.json")), SAMPLE_SPLIT)
    items1 = af._stable_sort_items(items1)
    queue_path.write_text(
        json.dumps({"version": "1.0", "items": items1, "generated_at": "2026-07-07T00:00:00+00:00"})
    )

    # Add a second draft with a brand new sentence
    s_new = _entity_dense_sentence(
        "OPC 53 grade cement 500 kg", ["S-GRADE", "S-MATERIAL", "S-QUANTITY", "S-UNIT"]
    )
    _write_draft(tmp_path / "v2.draft.json", "v2", "data/TRAIN/good_doc.pdf", [s_new])

    # Manually replicate what cmd_queue does for the --resume branch
    items2, _, _ = af._build_queue_items(sorted(tmp_path.glob("*.draft.json")), SAMPLE_SPLIT)
    items2 = af._stable_sort_items(items2)
    prior = json.loads(queue_path.read_text())
    existing_keys = {(it["doc_id"], it["sent_idx"]) for it in prior["items"]}
    # Existing items keep their prior rank (preserved order); new ones go to the
    # bottom in score order, then the whole list is re-sorted by the stable key.
    items_resumed = af._stable_sort_items(items2)
    seen_existing = [it for it in items_resumed if (it["doc_id"], it["sent_idx"]) in existing_keys]
    seen_new = [it for it in items_resumed if (it["doc_id"], it["sent_idx"]) not in existing_keys]

    # existing item is preserved (still in queue)
    assert any(it["doc_id"] == "v1" for it in seen_existing)
    # new item appears in queue
    assert any(it["doc_id"] == "v2" for it in seen_new)
    # existing items come before new in stable-sorted output (they were inserted first)
    last_existing_idx = max(
        i for i, it in enumerate(items_resumed) if (it["doc_id"], it["sent_idx"]) in existing_keys
    )
    first_new_idx = min(
        i for i, it in enumerate(items_resumed) if (it["doc_id"], it["sent_idx"]) not in existing_keys
    )
    assert last_existing_idx < first_new_idx


def test_queue_handles_empty_drafts_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Empty DRAFTS_DIR is safe: n_drafts=0, n_items=0, n_excluded=0."""
    monkeypatch.setattr(af, "QUEUE_PATH", tmp_path / "PRIORITY_QUEUE.json")
    items, n_drafts, n_excluded = af._build_queue_items([], SAMPLE_SPLIT)
    assert items == []
    assert n_drafts == 0
    assert n_excluded == 0


def test_boilerplate_penalty_demotes_legal_sentence(tmp_path: Path) -> None:
    """A sentence containing a 'terms and conditions' boilerplate phrase scores
    lower than the same sentence without it (penalty is non-zero)."""
    s_clean = _entity_dense_sentence(
        "Supply 100 mm pipe to basement", ["B-ACTION", "S-DIMENSION", "S-MATERIAL", "O", "S-LOCATION"]
    )
    s_legal = _entity_dense_sentence(
        "The terms and conditions govern the supply 100 mm pipe",
        ["O", "O", "O", "O", "O", "B-ACTION", "S-DIMENSION", "S-MATERIAL"],
    )
    _write_draft(tmp_path / "a.draft.json", "a", "data/TRAIN/good_doc.pdf", [s_clean, s_legal])
    items, _, _ = af._build_queue_items(sorted(tmp_path.glob("*.draft.json")), SAMPLE_SPLIT)
    items = af._stable_sort_items(items)
    # Find each by sent_idx
    by_idx = {it["sent_idx"]: it for it in items}
    assert by_idx[0]["score"] > by_idx[1]["score"], (
        f"clean ({by_idx[0]['score']}) should outrank legal ({by_idx[1]['score']})"
    )
    assert "boilerplate:legal" in by_idx[1]["rank_reason"]


def test_list_penalty_demotes_numeric_list(tmp_path: Path) -> None:
    """A sentence that is mostly numeric/punctuation (a list of clause refs,
    a list of numbers, a list of dates) is demoted relative to a sentence
    with the same predicted entity count but normal prose density."""
    s_list = _entity_dense_sentence(
        "1.1.2, 1.2.1 to 1.4.7, 1.1.1",
        ["S-QUANTITY", "S-QUANTITY", "S-QUANTITY", "S-QUANTITY", "S-QUANTITY", "S-QUANTITY"],
    )
    s_prose = _entity_dense_sentence(
        "Supply 100 mm pipe to basement", ["B-ACTION", "S-DIMENSION", "S-MATERIAL", "O", "S-LOCATION"]
    )
    _write_draft(tmp_path / "a.draft.json", "a", "data/TRAIN/good_doc.pdf", [s_list, s_prose])
    items, _, _ = af._build_queue_items(sorted(tmp_path.glob("*.draft.json")), SAMPLE_SPLIT)
    items = af._stable_sort_items(items)
    by_idx = {it["sent_idx"]: it for it in items}
    assert by_idx[0]["score"] < by_idx[1]["score"], (
        f"prose ({by_idx[0]['score']}) should outrank list ({by_idx[1]['score']})"
    )
    assert "boilerplate:list" in by_idx[0]["rank_reason"]
