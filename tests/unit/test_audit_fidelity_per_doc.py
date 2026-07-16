"""Regression tests for scripts/audit_fidelity_per_doc.py doc_id → path matching.

Background (P1_03 follow-up, ledger 2026-07-07 row 17):
The prior implementation used substring matching
``doc_id in path or doc_id.split("_")[0] in path``. That produced a silent
false positive: doc_id ``"10_gem_bid_7552777"`` has prefix ``"10"``, and
``"10" in "RFQ-75810 TMD-8.pdf"`` is True (substring of ``75810``). As a
result, audit runs for ``10_gem_bid_7552777`` were silently reading
``01_gsecl_wanakbori_tmd8``'s source file.

The fix replaces the substring check with exact path-component matching
(parent dir == doc_id, OR file stem == doc_id). These tests prove:

1. ``10_gem_bid_7552777`` no longer matches the 01_gsecl source path
   (the original bug — exact collision case from the bug report).
2. The two colliders each match their own file and only their own file.
3. Non-collision cases (sacred-10 dirs, spec-style basenames) still work
   so the fix doesn't regress the rest of the audit.

Tests use a synthetic corpus_manifest.json written to ``tmp_path`` so the
real manifest is never touched.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Load the audit script as a module so we can exercise _doc_id_matches_path
# without going through the pipeline.
_SPEC = importlib.util.spec_from_file_location("audit_fidelity_per_doc", SCRIPTS_DIR / "audit_fidelity_per_doc.py")
audit_mod = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(audit_mod)
doc_id_matches = audit_mod._doc_id_matches_path


def _fake_manifest(tmp_path: Path, files: list[str]) -> Path:
    """Write a tiny corpus_manifest.json with only ``files[].path`` and
    ``files[].format`` populated — the only fields the audit script reads."""
    payload = {
        "version": "test-fixture",
        "total_docs": len(files),
        "files": [{"path": p, "format": "pdf", "sha256": f"deadbeef{i}"} for i, p in enumerate(files)],
    }
    p = tmp_path / "corpus_manifest.json"
    p.write_text(json.dumps(payload))
    return p


def test_10_gem_does_not_match_01_gsecl_source_path() -> None:
    """The original bug: doc_id '10_gem_bid_7552777' must NOT match the
    01_gsecl_wanakbori_tmd8 source file (whose filename contains '75810')."""
    gsecl_path = "data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf"
    assert doc_id_matches("10_gem_bid_7552777", gsecl_path) is False, (
        "REGRESSION: substring '10' in 'RFQ-75810 TMD-8.pdf' is back. "
        "10_gem must not be matched against 01_gsecl's source file."
    )


def test_01_gsecl_matches_its_own_source_path() -> None:
    """The fix must keep the 01_gsecl case working (parent dir == doc_id)."""
    gsecl_path = "data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf"
    assert doc_id_matches("01_gsecl_wanakbori_tmd8", gsecl_path) is True


def test_10_gem_matches_its_own_source_path() -> None:
    """The fix must keep the 10_gem case working (parent dir == doc_id)."""
    gem_path = "data/real_rfqs/swa_enquiries/10_gem_bid_7552777/GeM-Bidding-9343469.pdf"
    assert doc_id_matches("10_gem_bid_7552777", gem_path) is True


def test_two_colliders_match_exclusively(tmp_path: Path) -> None:
    """With a manifest that contains both the colliding 01_gsecl path and
    the 10_gem path, _doc_id_matches_path must associate each doc_id with
    only its own file (no cross-match, no duplicate match)."""
    gsecl_path = "data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf"
    gem_path = "data/real_rfqs/swa_enquiries/10_gem_bid_7552777/GeM-Bidding-9343469.pdf"
    _fake_manifest(tmp_path, [gsecl_path, gem_path])

    gsecl_matches = [p for p in [gsecl_path, gem_path] if doc_id_matches("01_gsecl_wanakbori_tmd8", p)]
    gem_matches = [p for p in [gsecl_path, gem_path] if doc_id_matches("10_gem_bid_7552777", p)]

    assert gsecl_matches == [gsecl_path], f"01_gsecl should match only its own path, got {gsecl_matches}"
    assert gem_matches == [gem_path], f"10_gem should match only its own path, got {gem_matches}"


def test_sacred10_dir_style_works() -> None:
    """All sacred-10 entries (parent dir == doc_id) still match."""
    cases = [
        ("01_gsecl_wanakbori_tmd8", "data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf"),
        ("02_isro_vssc", "data/real_rfqs/swa_enquiries/02_isro_vssc/VSSC_BOQ_with_qty.xlsx"),
        ("09_gem_bid_7439924", "data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf"),
    ]
    for doc_id, path in cases:
        assert doc_id_matches(doc_id, path) is True, f"sanity: {doc_id} should match its own path"


def test_spec_basename_style_works() -> None:
    """Spec docs where doc_id == file stem (basename without ext) still match."""
    cases = [
        ("BOQ", "data/specifications/Specifications/BOQ.pdf"),
        ("Insulation Boq (1)", "data/specifications/Specifications/Insulation Boq (1).pdf"),
        (
            "47_Pipe Insulation_BOQ Compliance",
            "data/specifications/Specifications/47_Pipe Insulation_BOQ Compliance.pdf",
        ),
    ]
    for doc_id, path in cases:
        assert doc_id_matches(doc_id, path) is True, f"sanity: {doc_id} should match its own path"


def test_no_substring_false_positive_on_01_token() -> None:
    """A previous known false positive: any path with '01' as a substring
    would match doc_id prefix '01'. Verify the fix rejects all of them."""
    false_positive_paths = [
        "data/specifications/Specifications/23 07 13.01 Ductwork Insulation, Schedule.r0.pdf",
        "data/specifications/Specifications/37. RPMS-ENGG-SPC-HV-019-Thermal insulation.pdf",
        "data/specifications/Specification 2/DC-90 (DC 37801 )INSULATION - (Sample).pdf",
        "data/specifications/Specification 2/MECH-EIPL-HVAC-NXTRA-001-R2-BUFFER TANK.pdf",
    ]
    for p in false_positive_paths:
        assert doc_id_matches("01_gsecl_wanakbori_tmd8", p) is False, (
            f"REGRESSION: doc_id '01_gsecl_wanakbori_tmd8' substring-matches {p!r}"
        )


def test_empty_inputs_return_false() -> None:
    """Defensive: empty doc_id or path must not match anything."""
    assert doc_id_matches("", "data/foo/bar.pdf") is False
    assert doc_id_matches("foo", "") is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
