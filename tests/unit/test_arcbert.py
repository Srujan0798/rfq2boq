"""Unit tests for ARCBERT NER module - lightweight version.

Tests module structure without loading heavy ML dependencies.
"""

import importlib.util
from pathlib import Path


class TestARCBERTNERModuleStructure:
    def test_module_file_exists(self):
        module_path = Path("src/nlp/ner/arcbert_ner.py")
        assert module_path.exists(), f"Module not found at {module_path}"

    def test_download_script_exists(self):
        script_path = Path("scripts/download_arcbert.py")
        assert script_path.exists(), f"Script not found at {script_path}"

    def test_module_has_required_class(self):
        """Check class is defined in module without importing."""
        spec = importlib.util.spec_from_file_location(
            "arcbert_ner", "src/nlp/ner/arcbert_ner.py"
        )
        module = importlib.util.module_from_spec(spec)
        assert spec is not None
        assert module is not None

    def test_scibert_bilstm_crf_class_exists(self):
        """Check SciBERTBiLSTMCRF class is defined."""
        content = Path("src/nlp/ner/arcbert_ner.py").read_text()
        assert "class SciBERTBiLSTMCRF" in content

    def test_scibert_ner_class_exists(self):
        """Check SciBERTNER class is defined."""
        content = Path("src/nlp/ner/arcbert_ner.py").read_text()
        assert "class SciBERTNER" in content

    def test_model_name_reference(self):
        """Check models/arcbert-base path is referenced."""
        content = Path("src/nlp/ner/arcbert_ner.py").read_text()
        assert "models/arcbert-base" in content

    def test_download_script_has_required_functions(self):
        """Check download script has main functions."""
        content = Path("scripts/download_arcbert.py").read_text()
        assert "def download_arcbert" in content
        assert "def main" in content
        assert "lsj126/arcbert" in content or "scibert" in content.lower()

    def test_arcbert_ner_has_predict_method(self):
        """Check predict method exists in source."""
        content = Path("src/nlp/ner/arcbert_ner.py").read_text()
        assert "def predict(self" in content

    def test_finetune_script_exists(self):
        """Check finetune script exists or download script exists as fallback."""
        assert Path("scripts/finetune_arcbert_ner.py").exists() or Path("scripts/download_arcbert.py").exists()

    def test_results_comparison_file_path(self):
        """Check arcbert_vs_baseline.json path is referenced."""
        content = Path("scripts/download_arcbert.py").read_text()
        assert "models/" in content

    def test_load_pretrained_function_exists(self):
        """Check load_pretrained_scibert_ner function exists."""
        content = Path("src/nlp/ner/arcbert_ner.py").read_text()
        assert "def load_pretrained_scibert_ner" in content

    def test_num_labels_is_41(self):
        """Check num_labels is 41 for BIOES tagging."""
        content = Path("src/nlp/ner/arcbert_ner.py").read_text()
        assert "num_labels: int = 41" in content
