"""Leakage regression test for the frozen T3 corpus split.

data/real_rfqs/split_test.json freezes TEST = sacred10 + their email-bundle
duplicates + client-name carry-alongs + 5 explicitly chosen never-before-processed
Specification-2 documents (see docs/CORPUS_DEFINITION.md and
results/gazetteer_provenance_audit.md for the full justification).

This test fails if:
  1. Any TEST document's sha256 is double-counted into DEV or TRAIN in the
     frozen split (internal consistency).
  2. Any TEST document appears (by sha256-matched path, or by project-id-derived
     filename stem for the sacred10 folders) inside a directory that feeds
     training: data/annotations/cli_training/**, data/annotations/cli_drafts/**.
  3. Any mined-gazetteer term is confirmed TEST-exclusive per the frozen audit
     trail in results/gazetteer_provenance_audit.md (the two terms already
     found and removed must stay removed).

Legitimate TEST-eval artifacts (data/real_rfqs/gold/**, data/real_rfqs/annotated/**,
data/real_rfqs/annotations/**, data/real_rfqs/reference_real/**) are NOT flagged —
those exist to evaluate against TEST, not to train on it.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPLIT_PATH = ROOT / "data/real_rfqs/split_test.json"
MANIFEST_PATH = ROOT / "data/real_rfqs/corpus_manifest.json"
MINED_GAZETTEER_PATH = ROOT / "data/ontology/insulation_gazetteer_mined.json"

# Directories that are legitimate TEST-eval artifacts, never flagged as leakage.
EVAL_ONLY_DIRS = {
    "data/real_rfqs/gold",
    "data/real_rfqs/annotated",
    "data/real_rfqs/annotations",
    "data/real_rfqs/reference_real",
    "data/real_rfqs/raw",
    "data/real_rfqs/extracted",
    "data/real_rfqs/swa_enquiries",
}

# Directories that feed (or could feed) model training / silver-data pipelines.
# Any file here whose stem traces back to a TEST document is a leak.
TRAINING_DIRS = [
    "data/annotations/cli_training",
    "data/annotations/cli_drafts",
]

# Two terms confirmed TEST-exclusive (mined only from a chosen TEST document,
# with zero occurrence anywhere in the TRAIN pool) and removed from the mined
# gazetteer as part of this task. If they ever reappear, that is a reintroduced
# leak.
FORBIDDEN_GAZETTEER_TERMS = {
    "Anergy / Sevcon / Ensaviour / NES",
    "Based on the Insulation",
}


def _sanitize_stem(name: str) -> str:
    name = re.sub(r"\.json$", "", name, flags=re.I)
    name = re.sub(r"\.(extracted|rowgold)$", "", name, flags=re.I)
    name = re.sub(r"\.(pdf|xlsx|docx)$", "", name, flags=re.I)
    name = re.sub(r"[^A-Za-z0-9]+", "_", name)
    return name.strip("_").lower()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def split():
    if not SPLIT_PATH.exists():
        pytest.skip(f"{SPLIT_PATH} not present")
    return json.loads(SPLIT_PATH.read_text())


@pytest.fixture(scope="module")
def manifest():
    if not MANIFEST_PATH.exists():
        pytest.skip(f"{MANIFEST_PATH} not present")
    return json.loads(MANIFEST_PATH.read_text())


def test_split_files_exist(split):
    assert split["test"]["all_paths"], "TEST split is empty"
    assert split["dev"]["all_paths"], "DEV split is empty"
    assert split["train"]["all_paths"], "TRAIN split is empty"


def test_no_document_in_two_splits(split):
    test_set = set(split["test"]["all_paths"])
    dev_set = set(split["dev"]["all_paths"])
    train_set = set(split["train"]["all_paths"])

    overlap_td = test_set & dev_set
    overlap_tt = test_set & train_set
    overlap_dt = dev_set & train_set

    assert not overlap_td, f"documents in both TEST and DEV: {overlap_td}"
    assert not overlap_tt, f"documents in both TEST and TRAIN: {overlap_tt}"
    assert not overlap_dt, f"documents in both DEV and TRAIN: {overlap_dt}"


def test_sacred10_and_bundles_are_test(split):
    """The sacred 10 and their email-bundle duplicates must always be TEST."""
    test_set = set(split["test"]["all_paths"])
    for p in split["test"]["sacred10"]:
        assert p in test_set
    for p in split["test"]["bundle_duplicates_of_sacred10"]:
        assert p in test_set


def test_manifest_sha256_matches_split_sha256(split, manifest):
    """Every TEST path's sha256 in the manifest must be internally consistent
    (defends against silently swapping a TEST path's file contents)."""
    by_path = {e["path"]: e["sha256"] for e in manifest["files"]}
    for p in split["test"]["all_paths"]:
        assert p in by_path, f"TEST path missing from manifest: {p}"
        on_disk = ROOT / p
        if on_disk.exists():
            assert _sha256(on_disk) == by_path[p], f"sha256 drift for TEST doc {p}"


def test_no_test_stem_in_training_dirs(split):
    """No BIOES/training artifact may be derived from a TEST document.

    Regression target: data/annotations/cli_training/verified_bioes/*.json is
    named after the sacred10 project id (e.g. 06_avante_kirloskar_pune_030.json),
    i.e. built directly from TEST-split rowgold. That is TEST->TRAIN leakage
    and must fail this test until removed/fixed.
    """
    test_project_stems = set()
    for p in split["test"]["all_paths"]:
        # sacred10 paths look like data/real_rfqs/swa_enquiries/<project_id>/<file>
        parts = Path(p).parts
        if "swa_enquiries" in parts:
            idx = parts.index("swa_enquiries")
            if idx + 1 < len(parts):
                test_project_stems.add(parts[idx + 1].lower())
        test_project_stems.add(_sanitize_stem(Path(p).name))

    leaks: list[str] = []
    for d in TRAINING_DIRS:
        dir_path = ROOT / d
        if not dir_path.exists():
            continue
        for f in dir_path.rglob("*"):
            if not f.is_file():
                continue
            stem = _sanitize_stem(f.name)
            for proj in test_project_stems:
                if proj and (stem.startswith(proj) or proj in stem):
                    leaks.append(f"{f.relative_to(ROOT)} matches TEST project/doc '{proj}'")
                    break

    assert not leaks, (
        "TEST-split documents found feeding training directories "
        "(sacred-10 / TEST rowgold must never be used for training):\n" + "\n".join(sorted(set(leaks)))
    )


def test_forbidden_gazetteer_terms_stay_removed():
    """The two confirmed TEST-exclusive mined-gazetteer terms must never reappear."""
    if not MINED_GAZETTEER_PATH.exists():
        pytest.skip(f"{MINED_GAZETTEER_PATH} not present (gitignored local artifact)")
    mined = json.loads(MINED_GAZETTEER_PATH.read_text())
    materials = set(mined.get("materials", []))
    present = FORBIDDEN_GAZETTEER_TERMS & materials
    assert not present, f"TEST-exclusive gazetteer terms reintroduced: {present}"
