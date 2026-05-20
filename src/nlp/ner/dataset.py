"""NER Dataset class for BIOES token classification."""

import json
from pathlib import Path

import torch
from torch.utils.data import Dataset
from transformers import PreTrainedTokenizer


class NERDataset(Dataset):
    def __init__(
        self,
        data_path: str | Path,
        tokenizer: PreTrainedTokenizer,
        max_length: int = 512,
        label2id: dict[str, int] | None = None,
    ):
        self.data_path = Path(data_path)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.label2id = label2id or {}

        self.examples = self._load_data()

    def _load_data(self) -> list[dict]:
        if self.data_path.suffix == ".json":
            with open(self.data_path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return [data]
        elif self.data_path.suffix == ".jsonl":
            examples = []
            with open(self.data_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        examples.append(json.loads(line))
            return examples
        return []

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        example = self.examples[idx]

        tokens = example.get("tokens", [])
        tags = example.get("labels") or example.get("ner_tags") or example.get("tags", [])

        encoding = self.tokenizer(
            tokens,
            is_split_into_words=True,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
        )

        input_ids = encoding["input_ids"][0]
        attention_mask = encoding["attention_mask"][0]

        label_ids = self._align_labels(tags, encoding.word_ids(batch_index=0))

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": label_ids,
        }

    def _align_labels(
        self,
        tags: list[str],
        word_ids: list[int | None],
    ) -> torch.Tensor:
        label_ids = torch.full((self.max_length,), -100, dtype=torch.long)
        previous_word_id = None
        for token_index, word_id in enumerate(word_ids[: self.max_length]):
            if word_id is None:
                previous_word_id = word_id
                continue
            if word_id != previous_word_id and word_id < len(tags):
                label_ids[token_index] = self.label2id.get(tags[word_id], self.label2id.get("O", 0))
            previous_word_id = word_id

        return label_ids


def create_dataset(
    data_path: str | Path,
    tokenizer: PreTrainedTokenizer,
    max_length: int = 512,
    label2id: dict[str, int] | None = None,
) -> NERDataset:
    return NERDataset(
        data_path=data_path,
        tokenizer=tokenizer,
        max_length=max_length,
        label2id=label2id,
    )
