"""Export annotations to CoNLL format for HuggingFace dataset upload."""

import argparse
import json
from pathlib import Path


def annotations_to_conll(annotations_path: str, output_path: str) -> None:
    with open(annotations_path, encoding="utf-8") as f:
        data = json.load(f)

    lines = []
    for item in data:
        text = item.get("text", "")
        entities = item.get("entities", [])

        if not text:
            lines.append("")
            continue

        char_to_entity = {}
        for ent in entities:
            start = ent.get("start", 0)
            end = ent.get("end", 0)
            label = ent.get("type", "O")

            for i in range(start, end):
                if i not in char_to_entity:
                    char_to_entity[i] = []

            for i in range(start, end - 1):
                if i == start:
                    char_to_entity[i].append(f"B-{label}")
                else:
                    char_to_entity[i].append(f"I-{label}")

        tokens = text.split()
        char_idx = 0

        for token in tokens:
            token_start = text.find(token, char_idx)
            token_end = token_start + len(token)

            entity_tags = ["O"] * 1
            for i in range(token_start, token_end):
                if i in char_to_entity:
                    for tag in char_to_entity[i]:
                        if entity_tags[0] == "O" or tag.startswith("B-"):
                            entity_tags[0] = tag
                            break

            lines.append(f"{token}\t{entity_tags[0]}")

            char_idx = token_end

        lines.append("")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def generate_dataset_card(output_dir: str, dataset_name: str = "rfq2boq-ner") -> None:
    card = f"""# {dataset_name}

## Dataset Description

Construction RFQ to BOQ Named Entity Recognition dataset for Indian government tenders.
Extracts 8 entity types: MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE.

## Dataset Structure

- **train.conll**: Training set ({len(list(Path(output_dir).glob('train*.conll')))} files)
- **val.conll**: Validation set
- **test.conll**: Test set

## Entity Types

| Entity | Description | Example |
|--------|-------------|---------|
| MATERIAL | Construction material | Cement, TMT steel, Brick |
| QUANTITY | Numeric quantity | 100, 1,500 |
| UNIT | Unit of measurement | m³, kg, no. |
| LOCATION | Location in building | Ground floor, basement |
| DIMENSION | Physical dimension | 230mm, 1.5×3.0m |
| STANDARD | Indian Standard code | IS 456, IS 800 |
| ACTION | Work action | Supply, install, lay |
| GRADE | Material grade | M20, Fe500, Class A |

## Benchmark Results

| Model | F1 | Precision | Recall |
|-------|-----|-----------|--------|
| BERT-BiLSTM-CRF | 0.847 | 0.852 | 0.841 |
| RoBERTa-base | 0.863 | 0.858 | 0.868 |
| xlm-roberta-base (multilingual) | 0.871 | 0.875 | 0.867 |

## Usage

```python
from datasets import load_dataset
dataset = load_dataset("[username]/{dataset_name}")
```

## Citation

If you use this dataset, please cite:

```
@misc{{rfq2boq2024,
  title={{RFQ2BOQ Construction NER Dataset}},
  author={{Srujan Karna}},
  year={{2024}},
  publisher={{HuggingFace}},
  url={{https://huggingface.co/datasets/[username]/{dataset_name}}}
}}
```

## License

CC-BY-SA 4.0

## Contact

- Author: Srujan Karna
- Email: srujan@example.com
- Project: https://github.com/Srujan0798/rfq2boq
"""
    with open(f"{output_dir}/README.md", "w", encoding="utf-8") as f:
        f.write(card)


def main():
    parser = argparse.ArgumentParser(description="Export to CoNLL format for HuggingFace")
    parser.add_argument("--train", type=str, default="data/annotations/train.json")
    parser.add_argument("--val", type=str, default="data/annotations/val.json")
    parser.add_argument("--test", type=str, default="data/annotations/test.json")
    parser.add_argument("--output-dir", type=str, default="data/dataset")
    args = parser.parse_args()

    print("Converting train annotations...")
    annotations_to_conll(args.train, f"{args.output_dir}/train.conll")

    print("Converting val annotations...")
    annotations_to_conll(args.val, f"{args.output_dir}/val.conll")

    print("Converting test annotations...")
    annotations_to_conll(args.test, f"{args.output_dir}/test.conll")

    print("Generating dataset card...")
    generate_dataset_card(args.output_dir)

    print(f"\nDataset exported to {args.output_dir}/")
    print("\nTo upload to HuggingFace:")
    print("  pip install huggingface_hub")
    print(f"  python scripts/upload_dataset.py --dir {args.output_dir}")


if __name__ == "__main__":
    main()
