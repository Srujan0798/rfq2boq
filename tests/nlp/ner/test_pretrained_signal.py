"""Tests for src.nlp.ner.pretrained_signal."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from src.nlp.ner.pretrained_signal import LABEL_MAP, PretrainedNERSignal


class TestPretrainedNERSignal:
    def test_disabled_when_env_false(self):
        signal = PretrainedNERSignal(enabled=False)
        assert signal.enabled is False
        assert signal.predict("anything") == []

    def test_enabled_by_default(self, monkeypatch):
        monkeypatch.delenv("RFQ2BOQ_PRETRAINED_NER_ENABLED", raising=False)
        signal = PretrainedNERSignal()
        assert signal.enabled is True

    def test_env_var_respected(self, monkeypatch):
        monkeypatch.setenv("RFQ2BOQ_PRETRAINED_NER_ENABLED", "false")
        signal = PretrainedNERSignal()
        assert signal.enabled is False

    def test_label_map_coverage(self):
        """Every mapped label must map to a valid project entity type."""
        from config.constants import EntityType

        for generic_label, project_label in LABEL_MAP.items():
            assert project_label in {e.value for e in EntityType}

    def test_predict_returns_empty_on_blank_text(self):
        signal = PretrainedNERSignal(enabled=False)
        assert signal.predict("") == []
        assert signal.predict("   ") == []

    def test_predict_skips_unsupported_labels(self):
        """PER and ORG labels are dropped; only LOC/MISC are mapped."""
        # Mock the tokenizer / model so we don't need to download anything.
        signal = PretrainedNERSignal(enabled=True)

        mock_tokenizer = MagicMock()
        mock_model = MagicMock()
        mock_model.config.id2label = {
            0: "O",
            1: "B-PER",
            2: "I-PER",
            3: "B-ORG",
            4: "I-ORG",
            5: "B-LOC",
            6: "I-LOC",
            7: "B-MISC",
            8: "I-MISC",
        }
        # Logits shape: (1, 9, 9) -> argmax gives one prediction per token.
        import torch

        mock_logits = torch.zeros(1, 6, 9)
        # tokens: [CLS] Paris is nice [SEP]
        mock_logits[0, 1, 5] = 10.0  # B-LOC for "Paris"
        mock_logits[0, 2, 0] = 10.0  # O for "is"
        mock_logits[0, 3, 0] = 10.0  # O for "nice"
        mock_model.return_value = MagicMock(logits=mock_logits)

        mock_tokenizer.return_value = {
            "input_ids": torch.tensor([[101, 1, 2, 3, 102]]),
            "attention_mask": torch.tensor([[1, 1, 1, 1, 1]]),
            "offset_mapping": torch.tensor(
                [[(0, 0), (0, 5), (6, 8), (9, 13), (0, 0)]]
            ),
        }

        signal._tokenizer = mock_tokenizer
        signal._model = mock_model
        signal._device = "cpu"

        ents = signal.predict("Paris is nice")
        assert len(ents) == 1
        assert ents[0]["text"] == "Paris"
        assert ents[0]["type"] == "LOCATION"
        assert ents[0]["source"] == "pretrained_ner"

    def test_entity_has_required_keys(self):
        signal = PretrainedNERSignal(enabled=True)
        mock_tokenizer = MagicMock()
        mock_model = MagicMock()
        mock_model.config.id2label = {0: "O", 1: "B-LOC", 2: "I-LOC"}
        import torch

        mock_logits = torch.zeros(1, 4, 3)
        mock_logits[0, 1, 1] = 10.0
        mock_model.return_value = MagicMock(logits=mock_logits)
        mock_tokenizer.return_value = {
            "input_ids": torch.tensor([[101, 1, 102]]),
            "attention_mask": torch.tensor([[1, 1, 1]]),
            "offset_mapping": torch.tensor([[(0, 0), (0, 5), (0, 0)]]),
        }
        signal._tokenizer = mock_tokenizer
        signal._model = mock_model
        signal._device = "cpu"

        ents = signal.predict("Paris")
        assert len(ents) == 1
        e = ents[0]
        assert set(e.keys()) >= {"text", "type", "start", "end", "confidence", "source"}

    def test_module_cache_reuses_model(self):
        """Two instances with the same model should share the cached model."""
        from src.nlp.ner import pretrained_signal as mod

        mod._MODEL_CACHE.clear()
        s1 = PretrainedNERSignal(enabled=True)
        s2 = PretrainedNERSignal(enabled=True)
        mock_tokenizer = MagicMock()
        mock_model = MagicMock()
        mock_model.config.id2label = {0: "O"}
        mock_model.to = MagicMock(return_value=mock_model)
        mock_model.eval = MagicMock()

        with patch(
            "transformers.AutoTokenizer.from_pretrained", return_value=mock_tokenizer
        ), patch(
            "transformers.AutoModelForTokenClassification.from_pretrained",
            return_value=mock_model,
        ):
            s1._load()
            s2._load()

        # AutoModelForTokenClassification.from_pretrained should have been
        # called exactly once because the second load hits the cache.
        assert mock_model is s1._model
        assert mock_model is s2._model
        assert len(mod._MODEL_CACHE) == 1
