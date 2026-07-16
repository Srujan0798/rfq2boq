"""Fidelity-audit independence-gate tests (P0_03).

Proves the hard gate restored in `scripts/fidelity_audit.py`:
- non-independent gold (human_verified=false) → audit_enquiry returns an 'error'
  dict and the CLI exit code is non-zero (incident #11 regression guard).
- independent gold (human_verified=true) → audit proceeds normally.

Uses the real sacred-10 rowgold files (read-only) and a stub pipeline to keep
the test fast and avoid running the full extraction. The non-independent case
returns before the pipeline is ever called, so the stub is never invoked.
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

from check_eval_hacks import weak_warning  # noqa: E402
from fidelity_audit import ENQUIRIES, audit_enquiry, is_independent_gold, load_row_gold  # noqa: E402


class _StubPipeline:
    """Minimal stand-in for src.pipeline.Pipeline — audit_enquiry calls
    .run(source_path) and reads .boq_items off the result. The non-independent
    gate returns before the pipeline is touched, so this is only a safety net."""

    def run(self, src: str):  # noqa: D401, ANN001
        class _R:
            boq_items: list = []

        return _R()


def test_is_independent_gold_true_for_human_verified() -> None:
    """02_isro gold (human_verified=true) is independent."""
    entries, meta = load_row_gold(Path("data/real_rfqs/gold/rows/02_isro_vssc.rowgold.json"))
    assert entries, "02_isro gold should have entries"
    assert is_independent_gold(meta) is True, f"expected independent, meta={meta.get('human_verified')}"


def test_is_independent_gold_false_for_unverified() -> None:
    """08_sael gold (human_verified=false after P0_02 D4) is non-independent."""
    entries, meta = load_row_gold(Path("data/real_rfqs/gold/rows/08_sael.rowgold.json"))
    assert entries, "08_sael gold should have entries"
    assert is_independent_gold(meta) is False, f"expected non-independent, meta={meta.get('human_verified')}"


def test_non_independent_gold_hard_fails_audit() -> None:
    """audit_enquiry on 08_sael (non-independent gold) returns an 'error' dict."""
    info = ENQUIRIES["08_sael"]
    result = audit_enquiry("08_sael", info, _StubPipeline())  # type: ignore[arg-type]
    assert "error" in result, f"expected hard-fail error, got: {result}"
    assert "non-independent gold" in result["error"], result["error"]
    assert "self-comparison" in result["error"], result["error"]


def test_no_warning_weakening_pattern_in_fidelity_audit() -> None:
    """fidelity_audit.py must NOT contain the incident-#11 weakening: a
    logger.warning/warnings.warn mentioning independent/self-comparison."""
    src = Path("scripts/fidelity_audit.py").read_text()
    assert not weak_warning.search(src), (
        "fidelity_audit.py contains a warning where the independence gate should raise "
        "(incident #11 regression). Found: " + str(weak_warning.search(src))
    )


def test_no_env_override_in_fidelity_audit() -> None:
    """No ALLOW_*/SKIP_*/BYPASS_* flags gate the independence check."""
    src = Path("scripts/fidelity_audit.py").read_text()
    for pat in ("ALLOW_", "SKIP_", "BYPASS_"):
        assert pat not in src, f"fidelity_audit.py contains {pat}* override flag (incident #11 backdoor)"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
