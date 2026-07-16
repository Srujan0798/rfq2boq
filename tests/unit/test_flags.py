"""Tests for the typed flag system (P3_04).

Covers Flag dataclass, FlagStore, severity / stage / code attachment,
JSON round-trip, legacy-warning compat, and the convenience factories
used by pipeline producers.
"""

from __future__ import annotations

import json

import pytest
from src.domain.flags import (
    Flag,
    FlagSeverity,
    FlagStage,
    FlagStore,
    ambiguous_unit_flag,
    gem_non_catalog_flag,
    low_confidence_flag,
    no_boq_section_flag,
    pipeline_error_flag,
    quantity_missing_flag,
    structure_fallback_flag,
    table_type_flag,
    unknown_unit_flag,
)
from src.domain.models import BoqRow, ExtractionMetadata, ExtractionResult


class TestFlagBasics:
    """Flag dataclass: required fields, post-init validation, to_dict."""

    def test_required_fields(self) -> None:
        f = Flag(code="LOW_CONFIDENCE", severity=FlagSeverity.REVIEW, stage=FlagStage.ASSEMBLY, message="x")
        assert f.code == "LOW_CONFIDENCE"
        assert f.severity == FlagSeverity.REVIEW
        assert f.stage == FlagStage.ASSEMBLY
        assert f.message == "x"
        # Auto-generated
        assert len(f.flag_id) == 12
        assert f.row_ref is None
        assert f.original is None

    def test_empty_message_rejected(self) -> None:
        with pytest.raises(ValueError, match="message must be non-empty"):
            Flag(code="X", severity=FlagSeverity.REVIEW, stage=FlagStage.ASSEMBLY, message="")

    def test_to_dict_shape(self) -> None:
        f = Flag(
            code="UNKNOWN_UNIT",
            severity=FlagSeverity.REVIEW,
            stage=FlagStage.NORMALIZATION,
            message="not in alias table",
            row_ref="1",
            original="xyz",
        )
        d = f.to_dict()
        assert d["code"] == "UNKNOWN_UNIT"
        assert d["severity"] == "review"
        assert d["stage"] == "normalization"
        assert d["message"] == "not in alias table"
        assert d["row_ref"] == "1"
        assert d["original"] == "xyz"
        assert "flag_id" in d
        assert "created_at" in d

    def test_to_legacy_warning(self) -> None:
        f = Flag(
            code="LOW_CONFIDENCE",
            severity=FlagSeverity.REVIEW,
            stage=FlagStage.ASSEMBLY,
            message="below 0.7",
            row_ref="1",
        )
        w = f.to_legacy_warning()
        assert w == "LOW_CONFIDENCE: row=1: below 0.7"

    def test_to_legacy_warning_no_row(self) -> None:
        f = Flag(
            code="STRUCTURE_FALLBACK",
            severity=FlagSeverity.REVIEW,
            stage=FlagStage.STRUCTURE,
            message="fell back to text-line",
        )
        w = f.to_legacy_warning()
        assert w == "STRUCTURE_FALLBACK: fell back to text-line"


class TestFlagRoundTrip:
    """Flag <-> dict round-trip preserves all fields."""

    def test_round_trip(self) -> None:
        original = Flag(
            code="GEM_NON_CATALOG",
            severity=FlagSeverity.REVIEW,
            stage=FlagStage.CATALOG,
            message="material 'foo' not in catalog",
            row_ref="5",
            original="foo",
        )
        d = original.to_dict()
        # to_dict produces JSON-serializable values; round-trip via
        # from_dict should preserve identity.
        json.dumps(d)  # JSON-encodable
        restored = Flag.from_dict(d)
        assert restored.code == original.code
        assert restored.severity == original.severity
        assert restored.stage == original.stage
        assert restored.message == original.message
        assert restored.row_ref == original.row_ref
        assert restored.original == original.original
        assert restored.flag_id == original.flag_id


class TestFlagStore:
    """FlagStore: append, query by code/stage/severity/row, legacy export."""

    def _seed(self) -> tuple[FlagStore, list[Flag]]:
        store = FlagStore()
        f1 = Flag(
            code="LOW_CONFIDENCE", severity=FlagSeverity.REVIEW, stage=FlagStage.ASSEMBLY, message="x", row_ref="1"
        )
        f2 = Flag(
            code="UNKNOWN_UNIT", severity=FlagSeverity.REVIEW, stage=FlagStage.NORMALIZATION, message="y", row_ref="2"
        )
        f3 = Flag(
            code="GEM_NON_CATALOG", severity=FlagSeverity.REVIEW, stage=FlagStage.CATALOG, message="z", original="foo"
        )
        f4 = Flag(
            code="LOW_CONFIDENCE", severity=FlagSeverity.REVIEW, stage=FlagStage.ASSEMBLY, message="w", row_ref="1"
        )
        store.add_many([f1, f2, f3, f4])
        return store, [f1, f2, f3, f4]

    def test_len(self) -> None:
        store, _ = self._seed()
        assert len(store) == 4

    def test_flags_iter(self) -> None:
        store, flags = self._seed()
        assert list(store) == flags

    def test_by_code(self) -> None:
        store, _ = self._seed()
        assert len(store.by_code("LOW_CONFIDENCE")) == 2
        assert len(store.by_code("UNKNOWN_UNIT")) == 1

    def test_by_stage(self) -> None:
        store, _ = self._seed()
        assert len(store.by_stage(FlagStage.ASSEMBLY)) == 2
        assert len(store.by_stage(FlagStage.NORMALIZATION)) == 1
        assert len(store.by_stage(FlagStage.CATALOG)) == 1

    def test_by_severity(self) -> None:
        store, _ = self._seed()
        assert len(store.by_severity(FlagSeverity.REVIEW)) == 4
        assert len(store.by_severity(FlagSeverity.ERROR)) == 0

    def test_by_row(self) -> None:
        store, _ = self._seed()
        assert len(store.by_row("1")) == 2
        assert len(store.by_row("2")) == 1
        assert len(store.by_row("99")) == 0

    def test_legacy_warnings(self) -> None:
        store, _ = self._seed()
        warnings = store.legacy_warnings()
        assert len(warnings) == 4
        assert all(":" in w for w in warnings)

    def test_to_dicts(self) -> None:
        store, flags = self._seed()
        dicts = store.to_dicts()
        assert len(dicts) == 4
        assert all(isinstance(d, dict) for d in dicts)
        assert all("flag_id" in d for d in dicts)


class TestFlagAttachment:
    """Flag attachment: BoqRow.flags and ExtractionMetadata.flags survive JSON."""

    def test_boqrow_flag_survives_dump(self) -> None:
        f = Flag(
            code="LOW_CONFIDENCE", severity=FlagSeverity.REVIEW, stage=FlagStage.ASSEMBLY, message="x", row_ref="1"
        )
        r = BoqRow(material="cement", quantity=1, unit="kg", flags=[f], warnings=[f.to_legacy_warning()])
        j = json.loads(r.model_dump_json())
        assert len(j["flags"]) == 1
        assert j["flags"][0]["code"] == "LOW_CONFIDENCE"
        assert j["flags"][0]["row_ref"] == "1"
        assert j["warnings"] == ["LOW_CONFIDENCE: row=1: x"]

    def test_metadata_flag_survives_dump(self) -> None:
        f = Flag(
            code="STRUCTURE_FALLBACK",
            severity=FlagSeverity.REVIEW,
            stage=FlagStage.STRUCTURE,
            message="fell back",
        )
        m = ExtractionMetadata(flags=[f], warnings=[f.to_legacy_warning()])
        j = json.loads(m.model_dump_json())
        assert len(j["flags"]) == 1
        assert j["flags"][0]["code"] == "STRUCTURE_FALLBACK"
        assert j["warnings"] == ["STRUCTURE_FALLBACK: fell back"]

    def test_extractionresult_with_flags(self) -> None:
        f_doc = Flag(
            code="NO_BOQ_SECTION_FOUND",
            severity=FlagSeverity.REVIEW,
            stage=FlagStage.STRUCTURE,
            message="no BOQ found",
        )
        f_row = Flag(
            code="LOW_CONFIDENCE", severity=FlagSeverity.REVIEW, stage=FlagStage.ASSEMBLY, message="x", row_ref="1"
        )
        r = BoqRow(material="x", quantity=1, unit="kg", flags=[f_row])
        result = ExtractionResult(
            doc_id="test_doc",
            boq_items=[r],
            metadata=ExtractionMetadata(flags=[f_doc], warnings=[f_doc.to_legacy_warning()]),
        )
        j = json.loads(result.model_dump_json())
        # Document-level flag in metadata
        assert j["metadata"]["flags"][0]["code"] == "NO_BOQ_SECTION_FOUND"
        # Row-level flag in boq_items
        assert j["boq_items"][0]["flags"][0]["code"] == "LOW_CONFIDENCE"


class TestConvenienceFactories:
    """Convenience factory functions for the common flag shapes."""

    def test_low_confidence(self) -> None:
        f = low_confidence_flag(1, 0.5)
        assert f.code == "LOW_CONFIDENCE"
        assert f.severity == FlagSeverity.REVIEW
        assert f.row_ref == "1"
        assert "0.50" in f.message

    def test_unknown_unit(self) -> None:
        f = unknown_unit_flag("xyz", 1)
        assert f.code == "UNKNOWN_UNIT"
        assert f.original == "xyz"
        assert f.row_ref == "1"

    def test_ambiguous_unit(self) -> None:
        f = ambiguous_unit_flag("M", 1)
        assert f.code == "AMBIGUOUS_UNIT"
        assert f.original == "M"
        assert f.row_ref == "1"

    def test_structure_fallback(self) -> None:
        f = structure_fallback_flag()
        assert f.code == "STRUCTURE_FALLBACK"
        assert f.severity == FlagSeverity.REVIEW
        assert f.stage == FlagStage.STRUCTURE
        assert f.row_ref is None  # doc-level

    def test_table_type(self) -> None:
        f = table_type_flag("COMPLIANCE_CHECKLIST")
        assert f.code == "TABLE_TYPE_NOT_BOQ"
        assert f.severity == FlagSeverity.INFO
        assert f.stage == FlagStage.TABLE_CLASSIFY
        assert "COMPLIANCE_CHECKLIST" in f.message

    def test_gem_non_catalog(self) -> None:
        f = gem_non_catalog_flag("fancy pipe")
        assert f.code == "GEM_NON_CATALOG"
        assert f.original == "fancy pipe"

    def test_pipeline_error(self) -> None:
        f = pipeline_error_flag(ValueError("boom"))
        assert f.code == "PIPELINE_ERROR"
        assert f.severity == FlagSeverity.ERROR
        assert "ValueError" in f.message
        assert "boom" in f.message

    def test_no_boq_section(self) -> None:
        f = no_boq_section_flag()
        assert f.code == "NO_BOQ_SECTION_FOUND"
        assert f.severity == FlagSeverity.REVIEW

    def test_quantity_missing(self) -> None:
        f = quantity_missing_flag(1)
        assert f.code == "QUANTITY_MISSING"
        assert f.severity == FlagSeverity.REVIEW
        assert f.row_ref == "1"


class TestFlagSeverityEnum:
    """FlagSeverity is a StrEnum with the three expected members."""

    def test_members(self) -> None:
        assert {s.value for s in FlagSeverity} == {"info", "review", "error"}

    def test_string_comparable(self) -> None:
        # StrEnum members equal their string values.
        assert FlagSeverity.REVIEW == "review"
        assert FlagSeverity.INFO == "info"
        assert FlagSeverity.ERROR == "error"


class TestFlagStageEnum:
    """FlagStage is a StrEnum with the expected stages."""

    def test_members(self) -> None:
        members = {s.value for s in FlagStage}
        # Required: ingest, table_classify, extraction, normalization,
        # assembly, validation, export, catalog, structure.
        assert "ingest" in members
        assert "table_classify" in members
        assert "extraction" in members
        assert "normalization" in members
        assert "assembly" in members
        assert "validation" in members
        assert "export" in members
        assert "catalog" in members
        assert "structure" in members
