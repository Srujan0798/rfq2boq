"""Frozen-hash gate tests (P0_03).

`scripts/check_frozen_hashes.py` guards the integrity of every eval/measurement
file (Rule 5). These tests confirm the verifier catches modified, missing, and
extra files. Uses tmp_path fixtures so no real frozen file is touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pytest  # noqa: E402

from check_frozen_hashes import FROZEN_PATHS, pin_manifest, verify_frozen_hashes  # noqa: E402


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "scripts").mkdir()
    (repo / "tests" / "regression").mkdir(parents=True)
    (repo / "config").mkdir()
    (repo / "data" / "real_rfqs" / "gold").mkdir(parents=True)
    for rel in FROZEN_PATHS:
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_text(f"# placeholder for {rel}\n")
    return repo


def test_frozen_passes_on_pristine(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    manifest = repo / "config" / "FROZEN_HASHES.sha256"
    pin_manifest(repo, manifest)
    offenders = verify_frozen_hashes(repo, manifest)
    assert offenders == [], f"expected intact, got: {offenders}"


def test_frozen_fails_on_modified_file(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    manifest = repo / "config" / "FROZEN_HASHES.sha256"
    pin_manifest(repo, manifest)
    (repo / "scripts" / "fidelity_audit.py").write_text("# tampered\n")
    offenders = verify_frozen_hashes(repo, manifest)
    assert any("MODIFIED" in o and "fidelity_audit.py" in o for o in offenders), offenders


def test_frozen_fails_on_missing_file(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    manifest = repo / "config" / "FROZEN_HASHES.sha256"
    pin_manifest(repo, manifest)
    (repo / "scripts" / "eval_ner.py").unlink()
    offenders = verify_frozen_hashes(repo, manifest)
    assert any("MISSING" in o and "eval_ner.py" in o for o in offenders), offenders


def test_frozen_fails_on_extra_manifest_entry(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    manifest = repo / "config" / "FROZEN_HASHES.sha256"
    pin_manifest(repo, manifest)
    bogus = "deadbeef" * 8
    manifest.write_text(manifest.read_text() + f"{bogus}  scripts/not_in_set.py\n")
    offenders = verify_frozen_hashes(repo, manifest)
    assert any("EXTRA" in o for o in offenders), offenders


def test_frozen_fails_when_manifest_missing(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    offenders = verify_frozen_hashes(repo, repo / "config" / "FROZEN_HASHES.sha256")
    assert len(offenders) == 1
    assert "manifest missing" in offenders[0].lower()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
