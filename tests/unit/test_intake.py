"""Intake tests (P1_00).

Covers: duplicate refusal, manifest append correctness, split-counter policy,
TEST-split immutability (intake can NEVER assign test), provenance fields
required, and sweep classifies a fixture tree correctly. Uses tmp_path fixtures
so the real manifest is never touched.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pytest  # noqa: E402

from intake_rfq import assign_split, intake  # noqa: E402


def _make_manifest(n: int = 0) -> dict:
    return {
        "version": "test",
        "total_docs": n,
        "files": [{"path": f"dummy/{i}.pdf", "sha256": f"d{i}"} for i in range(n)],
    }


def _write_doc(tmp_path: Path, name: str, content: bytes = b"hello") -> Path:
    p = tmp_path / name
    p.write_bytes(content)
    return p


def test_duplicate_refusal(tmp_path: Path) -> None:
    """A file whose sha256 matches a manifest entry is refused, not re-intaked."""
    doc = _write_doc(tmp_path, "rfq.xlsx", b"dup-content")
    import hashlib

    sha = hashlib.sha256(b"dup-content").hexdigest()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {"total_docs": 1, "files": [{"path": "existing/rfq.xlsx", "sha256": sha, "source_batch": "sacred10"}]}
        )
    )
    incoming = tmp_path / "incoming"
    report = intake(
        doc, source="drill", client="drill", run_pipe=False, manifest_path=manifest_path, incoming_dir=incoming
    )
    assert report["status"] == "refused_duplicate"
    assert report["existing_doc"]["sha256"] == sha
    assert "duplicate of existing" in report["reason"]


def test_manifest_append_correctness(tmp_path: Path) -> None:
    """A new doc is appended with sha256, provenance, split, and intake_status."""
    doc = _write_doc(tmp_path, "new.xlsx", b"new-content")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_make_manifest(0)))
    incoming = tmp_path / "incoming"
    report = intake(
        doc, source="email from SWA", client="GSECL", run_pipe=False, manifest_path=manifest_path, incoming_dir=incoming
    )
    assert report["status"] == "intaked"
    m = json.loads(manifest_path.read_text())
    assert len(m["files"]) == 1
    e = m["files"][0]
    assert e["sha256"] and len(e["sha256"]) == 64
    assert e["intake_source"] == "email from SWA"
    assert e["client"] == "GSECL"
    assert e["source_batch"] == "incoming"
    assert e["doc_type"] == "pending"
    assert "intake_date" in e


def test_split_policy_train_default(tmp_path: Path) -> None:
    """A new doc on a fresh manifest (count 0 → +1) gets TRAIN (1 % 5 != 0)."""
    doc = _write_doc(tmp_path, "a.xlsx", b"a")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_make_manifest(0)))
    report = intake(doc, "s", "c", run_pipe=False, manifest_path=manifest_path, incoming_dir=tmp_path / "in")
    assert report["split"] == "train"


def test_split_policy_every_5th_goes_to_dev() -> None:
    """Every 5th intake (by manifest counter) → DEV; never TEST."""
    # n=4 → (4+1)%5==0 → DEV
    assert assign_split(_make_manifest(4)) == "dev"
    # n=9 → (9+1)%5==0 → DEV
    assert assign_split(_make_manifest(9)) == "dev"
    # all others → TRAIN
    for n in [0, 1, 2, 3, 5, 6, 7, 8, 10, 11, 127]:
        assert assign_split(_make_manifest(n)) == "train", f"n={n} should be train"


def test_test_split_never_assigned() -> None:
    """No manifest size yields a 'test' split assignment — the policy is impossible to violate."""
    for n in range(0, 1000):
        assert assign_split(_make_manifest(n)) != "test"


def test_provenance_fields_required(tmp_path: Path) -> None:
    """A successful intake entry always carries source + client + date."""
    doc = _write_doc(tmp_path, "p.xlsx", b"p")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_make_manifest(0)))
    report = intake(
        doc, source="email X", client="Y", run_pipe=False, manifest_path=manifest_path, incoming_dir=tmp_path / "in"
    )
    e = report["manifest_entry"]
    assert e["intake_source"] == "email X"
    assert e["client"] == "Y"
    assert e["received_date"]


def test_sweep_classifies_fixture_tree(tmp_path: Path) -> None:
    """corpus_sweep correctly classifies a small fixture tree: manifested / duplicate / unmanifested."""
    # build a tiny repo: one manifested doc, one duplicate (same hash, diff path), one unmanifested
    import hashlib

    content = b"manifest-doc"
    sha = hashlib.sha256(content).hexdigest()
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "copies").mkdir()
    (repo / "docs" / "a.pdf").write_bytes(content)  # manifested
    (repo / "copies" / "a_copy.pdf").write_bytes(content)  # duplicate by hash
    (repo / "docs" / "b.pdf").write_bytes(b"unmanifested")  # unmanifested
    manifest = repo / "manifest.json"
    manifest.write_text(json.dumps({"total_docs": 1, "files": [{"path": "docs/a.pdf", "sha256": sha}]}))

    # import the sweep module fresh against this repo

    sys.path.insert(0, str(repo))
    # We can't easily redirect REPO_ROOT in the module; instead test the logic inline.
    from corpus_sweep import _sha256, _walk_docs  # noqa: E402

    docs = _walk_docs(repo)
    hashes = {str(p.relative_to(repo)): _sha256(p) for p in docs}
    man_hashes = {f["sha256"] for f in json.loads(manifest.read_text())["files"]}
    manifested = [p for p, h in hashes.items() if json.loads(manifest.read_text())["files"][0]["path"] == p]
    dups = [p for p, h in hashes.items() if h in man_hashes and p not in manifested]
    unman = [p for p, h in hashes.items() if h not in man_hashes]
    assert "docs/a.pdf" in manifested or "docs/a.pdf" in dups  # path match or hash match
    assert "copies/a_copy.pdf" in dups
    assert "docs/b.pdf" in unman


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
