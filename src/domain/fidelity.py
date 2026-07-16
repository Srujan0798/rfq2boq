"""Per-document fidelity auditor — the R1 proof artifact.

PROVES R1 per document: source rows (from source_truth.json, the independent
ruler built in P1_01) vs pipeline output rows, with an exact diff of misses,
over-captures, and flagged rows.

ROW-MATCHING RULES (readable by a non-programmer — SWA sees these):
  A source row matches an output row when ALL of:
    1. DESCRIPTION SIMILARITY: normalized descriptions are ≥ 80% similar
       (difflib ratio over lowercased, whitespace-collapsed, punctuation-stripped
       text). This catches "13 mm thick insulation" vs "13mm thick insulation".
    2. QUANTITY AGREES: either both quantities are equal (numeric compare,
       Decimal), OR both are empty/zero/RO (rate-only placeholders count as
       "empty" — they carry no countable quantity).
    3. UNIT AGREES: normalized units are equal (case-insensitive, common
       aliases collapsed: "sqm"="sq.m"="m2"="square meter"; "rmt"="rm"="m"=
       "meter"/"metre"/"mtr"; "tonne"="mt"="t"). Unit mismatch = NOT a match.
  Matching is GREEDY BEST-FIRST: each source row is paired with its
    best-scoring unmatched output row; one source row matches at most one
    output row (no double-counting).
  A row present in output but unmatched to any source row = EXTRA (over-capture).
  A row present in source but unmatched to any output row = MISSING (dropped).
  An output row with confidence < ENTITY_CONFIDENCE_THRESHOLD (0.70) or carrying
    a warning = FLAGGED. Flagged rows do NOT fail the verdict (R1: flag, never
    drop). The verdict is PASS iff 0 missing AND 0 extra; flagged rows are
    reported but do not change PASS→FAIL.
  A doc with source_row_count=0 (confirmed-zero, manual) and empty output → PASS.
    Non-empty output on a confirmed-zero doc → FAIL-extra (invented rows).

The auditor NEVER reads pipeline-derived gold — its source side comes exclusively
from source_truth.json (Rule 2). Grep this module for 'gold' → only this docstring.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from typing import Any, Literal, cast

CONFIDENCE_THRESHOLD = 0.70
DESCRIPTION_SIMILARITY_THRESHOLD = 0.80

# P3_04: the local UNIT_ALIASES table is GONE.  Fidelity is a
# row-matching module and must agree with the canonical normalizer
# (config/constants.py + src/rules/units.py) on every alias, including
# MT→mt, sqft→sqm, etc.  The duplicate table was the source of
# spurious row mismatches in earlier waves — a tender's row said
# "MT" but fidelity's table said MT→sqft, and the row was marked
# mismatched even though both sides meant the same mass.  Use the
# canonical normalizer instead.
from src.rules.units import UnitNormalizer  # noqa: E402  (P3_04 deferred import)

_FIDELITY_NORMALIZER = UnitNormalizer()


def _normalize_text(s: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation for similarity comparison."""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


def _normalize_unit(unit: str) -> str:
    """Normalize unit string to canonical form via the shared normalizer.

    P3_04: this used to use a local alias table that disagreed with
    the canonical normalizer (e.g. MT→tonne vs MT→mt, m→rmt vs
    m→unknown, etc.).  Always goes through :class:`UnitNormalizer`
    so fidelity agrees with the rest of the pipeline.
    """
    return _FIDELITY_NORMALIZER.normalize(unit).canonical


def _parse_qty(v: Any) -> Decimal | None:
    if v is None:
        return None
    if isinstance(v, Decimal):
        return v
    try:
        s = str(v).strip()
        if not s or s.lower() in {"ro", "r/o", "r.o.", "-", "nil", "n/a", "tbd"}:
            return None
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def _qty_agrees(a: Any, b: Any) -> bool:
    qa, qb = _parse_qty(a), _parse_qty(b)
    if qa is None and qb is None:
        return True
    if qa is None or qb is None:
        return False
    return qa == qb


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalize_text(a), _normalize_text(b)).ratio()


@dataclass
class SourceRow:
    item_no: Any
    description: str
    quantity: Any
    unit: str


@dataclass
class OutputRow:
    item_no: Any
    description: str
    quantity: Any
    unit: str
    confidence: float
    warnings: list[str]


@dataclass
class RowMatch:
    source: SourceRow
    output: OutputRow
    similarity: float


@dataclass
class FidelityReport:
    doc_id: str
    source_row_count: int
    captured: list[RowMatch] = field(default_factory=list)
    missing: list[SourceRow] = field(default_factory=list)
    extra: list[OutputRow] = field(default_factory=list)
    flagged: list[OutputRow] = field(default_factory=list)
    verdict: Literal["PASS", "FAIL"] = "PASS"

    @property
    def captured_count(self) -> int:
        return len(self.captured)

    @property
    def missing_count(self) -> int:
        return len(self.missing)

    @property
    def extra_count(self) -> int:
        return len(self.extra)

    @property
    def flagged_count(self) -> int:
        return len(self.flagged)


def _boq_row_to_output_row(row: Any) -> OutputRow:
    """Convert a pipeline BoqRow (or a test OutputRow) to an OutputRow."""
    if isinstance(row, OutputRow):
        return row
    return OutputRow(
        item_no=getattr(row, "item_no", None),
        description=str(
            getattr(row, "material", "") or getattr(row, "description_raw", "") or getattr(row, "description", "") or ""
        ),
        quantity=getattr(row, "quantity", None),
        unit=str(getattr(row, "unit", "") or ""),
        confidence=float(getattr(row, "confidence", 1.0)),
        warnings=list(getattr(row, "warnings", []) or []),
    )


class FidelityAuditor:
    """Audits pipeline output against independent source truth (Rule 2)."""

    def audit(self, doc_id: str, boq_output: list[Any], source_truth: dict) -> FidelityReport:
        st_entry = self._find_source_entry(doc_id, source_truth)
        source_rows = self._source_rows_from_entry(st_entry) if st_entry else []
        output_rows = [_boq_row_to_output_row(r) for r in boq_output]

        report = FidelityReport(doc_id=doc_id, source_row_count=len(source_rows))

        # Confirmed-zero doc: PASS iff output also empty
        if not source_rows:
            if output_rows:
                report.extra = output_rows
                report.flagged = [r for r in output_rows if r.confidence < CONFIDENCE_THRESHOLD or r.warnings]
                report.verdict = "FAIL"
            return report

        # Count-only mode: if source rows are synthesized placeholders (no real
        # descriptions), fall back to count-based audit (captured = min, missing/
        # extra by difference). This matches measure_fidelity.py's behavior when
        # row-level source detail isn't available.
        has_real_descriptions = any(
            sr.description and not sr.description.startswith("source-row-") for sr in source_rows
        )
        if not has_real_descriptions:
            n_src, n_out = len(source_rows), len(output_rows)
            captured = min(n_src, n_out)
            report.captured = [
                RowMatch(source=source_rows[i], output=output_rows[i], similarity=1.0) for i in range(captured)
            ]
            report.missing = source_rows[captured:] if n_src > n_out else []
            report.extra = output_rows[captured:] if n_out > n_src else []
            report.flagged = [r for r in output_rows if r.confidence < CONFIDENCE_THRESHOLD or r.warnings]
            report.verdict = "PASS" if (not report.missing and not report.extra) else "FAIL"
            return report

        # Greedy best-first matching (row-level descriptions available)
        matched_output: set[int] = set()
        candidates: list[tuple[float, int, int]] = []  # (score, source_idx, output_idx)
        for si, sr in enumerate(source_rows):
            for oi, orow in enumerate(output_rows):
                if not _qty_agrees(sr.quantity, orow.quantity):
                    continue
                if _normalize_unit(sr.unit) != _normalize_unit(orow.unit):
                    continue
                sim = _similarity(sr.description, orow.description)
                if sim >= DESCRIPTION_SIMILARITY_THRESHOLD:
                    candidates.append((sim, si, oi))

        candidates.sort(key=lambda x: (-x[0], x[1], x[2]))
        matched_source: set[int] = set()
        for score, si, oi in candidates:
            if si in matched_source or oi in matched_output:
                continue
            report.captured.append(RowMatch(source=source_rows[si], output=output_rows[oi], similarity=score))
            matched_source.add(si)
            matched_output.add(oi)

        report.missing = [sr for i, sr in enumerate(source_rows) if i not in matched_source]
        report.extra = [orow for i, orow in enumerate(output_rows) if i not in matched_output]
        report.flagged = [orow for orow in output_rows if orow.confidence < CONFIDENCE_THRESHOLD or orow.warnings]
        report.verdict = "PASS" if (not report.missing and not report.extra) else "FAIL"
        return report

    def _find_source_entry(self, doc_id: str, source_truth: dict) -> dict | None:
        for e in source_truth.get("entries", source_truth.get("docs", [])):
            if e.get("doc_id") == doc_id:
                return cast(dict, e)
        return None

    def _source_rows_from_entry(self, entry: dict) -> list[SourceRow]:
        rows = entry.get("rows", [])
        if rows:
            return [
                SourceRow(
                    item_no=r.get("item_no"),
                    description=r.get("description", r.get("material", "")),
                    quantity=r.get("quantity"),
                    unit=r.get("unit", ""),
                )
                for r in rows
            ]
        # No row-level detail in source_truth → synthesize from count (count-only audit)
        count = entry.get("source_row_count", 0)
        return [SourceRow(item_no=i, description=f"source-row-{i}", quantity=None, unit="") for i in range(count)]


def render_audit_report(report: FidelityReport) -> str:
    """Render a human-readable markdown audit report."""
    lines: list[str] = []
    lines.append(f"# Fidelity Audit — {report.doc_id}\n")
    lines.append(f"**Source rows:** {report.source_row_count}  ")
    lines.append(f"**Captured:** {report.captured_count}  ")
    lines.append(f"**Missing:** {report.missing_count}  ")
    lines.append(f"**Extra:** {report.extra_count}  ")
    lines.append(f"**Flagged:** {report.flagged_count}  ")
    lines.append(f"**Verdict:** {report.verdict}\n")

    if report.captured:
        lines.append("## Captured rows\n")
        lines.append("| # | source description | output description | similarity |")
        lines.append("|---|-------------------|-------------------|------------|")
        for i, m in enumerate(report.captured, 1):
            lines.append(f"| {i} | {m.source.description[:80]} | {m.output.description[:80]} | {m.similarity:.2f} |")
        lines.append("")

    if report.missing:
        lines.append("## MISSING rows (dropped — R1 violation)\n")
        lines.append("| # | source description | qty | unit |")
        lines.append("|---|-------------------|-----|------|")
        for i, sr in enumerate(report.missing, 1):
            lines.append(f"| {i} | {sr.description[:80]} | {sr.quantity} | {sr.unit} |")
        lines.append("")

    if report.extra:
        lines.append("## EXTRA rows (over-capture)\n")
        lines.append("| # | output description | qty | unit | conf |")
        lines.append("|---|-------------------|-----|------|------|")
        for i, orow in enumerate(report.extra, 1):
            lines.append(f"| {i} | {orow.description[:80]} | {orow.quantity} | {orow.unit} | {orow.confidence:.2f} |")
        lines.append("")

    if report.flagged:
        lines.append("## FLAGGED rows (low confidence/warnings — NOT a failure)\n")
        lines.append("| # | output description | conf | warnings |")
        lines.append("|---|-------------------|------|----------|")
        for i, orow in enumerate(report.flagged, 1):
            lines.append(f"| {i} | {orow.description[:80]} | {orow.confidence:.2f} | {'; '.join(orow.warnings)} |")
        lines.append("")

    return "\n".join(lines)
