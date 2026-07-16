"""Tests for LayoutLM integration."""

import pytest

pytest.importorskip("torch")


class TestLayoutLMDataset:
    def test_initialization(self):
        from src.nlp.ner.layoutlm_dataset import LayoutLMDataset

        ds = LayoutLMDataset("data/annotations_bbox/train.json")
        assert ds.max_length == 512

    def test_load_nonexistent_file(self):
        from src.nlp.ner.layoutlm_dataset import LayoutLMDataset

        ds = LayoutLMDataset("nonexistent/file.json")
        assert len(ds) == 0


class TestLayoutLMv3NER:
    def test_initialization_without_model(self):
        from src.nlp.ner.layoutlm_ner import LayoutLMv3NER

        ner = LayoutLMv3NER(model_dir=None)
        assert ner.model is None
        assert ner.tokenizer is None

    def test_predict_without_model(self):
        from src.nlp.ner.layoutlm_ner import LayoutLMv3NER

        ner = LayoutLMv3NER(model_dir=None)
        result = ner.predict(["test"], [[0, 0, 100, 100]])
        assert result == []

    def test_label_mappings(self):
        from src.nlp.ner.layoutlm_ner import ID2LABEL, LABEL2ID

        assert LABEL2ID["O"] == 0
        assert LABEL2ID["B-MATERIAL"] == 1
        assert ID2LABEL[0] == "O"
        assert ID2LABEL[1] == "B-MATERIAL"

    def test_device_property(self):
        from src.nlp.ner.layoutlm_ner import LayoutLMv3NER

        ner = LayoutLMv3NER(model_dir=None)
        assert ner.device.type == "cpu"


class TestPDFExtractorWithBBox:
    def test_initialization(self):
        from src.ingest.pdf_extractor_bbox import PDFExtractorWithBBox

        extractor = PDFExtractorWithBBox()
        assert extractor is not None

    def test_detect_tables_nonexistent(self):
        from src.ingest.pdf_extractor_bbox import PDFExtractorWithBBox

        extractor = PDFExtractorWithBBox()
        result = extractor.detect_tables("nonexistent.pdf")
        assert result is False

    def test_detect_multi_column_nonexistent(self):
        from src.ingest.pdf_extractor_bbox import PDFExtractorWithBBox

        extractor = PDFExtractorWithBBox()
        result = extractor.detect_multi_column("nonexistent.pdf")
        assert result is False


class TestPipelineRouting:
    def test_pipeline_with_layout_aware(self):
        from src.nlp.pipeline import NLPPipeline

        pipeline = NLPPipeline(layout_aware=True)
        assert pipeline.layout_aware is True

    def test_pipeline_without_layout(self):
        from src.nlp.pipeline import NLPPipeline

        pipeline = NLPPipeline(layout_aware=False)
        assert pipeline.layout_aware is False
        assert pipeline.layout_ner is None

    def test_process_without_bboxes_routes_to_text(self):
        from src.nlp.pipeline import NLPPipeline

        pipeline = NLPPipeline(layout_aware=True, layoutlm_model_dir="models/layoutlm-v3")
        result = pipeline.process("Supply 500 kg cement")
        assert result is not None
        assert isinstance(result.entities, list)
