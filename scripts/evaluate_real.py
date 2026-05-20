#!/usr/bin/env python3
"""Real-world evaluation on real RFQ annotations."""

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nlp.pipeline import NLPPipeline


def load_annotations(path):
    with open(path) as f:
        return json.load(f)


def span_f1(extracted, expected):
    """Compute span-level F1 for entities."""
    tp = fp = fn = 0
    ext_spans = {(e['start'], e['end'], e['type']) for e in extracted}
    exp_spans = {(e['start'], e['end'], e['type']) for e in expected}

    tp = len(ext_spans & exp_spans)
    fp = len(ext_spans - exp_spans)
    fn = len(exp_spans - ext_spans)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return precision, recall, f1


def main():
    real_dir = Path("data/real_rfqs/annotations")

    if not real_dir.exists():
        print("No real annotations found. Add annotated RFQs to data/real_rfqs/annotations/")
        print("Expected format: one JSON file with array of {doc_id, tokens, ner_tags}")
        return 0

    files = list(real_dir.glob("*.json"))
    if not files:
        print("No annotation files in data/real_rfqs/annotations/")
        return 0

    print("=== REAL-WORLD EVALUATION ===\n")

    pipeline = NLPPipeline()

    all_results = []
    entity_stats = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})

    for ann_file in files:
        data = load_annotations(ann_file)
        if isinstance(data, dict) or not isinstance(data, list):
            data = [data]

        for item in data:
            text = " ".join(item.get('tokens', []))
            doc_id = item.get('doc_id', ann_file.stem)

            result = pipeline.process(text)
            extracted = result.entities

            expected = []
            tokens = item.get('tokens', [])
            tags = item.get('ner_tags', [])
            start = 0
            i = 0
            while i < len(tags):
                tag = tags[i]
                if tag == 'O':
                    start += len(tokens[i]) + 1
                    i += 1
                    continue
                if tag.startswith('B-') or tag.startswith('S-'):
                    ent_type = tag[2:]
                    ent_start = start
                    ent_text = tokens[i]
                    j = i + 1
                    # Collect I- and E-tags for multi-token entities
                    while j < len(tags) and tags[j] in (f'I-{ent_type}', f'E-{ent_type}'):
                        ent_text += ' ' + tokens[j]
                        j += 1
                    ent_end = ent_start + len(ent_text)
                    expected.append({'text': ent_text, 'type': ent_type, 'start': ent_start, 'end': ent_end})
                    i = j
                    start = ent_end + 1
                else:
                    start += len(tokens[i]) + 1
                    i += 1

            p, r, f = span_f1(extracted, expected)
            all_results.append({'doc_id': doc_id, 'precision': p, 'recall': r, 'f1': f})

            for e in extracted:
                for exp in expected:
                    if (exp['start'], exp['end'], exp['type']) == (e['start'], e['end'], e['type']):
                        entity_stats[e['type']]['tp'] += 1
                        break
                else:
                    entity_stats[e['type']]['fp'] += 1

            for exp in expected:
                found = any(
                    e['start'] == exp['start'] and e['end'] == exp['end'] and e['type'] == exp['type']
                    for e in extracted
                )
                if not found:
                    entity_stats[exp['type']]['fn'] += 1

    if not all_results:
        print("No results computed")
        return 0

    macro_f1 = sum(r['f1'] for r in all_results) / len(all_results)
    micro_tp = sum(s['tp'] for s in entity_stats.values())
    micro_fp = sum(s['fp'] for s in entity_stats.values())
    micro_fn = sum(s['fn'] for s in entity_stats.values())
    micro_p = micro_tp / (micro_tp + micro_fp) if (micro_tp + micro_fp) > 0 else 0
    micro_r = micro_tp / (micro_tp + micro_fn) if (micro_tp + micro_fn) > 0 else 0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0

    print(f"Documents evaluated: {len(all_results)}")
    print(f"\nOverall Micro F1: {micro_f1:.4f}")
    print(f"Overall Macro F1: {macro_f1:.4f}")

    print("\n--- Per-Entity F1 ---")
    print(f"{'Entity':<12} {'Prec':>6} {'Rec':>6} {'F1':>6}")
    print("-" * 36)
    for ent_type in sorted(entity_stats.keys()):
        s = entity_stats[ent_type]
        tp, fp, fn = s['tp'], s['fp'], s['fn']
        p = tp / (tp + fp) if (tp + fp) > 0 else 0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0
        f = 2 * p * r / (p + r) if (p + r) > 0 else 0
        print(f"{ent_type:<12} {p:>6.3f} {r:>6.3f} {f:>6.3f}")

    metrics = {
        'micro_f1': micro_f1,
        'macro_f1': macro_f1,
        'documents': len(all_results),
        'per_entity': {
            k: {
                'precision': v['tp'] / (v['tp'] + v['fp']) if (v['tp'] + v['fp']) > 0 else 0,
                'recall': v['tp'] / (v['tp'] + v['fn']) if (v['tp'] + v['fn']) > 0 else 0,
                'tp': v['tp'], 'fp': v['fp'], 'fn': v['fn']
            }
            for k, v in entity_stats.items()
        },
        'document_results': all_results
    }

    out_path = Path("results/real_world_metrics_v2.json")
    with open(out_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\nSaved to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
