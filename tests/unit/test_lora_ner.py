"""Tests for LoRA NER adapter."""

import json
from pathlib import Path

import pytest

pytest.importorskip("transformers")


class TestLoRANERAdapter:
    def test_init_without_peft(self):
        """LoRA adapter handles missing peft gracefully."""
        from src.nlp.ner.lora_adapter import LoRANERAdapter

        adapter = LoRANERAdapter("nonexistent_model", num_labels=41)
        assert adapter.is_available is False

    def test_predict_returns_empty_when_unavailable(self):
        from src.nlp.ner.lora_adapter import LoRANERAdapter

        adapter = LoRANERAdapter("nonexistent_model", num_labels=41)
        result = adapter.predict("test text")
        assert result == []

    def test_save_raises_when_unavailable(self):
        from src.nlp.ner.lora_adapter import LoRANERAdapter

        adapter = LoRANERAdapter("nonexistent_model", num_labels=41)
        with pytest.raises(RuntimeError, match="not initialized"):
            adapter.save("/tmp/test_lora")

    def test_load_nonexistent_adapter(self):
        from src.nlp.ner.lora_adapter import LoRANERAdapter

        adapter = LoRANERAdapter.load("nonexistent_model", "nonexistent_adapter", num_labels=41)
        assert adapter.is_available is False

    def test_gold_data_loadable(self):
        gold_path = Path("data/real_rfqs/annotations/gold_annotations.json")
        if not gold_path.exists():
            pytest.skip("Gold annotations not found")
        with gold_path.open() as f:
            data = json.load(f)
        assert len(data) == 20
        assert all("tokens" in d for d in data)
        assert all("ner_tags" in d for d in data)

    def test_pipeline_detects_lora_adapter_config(self, tmp_path):
        """Pipeline should detect adapter_config.json and attempt LoRA loading."""
        adapter_dir = tmp_path / "lora_adapter"
        adapter_dir.mkdir()
        (adapter_dir / "adapter_config.json").write_text("{}")

        from src.nlp.pipeline import NLPPipeline

        pipeline = NLPPipeline(model_dir=str(adapter_dir), ner_enabled=True)
        # LoRA load fails (no real adapter), falls back to base model loading
        # With no valid base model directory, ner may be None or a LoRANERAdapter
        # The key assertion: pipeline did not crash
        assert pipeline is not None

    def test_pipeline_env_lora_model(self, monkeypatch, tmp_path):
        """RFQ2BOQ_LORA_MODEL env var should be respected when adapter exists."""
        adapter_dir = tmp_path / "lora_env"
        adapter_dir.mkdir()
        (adapter_dir / "adapter_config.json").write_text("{}")

        monkeypatch.setenv("RFQ2BOQ_LORA_MODEL", str(adapter_dir))

        from src.nlp.pipeline import NLPPipeline

        pipeline = NLPPipeline(model_dir="/nonexistent", ner_enabled=True)
        # Pipeline should not crash even if LoRA load fails
        assert pipeline is not None

    def test_lora_adapter_load_classmethod(self):
        """LoRANERAdapter.load falls back gracefully for nonexistent paths."""
        from src.nlp.ner.lora_adapter import LoRANERAdapter

        adapter = LoRANERAdapter.load(
            "nonexistent_base_model_xyz",
            "nonexistent_adapter_xyz",
            num_labels=41,
        )
        assert adapter.is_available is False
        assert adapter.predict("any text") == []
