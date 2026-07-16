"""Manual review queue routes for low-confidence extraction items."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from config.settings import settings
from fastapi import APIRouter

router = APIRouter(tags=["review"])

QUEUE_PATH = settings.DATA_DIR / "review_queue.json"


@router.get("/v1/review-queue")
async def get_review_queue() -> dict[str, list[dict[str, Any]]]:
    return {"items": _load_queue()}


@router.post("/v1/review-queue")
async def add_review_item(item: dict[str, Any]) -> dict[str, Any]:
    queue = _load_queue()
    queue.append(item)
    _save_queue(queue)
    return {"status": "queued", "count": len(queue)}


def _load_queue(path: Path = QUEUE_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_queue(queue: list[dict[str, Any]], path: Path = QUEUE_PATH) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(queue, indent=2), encoding="utf-8")
