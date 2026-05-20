#!/usr/bin/env python3
"""Compare ARCBERT NER vs baseline (bert-base-cased) on test set.

Usage:
    python scripts/compare_arcbert.py
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_metrics(model_dir: str) -> dict | None:
    """Load metrics.json if it exists."""
    metrics_path = Path(model_dir) / "metrics.json"
    if metrics_path.exists():
        return json.load(open(metrics_path))
    return None


def main():
    parser = argparse.ArgumentParser(description="Compare ARCBERT vs baseline NER models")
    parser.add_argument(
        "--baseline",
        default="models/ner-bert-bilstm-crf-v1/metrics.json",
        help="Baseline model metrics"
    )
    parser.add_argument(
        "--arcbert",
        default="models/arcbert-ner-v1/metrics.json",
        help="ARCBERT model metrics"
    )
    parser.add_argument(
        "--output",
        default="results/arcbert_vs_baseline.json",
        help="Output comparison JSON"
    )
    args = parser.parse_args()

    baseline_metrics = load_metrics(args.baseline)
    arcbert_metrics = load_metrics(args.arcbert)

    comparison = {
        "baseline_model": args.baseline,
        "arcbert_model": args.arcbert,
        "baseline_f1": baseline_metrics.get("test_f1") if baseline_metrics else None,
        "arcbert_f1": arcbert_metrics.get("test_f1") if arcbert_metrics else None,
        "timestamp": Path(__file__).stat().st_mtime,
    }

    if comparison["baseline_f1"] and comparison["arcbert_f1"]:
        comparison["improvement"] = comparison["arcbert_f1"] - comparison["baseline_f1"]
        comparison["arcbert_better"] = comparison["arcbert_f1"] > comparison["baseline_f1"]
    else:
        comparison["note"] = "One or both models not trained yet (metrics missing)"

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(comparison, f, indent=2)

    print(f"Comparison saved to {args.output}")
    print(f"Baseline F1: {comparison.get('baseline_f1', 'N/A')}")
    print(f"ARCBERT F1: {comparison.get('arcbert_f1', 'N/A')}")
    if "improvement" in comparison:
        print(f"Improvement: {comparison['improvement']:+.4f}")


if __name__ == "__main__":
    main()
