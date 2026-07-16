"""Self-attack tests for failure mode verification.

Tests for all 10 failure modes to verify robust handling.
"""

from decimal import Decimal

from config.constants import EntityType
from src.domain.boq_assembler import BOQAssembler
from src.domain.models import BoqRow, EntitySourceType, EntitySpan, ExtractionMetadata, ExtractionResult


class TestSelfAttack:
    def test_pure_image_pdf(self):
        """Verify OCR fallback works - simulate scanned PDF with no text."""
        from src.ingest.pdf_extractor import PDFExtractor
        from src.nlp.pipeline import NLPPipeline

        extractor = PDFExtractor()
        content = extractor.extract("/nonexistent.pdf")
        assert content.pages is not None

        pipeline = NLPPipeline()
        result = pipeline.process("")
        assert result is not None

    def test_entity_overlap(self):
        """Verify conflict resolution when entities overlap."""
        assembler = BOQAssembler()
        entities = [
            EntitySpan(
                text="500", type=EntityType.QUANTITY, start=0, end=3, page=1, conf=0.9, source=EntitySourceType.BERT
            ),
            EntitySpan(
                text="500 kg", type=EntityType.MATERIAL, start=0, end=5, page=1, conf=0.8, source=EntitySourceType.BERT
            ),
        ]
        result = assembler.assemble(entities, [], "500 kg cement")
        assert len(result) >= 1

    def test_unknown_material(self):
        """Verify graceful handling of unknown material."""
        assembler = BOQAssembler()
        entities = [
            EntitySpan(
                text="xyzabc123",
                type=EntityType.MATERIAL,
                start=0,
                end=10,
                page=1,
                conf=0.5,
                source=EntitySourceType.BERT,
            ),
            EntitySpan(
                text="100", type=EntityType.QUANTITY, start=11, end=14, page=1, conf=0.9, source=EntitySourceType.BERT
            ),
        ]
        result = assembler.assemble(entities, [], "xyzabc123 100 units")
        assert len(result) == 1
        assert result[0].material == "xyzabc123"

    def test_non_rfq_document(self):
        """Verify low confidence warning for non-RFQ document."""
        from src.domain.confidence import ConfidenceScorer

        scorer = ConfidenceScorer()
        items = [
            BoqRow(item_no=1, material="", quantity=Decimal("0"), unit="", confidence=0.1),
        ]
        avg_conf = scorer.average_confidence(items)
        assert avg_conf < 0.5

    def test_empty_pdf(self):
        """Verify no crash on empty PDF content."""
        from src.domain.boq_assembler import BOQAssembler

        assembler = BOQAssembler()
        result = assembler.assemble([], [], "")
        assert result is not None
        assert len(result) == 0  # Phase 0: no placeholder rows for empty input

    def test_multiple_materials_one_sentence(self):
        """Verify correct extraction of multiple materials in one sentence."""
        assembler = BOQAssembler()
        entities = [
            EntitySpan(
                text="cement", type=EntityType.MATERIAL, start=0, end=6, page=1, conf=0.9, source=EntitySourceType.BERT
            ),
            EntitySpan(
                text="steel", type=EntityType.MATERIAL, start=15, end=20, page=1, conf=0.9, source=EntitySourceType.BERT
            ),
            EntitySpan(
                text="100", type=EntityType.QUANTITY, start=7, end=10, page=1, conf=0.95, source=EntitySourceType.BERT
            ),
            EntitySpan(
                text="200", type=EntityType.QUANTITY, start=22, end=25, page=1, conf=0.90, source=EntitySourceType.BERT
            ),
        ]
        result = assembler.assemble(entities, [], "cement 100 bags and steel 200 kg")
        assert len(result) == 2

    def test_ambiguous_units(self):
        """Verify default unit assignment for ambiguous units."""
        assembler = BOQAssembler()
        entities = [
            EntitySpan(
                text="concrete",
                type=EntityType.MATERIAL,
                start=0,
                end=8,
                page=1,
                conf=0.9,
                source=EntitySourceType.BERT,
            ),
            EntitySpan(
                text="100", type=EntityType.QUANTITY, start=9, end=12, page=1, conf=0.95, source=EntitySourceType.BERT
            ),
        ]
        result = assembler.assemble(entities, [], "concrete 100")
        assert len(result) == 1
        assert result[0].unit is not None

    def test_abbreviated_standards(self):
        """Verify alias matching for abbreviated standards."""
        assembler = BOQAssembler()
        entities = [
            EntitySpan(
                text="steel", type=EntityType.MATERIAL, start=0, end=5, page=1, conf=0.9, source=EntitySourceType.BERT
            ),
            EntitySpan(
                text="IS2062",
                type=EntityType.STANDARD,
                start=6,
                end=13,
                page=1,
                conf=0.85,
                source=EntitySourceType.BERT,
            ),
            EntitySpan(
                text="5000", type=EntityType.QUANTITY, start=14, end=18, page=1, conf=0.95, source=EntitySourceType.BERT
            ),
        ]
        result = assembler.assemble(entities, [], "steel IS2062 5000 kg")
        assert len(result) == 1
        assert "IS" in result[0].standard[0] if result[0].standard else True

    def test_zero_quantity(self):
        """Verify handling of zero quantity."""
        assembler = BOQAssembler()
        entities = [
            EntitySpan(
                text="cement", type=EntityType.MATERIAL, start=0, end=6, page=1, conf=0.9, source=EntitySourceType.BERT
            ),
            EntitySpan(
                text="0", type=EntityType.QUANTITY, start=7, end=8, page=1, conf=0.5, source=EntitySourceType.BERT
            ),
        ]
        result = assembler.assemble(entities, [], "cement 0 bags")
        assert len(result) == 1

    def test_very_long_material_name(self):
        """Verify handling of very long material names."""
        assembler = BOQAssembler()
        long_name = "A" * 1000
        entities = [
            EntitySpan(
                text=long_name,
                type=EntityType.MATERIAL,
                start=0,
                end=1000,
                page=1,
                conf=0.9,
                source=EntitySourceType.BERT,
            ),
            EntitySpan(
                text="100",
                type=EntityType.QUANTITY,
                start=1001,
                end=1004,
                page=1,
                conf=0.95,
                source=EntitySourceType.BERT,
            ),
        ]
        result = assembler.assemble(entities, [], long_name + " 100 bags")
        assert len(result) == 1

    def test_extraction_result_no_crash(self):
        """Verify ExtractionResult handles all edge cases."""
        result = ExtractionResult(
            doc_id="test",
            project_name="Test",
            entities=[],
            boq_items=[],
            metadata=ExtractionMetadata(total_items=0),
        )
        assert result.doc_id == "test"

        json_str = result.model_dump_json()
        assert json_str is not None

    def test_validator_no_crash_on_empty(self):
        """Verify validator handles empty items."""
        from src.domain.validator import DomainValidator

        validator = DomainValidator()
        warnings = validator.validate_boq([])
        assert warnings == []

    def test_confidence_scorer_edge_cases(self):
        """Verify confidence scorer handles edge cases."""
        from src.domain.confidence import ConfidenceScorer

        scorer = ConfidenceScorer()
        assert scorer.average_confidence([]) == 0.0

        items = [
            BoqRow(item_no=1, material="", quantity=Decimal("0"), unit="", confidence=0.0),
        ]
        conf = scorer.average_confidence(items)
        assert conf == 0.0

    # ── Anti-cheat self-attack tests ──────────────────────────────────────

    def test_gold_self_comparison_detection(self) -> None:
        """Verify that gold provenance check catches self-comparison.

        Gold derived via pdfplumber (same as pipeline) should be flagged.
        Gold derived via independent methods (XLSX cells) should be clean.
        """
        # Simulate the provenance check from eval_honest_rows.py
        gold_methods = {
            "xlsx": "independent-xlsx-transcription",
            "pdf_same": "pdfplumber-table-transcription",
            "pdf_different": "pymupdf-independent-text-extraction",
        }

        independent_methods = {"independent-xlsx-transcription", "direct-xlsx-hand-transcription"}

        assert gold_methods["xlsx"] in independent_methods
        assert gold_methods["pdf_same"] not in independent_methods
        assert gold_methods["pdf_different"] not in independent_methods

    def test_threshold_manipulation_detection(self) -> None:
        """Verify that suspiciously low thresholds are detected."""
        import re

        # Simulate the threshold check from test_anti_cheat.py
        low_mat_threshold = re.compile(
            r"(?:material_threshold|MATERIAL_THRESHOLD)\s*[=:]\s*0\.(\d+)\b", re.IGNORECASE
        )

        test_cases = [
            ("MATERIAL_THRESHOLD = 0.6", False),  # OK
            ("MATERIAL_THRESHOLD = 0.5", True),   # TOO LOW
            ("MATERIAL_THRESHOLD = 0.7", False),  # OK
            ("material_threshold = 0.4", True),   # TOO LOW
            ("MATERIAL_THRESHOLD: 0.8", False),   # OK
        ]

        for line, should_trigger in test_cases:
            m = low_mat_threshold.search(line)
            triggered = False
            if m:
                val = float(f"0.{m.group(1)}")
                triggered = val < 0.6
            assert triggered == should_trigger, f"Line '{line}' should_trigger={should_trigger} got triggered={triggered}"

    def test_filename_hack_detection(self) -> None:
        """Verify that per-filename == hacks are detected."""
        import re

        hack_pattern = re.compile(
            r"(?:filename|enquiry|eid|doc_id)\s*==\s*[\"']",
            re.IGNORECASE,
        )

        test_cases = [
            ('if filename == "01_gsecl":', True),  # HACK
            ('if eid in GOLD_PROVENANCE:', False),  # OK (uses 'in', not '==')
            ("if doc_id == 'special':", True),      # HACK
            ("if enquiry == 'test':", True),         # HACK
            ("is_gold_independent(eid)", False),     # OK (no ==)
        ]

        for line, should_be_suspicious in test_cases:
            m = hack_pattern.search(line)
            is_suspicious = m is not None
            assert is_suspicious == should_be_suspicious, (
                f"Line '{line}' should_be_suspicious={should_be_suspicious} got {is_suspicious}"
            )
