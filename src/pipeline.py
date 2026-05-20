"""Main extraction pipeline: PDF/Text → Ingest → NLP → BOQ → Export."""

from contextlib import suppress
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from config.constants import EntityType, RelationType
from config.settings import settings

from src.confidence.calibration import ConformalPredictor
from src.domain.boq_assembler import BOQAssembler
from src.domain.confidence import ConfidenceScorer
from src.domain.models import EntitySpan, ExtractionMetadata, ExtractionResult, Relation
from src.domain.validator import DomainValidator
from src.export import ExcelGenerator, JSONFormatter
from src.export.csv_exporter import CSVExporter
from src.export.report import ReportGenerator
from src.ingest.layout_analyzer import LayoutAnalyzer
from src.ingest.ocr_processor import OCRProcessor
from src.ingest.pdf_extractor import PDFExtractor
from src.ingest.preprocessor import TextPreprocessor
from src.ingest.table_extractor import TableExtractor
from src.nlp.pipeline import NLPPipeline
from src.risk.engine import RiskEngine


class Pipeline:
    """Main extraction pipeline wiring all components."""

    def __init__(
        self,
        model_dir: str | None = None,
        ontology_dir: str | None = None,
    ):
        self.pdf_extractor = PDFExtractor()
        self.ocr_processor = OCRProcessor()
        self.layout_analyzer = LayoutAnalyzer()
        self.preprocessor = TextPreprocessor()

        self.nlp_pipeline = NLPPipeline(
                model_dir=model_dir,
                ontology_dir=ontology_dir or str(settings.ONTOLOGY_DIR),
            )

        self.assembler = BOQAssembler()
        self.validator = DomainValidator()
        self.confidence_scorer = ConfidenceScorer()

        self.json_formatter = JSONFormatter()
        self.excel_generator = ExcelGenerator()
        self.csv_exporter = CSVExporter()
        self.report_generator = ReportGenerator()
        self.table_extractor = TableExtractor()
        self.risk_engine = RiskEngine()
        self.conformal_predictor = ConformalPredictor(target_coverage=0.95)

    def run(self, pdf_path: str | Path) -> ExtractionResult:
        """Run full extraction pipeline on a PDF or plain-text file."""
        path = Path(pdf_path)
        doc_id = f"pipeline-{path.stem}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if path.suffix.lower() == ".txt":
            raw_text = path.read_text(encoding="utf-8")
            pages = [type("Page", (), {"text": raw_text, "page_number": 1})()]
        else:
            document = self.pdf_extractor.extract(str(path))
            pages = document.pages
            if document.is_scanned or not pages or all(not p.text.strip() for p in pages):
                ocr_result = self.ocr_processor.process_pdf(str(path))
                if ocr_result.pages:
                    pages = [
                        type("Page", (), {"text": page.text, "page_number": page.page_number})()
                        for page in ocr_result.pages
                    ]

        all_text = "\n".join(p.text for p in pages)
        cleaned_text = self.preprocessor.normalize(all_text)

        nlp_result = self.nlp_pipeline.process(cleaned_text)

        entities: list[EntitySpan] = []
        for e_dict in getattr(nlp_result, "entities", []):
            ent_type = e_dict.get("type", "MATERIAL")
            try:
                entity_type = EntityType[ent_type.upper()]
            except KeyError:
                entity_type = EntityType.MATERIAL
            entities.append(EntitySpan(
                text=e_dict.get("text", ""),
                type=entity_type,
                start=e_dict.get("start", 0),
                end=e_dict.get("end", 0),
                page=e_dict.get("page", 1),
                conf=e_dict.get("confidence", 0.5),
            ))

        relations: list[Relation] = []
        for r_dict in getattr(nlp_result, "relations", []):
            rel_type = r_dict.get("type", "HAS_QUANTITY")
            try:
                relation_type = RelationType[rel_type.upper()]
            except KeyError:
                relation_type = RelationType.HAS_QUANTITY
            relations.append(Relation(
                head_id=str(r_dict.get("head_id", "")),
                tail_id=str(r_dict.get("tail_id", "")),
                type=relation_type,
                conf=r_dict.get("confidence", 0.5),
            ))

        boq_items = self.assembler.assemble(entities, relations, cleaned_text)

        for item in boq_items:
            item.confidence = self.confidence_scorer.score_item(item)

        try:
            tables = self.table_extractor.extract(str(path))
            if tables:
                table_boq_rows = self.table_extractor.map_to_boq_rows(tables)
                for row_data in table_boq_rows:
                    from src.domain.models import BoqRow
                    new_item = BoqRow(
                        material=row_data.get("material", ""),
                        quantity=row_data.get("quantity", 0),
                        unit=row_data.get("unit", "no."),
                        description_raw=row_data.get("description", ""),
                        grade=row_data.get("grade", ""),
                        location=row_data.get("location", ""),
                        action=row_data.get("action", "supply"),
                        confidence=0.85,
                    )
                    if new_item.material:
                        boq_items.append(new_item)
        except Exception:
            pass

        entity_counts = {}
        for e in entities:
            t = e.type.value if hasattr(e.type, "value") else str(e.type)
            entity_counts[t] = entity_counts.get(t, 0) + 1

        avg_conf = sum(i.confidence for i in boq_items) / len(boq_items) if boq_items else 0.0

        with suppress(Exception):
            risk_report = self.risk_engine.analyze(boq_items)

        high_conf_entities, low_conf_entities = self.conformal_predictor.filter_low_confidence(
            [
                {
                    "text": e.text,
                    "type": e.type.value if hasattr(e.type, "value") else str(e.type),
                    "confidence": e.conf,
                    "has_quantity": bool(any(r.type == RelationType.HAS_QUANTITY for r in relations)),
                    "has_unit": bool(any(r.type == RelationType.HAS_UNIT for r in relations)),
                    "has_material": True,
                }
                for e in entities
            ]
        )

        result = ExtractionResult(
            doc_id=doc_id,
            project_name=path.stem,
            extraction_date=datetime.now(UTC),
            source_file=str(path),
            entities=entities,
            relations=relations,
            boq_items=boq_items,
            metadata=ExtractionMetadata(
                total_items=len(boq_items),
                avg_confidence=avg_conf,
                processing_time_sec=0.0,
                pages_processed=len(pages),
                entity_counts=entity_counts,
                warnings=list(getattr(nlp_result, "warnings", [])),
            ),
            risk_report=asdict(risk_report) if risk_report else None,
            low_confidence_entities=low_conf_entities,
        )

        return result

    def export(self, result: ExtractionResult, output_path: str, format: str = "excel") -> None:
        """Export extraction result to file."""
        path = Path(output_path)
        fmt = format.lower()

        if fmt == "json":
            content = self.json_formatter.format_to_string(result)
            path.write_text(content, encoding="utf-8")
        elif fmt == "excel":
            self.excel_generator.generate(result, str(path))
        elif fmt == "csv":
            self.csv_exporter.export(result, str(path))
        elif fmt == "sap":
            from src.export.adapters.sap_xml import SAPExporter
            SAPExporter().export(result, str(path))
        elif fmt == "primavera":
            from src.export.adapters.primavera_xer import PrimaveraExporter
            PrimaveraExporter().export(result, str(path))
        elif fmt == "ifc":
            from src.export.adapters.ifc_export import IFCExporter
            IFCExporter().export(result, str(path))
        elif fmt in ("costx", "buildsoft"):
            from src.export.adapters.costx_csv import CostXExporter
            CostXExporter(format=fmt).export(result, str(path))
        elif fmt in ("cpwd", "dsr"):
            from src.export.adapters.excel_templates import export_cpwd, export_dsr
            if fmt == "cpwd":
                export_cpwd(result, str(path))
            else:
                export_dsr(result, str(path))
        else:
            raise ValueError(f"Unknown format: {format}")
