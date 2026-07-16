"""Regression test: 04_adani source file in eval_honest.py must point to the pipe BOQ.

History: the eval was using `BOQ PAGE2adani proj.pdf` (the duct insulation
file) as the source, but the gold (swa_04_adani.json) annotates the PIPE
insulation table which is on `BOQ PAGEadani proj.pdf`. This made F1
artificially 0.000 for many runs before the fix.

This test pins the source file so the config bug cannot return.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

EVAL_SCRIPT = Path("scripts/eval_honest.py")


@pytest.mark.unit
class TestEvalHonestAdaniSource:
    """Pin the 04_adani source to the pipe-insulation PDF, not the duct one."""

    def test_eval_script_exists(self) -> None:
        assert EVAL_SCRIPT.exists(), f"Missing: {EVAL_SCRIPT}"

    def test_04_adani_source_uses_pipe_pdf(self) -> None:
        content = EVAL_SCRIPT.read_text()
        # Find the 04_adani block
        m = re.search(r'"04_adani"\s*:\s*\{[^}]+\}', content, re.DOTALL)
        assert m, "04_adani block not found in eval_honest.py"
        block = m.group(0)
        assert "BOQ PAGEadani proj.pdf" in block, (
            f"04_adani source must include 'BOQ PAGEadani proj.pdf' "
            f"(the pipe-insulation file, which matches the gold). "
            f"Got block: {block}"
        )

    def test_04_adani_source_excludes_duct_pdf(self) -> None:
        """The duct file alone is the wrong source for the pipe gold."""
        content = EVAL_SCRIPT.read_text()
        m = re.search(r'"04_adani"\s*:\s*\{[^}]+\}', content, re.DOTALL)
        assert m, "04_adani block not found"
        block = m.group(0)
        # It's OK to have both files in a list, but not to point at PAGE2
        # as the only source. We allow both, forbid-only-PAGE2.
        only_page2 = (
            "PAGE2adani proj.pdf" in block
            and "PAGEadani proj.pdf" not in block
        )
        assert not only_page2, (
            f"04_adani source points to duct PDF (PAGE2) only. "
            f"Gold is for pipe insulation (PAGE). Block: {block}"
        )

    def test_04_adani_source_file_exists(self) -> None:
        path = Path("data/real_rfqs/swa_enquiries/04_adani/BOQ PAGEadani proj.pdf")
        assert path.exists(), f"Required source PDF missing: {path}"
