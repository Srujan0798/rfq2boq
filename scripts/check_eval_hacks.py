#!/usr/bin/env python3
"""Check eval scripts for threshold manipulation and per-filename hacks.

P0_03 (2026-07-06) extension: also scans for incident-reintroduction patterns:
env-gated eval behavior (ALLOW_*/SKIP_* flags, os.environ reads that gate the
check), and `logger.warning` / `warnings.warn` where the independence gate in
fidelity_audit.py should raise instead (incident #11 regression guard).
"""

import re
from pathlib import Path

scripts_dir = Path("scripts")
eval_scripts = list(scripts_dir.glob("eval_*.py"))
# fidelity_audit.py is scanned for the independence-gate weakening pattern too.
gate_scripts = [scripts_dir / "fidelity_audit.py"]

# Pattern: per-filename == comparison (hack)
# Excludes "args.enquiry" / "args.filename" which are legitimate CLI argument checks
hack_pattern = re.compile(
    r'(?<!args\.)(?:filename|enquiry|eid|doc_id)\s*==\s*["\']',
    re.IGNORECASE,
)

# Pattern: material threshold below 0.6
low_threshold = re.compile(
    r"(?:material_threshold|MATERIAL_THRESHOLD)\s*[=:]\s*0\.([0-4])\d*\b",
)

# Pattern (P0_03): env-gated eval behavior — ALLOW_*/SKIP_* flags or os.environ
# reads that gate an eval/provenance check. Legitimate reads of RFQ2BOQ_* settings
# are not a hit; the hit is a flag that bypasses a check.
env_override = re.compile(
    r'\b(?:ALLOW_[A-Z_]+|SKIP_[A-Z_]+|BYPASS_[A-Z_]+)\b',
)

# Pattern (P0_03): os.environ.get / os.getenv used to gate a check in eval/gate scripts
# (incident #11-style backdoor). Heuristic: an env read assigned to a flag used in a
# conditional that skips a hard check.
env_get_pattern = re.compile(
    r'os\.(?:environ|getenv)\[?["\']',
)

# Pattern (P0_03): a logger.warning / warnings.warn call on the line immediately
# following an is_independent_gold check in fidelity_audit.py — the incident #11
# weakening. We flag the warning call itself when it mentions "self-comparison" or
# "self_reference" or "independent".
weak_warning = re.compile(
    r'(?:logger\.warning|warnings\.warn)\s*\([^)]*(?:self.comparison|self_reference|independent|human_verified)',
    re.IGNORECASE,
)


def _scan(s: Path) -> int:
    """Scan one script; return the number of anti-cheat patterns found."""
    found = 0
    content = s.read_text()
    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
            continue

        m = hack_pattern.search(line)
        if m:
            print(f'    \u26a0 {s.name}:{i}: potential filename hack: {stripped[:80]}')
            found += 1

        m2 = low_threshold.search(line)
        if m2:
            print(f'    FAIL {s.name}:{i}: threshold below 0.6: {stripped[:80]}')
            found += 1

        if s.name in {"fidelity_audit.py", "check_gold_provenance.py"} or s.name.startswith("eval_"):
            m3 = env_override.search(line)
            if m3:
                print(f'    FAIL {s.name}:{i}: env override flag (incident #11 pattern): {stripped[:80]}')
                found += 1

            m4 = env_get_pattern.search(line)
            if m4:
                print(f'    \u26a0 {s.name}:{i}: os.environ/getenv read in eval/gate script (review for backdoor): {stripped[:80]}')
                found += 1

        if s.name == "fidelity_audit.py":
            m5 = weak_warning.search(line)
            if m5:
                print(f'    FAIL {s.name}:{i}: warning where independence gate should raise (incident #11 regression): {stripped[:80]}')
                found += 1
    return found


def main() -> int:
    found = 0
    for s in eval_scripts + gate_scripts:
        if s.exists():
            found += _scan(s)
    if found:
        print(f"FAIL: {found} anti-cheat pattern(s) detected")
        return 1
    print("  (clean)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
