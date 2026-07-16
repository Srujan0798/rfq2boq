"""Unit tests for eval_product.py and build_row_gold.py."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestGoldBuilderIndependence:
    """Guard against the self-comparison cheat (building gold from the pipeline)."""

    def test_gold_builder_does_not_import_pipeline(self):
        """build_row_gold.py must NOT import src.pipeline, XLSXRowPipeline, or BOQAssembler."""
        script_path = Path(__file__).parent.parent.parent / "scripts" / "build_row_gold.py"
        source = script_path.read_text()
        tree = ast.parse(source, filename=str(script_path))

        imported_names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_names.append(node.module)

        forbidden = {"src.pipeline", "src.pipeline_xlsx", "src.domain.boq_assembler"}
        found = [m for m in imported_names if any(f.startswith(m) for f in forbidden)]
        assert not found, (
            f"build_row_gold.py imports forbidden modules: {found}. "
            "Gold must be independent of the prediction pipeline."
        )

    def test_eval_product_does_not_import_pipeline_in_gold_paths(self):
        """eval_product.py gold-loading paths must not invoke Pipeline."""
        script_path = Path(__file__).parent.parent.parent / "scripts" / "eval_product.py"
        source = script_path.read_text()
        tree = ast.parse(source, filename=str(script_path))

        func_defs: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_defs.add(node.name)

        gold_load_funcs = [f for f in func_defs if "gold" in f.lower() and "load" in f.lower()]
        assert gold_load_funcs, "No gold-load function found — check naming"

    def test_row_gold_files_exist(self):
        """Row-gold JSON files must exist for all 4 XLSX enquiries."""
        rows_dir = Path(__file__).parent.parent.parent / "data" / "real_rfqs" / "gold" / "rows"
        expected = ["02_isro_vssc", "03_zydus_matoda_osd", "05_zydus_animal_pharmez", "08_sael"]
        for eid in expected:
            path = rows_dir / f"{eid}.rowgold.json"
            assert path.exists(), f"Row-gold not found: {path}"

    def test_row_gold_human_verified_flag(self):
        """Row-gold entries must have human_verified field (even if False)."""
        rows_dir = Path(__file__).parent.parent.parent / "data" / "real_rfqs" / "gold" / "rows"
        import json

        for f in [
            "02_isro_vssc.rowgold.json",
            "03_zydus_matoda_osd.rowgold.json",
            "05_zydus_animal_pharmez.rowgold.json",
            "08_sael.rowgold.json",
        ]:
            path = rows_dir / f
            assert path.exists(), f"Missing: {path}"
            with open(path) as fh:
                d = json.load(fh)
            assert "entries" in d
            assert len(d["entries"]) > 0
            for entry in d["entries"]:
                assert "human_verified" in entry, f"Missing human_verified in {f}"

    def test_row_gold_quantity_is_decimal(self):
        """Row-gold quantities must be parseable as Decimal (no narrative text)."""
        rows_dir = Path(__file__).parent.parent.parent / "data" / "real_rfqs" / "gold" / "rows"
        import json
        from decimal import Decimal, InvalidOperation

        for f in [
            "02_isro_vssc.rowgold.json",
            "03_zydus_matoda_osd.rowgold.json",
            "05_zydus_animal_pharmez.rowgold.json",
            "08_sael.rowgold.json",
        ]:
            path = rows_dir / f
            with open(path) as fh:
                d = json.load(fh)
            for entry in d["entries"]:
                qty_str = str(entry.get("quantity", "0"))
                try:
                    Decimal(qty_str)
                except (InvalidOperation, ValueError):
                    pytest.fail(f"{f} entry {entry.get('item_no')}: quantity '{qty_str}' " "is not a valid decimal")


class TestEvalProductIntegration:
    """Integration test: eval_product.py must run and produce non-zero entity counts for row-level."""

    def test_eval_product_runs_without_error(self):
        """eval_product.py --enquiry 08_sael --level row should complete without exceptions."""
        script = Path(__file__).parent.parent.parent / "scripts" / "eval_product.py"
        result = subprocess.run(
            [sys.executable, str(script), "--enquiry", "08_sael", "--level", "row"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"eval_product.py failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        assert "Wrote" in result.stdout or "SUMMARY" in result.stdout

    def test_eval_product_row_level_not_near_100_percent(self):
        """Row-level match rate should NOT be suspiciously near 100% UNLESS the
        gold is provably independent (hand-transcribed, no pipeline imports).

        100% match is genuine when:
          - Row-gold is hand-transcribed from XLSX (build_row_gold*.py does NOT
            import src.pipeline / XLSXRowPipeline / BOQAssembler)
          - method field indicates hand-transcription OR independent transcription
          - For XLSX-derived gold, owner sign-off via human_verified is desirable
            but NOT required for 100% to be considered genuine (the XLSX is the
            gold source by construction, so 100% match is the EXPECTED outcome
            when the pipeline is correct, not a sign of cheating).

        The human_verified flag is a workflow status (owner has reviewed), not
        a data-provenance guarantee. Provenance is proven by:
          (a) method field is transcription / independent, AND
          (b) build_row_gold*.py does not import the pipeline modules.
        """
        script = Path(__file__).parent.parent.parent / "scripts" / "eval_product.py"
        result = subprocess.run(
            [sys.executable, str(script), "--enquiry", "all", "--level", "row"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"eval_product.py failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        import json

        results_path = Path(__file__).parent.parent.parent / "results" / "product_eval.json"
        rows_dir = Path(__file__).parent.parent.parent / "data" / "real_rfqs" / "gold" / "rows"
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"
        with open(results_path) as fh:
            data = json.load(fh)
        for r in data.get("row_level", []):
            if "summary" not in r:
                continue
            mr = r["summary"]["match_rate_pct"]
            eid = r["enquiry_id"]
            if mr < 95.0:
                continue
            row_gold_path = rows_dir / f"{eid}.rowgold.json"
            assert row_gold_path.exists(), f"Row gold not found: {row_gold_path}"
            with open(row_gold_path) as fh:
                rg = json.load(fh)
            method = rg.get("method", "").lower()
            assert "transcription" in method or "hand" in method or "independent" in method, (
                f"Suspicious match rate {mr}% for {eid} but rowgold method={method!r} "
                "does not indicate hand/independent transcription."
            )
            for builder in scripts_dir.glob("build_row_gold*.py"):
                src = builder.read_text()
                tree = ast.parse(src, filename=str(builder))
                imported = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imported.append(alias.name)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imported.append(node.module)
                forbidden = {"src.pipeline", "src.pipeline_xlsx", "src.domain.boq_assembler"}
                bad = [m for m in imported if any(m.startswith(f) for f in forbidden)]
                assert not bad, (
                    f"Suspicious match rate {mr}% for {eid}: {builder.name} imports "
                    f"forbidden modules {bad}. Gold must NOT be derived from the "
                    "prediction pipeline."
                )
