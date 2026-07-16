"""Verify frozen files still exist at their exact paths.

This test ensures a future cleanup pass cannot accidentally break the
frozen-hash verification chain. Run as part of make verify.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

FROZEN_HASHES_FILE = Path("config/FROZEN_HASHES.sha256")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_frozen_hashes() -> dict[str, str]:
    """Parse FROZEN_HASHES.sha256 into {path: sha256}."""
    hashes: dict[str, str] = {}
    for line in FROZEN_HASHES_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        sha, relpath = line.split("  ", 1)
        hashes[relpath] = sha
    return hashes


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


class TestFrozenFilesExist:
    """Every file listed in FROZEN_HASHES.sha256 must exist at its exact path."""

    def test_frozen_hashes_file_exists(self):
        assert FROZEN_HASHES_FILE.exists(), f"{FROZEN_HASHES_FILE} missing"

    def test_all_frozen_files_exist(self):
        hashes = _load_frozen_hashes()
        missing = []
        for relpath in hashes:
            full = REPO_ROOT / relpath
            if not full.exists():
                missing.append(relpath)
        assert not missing, f"Frozen files missing: {missing}"

    def test_all_frozen_files_hashes_match(self):
        hashes = _load_frozen_hashes()
        mismatches = []
        for relpath, expected_sha in hashes.items():
            full = REPO_ROOT / relpath
            if full.exists():
                actual_sha = _sha256(full)
                if actual_sha != expected_sha:
                    mismatches.append(f"{relpath}: expected {expected_sha[:12]}... got {actual_sha[:12]}...")
        assert not mismatches, f"Hash mismatches: {mismatches}"

    def test_sacred_dirs_exist(self):
        """Critical directories that must never be moved."""
        sacred = [
            "data/real_rfqs/swa_enquiries",
            "data/real_rfqs/gold",
            "config",
            "src",
            "tests",
            "resources",
            "tasks/phase9",
        ]
        missing = [d for d in sacred if not (REPO_ROOT / d).is_dir()]
        assert not missing, f"Sacred directories missing: {missing}"
