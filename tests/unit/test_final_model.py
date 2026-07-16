"""Tests for final NER model integration."""

from src.nlp.pipeline import ExtractionResult, NLPPipeline


class TestFinalModelPipeline:
    """Test that the pipeline correctly loads and uses the final model."""

    def test_pipeline_loads_without_error(self):
        """Pipeline should initialize without errors."""
        pipeline = NLPPipeline()
        assert pipeline is not None

    def test_pipeline_processes_text(self):
        """Pipeline should process text and return extraction result."""
        pipeline = NLPPipeline()
        result = pipeline.process("Supply 500 kg cement as per IS 456 M20 grade")
        assert isinstance(result, ExtractionResult)
        assert hasattr(result, "entities")
        assert hasattr(result, "relations")
        assert hasattr(result, "confidence")

    def test_pipeline_extracts_multiple_entity_types(self):
        """Pipeline should extract multiple entity types from construction text."""
        pipeline = NLPPipeline()
        text = "Supply 500 kg cement as per IS 456 M20 grade at ground floor"
        result = pipeline.process(text)

        entity_types = {e["type"] for e in result.entities}
        assert len(entity_types) >= 4, f"Expected >= 4 entity types, got {entity_types}"

    def test_pipeline_extracts_material(self):
        """Pipeline should extract MATERIAL entities."""
        pipeline = NLPPipeline()
        result = pipeline.process("Supply cement and steel bars")
        materials = [e for e in result.entities if e["type"] == "MATERIAL"]
        assert len(materials) > 0, "Should extract at least one MATERIAL"

    def test_pipeline_extracts_quantity(self):
        """Pipeline should extract QUANTITY entities."""
        pipeline = NLPPipeline()
        result = pipeline.process("Supply 500 kg cement")
        quantities = [e for e in result.entities if e["type"] == "QUANTITY"]
        assert len(quantities) > 0, "Should extract at least one QUANTITY"

    def test_pipeline_extracts_grade(self):
        """Pipeline should extract GRADE entities like M20, Fe500."""
        pipeline = NLPPipeline()
        result = pipeline.process("Use M20 concrete with Fe500 steel")
        grades = [e for e in result.entities if e["type"] == "GRADE"]
        assert len(grades) > 0, f"Should extract GRADE, got {[e['text'] for e in result.entities]}"

    def test_pipeline_extracts_standard(self):
        """Pipeline should extract STANDARD entities like IS 456."""
        pipeline = NLPPipeline()
        result = pipeline.process("Cement shall conform to IS 456")
        standards = [e for e in result.entities if e["type"] == "STANDARD"]
        assert len(standards) > 0, "Should extract STANDARD"

    def test_pipeline_extracts_location(self):
        """Pipeline should extract LOCATION entities."""
        pipeline = NLPPipeline()
        result = pipeline.process("Work at ground floor and first floor")
        locations = [e for e in result.entities if e["type"] == "LOCATION"]
        assert len(locations) > 0, "Should extract LOCATION"

    def test_pipeline_handles_empty_text(self):
        """Pipeline should handle empty text gracefully."""
        pipeline = NLPPipeline()
        result = pipeline.process("")
        assert isinstance(result, ExtractionResult)

    def test_pipeline_returns_confidence_score(self):
        """Pipeline should return a confidence score."""
        pipeline = NLPPipeline()
        result = pipeline.process("Supply 500 kg cement as per IS 456 M20 grade")
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0

    def test_no_contaminated_checkpoint_loaded_by_default(self):
        """Production NER is pattern-based; ensure no LoRA checkpoint is loaded."""
        pipeline = NLPPipeline()
        # The pattern-based pipeline should not reference any LoRA adapter path.
        assert not hasattr(pipeline, "lora_adapter") or pipeline.lora_adapter is None, (
            "Production NER should be pattern-based, not LoRA. "
            "If you need the LoRA model, load it explicitly."
        )

    def test_combined_annotations_skip(self):
        """Legacy synthetic-annotation files are not part of the current pipeline."""
        import pytest

        pytest.skip(
            "Legacy data/annotations_combined/ is not part of the honest pipeline. "
            "Production NER is pattern-based; synthetic training data was quarantined."
        )

    def test_results_file_skip(self):
        """Legacy results/final_model_eval.json is not part of the current pipeline."""
        import pytest

        pytest.skip(
            "Legacy results/final_model_eval.json is not part of the honest pipeline. "
            "See eval_honest.py for current evaluation outputs."
        )
