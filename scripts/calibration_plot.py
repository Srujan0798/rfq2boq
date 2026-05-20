"""Generate calibration reliability diagrams.

Creates before/after calibration reliability diagrams comparing
raw model confidence vs calibrated confidence.

Usage:
    python scripts/calibration_plot.py [--output report/figures/calibration.png]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nlp.calibration import compute_ece


def load_calibration_data(
    before_path: Path | None = None,
    after_path: Path | None = None,
) -> tuple[list[float], list[float], list[float], list[float]]:
    if before_path and before_path.exists():
        with open(before_path) as f:
            data = json.load(f)
        raw_confs = [d["raw_confidence"] for d in data]
        accuracies = [d["correct"] for d in data]
    else:
        raw_confs = [0.95, 0.85, 0.75, 0.65, 0.55, 0.45, 0.35, 0.25, 0.15, 0.05]
        accuracies = [1, 1, 1, 0, 1, 0, 1, 0, 0, 0]

    if after_path and after_path.exists():
        with open(after_path) as f:
            data = json.load(f)
        calibrated_confs = [d["calibrated_confidence"] for d in data]
    else:
        calibrated_confs = raw_confs

    return raw_confs, calibrated_confs, accuracies, [a for a in accuracies]


def plot_reliability_diagram(
    raw_confs: list[float],
    calibrated_confs: list[float],
    accuracies: list[bool],
    output_path: Path,
    title: str = "Reliability Diagram",
) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.patches  # noqa: F401
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available, skipping plot")
        return

    n_bins = 10
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    raw_bin_accs = [[] for _ in range(n_bins)]
    raw_bin_confs = [[] for _ in range(n_bins)]
    cal_bin_accs = [[] for _ in range(n_bins)]
    cal_bin_confs = [[] for _ in range(n_bins)]

    for conf, acc in zip(raw_confs, accuracies, strict=False):
        for i in range(n_bins):
            if bin_edges[i] <= conf < bin_edges[i + 1]:
                raw_bin_confs[i].append(conf)
                raw_bin_accs[i].append(1.0 if acc else 0.0)
                break

    for conf, acc in zip(calibrated_confs, accuracies, strict=False):
        for i in range(n_bins):
            if bin_edges[i] <= conf < bin_edges[i + 1]:
                cal_bin_confs[i].append(conf)
                cal_bin_accs[i].append(1.0 if acc else 0.0)
                break

    raw_avg_accs = []
    raw_avg_confs = []
    for i in range(n_bins):
        if raw_bin_accs[i]:
            raw_avg_accs.append(sum(raw_bin_accs[i]) / len(raw_bin_accs[i]))
            raw_avg_confs.append(sum(raw_bin_confs[i]) / len(raw_bin_confs[i]))
        else:
            raw_avg_accs.append(0)
            raw_avg_confs.append(bin_centers[i])

    cal_avg_accs = []
    cal_avg_confs = []
    for i in range(n_bins):
        if cal_bin_accs[i]:
            cal_avg_accs.append(sum(cal_bin_accs[i]) / len(cal_bin_accs[i]))
            cal_avg_confs.append(sum(cal_bin_confs[i]) / len(cal_bin_confs[i]))
        else:
            cal_avg_accs.append(0)
            cal_avg_confs.append(bin_centers[i])

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax1 = axes[0]
    ax1.plot([0, 1], [0, 1], "k--", linewidth=1.5, label="Perfect calibration")
    ax1.plot(raw_avg_confs, raw_avg_accs, "ro-", linewidth=2, markersize=8, label="Before calibration")
    ax1.fill_between(raw_avg_confs, raw_avg_accs, raw_avg_confs, alpha=0.2, color="red")
    ax1.set_xlabel("Confidence", fontsize=12)
    ax1.set_ylabel("Accuracy", fontsize=12)
    ax1.set_title("Before Temperature Scaling", fontsize=14)
    ax1.set_xlim([0, 1])
    ax1.set_ylim([0, 1])
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    ax2 = axes[1]
    ax2.plot([0, 1], [0, 1], "k--", linewidth=1.5, label="Perfect calibration")
    ax2.plot(cal_avg_confs, cal_avg_accs, "go-", linewidth=2, markersize=8, label="After calibration")
    ax2.fill_between(cal_avg_confs, cal_avg_accs, cal_avg_confs, alpha=0.2, color="green")
    ax2.set_xlabel("Confidence", fontsize=12)
    ax2.set_ylabel("Accuracy", fontsize=12)
    ax2.set_title("After Temperature Scaling", fontsize=14)
    ax2.set_xlim([0, 1])
    ax2.set_ylim([0, 1])
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)

    before_ece = compute_ece(raw_confs, accuracies, n_bins)
    after_ece = compute_ece(calibrated_confs, accuracies, n_bins)

    fig.suptitle(f"{title}\nECE Before: {before_ece:.3f} | ECE After: {after_ece:.3f}", fontsize=14, y=1.02)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved reliability diagram to {output_path}")

    plt.close(fig)


def plot_confidence_distribution(
    raw_confs: list[float],
    calibrated_confs: list[float],
    output_path: Path,
) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].hist(raw_confs, bins=20, alpha=0.7, color="red", edgecolor="black")
    axes[0].set_xlabel("Raw Confidence")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Raw Model Confidence Distribution")
    axes[0].axvline(np.mean(raw_confs), color="darkred", linestyle="--", label=f"Mean: {np.mean(raw_confs):.3f}")
    axes[0].legend()

    axes[1].hist(calibrated_confs, bins=20, alpha=0.7, color="green", edgecolor="black")
    axes[1].set_xlabel("Calibrated Confidence")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Calibrated Confidence Distribution")
    axes[1].axvline(np.mean(calibrated_confs), color="darkgreen", linestyle="--", label=f"Mean: {np.mean(calibrated_confs):.3f}")
    axes[1].legend()

    plt.tight_layout()
    dist_path = output_path.parent / "confidence_distribution.png"
    plt.savefig(dist_path, dpi=150, bbox_inches="tight")
    print(f"Saved confidence distribution to {dist_path}")

    plt.close(fig)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate calibration reliability diagrams")
    parser.add_argument("--before", type=str, default=None, help="Before calibration data JSON")
    parser.add_argument("--after", type=str, default=None, help="After calibration data JSON")
    parser.add_argument("--output", type=str, default="report/figures/calibration.png", help="Output PNG path")
    parser.add_argument("--title", type=str, default="Confidence Calibration Reliability", help="Plot title")
    return parser.parse_args()


def main():
    args = parse_args()

    before_path = Path(args.before) if args.before else None
    after_path = Path(args.after) if args.after else None
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    raw_confs, calibrated_confs, accuracies, _ = load_calibration_data(before_path, after_path)

    plot_reliability_diagram(raw_confs, calibrated_confs, accuracies, output_path, args.title)
    plot_confidence_distribution(raw_confs, calibrated_confs, output_path)

    raw_ece = compute_ece(raw_confs, accuracies)
    cal_ece = compute_ece(calibrated_confs, accuracies)

    result = {
        "before_ece": raw_ece,
        "after_ece": cal_ece,
        "improvement_ece": raw_ece - cal_ece,
        "num_samples": len(raw_confs),
    }

    result_path = output_path.parent / "calibration_results.json"
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nCalibration results: ECE {raw_ece:.3f} → {cal_ece:.3f} (improvement: {raw_ece - cal_ece:.3f})")


if __name__ == "__main__":
    main()
