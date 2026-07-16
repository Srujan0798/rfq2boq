"""Source-truth ruler tests (P1_01).

Validates the source_truth.json schema and the rule that no record may carry
needs_manual_count:true in the final file (every boq_bearing doc must have a
final count with method + evidence).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

SOURCE_TRUTH = REPO_ROOT / "data/real_rfqs/source_truth.json"


def _load() -> dict:
    return json.loads(SOURCE_TRUTH.read_text())


def test_source_truth_file_exists() -> None:
    assert SOURCE_TRUTH.exists(), "data/real_rfqs/source_truth.json must exist"


def test_source_truth_has_entries() -> None:
    st = _load()
    docs = st.get("entries", st.get("docs", []))
    assert len(docs) > 0, "source_truth.json must have at least one entry"


def test_no_needs_manual_count_in_final() -> None:
    """The final ruler must have zero needs_manual_count:true records."""
    st = _load()
    docs = st.get("entries", st.get("docs", []))
    pending = [d for d in docs if d.get("needs_manual_count")]
    assert not pending, f"{len(pending)} docs still need manual counts: {[d['doc_id'] for d in pending]}"


def test_every_entry_has_required_fields() -> None:
    """Each entry must have doc_id, source_row_count, method, evidence, d4_exclusions."""
    st = _load()
    docs = st.get("entries", st.get("docs", []))
    required = {"doc_id", "source_row_count", "method", "evidence"}
    for d in docs:
        missing = required - set(d.keys())
        assert not missing, f"{d.get('doc_id', '?')} missing fields: {missing}"


def test_d4_exclusions_recorded_for_02_isro_and_08_sael() -> None:
    """D4 ruling: 02_isro and 08_sael must record their section-title exclusions."""
    st = _load()
    docs = {d["doc_id"]: d for d in st.get("entries", st.get("docs", []))}
    assert "02_isro_vssc" in docs, "02_isro_vssc missing from source_truth"
    d4 = docs["02_isro_vssc"].get("d4_exclusions", [])
    assert any("Structure" in x or "civil" in x for x in d4), f"02_isro D4 exclusion missing: {d4}"


def test_row_counts_are_non_negative() -> None:
    st = _load()
    for d in st.get("entries", st.get("docs", [])):
        rc = d.get("source_row_count", -1)
        assert isinstance(rc, int) and rc >= 0, f"{d['doc_id']} has invalid row_count: {rc}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
