#!/usr/bin/env python3
"""Compare NER model results and print comparison table."""

import json
from pathlib import Path


def load_metrics(model_dir):
    metrics_file = Path(model_dir) / "metrics.json"
    if metrics_file.exists():
        with open(metrics_file) as f:
            return json.load(f)
    return None


def main():
    baseline_metrics = load_metrics("models/ner-bert-baseline")
    bilstm_metrics = load_metrics("models/ner-bert-bilstm-crf-v1")

    print("| Entity    | BERT-baseline F1 | BERT-BiLSTM-CRF F1 | Delta |")
    print("|-----------|------------------|--------------------|-------|")

    entity_types = ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"]

    overall_baseline = baseline_metrics.get("overall_f1", 0) if baseline_metrics else 0
    overall_bilstm = bilstm_metrics.get("overall_f1", 0) if bilstm_metrics else 0

    for entity in entity_types:
        baseline_f1 = 0.0
        bilstm_f1 = 0.0

        if baseline_metrics and "per_entity" in baseline_metrics:
            baseline_f1 = baseline_metrics["per_entity"].get(entity, {}).get("f1", 0.0)

        if bilstm_metrics and "per_entity" in bilstm_metrics:
            bilstm_f1 = bilstm_metrics["per_entity"].get(entity, {}).get("f1", 0.0)

        delta = bilstm_f1 - baseline_f1
        delta_str = f"+{delta:.2f}" if delta >= 0 else f"{delta:.2f}"

        print(f"| {entity:9} | {baseline_f1:16.4f} | {bilstm_f1:17.4f} | {delta_str:5} |")

    print("|-----------|------------------|--------------------|-------|")
    overall_delta = overall_bilstm - overall_baseline
    delta_str = f"+{overall_delta:.2f}" if overall_delta >= 0 else f"{overall_delta:.2f}"
    print(f"| OVERALL   | {overall_baseline:16.4f} | {overall_bilstm:17.4f} | {delta_str:5} |")

    comparison = {
        "baseline": baseline_metrics,
        "bilstm_crf": bilstm_metrics,
        "delta_per_entity": {},
        "overall_delta": overall_delta,
    }

    for entity in entity_types:
        baseline_f1 = baseline_metrics.get("per_entity", {}).get(entity, {}).get("f1", 0) if baseline_metrics else 0
        bilstm_f1 = bilstm_metrics.get("per_entity", {}).get(entity, {}).get("f1", 0) if bilstm_metrics else 0
        comparison["delta_per_entity"][entity] = round(bilstm_f1 - baseline_f1, 4)

    Path("results").mkdir(exist_ok=True)
    with open("results/model_comparison.json", "w") as f:
        json.dump(comparison, f, indent=2)

    print("\nSaved comparison to results/model_comparison.json")


if __name__ == "__main__":
    main()
