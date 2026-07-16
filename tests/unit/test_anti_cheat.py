"""Anti-cheat regression test: ensure no evaluation script builds gold from pipeline.

The project was cheated twice: eval scripts that compare pipeline output against
pipeline-derived "gold" (self-comparison). This test catches the pattern.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

SCRIPTS_DIR = Path("scripts")
EVAL_PRODUCT = SCRIPTS_DIR / "eval_product.py"


def _is_code_line(line: str) -> bool:
    """Check if a line is executable code, not a string literal."""
    stripped = line.lstrip()
    if not stripped or stripped.startswith("#"):
        return False
    in_string = False
    for ch in line:
        if ch in ('"', "'") and (line.index(ch) == 0 or line[line.index(ch) - 1] != "\\"):
            in_string = not in_string
        if not in_string and stripped.startswith(
            ("if ", "for ", "while ", "return ", "assert ", "raise ", "def ", "class ", "import ", "from ", "=", "(")
        ):
            return True
    return False


@pytest.mark.unit
class TestAntiCheatRegression:
    """Regression tests to prevent self-comparison cheating."""

    def test_validate_product_script_exists(self) -> None:
        assert EVAL_PRODUCT.exists(), f"validate_product.py not found at {EVAL_PRODUCT}"

    def test_validate_product_gold_loaded_from_gold_dir(self) -> None:
        """Gold rows must be loaded from data/real_rfqs/gold/, not from Pipeline output."""
        content = EVAL_PRODUCT.read_text()

        gold_dir_pattern = re.compile(r'["\']data/real_rfqs/gold["\']')
        pipeline_pattern = re.compile(r"Pipeline\(\)\.run|XLSXRowPipeline\(\)")

        gold_dir_lines = [(i + 1, line) for i, line in enumerate(content.splitlines()) if gold_dir_pattern.search(line)]

        pipeline_lines = [(i + 1, line) for i, line in enumerate(content.splitlines()) if pipeline_pattern.search(line)]

        if pipeline_lines and not gold_dir_lines:
            pytest.fail(
                f"{EVAL_PRODUCT} uses Pipeline but does not reference gold directory.\n"
                f"  Pipeline lines: {[l for _, l in pipeline_lines]}"
            )

    def test_no_self_comparison_pattern_in_validate_product(self) -> None:
        """Hard-check: no script should compare pipeline output to pipeline-produced gold."""
        content = EVAL_PRODUCT.read_text()

        tree = ast.parse(content)
        pipeline_calls: list[int] = []
        gold_load_functions: set[str] = set()

        class Visitor(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                name = ""
                if isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                elif isinstance(node.func, ast.Name):
                    name = node.func.id

                lineno = node.lineno or 0
                if (
                    name in ("run",)
                    and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Call)
                    and isinstance(node.func.value.func, ast.Name)
                    and node.func.value.func.id == "Pipeline"
                ):
                    pipeline_calls.append(lineno)

                self.generic_visit(node)

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                if "gold" in node.name.lower():
                    gold_load_functions.add(node.name)
                self.generic_visit(node)

        Visitor().visit(tree)

        func_def_lines: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.lineno:
                func_def_lines.add(node.lineno)

        for lineno in pipeline_calls:
            line_content = content.splitlines()[lineno - 1]
            if not _is_code_line(line_content):
                continue

            for glf in gold_load_functions:
                if glf in line_content:
                    pytest.fail(
                        f"{EVAL_PRODUCT}:{lineno}: Pipeline call inside gold-loading function '{glf}'.\n"
                        f"  Line: {line_content.strip()}"
                    )

    def test_validate_product_loads_gold_independently(self) -> None:
        """validate_product.py must load gold from human-annotated files, not from pipeline."""
        content = EVAL_PRODUCT.read_text()
        tree = ast.parse(content)

        gold_func_names: list[str] = []
        pipeline_in_gold_func: list[tuple[str, int]] = []

        class Visitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                if "gold" in node.name.lower() or node.name.startswith("_load_gold"):
                    gold_func_names.append(node.name)
                self.generic_visit(node)

            def visit_Call(self, node: ast.Call) -> None:
                name = ""
                if isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                elif isinstance(node.func, ast.Name):
                    name = node.func.id

                func_name = ""
                for n in ast.walk(node):
                    if isinstance(n, ast.FunctionDef):
                        func_name = n.name
                        break

                if name == "run" and func_name and ("gold" in func_name.lower() or func_name.startswith("_load_gold")):
                    pipeline_in_gold_func.append((func_name, node.lineno or 0))
                self.generic_visit(node)

        Visitor().visit(tree)

        if pipeline_in_gold_func:
            for func, lineno in pipeline_in_gold_func:
                pytest.fail(
                    f"{EVAL_PRODUCT}:{lineno}: Pipeline().run() called inside gold-loading "
                    f"function '{func}'. Gold must come from human annotation."
                )

    def test_scripts_dir_no_pipeline_in_gold_loading_functions(self) -> None:
        """Every script in scripts/ that loads gold must NOT use Pipeline to produce it."""
        gold_loading_scripts = [
            "validate_product.py",
            "bootstrap_swa_gold.py",
            "evaluate_real.py",
        ]

        for script_name in gold_loading_scripts:
            script_path = SCRIPTS_DIR / script_name
            if not script_path.exists():
                continue

            content = script_path.read_text()
            tree = ast.parse(content)

            gold_funcs: list[str] = []
            pipeline_calls_in_gold_func: list[tuple[str, int]] = []

            class Visitor(ast.NodeVisitor):
                def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                    if "gold" in node.name.lower() or node.name.startswith("_load_gold"):
                        gold_funcs.append(node.name)
                    self.generic_visit(node)

                def visit_Call(self, node: ast.Call) -> None:
                    name = ""
                    if isinstance(node.func, ast.Attribute):
                        name = node.func.attr
                    elif isinstance(node.func, ast.Name):
                        name = node.func.id

                    enclosing_func = ""
                    for parent in ast.walk(node):
                        if isinstance(parent, ast.FunctionDef):
                            enclosing_func = parent.name
                            break

                    if (
                        name == "run"
                        and enclosing_func
                        and ("gold" in enclosing_func.lower() or enclosing_func.startswith("_load_gold"))
                    ):
                        pipeline_calls_in_gold_func.append((enclosing_func, node.lineno or 0))
                    self.generic_visit(node)

            Visitor().visit(tree)

            for func_name, lineno in pipeline_calls_in_gold_func:
                pytest.fail(
                    f"{script_path}:{lineno}: Pipeline call inside gold-loading function '{func_name}'.\n"
                    f"  Gold must be loaded from data/real_rfqs/gold/, not produced by pipeline."
                )

    def test_no_pipeline_self_comparison_any_script(self) -> None:
        """Comprehensive scan: any script that uses Pipeline must also reference gold directory."""
        eval_scripts = list(SCRIPTS_DIR.glob("evaluate*.py")) + list(SCRIPTS_DIR.glob("validate*.py"))

        for script in eval_scripts:
            content = script.read_text()

            if "Pipeline().run" not in content and "XLSXRowPipeline" not in content:
                continue

            if "data/real_rfqs/gold" not in content:
                pytest.fail(
                    f"{script}: uses Pipeline but does not load from data/real_rfqs/gold.\n"
                    f"  This is suspicious: pipeline output being compared to something that is not"
                    f"  independently human-annotated gold."
                )

    # ── New anti-cheat tests (Lane A hardening) ──────────────────────────

    def test_row_gold_provenance_warning(self) -> None:
        """Warn if row gold is pipeline-derived (pdfplumber = same as pipeline).

        This is a SOFT check (does not fail CI) — it warns about self-comparison risk.
        """
        gold_dir = Path("data/real_rfqs/gold/rows")
        if not gold_dir.exists():
            return

        import json
        independent: list[str] = []
        suspicious: list[str] = []
        for gf in sorted(gold_dir.glob("*.rowgold.json")):
            data = json.loads(gf.read_text())
            method = data.get("method", "")
            if "pdfplumber" in method.lower():
                suspicious.append(f"{gf.name}: method='{method}'")
            else:
                independent.append(f"{gf.name}: method='{method}'")

        msg = f"Gold provenance: {len(independent)} independent, {len(suspicious)} pipeline-derived"
        print(f"\n  {msg}")
        for s in suspicious:
            print(f"    ⚠ SELF-COMPARE: {s}")
        for i in independent:
            print(f"    ✓ INDEPENDENT: {i}")
        print()

        # Hard-fail only if ALL gold is pipeline-derived (means no independent gold exists)
        if independent and suspicious:
            pass  # warn only — some gold is independent
        elif suspicious and not independent:
            pytest.fail(f"ALL gold is pipeline-derived ({len(suspicious)} files). No independent gold!")

    def test_no_threshold_lowering_in_eval_scripts(self) -> None:
        """Eval scripts must not lower matching thresholds to inflate scores.

        Minimum allowed: material_threshold >= 0.6, quantity_tolerance <= 0.05.
        """
        eval_scripts = list(SCRIPTS_DIR.glob("eval_*.py")) + list(SCRIPTS_DIR.glob("validate_*.py"))
        low_mat_threshold = re.compile(r"(?:material_threshold|MATERIAL_THRESHOLD)\s*[=:]\s*0\.(\d+)\b", re.IGNORECASE)

        for script in eval_scripts:
            content = script.read_text()
            lines = content.splitlines()

            for i, line in enumerate(lines, 1):
                m = low_mat_threshold.search(line)
                if m:
                    threshold_str = f"0.{m.group(1)}"
                    threshold_val = float(threshold_str)
                    if threshold_val < 0.6:
                        pytest.fail(
                            f"{script}:{i}: material threshold {threshold_val:.2f} is below 0.6.\n"
                            f"  Line: {line.strip()}"
                        )

    def test_no_filename_hacks_in_eval(self) -> None:
        """Eval scripts must not have 'if filename ==' hacks for specific enquiries.

        Legitimate patterns like 'if eid in GOLD_PROVENANCE' are allowed.
        Suspicious patterns: 'if filename == "..."', 'if eid == "..."' that
        change matching criteria per file.
        """
        eval_scripts = list(SCRIPTS_DIR.glob("eval_*.py")) + list(SCRIPTS_DIR.glob("validate_*.py"))

        # Look for direct '==' comparisons against string literals for filenames/enquiries
        # Exclude "args.enquiry" which is legitimate CLI argument checking
        hack_pattern = re.compile(
            r'(?<!args\.)(?:filename|enquiry|eid|doc_id)\s*==\s*["\']',
            re.IGNORECASE,
        )

        for script in eval_scripts:
            content = script.read_text()
            lines = content.splitlines()

            suspicious_lines: list[tuple[int, str]] = []
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue
                # Skip lines that are comments or docstrings
                if hack_pattern.search(line):
                    suspicious_lines.append((i, stripped))

            if suspicious_lines:
                # Only warn if the hack changes matching behavior (hard to detect statically,
                # so warn instead of fail)
                print(f"\n  ⚠ {script}: {len(suspicious_lines)} potential per-filename comparison(s):")
                for n, s in suspicious_lines[:5]:
                    print(f"    L{n}: {s}")
                print()

    def test_no_false_100_claims_in_results(self) -> None:
        """Reject '100% COMPLETE' or equivalent claims in results/.

        Excludes lines that discuss the anti-cheat rule itself (e.g.
        '~100% is a red flag to investigate').
        """
        results_dir = Path("results")
        if not results_dir.exists():
            return

        claim_pattern = re.compile(
            r'(?:^|[^"\'])(100%\s*(?:COMPLETE|ACCURACY|F1|PERFECT|MATCH|RECALL|PRECISION))',
            re.IGNORECASE,
        )
        suspicious: list[str] = []
        for rf in sorted(results_dir.iterdir()):
            if rf.suffix not in (".json", ".md", ".txt"):
                continue
            content = rf.read_text()
            lines = content.splitlines()
            for line in lines:
                if "red flag" in line.lower() or "anti-cheat" in line.lower() or "greps for" in line.lower():
                    continue  # skip discussion of the rule itself
                if claim_pattern.search(line):
                    suspicious.append(f"{rf.name}: {line.strip()[:120]}")

        if suspicious:
            detail = "\n".join(suspicious[:5])
            pytest.fail(
                f"Found {len(suspicious)} '100% COMPLETE' claims in results/:\n{detail}\n"
                f"  Per anti-cheat rule: '~100% is a red flag to investigate, not celebrate.'"
            )

    def test_human_verified_not_set_on_regenerated_gold(self) -> None:
        """When gold is regenerated, human_verified must remain False."""
        gold_dir = Path("data/real_rfqs/gold/rows/independent")
        if not gold_dir.exists():
            return

        import json
        for gf in sorted(gold_dir.glob("*.rowgold.json")):
            data = json.loads(gf.read_text())
            if data.get("human_verified", False):
                pytest.fail(
                    f"{gf.name}: human_verified=true on auto-regenerated gold.\n"
                    f"  Auto-generated gold must have human_verified=false until reviewed."
                )
