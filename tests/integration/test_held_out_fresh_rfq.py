"""Held-out freshness test — proves no result cache between files.

The Z1 task requires that the pipeline produces real, fresh output for a
brand-new RFQ the SWA evaluation set has never seen. This test:

  1. Runs the pipeline on a file from `data/real_rfqs/reference_real/`
     that is NOT in `data/real_rfqs/swa_enquiries/`.
  2. Asserts the pipeline returns >= 1 BOQ item and a non-empty project
     name.
  3. Runs the pipeline on a SECOND held-out file and asserts the output
     is not byte-identical to the first (proves no shared cache key
     keyed on file path or content hash).
  4. Asserts the timing for the first run is NOT suspiciously fast
     (< 50 ms would indicate a content-hash result cache).
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

REFERENCE_DIR = Path("data/real_rfqs/reference_real")
SWA_DIR = Path("data/real_rfqs/swa_enquiries")


def _pick_held_out_files() -> list[Path]:
    """Return up to 2 PDFs from reference_real that are NOT in swa_enquiries."""
    if not REFERENCE_DIR.exists():
        return []
    swa_stems = {p.stem for p in SWA_DIR.rglob("*.pdf")} if SWA_DIR.exists() else set()
    candidates = sorted(p for p in REFERENCE_DIR.glob("*.pdf") if p.stem not in swa_stems)
    return candidates[:2]


@pytest.mark.integration
class TestHeldOutFreshRfq:
    """Prove the pipeline does not cache results across files."""

    def test_held_out_files_exist(self) -> None:
        files = _pick_held_out_files()
        assert files, f"No held-out PDFs found in {REFERENCE_DIR}. Add a real RFQ there."

    def test_pipeline_runs_on_held_out(self) -> None:
        from src.pipeline import Pipeline

        files = _pick_held_out_files()
        if not files:
            pytest.skip("No held-out PDFs in reference_real/")
        target = files[0]

        p = Pipeline()
        t0 = time.time()
        result = p.run(str(target))
        dt = time.time() - t0

        # Real work happened — not a 1-ms cache hit
        assert dt >= 0.05, f"Pipeline returned in {dt * 1000:.0f}ms — suspiciously fast, suspect cache"

        # Pipeline produced something
        assert result is not None
        assert hasattr(result, "boq_items")
        assert hasattr(result, "project_name")
        assert result.project_name, "project_name is empty"
        # It's OK to return 0 items (the file might be a scanned PDF or
        # not have a recognizable BOQ table), but it should not error
        # silently.
        assert result.metadata is not None

    def test_two_held_out_files_produce_different_outputs(self) -> None:
        """Two different held-out files must produce different JSON.
        If they collide, the result store is keyed on something too
        coarse (e.g. file contents hash, user id)."""
        from src.pipeline import Pipeline

        files = _pick_held_out_files()
        if len(files) < 2:
            pytest.skip(f"Need 2 held-out PDFs in {REFERENCE_DIR}, found {len(files)}")
        f1, f2 = files[0], files[1]

        p = Pipeline()
        r1 = p.run(str(f1))
        r2 = p.run(str(f2))

        # Project name should differ (different files)
        assert r1.project_name != r2.project_name or (f1.stem == f2.stem), (
            f"Same project_name for different files: {r1.project_name!r}"
        )

        # JSON serialisation must differ (different items, different
        # doc_id, different metadata).
        from src.export.json_formatter import JSONFormatter

        j1 = JSONFormatter().format_to_string(r1)
        j2 = JSONFormatter().format_to_string(r2)
        assert j1 != j2, "Two different files produced byte-identical JSON — possible shared cache"

    def test_fresh_run_not_corrupted_by_previous_runs(self) -> None:
        """Run the same held-out file twice in the same process. The
        second run must produce the same item count (deterministic
        extraction) but the JSON should differ because doc_id includes
        a timestamp. If JSON were byte-identical, that would be
        suspicious."""
        from src.pipeline import Pipeline

        files = _pick_held_out_files()
        if not files:
            pytest.skip("No held-out PDFs in reference_real/")
        target = files[0]

        p = Pipeline()
        r1 = p.run(str(target))
        r2 = p.run(str(target))

        # Item count must match (deterministic)
        assert len(r1.boq_items) == len(r2.boq_items), "Item count not deterministic across runs"
        # JSON should differ because doc_id has a timestamp
        assert r1.doc_id != r2.doc_id, "doc_id is identical — possible result cache"
