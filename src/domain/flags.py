"""Typed flag system (P3_04) — flag, never drop; flag, never guess.

R1's bar — "100% of the data in the document, converted, nothing
lost" — is implemented as three guarantees, of which this module is
the third:

    1. Captured rows (fidelity audit artifact per doc)
    2. Normalized units (src/rules/units.py)
    3. Typed flags for every uncertainty (this module)

Every place the pipeline used to silently drop a row, return None,
swallow an exception, or guess at a unit/material/standard now
emits a typed :class:`Flag` instead.  The flag carries:

- a stable ``code`` (closed enum, mirrored in config/constants.py
  via an orchestrator-applied patch — the Flag module is designed
  to work whether the FlagCode enum has been added to constants
  or not; if absent, flag codes are accepted as plain strings).
- a ``severity`` (info / review / error)
- the ``stage`` that produced it (extraction / normalization / …)
- a human-readable ``message``
- an optional ``row_ref`` (row item_no or row index)
- an optional ``original`` (the raw text that triggered the flag)

The flag system is consumed by the JSON exporter and (in P5_01) the
Excel exporter.  Nothing flags silently.  Nothing drops silently.

Backward-compat: the existing ``BoqRow.warnings`` list (list[str])
and ``ExtractionResult.metadata.warnings`` (list[str]) are KEPT and
now populated from the same source.  Each emitted ``Flag`` is also
stringified into ``BoqRow.warnings`` so callers that only know
about strings still see them.  New code should attach ``Flag``
objects directly so the typed fields survive into JSON.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

# P3_04: ``FlagCode`` is a closed enum of stable flag codes.
# It lives in config/constants.py (which is FROZEN per the spec),
# so the orchestrator must apply the addition patch + re-pin the
# file's hash.  This module is importable regardless — we lazily
# import FlagCode and fall back to ``str`` if it's not present,
# so dev work doesn't break before the patch is applied.
try:
    from config.constants import FlagCode

    _HAS_FLAGCODE_ENUM = True
except ImportError:
    FlagCode = str  # type: ignore[misc,assignment]
    _HAS_FLAGCODE_ENUM = False


def _flag_code(code: str) -> FlagCode:
    """Return a FlagCode enum member if the enum is available, else the raw string.

    This helper keeps the flags module importable even when the FlagCode enum
    has not yet been patched into config/constants.py, while satisfying mypy
    once the enum is present.
    """
    if _HAS_FLAGCODE_ENUM and isinstance(FlagCode, type) and issubclass(FlagCode, StrEnum):
        return FlagCode(code)
    return code  # type: ignore[return-value]


class FlagSeverity(StrEnum):
    """How serious is this flag?

    - INFO     — observation, not blocking.  Example: a row used a
      "non-preferred" alias that was resolved correctly.
    - REVIEW   — the row was captured but a human should sanity-check
      it.  Example: confidence < 0.7, GeM non-catalog material,
      table-type not BOQ.
    - ERROR    — capture failed or is suspect.  Example: pipeline
      exception, missing source row.
    """

    INFO = "info"
    REVIEW = "review"
    ERROR = "error"


# Stage names — where the flag was produced.  Keeps the JSON shape
# greppable and lets audits group flags by stage.
class FlagStage(StrEnum):
    INGEST = "ingest"
    TABLE_CLASSIFY = "table_classify"
    EXTRACTION = "extraction"
    NORMALIZATION = "normalization"
    ASSEMBLY = "assembly"
    VALIDATION = "validation"
    EXPORT = "export"
    CATALOG = "catalog"
    STRUCTURE = "structure"


@dataclass(frozen=True)
class Flag:
    """A typed uncertainty / concern surfaced by the pipeline (P3_04).

    Every extraction-time decision that used to be silent (a None
    return, a swallowed except, a guessed unit, a dropped row) is
    now represented as a :class:`Flag`.  Flags are attached to
    either a :class:`BoqRow` (row-level) or the
    :class:`ExtractionResult` (document-level) and flow through the
    JSON exporter as ``row.flags`` and ``metadata.flags`` arrays.
    """

    code: FlagCode
    severity: FlagSeverity
    stage: FlagStage
    message: str
    row_ref: str | None = None
    original: str | None = None
    flag_id: str = field(default_factory=lambda: uuid4().hex[:12])
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.message:
            raise ValueError("Flag.message must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "flag_id": self.flag_id,
            "code": self.code.value if hasattr(self.code, "value") else str(self.code),
            "severity": self.severity.value,
            "stage": self.stage.value,
            "message": self.message,
            "row_ref": self.row_ref,
            "original": self.original,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Flag:
        import contextlib

        code = d["code"]
        if _HAS_FLAGCODE_ENUM and isinstance(code, str):
            # Unknown code (e.g. from a future build) — keep the
            # raw string so the JSON round-trip doesn't lose info.
            with contextlib.suppress(ValueError):
                code = FlagCode(code)
        severity = d["severity"]
        if isinstance(severity, str):
            with contextlib.suppress(ValueError):
                severity = FlagSeverity(severity)
        stage = d["stage"]
        if isinstance(stage, str):
            with contextlib.suppress(ValueError):
                stage = FlagStage(stage)
        return cls(
            code=code,
            severity=severity,
            stage=stage,
            message=d["message"],
            row_ref=d.get("row_ref"),
            original=d.get("original"),
            flag_id=d.get("flag_id") or uuid4().hex[:12],
            created_at=datetime.fromisoformat(d["created_at"]) if d.get("created_at") else datetime.now(UTC),
        )

    def to_legacy_warning(self) -> str:
        """Return the flag in the legacy ``warnings: list[str]`` form.

        Used to populate the existing ``BoqRow.warnings`` and
        ``ExtractionResult.metadata.warnings`` lists so callers
        that only know about strings keep working.
        """
        prefix = self.code.value if hasattr(self.code, "value") else str(self.code)
        parts = [prefix]
        if self.row_ref:
            parts.append(f"row={self.row_ref}")
        if self.message and self.message != prefix:
            parts.append(self.message)
        return ": ".join(parts) if len(parts) > 1 else parts[0]


# ---------------------------------------------------------------------------
# Container: FlagStore — accumulates flags and serializes for export
# ---------------------------------------------------------------------------


@dataclass
class FlagStore:
    """A simple append-only container of :class:`Flag` instances.

    Producers call :meth:`add` or :meth:`add_many` as they encounter
    uncertainties.  Consumers (JSON exporter, audits) iterate via
    :meth:`flags` or :meth:`to_dicts`.

    The store does NOT deduplicate — every producer gets a new
    :class:`Flag` and a unique :attr:`Flag.flag_id`.  This is
    intentional: dedup of flags is the consumer's responsibility
    (e.g. for row-level flags, group by row_ref and code).
    """

    _flags: list[Flag] = field(default_factory=list)

    def add(self, flag: Flag) -> Flag:
        self._flags.append(flag)
        return flag

    def add_many(self, flags: Iterable[Flag]) -> list[Flag]:
        out = list(flags)
        self._flags.extend(out)
        return out

    def flags(self) -> list[Flag]:
        return list(self._flags)

    def by_code(self, code: FlagCode) -> list[Flag]:
        return [f for f in self._flags if f.code == code]

    def by_stage(self, stage: FlagStage) -> list[Flag]:
        return [f for f in self._flags if f.stage == stage]

    def by_severity(self, severity: FlagSeverity) -> list[Flag]:
        return [f for f in self._flags if f.severity == severity]

    def by_row(self, row_ref: str) -> list[Flag]:
        return [f for f in self._flags if f.row_ref == row_ref]

    def legacy_warnings(self) -> list[str]:
        """Return a list of legacy string-form warnings for
        :class:`ExtractionResult.metadata.warnings` compat."""
        return [f.to_legacy_warning() for f in self._flags]

    def to_dicts(self) -> list[dict[str, Any]]:
        return [f.to_dict() for f in self._flags]

    def __iter__(self) -> Iterator[Flag]:
        return iter(self._flags)

    def __len__(self) -> int:
        return len(self._flags)


# ---------------------------------------------------------------------------
# Convenience factories for the most common flag shapes
# ---------------------------------------------------------------------------


def low_confidence_flag(row_ref: str | int, confidence: float, stage: FlagStage = FlagStage.ASSEMBLY) -> Flag:
    """A low-confidence row (R1 review trigger)."""
    return Flag(
        code=_flag_code("LOW_CONFIDENCE"),
        severity=FlagSeverity.REVIEW,
        stage=stage,
        message=f"row confidence {confidence:.2f} below 0.7 threshold",
        row_ref=str(row_ref),
    )


def unknown_unit_flag(raw_unit: str, row_ref: str | int, stage: FlagStage = FlagStage.NORMALIZATION) -> Flag:
    """Unit string that didn't match any alias / canonical."""
    return Flag(
        code=_flag_code("UNKNOWN_UNIT"),
        severity=FlagSeverity.REVIEW,
        stage=stage,
        message=f"unit '{raw_unit}' not in alias table — flagged for review",
        row_ref=str(row_ref),
        original=raw_unit,
    )


def ambiguous_unit_flag(raw_unit: str, row_ref: str | int, stage: FlagStage = FlagStage.NORMALIZATION) -> Flag:
    """Bare single-character unit (e.g. M, T, L) — too ambiguous to guess (P3_04 §9)."""
    return Flag(
        code=_flag_code("AMBIGUOUS_UNIT"),
        severity=FlagSeverity.REVIEW,
        stage=stage,
        message=f"unit '{raw_unit}' is a bare single character (ambiguous meter-vs-thousand or similar) — flagged for review",
        row_ref=str(row_ref),
        original=raw_unit,
    )


def structure_fallback_flag() -> Flag:
    """No BOQ section found — fallback to text-line path (P3_01)."""
    return Flag(
        code=_flag_code("STRUCTURE_FALLBACK"),
        severity=FlagSeverity.REVIEW,
        stage=FlagStage.STRUCTURE,
        message="no BOQ section found via structure-first scan; fell back to text-line path",
    )


def column_fallback_flag() -> Flag:
    """Multi-column detection failed; fell back to text-line assembly (P3_02)."""
    return Flag(
        code=_flag_code("COLUMN_FALLBACK"),
        severity=FlagSeverity.REVIEW,
        stage=FlagStage.INGEST,
        message="multi-column detection failed; fell back to text-line assembly",
    )


def table_type_flag(table_type: str) -> Flag:
    """Table type is not BOQ (P3_03) — flagged at document level, 0 rows emitted."""
    return Flag(
        code=_flag_code("TABLE_TYPE_NOT_BOQ"),
        severity=FlagSeverity.INFO,
        stage=FlagStage.TABLE_CLASSIFY,
        message=f"classified table is '{table_type}', not BOQ — 0 rows emitted; document not skippable",
    )


def gem_non_catalog_flag(material: str) -> Flag:
    """Material not in GeM catalog (R2)."""
    return Flag(
        code=_flag_code("GEM_NON_CATALOG"),
        severity=FlagSeverity.REVIEW,
        stage=FlagStage.CATALOG,
        message=f"material '{material}' is not in the GeM catalog — flagged for review",
        original=material,
    )


def pipeline_error_flag(exc: Exception) -> Flag:
    """Pipeline exception during extraction."""
    return Flag(
        code=_flag_code("PIPELINE_ERROR"),
        severity=FlagSeverity.ERROR,
        stage=FlagStage.EXTRACTION,
        message=f"{type(exc).__name__}: {exc}",
    )


def no_boq_section_flag() -> Flag:
    """No BOQ section / page-range found in the document."""
    return Flag(
        code=_flag_code("NO_BOQ_SECTION_FOUND"),
        severity=FlagSeverity.REVIEW,
        stage=FlagStage.STRUCTURE,
        message="no BOQ section or page range was found in this document",
    )


def quantity_missing_flag(row_ref: str | int) -> Flag:
    """Row has a material but no quantity — review needed."""
    return Flag(
        code=_flag_code("QUANTITY_MISSING"),
        severity=FlagSeverity.REVIEW,
        stage=FlagStage.ASSEMBLY,
        message="row has a material but no quantity — review needed",
        row_ref=str(row_ref),
    )
