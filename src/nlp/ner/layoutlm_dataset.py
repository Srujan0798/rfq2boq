"""LayoutLM dataset for token classification with bounding boxes."""

import json
from pathlib import Path
from typing import Any

from torch.utils.data import Dataset


class LayoutLMDataset(Dataset):
    """Dataset for LayoutLMv3 token classification with bboxes."""

    def __init__(
        self,
        json_path: str,
        model_name: str = "microsoft/layoutlmv3-base",
        max_length: int = 512,
        label2id: dict[str, int] | None = None,
    ):
        self.json_path = Path(json_path)
        self.max_length = max_length
        self.model_name = model_name
        self.label2id = label2id or {}
        self.examples = self._load_examples()

    def _load_examples(self) -> list[dict[str, Any]]:
        """Load examples from JSON file."""
        if not self.json_path.exists():
            return []
        with open(self.json_path) as f:
            data = json.load(f)
        return data if isinstance(data, list) else []

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        example = self.examples[idx]
        return {
            "tokens": example.get("tokens", []),
            "bboxes": example.get("bboxes", []),
            "labels": example.get("labels", []),
        }

    @staticmethod
    def collate_fn(batch: list[dict[str, Any]]) -> dict[str, Any]:
        """Collate function for DataLoader."""
        tokens = [item["tokens"] for item in batch]
        bboxes = [item["bboxes"] for item in batch]
        labels = [item["labels"] for item in batch]
        return {
            "tokens": tokens,
            "bboxes": bboxes,
            "labels": labels,
        }


class LayoutLMNERDataset(LayoutLMDataset):
    """Alias for LayoutLMDataset for backwards compatibility."""


def create_layoutlm_dataset(
    data_dir: str,
    split: str = "train",
    model_name: str = "microsoft/layoutlmv3-base",
) -> LayoutLMDataset:
    """Create LayoutLM dataset from directory."""
    json_path = Path(data_dir) / f"{split}.json"
    return LayoutLMDataset(str(json_path), model_name=model_name)
