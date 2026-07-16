"""Tests for output generators."""

from datetime import UTC, datetime
from decimal import Decimal

from src.domain.models import BoqRow, ExtractionMetadata, ExtractionResult
from src.export.csv_exporter import CSVExporter
from src.export.excel_generator import ExcelGenerator
from src.export.json_formatter import JSONFormatter
from src.export.report import ReportGenerator


class TestJSONFormatter:
    def test_format_empty_result(self):
        formatter = JSONFormatter()
        result = ExtractionResult(
            doc_id="test-123",
            project_name="Test Project",
            extraction_date=datetime.now(UTC),
            source_file="test.pdf",
            entities=[],
            boq_items=[],
            metadata=ExtractionMetadata(
                total_items=0,
                avg_confidence=0.0,
                processing_time_sec=0.0,
                pages_processed=0,
            ),
        )
        json_str = formatter.format(result)
        assert "test-123" in json_str
        assert "Test Project" in json_str

    def test_format_with_items(self):
        formatter = JSONFormatter()
        result = ExtractionResult(
            doc_id="test-456",
            project_name="Construction Project",
            extraction_date=datetime.now(UTC),
            source_file="rfq.pdf",
            entities=[],
            boq_items=[
                BoqRow(
                    item_no=1,
                    material="cement",
                    quantity=Decimal("100"),
                    unit="bags",
                    confidence=0.9,
                )
            ],
            metadata=ExtractionMetadata(
                total_items=1,
                avg_confidence=0.9,
                processing_time_sec=1.5,
                pages_processed=5,
            ),
        )
        json_str = formatter.format(result)
        assert "cement" in json_str
        assert "100" in json_str


class TestReportGenerator:
    def test_generate_empty(self):
        generator = ReportGenerator()
        result = ExtractionResult(
            doc_id="test-789",
            project_name="Empty Test",
            extraction_date=datetime.now(UTC),
            source_file="empty.pdf",
            entities=[],
            boq_items=[],
            metadata=ExtractionMetadata(
                total_items=0,
                avg_confidence=0.0,
                processing_time_sec=0.0,
                pages_processed=0,
            ),
        )
        report = generator.generate(result)
        assert "Empty Test" in report
        assert "Total Items" in report

    def test_generate_with_low_confidence_items(self):
        generator = ReportGenerator()
        result = ExtractionResult(
            doc_id="low-conf-123",
            project_name="Low Confidence Test",
            extraction_date=datetime.now(UTC),
            source_file="rfq.pdf",
            entities=[],
            boq_items=[
                BoqRow(
                    item_no=1,
                    material="cement",
                    quantity=Decimal("100"),
                    unit="bags",
                    confidence=0.5,
                ),
                BoqRow(
                    item_no=2,
                    material="steel",
                    quantity=Decimal("200"),
                    unit="kg",
                    confidence=0.95,
                ),
            ],
            metadata=ExtractionMetadata(
                total_items=2,
                avg_confidence=0.725,
                processing_time_sec=2.0,
                pages_processed=10,
            ),
        )
        report = generator.generate(result)
        assert "Low Confidence Test" in report
        assert "Total Items: 2" in report


class TestStructuredExporters:
    def test_excel_and_csv_export(self, tmp_path):
        result = ExtractionResult(
            doc_id="export-123",
            project_name="Export Test",
            extraction_date=datetime.now(UTC),
            source_file="rfq.pdf",
            boq_items=[
                BoqRow(
                    item_no=1,
                    material="concrete",
                    grade="M20",
                    quantity=Decimal("150"),
                    unit="cum",
                    confidence=0.9,
                    dimensions=["150mm thick"],
                    standard=["IS 456"],
                    location="ground floor",
                )
            ],
            metadata=ExtractionMetadata(total_items=1, avg_confidence=0.9),
        )

        excel_path = tmp_path / "boq.xlsx"
        csv_path = tmp_path / "boq.csv"

        ExcelGenerator().generate(result, str(excel_path))
        CSVExporter().export(result, str(csv_path))

        assert excel_path.exists()
        assert "concrete" in csv_path.read_text(encoding="utf-8")
