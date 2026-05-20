"""Active learning module for RFQ entity extraction.

Runs the current model on real RFQ PDFs, computes uncertainty scores
(entropy of softmax), and surfaces the most uncertain predictions
for human review.

Usage:
    python src/labeling/active_learner.py --rfqs data/real_rfqs/raw --output data/review_queue
"""

import argparse
import json
import sys
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

ENTROPY_CACHE: dict[str, float] = {}


def compute_entropy(probs: torch.Tensor) -> float:
    min_val = 1e-10
    probs = torch.clamp(probs, min=min_val, max=1.0 - min_val)
    entropy = -torch.sum(probs * torch.log(probs), dim=-1).item()
    return entropy


def load_ner_model(model_dir: str) -> tuple[Any, AutoTokenizer]:
    tokenizer = AutoTokenizer.from_pretrained("bert-base-cased")
    try:
        model = AutoModelForTokenClassification.from_pretrained(model_dir)
    except Exception:
        model = AutoModelForTokenClassification.from_pretrained(
            "bert-base-cased", num_labels=41
        )
    model.eval()
    return model, tokenizer


def extract_entities_with_uncertainty(
    text: str,
    model: Any,
    tokenizer: AutoTokenizer,
    id2label: dict[int, str],
) -> list[dict[str, Any]]:
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True,
    )
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    device = next(model.parameters()).device
    input_ids = input_ids.to(device)
    attention_mask = attention_mask.to(device)

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits

    probs = torch.softmax(logits, dim=-1)
    predictions = torch.argmax(logits, dim=-1)
    scores = torch.max(probs, dim=-1).values

    tokens = tokenizer.convert_ids_to_tokens(input_ids[0])
    word_ids = inputs.word_ids(batch_index=0)

    word_entities: dict[int, dict[str, Any]] = {}
    word_scores: dict[int, float] = defaultdict(list)
    word_preds: dict[int, int] = {}

    for token_idx, (token, pred_id, score, word_id) in enumerate(
        zip(tokens, predictions[0], scores[0], word_ids, strict=False)
    ):
        if word_id is None or token in ["[CLS]", "[SEP]", "[PAD]"]:
            continue

        label = id2label.get(pred_id.item(), "O")
        if label == "O":
            continue

        word_scores[word_id].append(score.item())
        if word_id not in word_preds or score.item() > word_scores[word_id][0]:
            word_preds[word_id] = pred_id.item()
            word_entities[word_id] = {
                "text": token.replace("##", ""),
                "type": label[2:] if label.startswith(("B-", "I-", "E-", "S-")) else label,
                "pred_id": pred_id.item(),
                "token_idx": token_idx,
            }

    results = []
    for word_id, entity in word_entities.items():
        token_probs = probs[0, entity["token_idx"]]
        entropy = compute_entropy(token_probs)

        avg_score = sum(word_scores[word_id]) / len(word_scores[word_id])
        uncertainty = 1.0 - avg_score + entropy * 0.1

        results.append({
            "text": entity["text"],
            "type": entity["type"],
            "pred_id": entity["pred_id"],
            "avg_score": avg_score,
            "entropy": entropy,
            "uncertainty": uncertainty,
            "word_id": word_id,
        })

    return results


def run_on_rfq(
    pdf_path: Path,
    model: Any,
    tokenizer: AutoTokenizer,
    id2label: dict[int, str],
    max_length: int = 200,
) -> list[dict[str, Any]]:
    try:
        import pdfplumber

        with pdfplumber.open(str(pdf_path)) as pdf:
            all_entities = []
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                words = page.extract_words() or []

                if not text.strip():
                    continue

                sentences = text.split(".")
                for _sent_idx, sentence in enumerate(sentences[:50]):
                    if len(sentence.strip()) < 10:
                        continue

                    entities = extract_entities_with_uncertainty(
                        sentence.strip(), model, tokenizer, id2label
                    )

                    for entity in entities:
                        page_width = page.width or 612
                        page_height = page.height or 792

                        bbox = None
                        for word in words:
                            if entity["text"].lower() in word.get("text", "").lower():
                                bbox = (
                                    word.get("x0", 0) / page_width,
                                    word.get("top", 0) / page_height,
                                    word.get("x1", page_width) / page_width,
                                    word.get("bottom", page_height) / page_height,
                                )
                                break

                        all_entities.append({
                            "text": entity["text"],
                            "type": entity["type"],
                            "uncertainty": entity["uncertainty"],
                            "score": entity["avg_score"],
                            "entropy": entity["entropy"],
                            "page": page_num,
                            "sentence": sentence.strip()[:200],
                            "bbox": bbox,
                        })

            return all_entities

    except Exception as e:
        print(f"Failed to process {pdf_path.name}: {e}")
        return []


def generate_review_tasks(
    all_entities: list[dict[str, Any]],
    top_n: int = 100,
    uncertainty_threshold: float = 0.3,
) -> list[dict[str, Any]]:
    sorted_entities = sorted(all_entities, key=lambda x: x["uncertainty"], reverse=True)

    review_tasks = []
    for entity in sorted_entities[:top_n]:
        if entity["uncertainty"] < uncertainty_threshold:
            continue

        task_id = str(uuid.uuid4())[:8]
        review_tasks.append({
            "task_id": task_id,
            "text": entity["text"],
            "type": entity["type"],
            "predicted_type": entity["type"],
            "sentence": entity["sentence"],
            "page": entity["page"],
            "uncertainty": round(entity["uncertainty"], 4),
            "score": round(entity["score"], 4),
            "entropy": round(entity["entropy"], 4),
            "status": "pending",
            "reviewer_notes": "",
        })

    return review_tasks


def save_review_queue(review_tasks: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    queue_path = output_dir / "review_queue.json"
    existing = []
    if queue_path.exists():
        with open(queue_path) as f:
            existing = json.load(f)

    existing_ids = {t["task_id"] for t in existing}
    new_tasks = [t for t in review_tasks if t["task_id"] not in existing_ids]

    combined = existing + new_tasks
    combined = sorted(combined, key=lambda x: x["uncertainty"], reverse=True)

    with open(queue_path, "w") as f:
        json.dump(combined, f, indent=2)

    print(f"Saved {len(new_tasks)} new review tasks ({len(combined)} total)")


def generate_stats(review_tasks: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    if not review_tasks:
        return {}

    stats = {
        "total_tasks": len(review_tasks),
        "by_type": {},
        "by_source": {},
        "uncertainty_histogram": {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0,
        },
        "avg_uncertainty": sum(t["uncertainty"] for t in review_tasks) / len(review_tasks),
    }

    for task in review_tasks:
        entity_type = task["type"]
        stats["by_type"][entity_type] = stats["by_type"].get(entity_type, 0) + 1

        unc = task["uncertainty"]
        if unc < 0.2:
            stats["uncertainty_histogram"]["0.0-0.2"] += 1
        elif unc < 0.4:
            stats["uncertainty_histogram"]["0.2-0.4"] += 1
        elif unc < 0.6:
            stats["uncertainty_histogram"]["0.4-0.6"] += 1
        elif unc < 0.8:
            stats["uncertainty_histogram"]["0.6-0.8"] += 1
        else:
            stats["uncertainty_histogram"]["0.8-1.0"] += 1

    stats_path = output_dir / "review_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    print("\nReview queue stats:")
    print(f"  Total tasks: {stats['total_tasks']}")
    print(f"  Average uncertainty: {stats['avg_uncertainty']:.4f}")
    print(f"  By entity type: {stats['by_type']}")

    return stats


def parse_args():
    parser = argparse.ArgumentParser(description="Active learning for RFQ entity extraction")
    parser.add_argument("--rfqs", type=str, default="data/real_rfqs/raw", help="Directory with RFQ PDFs")
    parser.add_argument("--output", type=str, default="data/review_queue", help="Output directory for review tasks")
    parser.add_argument("--model", type=str, default="models/ner-bert-bilstm-crf-v1", help="Model directory")
    parser.add_argument("--top-n", type=int, default=100, help="Number of top uncertain predictions to surface")
    parser.add_argument("--threshold", type=float, default=0.3, help="Uncertainty threshold")
    return parser.parse_args()


ID2LABEL = {
    i: label for i, label in enumerate(
        ["O"] + [f"{p}-{t}" for t in ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"]
        for p in ["B", "I", "E", "S"]]
    )
}


class ActiveLearner:
    def score_uncertainty(self, predictions: list[dict], method: str = "entropy") -> float:
        if not predictions:
            return 0.0

        if method == "entropy":
            probs = []
            for p in predictions:
                conf = p.get("confidence", 0.5)
                probs.append(conf)

            probs_arr = np.array(probs)
            probs_arr = probs_arr / probs_arr.sum() if probs_arr.sum() > 0 else probs_arr + 1 / len(probs_arr)
            entropy = -np.sum(probs_arr * np.log(probs_arr + 1e-10))
            return entropy

        elif method == "margin":
            confs = sorted([p.get("confidence", 0.5) for p in predictions], reverse=True)
            if len(confs) < 2:
                return 1.0
            return confs[0] - confs[1]

        return 0.0

    def rank_documents(self, predictions_per_doc: dict[str, list[dict]]) -> list[tuple[str, float]]:
        scores = {}
        for doc_id, preds in predictions_per_doc.items():
            scores[doc_id] = self.score_uncertainty(preds)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def sample_for_review(self, predictions_per_doc: dict[str, list[dict]], n: int = 100) -> list[str]:
        ranked = self.rank_documents(predictions_per_doc)
        return [doc_id for doc_id, _ in ranked[:n]]

    def export_to_review_queue(self, samples: list[dict], output_dir: Path = Path("data/review_queue")):
        output_dir.mkdir(parents=True, exist_ok=True)
        for i, sample in enumerate(samples):
            with open(output_dir / f"sample_{i:04d}.json", "w") as f:
                json.dump(sample, f, indent=2)


def main():
    args = parse_args()
    rfqs_dir = Path(args.rfqs)
    output_dir = Path(args.output)

    if not rfqs_dir.exists():
        print(f"RFQs directory not found: {rfqs_dir}")
        print("Run scripts/scrape_etenders.py first to collect real RFQ PDFs")
        sys.exit(1)

    print(f"Loading model from {args.model}...")
    model, tokenizer = load_ner_model(args.model)

    all_entities = []

    pdf_files = list(rfqs_dir.glob("*.pdf"))
    print(f"Processing {len(pdf_files)} RFQ PDFs...")

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")
        entities = run_on_rfq(pdf_path, model, tokenizer, ID2LABEL)
        for entity in entities:
            entity["source_file"] = pdf_path.name
        all_entities.extend(entities)
        print(f"  Found {len(entities)} entities")

    if not all_entities:
        print("No entities extracted! Check model and input PDFs.")
        sys.exit(1)

    review_tasks = generate_review_tasks(all_entities, args.top_n, args.threshold)
    save_review_queue(review_tasks, output_dir)
    generate_stats(review_tasks, output_dir)

    print("\nActive learning complete!")
    print("Run: streamlit run ui/annotate.py to review tasks")


if __name__ == "__main__":
    main()
