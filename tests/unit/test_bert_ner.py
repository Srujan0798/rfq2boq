"""Tests for BERT NER model."""

import torch
from src.nlp.ner.bert_ner import BERTBiLSTMCRF, ConstructionNER


class TestBERTBiLSTMCRF:
    def test_model_initialization(self):
        model = BERTBiLSTMCRF(
            model_name="bert-base-cased",
            num_labels=41,
            lstm_hidden=256,
            lstm_layers=1,
            dropout=0.1,
            use_crf=True,
        )
        assert model.num_labels == 41
        assert model.use_crf is True

    def test_forward_pass(self):
        model = BERTBiLSTMCRF(
            model_name="bert-base-cased",
            num_labels=41,
            lstm_hidden=256,
            lstm_layers=1,
            dropout=0.1,
            use_crf=False,
        )
        batch_size = 2
        seq_length = 10
        input_ids = torch.randint(0, 1000, (batch_size, seq_length))
        attention_mask = torch.ones(batch_size, seq_length)

        result = model(input_ids=input_ids, attention_mask=attention_mask)

        assert isinstance(result, dict)
        assert "logits" in result
        assert result["logits"].shape == (batch_size, seq_length, 41)


class TestConstructionNER:
    def test_initialization(self):
        ner = ConstructionNER(
            model_name="bert-base-cased",
            num_labels=41,
            id2label={0: "O"},
            label2id={"O": 0},
        )
        assert ner.num_labels == 41
        assert ner.device.type in ["cuda", "cpu"]

    def test_id2label_mapping(self):
        id2label = {0: "O", 1: "B-MATERIAL", 2: "I-MATERIAL", 3: "E-MATERIAL", 4: "S-MATERIAL"}
        label2id = {"O": 0, "B-MATERIAL": 1, "I-MATERIAL": 2, "E-MATERIAL": 3, "S-MATERIAL": 4}
        ner = ConstructionNER(
            model_name="bert-base-cased",
            num_labels=5,
            id2label=id2label,
            label2id=label2id,
        )
        assert ner.id2label == id2label
        assert ner.label2id == label2id


class TestEntityDecoding:
    def test_decode_empty_predictions(self):
        ner = ConstructionNER(
            model_name="bert-base-cased",
            num_labels=41,
            id2label={0: "O"},
            label2id={"O": 0},
        )
        tokens = ["[CLS]", "cement", "[SEP]", "[PAD]"]
        predictions = torch.tensor([0, 0, 0, 0])
        scores = torch.ones(4, 41)

        entities = ner._decode_predictions(tokens, predictions, scores)
        assert isinstance(entities, list)

    def test_decode_single_token_entity(self):
        ner = ConstructionNER(
            model_name="bert-base-cased",
            num_labels=41,
            id2label={0: "O", 4: "S-MATERIAL"},
            label2id={"O": 0, "S-MATERIAL": 4},
        )
        tokens = ["[CLS]", "cement", "[SEP]"]
        predictions = torch.tensor([0, 4, 0])
        scores = torch.ones(3, 41)

        entities = ner._decode_predictions(tokens, predictions, scores)
        assert len(entities) == 1
        assert entities[0]["type"] == "MATERIAL"
        assert entities[0]["text"] == "cement"

    def test_decode_multi_token_entity(self):
        ner = ConstructionNER(
            model_name="bert-base-cased",
            num_labels=41,
            id2label={0: "O", 1: "B-MATERIAL", 2: "I-MATERIAL"},
            label2id={"O": 0, "B-MATERIAL": 1, "I-MATERIAL": 2},
        )
        tokens = ["[CLS]", "cement", "mortar", "[SEP]"]
        predictions = torch.tensor([0, 1, 2, 0])
        scores = torch.ones(4, 41)

        entities = ner._decode_predictions(tokens, predictions, scores)
        assert len(entities) == 1
        assert entities[0]["type"] == "MATERIAL"
        assert entities[0]["text"] == "cementmortar"
