#!/usr/bin/env python3
"""Evaluate NER models on test set and compute per-entity metrics."""

import json
import sys
from pathlib import Path

from config.constants import ID2LABEL, LABEL2ID, NUM_LABELS
from src.nlp.ner.bert_ner import ConstructionNER
from src.nlp.pipeline import NLPPipeline
from transformers import AutoTokenizer


def compute_entity_metrics(pred_entities, true_entities):
    """Compute precision, recall, F1 per entity type."""
    metrics = {}
    entity_types = set(e["type"] for e in pred_entities + true_entities)

    for entity_type in entity_types:
        tp = sum(1 for p in pred_entities if p["type"] == entity_type and
                 any(t["type"] == entity_type and t["text"] == p["text"] for t in true_entities))
        pred_count = sum(1 for p in pred_entities if p["type"] == entity_type)
        true_count = sum(1 for t in true_entities if t["type"] == entity_type)

        precision = tp / pred_count if pred_count > 0 else 0.0
        recall = tp / true_count if true_count > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        metrics[entity_type] = {
            "f1": round(f1, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "tp": tp,
            "pred_count": pred_count,
            "true_count": true_count,
        }

    return metrics


def evaluate_model(model_path, test_data_path, model_name="bert-bilstm-crf"):
    """Evaluate a trained model on test data."""
    with open(test_data_path) as f:
        test_data = json.load(f)

    AutoTokenizer.from_pretrained("bert-base-cased")

    try:
        model = ConstructionNER(
            model_name="bert-base-cased",
            num_labels=NUM_LABELS,
            id2label=ID2LABEL,
            label2id=LABEL2ID,
        )
        if Path(model_path).exists():
            model.load(model_path)
    except Exception:
        return None

    pipeline = NLPPipeline(model_dir=str(Path(model_path).parent))

    for sample in test_data:
        tokens = sample.get("tokens", [])
        true_tags = sample.get("ner_tags", sample.get("labels", []))

        text = " ".join(tokens)
        result = pipeline.process(text)

        pred_entities = [
            {"type": e.get("type"), "text": e.get("text")}
            for e in result.entities
        ]

        true_entities = []
        current_entity = None
        current_type = None
        current_text = []
        for token, tag in zip(tokens, true_tags, strict=False):
            if tag.startswith("S-"):
                entity_type = tag[2:]
                true_entities.append({"type": entity_type, "text": token})
            elif tag.startswith("B-"):
                if current_entity:
                    true_entities.append({"type": current_type, "text": "".join(current_text)})
                current_type = tag[2:]
                current_text = [token]
            elif tag.startswith("I-") and current_type == tag[2:]:
                current_text.append(token)
            elif tag.startswith("E-") and current_type == tag[2:]:
                current_text.append(token)
                true_entities.append({"type": current_type, "text": "".join(current_text)})
                current_entity = None
                current_type = None
                current_text = []
            elif tag == "O":
                if current_entity:
                    true_entities.append({"type": current_type, "text": "".join(current_text)})
                    current_entity = None
                    current_type = None
                    current_text = []

    return compute_entity_metrics(pred_entities, true_entities)


def main():
    test_data_path = "data/annotations/test.json"

    with open(test_data_path) as f:
        test_data = json.load(f)

    pipeline = NLPPipeline()

    all_pred_entities = []
    all_true_entities = []

    for sample in test_data:
        tokens = sample.get("tokens", [])
        true_tags = sample.get("ner_tags", sample.get("labels", []))

        text = " ".join(tokens)
        result = pipeline.process(text)

        pred_entities = [
            {"type": e.get("type", "").upper(), "text": e.get("text", "")}
            for e in result.entities
        ]

        true_entities = []
        current_type = None
        current_text = []
        for token, tag in zip(tokens, true_tags, strict=False):
            if tag.startswith("S-"):
                entity_type = tag[2:]
                true_entities.append({"type": entity_type, "text": token})
            elif tag.startswith("B-"):
                if current_type:
                    true_entities.append({"type": current_type, "text": "".join(current_text)})
                current_type = tag[2:]
                current_text = [token]
            elif tag.startswith("I-") and current_type == tag[2:]:
                current_text.append(token)
            elif tag.startswith("E-") and current_type == tag[2:]:
                current_text.append(token)
                true_entities.append({"type": current_type, "text": "".join(current_text)})
                current_type = None
                current_text = []
            elif tag == "O":
                if current_type:
                    true_entities.append({"type": current_type, "text": "".join(current_text)})
                    current_type = None
                    current_text = []

        all_pred_entities.extend(pred_entities)
        all_true_entities.extend(true_entities)

    entity_metrics = compute_entity_metrics(all_pred_entities, all_true_entities)

    all_tp = sum(m["tp"] for m in entity_metrics.values())
    all_pred = sum(m["pred_count"] for m in entity_metrics.values())
    all_true = sum(m["true_count"] for m in entity_metrics.values())

    overall_precision = all_tp / all_pred if all_pred > 0 else 0.0
    overall_recall = all_tp / all_true if all_true > 0 else 0.0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0.0

    metrics = {
        "model": "pipeline-patterns",
        "overall_f1": round(overall_f1, 4),
        "overall_precision": round(overall_precision, 4),
        "overall_recall": round(overall_recall, 4),
        "per_entity": entity_metrics,
    }

    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    sys.exit(main())
