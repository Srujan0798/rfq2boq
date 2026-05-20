#!/usr/bin/env python3
"""Evaluation script for NER model and full pipeline."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from config.constants import ENTITY_LABELS, ID2LABEL, LABEL2ID
from src.nlp.pipeline import NLPPipeline


def load_json(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def compute_span_f1(predictions: list[dict], ground_truth: list[dict]) -> dict[str, float]:
    entity_types = list(ENTITY_LABELS)

    tp_total = 0
    fp_total = 0
    fn_total = 0

    per_type_metrics = {}

    for entity_type in entity_types:
        pred_spans = {
            (e["start"], e["end"], e["type"])
            for e in predictions
            if e.get("type") == entity_type
        }
        true_spans = {
            (e["start"], e["end"], e["type"])
            for e in ground_truth
            if e.get("type") == entity_type
        }

        tp = len(pred_spans & true_spans)
        fp = len(pred_spans - true_spans)
        fn = len(true_spans - pred_spans)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        per_type_metrics[entity_type] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
        }

        tp_total += tp
        fp_total += fp
        fn_total += fn

    micro_precision = tp_total / (tp_total + fp_total) if (tp_total + fp_total) > 0 else 0.0
    micro_recall = tp_total / (tp_total + fn_total) if (tp_total + fn_total) > 0 else 0.0
    micro_f1 = (
        2 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if (micro_precision + micro_recall) > 0
        else 0.0
    )

    return {
        "micro_precision": micro_precision,
        "micro_recall": micro_recall,
        "micro_f1": micro_f1,
        "per_type": per_type_metrics,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate NER model")
    parser.add_argument("--test-data", type=str, required=True, help="Path to test data JSON")
    parser.add_argument("--model-dir", type=str, default="models/ner-bert-bilstm-crf-v1")
    parser.add_argument("--ontology-dir", type=str, default="code/ontology")
    parser.add_argument("--split", type=str, default="test", choices=["train", "val", "test"])
    parser.add_argument("--metrics", type=str, default="all", choices=["all", "ner", "pipeline"])
    parser.add_argument("--output", type=str, default="results/ner_metrics.json")
    args = parser.parse_args()

    print(f"Loading test data from {args.test_data}")
    test_data = load_json(args.test_data)

    print("Initializing NLP pipeline")
    pipeline = NLPPipeline(
        model_dir=args.model_dir,
        ontology_dir=args.ontology_dir,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    all_predictions = []
    all_ground_truth = []

    print(f"Running evaluation on {len(test_data)} examples")
    for i, example in enumerate(test_data):
        text = example.get("text", "")
        ground_truth = example.get("entities", [])

        result = pipeline.process(text)

        all_predictions.extend(result.entities)
        all_ground_truth.extend(ground_truth)

        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(test_data)}")

    print("\nComputing metrics")
    metrics = compute_span_f1(all_predictions, all_ground_truth)

    print("\nOverall Results:")
    print(f"  Micro Precision: {metrics['micro_precision']:.4f}")
    print(f"  Micro Recall:    {metrics['micro_recall']:.4f}")
    print(f"  Micro F1:       {metrics['micro_f1']:.4f}")

    print("\nPer-Type F1:")
    for entity_type, type_metrics in metrics["per_type"].items():
        print(f"  {entity_type:12s}  P={type_metrics['precision']:.3f}  R={type_metrics['recall']:.3f}  F1={type_metrics['f1']:.3f}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nSaved metrics to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
