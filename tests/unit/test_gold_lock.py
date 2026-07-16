"""Gold sha256 lock tests (P0_02).

The lock (`data/real_rfqs/gold/GOLD_LOCK.sha256`) is the foundation of the
anti-cheat Rule 3 (gold is owner-only). `verify_gold_lock()` must catch every
form of tampering: modified, added, or deleted files. These tests build a tiny
fake gold tree on `tmp_path` (never touching real gold) and confirm each case.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from check_gold_provenance import LOCK_FILENAME, verify_gold_lock  # noqa: E402


def _make_gold_tree(tmp_path: Path) -> Path:
    gold_root = tmp_path / "gold"
    gold_root.mkdir()
    (gold_root / "rows").mkdir()
    (gold_root / "swa_01.json").write_text('{"doc_id": "01"}')
    (gold_root / "rows" / "01.rowgold.json").write_text('{"doc_id": "01", "entries": []}')
    return gold_root


def _write_lock(gold_root: Path) -> None:
    import hashlib

    lines = []
    for f in sorted(gold_root.rglob("*")):
        if not f.is_file() or f.name == LOCK_FILENAME:
            continue
        rel = f.relative_to(gold_root)
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        lines.append(f"{digest}  {rel}")
    (gold_root / LOCK_FILENAME).write_text("\n".join(lines) + "\n")


def test_lock_passes_on_pristine_gold(tmp_path: Path) -> None:
    gold_root = _make_gold_tree(tmp_path)
    _write_lock(gold_root)
    offenders = verify_gold_lock(gold_root)
    assert offenders == [], f"expected intact lock, got: {offenders}"


def test_lock_fails_on_modified_file(tmp_path: Path) -> None:
    gold_root = _make_gold_tree(tmp_path)
    _write_lock(gold_root)
    (gold_root / "swa_01.json").write_text('{"doc_id": "01-tampered"}')
    offenders = verify_gold_lock(gold_root)
    assert len(offenders) == 1, f"expected 1 offender, got: {offenders}"
    assert "MODIFIED" in offenders[0]
    assert "swa_01.json" in offenders[0]


def test_lock_fails_on_added_file(tmp_path: Path) -> None:
    gold_root = _make_gold_tree(tmp_path)
    _write_lock(gold_root)
    (gold_root / "rows" / "sneaky.rowgold.json").write_text('{"injected": true}')
    offenders = verify_gold_lock(gold_root)
    assert len(offenders) == 1, f"expected 1 offender, got: {offenders}"
    assert "ADDED" in offenders[0]
    assert "sneaky.rowgold.json" in offenders[0]


def test_lock_fails_on_deleted_file(tmp_path: Path) -> None:
    gold_root = _make_gold_tree(tmp_path)
    _write_lock(gold_root)
    (gold_root / "rows" / "01.rowgold.json").unlink()
    offenders = verify_gold_lock(gold_root)
    assert len(offenders) == 1, f"expected 1 offender, got: {offenders}"
    assert "DELETED" in offenders[0]
    assert "01.rowgold.json" in offenders[0]


def test_lock_fails_when_lock_file_missing(tmp_path: Path) -> None:
    gold_root = _make_gold_tree(tmp_path)
    offenders = verify_gold_lock(gold_root)
    assert len(offenders) == 1
    assert "missing" in offenders[0].lower()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
