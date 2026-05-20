"""Review router for active learning based on uncertainty.

Routes entities with high uncertainty to human review queue.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ReviewTask:
    task_id: str
    text: str
    entity_text: str
    entity_type: str
    calibrated_confidence: float
    epistemic_uncertainty: float
    needs_review: bool
    priority: str
    source_file: str = ""


class ReviewRouter:
    def __init__(
        self,
        uncertainty_threshold: float = 0.15,
        confidence_threshold: float = 0.6,
        review_queue_path: str | Path = "data/review_queue/uncertain_entities.json",
    ):
        self.uncertainty_threshold = uncertainty_threshold
        self.confidence_threshold = confidence_threshold
        self.review_queue_path = Path(review_queue_path)
        self.review_queue_path.parent.mkdir(parents=True, exist_ok=True)

    def route_entities(
        self,
        entities: list[dict],
        text: str,
        source_file: str = "",
    ) -> list[ReviewTask]:
        tasks = []

        for entity in entities:
            needs_review = entity.get("needs_review", False)
            calibrated_conf = entity.get("calibrated_confidence", 0.0)
            epistemic_unc = entity.get("epistemic_uncertainty", 0.0)

            if calibrated_conf < self.confidence_threshold:
                needs_review = True

            if epistemic_unc > self.uncertainty_threshold:
                needs_review = True

            priority = "low"
            if calibrated_conf < 0.4 or epistemic_unc > 0.25:
                priority = "high"
            elif calibrated_conf < 0.6 or epistemic_unc > 0.15:
                priority = "medium"

            if needs_review:
                import uuid
                task_id = str(uuid.uuid4())[:8]

                task = ReviewTask(
                    task_id=task_id,
                    text=text[:200],
                    entity_text=entity.get("text", ""),
                    entity_type=entity.get("type", "O"),
                    calibrated_confidence=calibrated_conf,
                    epistemic_uncertainty=epistemic_unc,
                    needs_review=needs_review,
                    priority=priority,
                    source_file=source_file,
                )
                tasks.append(task)

        return tasks

    def save_to_queue(self, tasks: list[ReviewTask]) -> int:
        existing = []
        if self.review_queue_path.exists():
            with open(self.review_queue_path) as f:
                existing = json.load(f)

        existing_ids = {t.get("task_id") for t in existing}
        new_tasks = [t for t in tasks if t.task_id not in existing_ids]

        for task in tasks:
            existing.append({
                "task_id": task.task_id,
                "text": task.text,
                "entity_text": task.entity_text,
                "entity_type": task.entity_type,
                "calibrated_confidence": task.calibrated_confidence,
                "epistemic_uncertainty": task.epistemic_uncertainty,
                "needs_review": task.needs_review,
                "priority": task.priority,
                "source_file": task.source_file,
                "status": "pending",
            })

        existing = sorted(existing, key=lambda x: (
            {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", "low"), 2),
            x.get("calibrated_confidence", 0),
        ))

        with open(self.review_queue_path, "w") as f:
            json.dump(existing, f, indent=2)

        return len(new_tasks)

    def get_queue_stats(self) -> dict[str, Any]:
        if not self.review_queue_path.exists():
            return {"total": 0, "pending": 0, "reviewed": 0, "by_priority": {}}

        with open(self.review_queue_path) as f:
            tasks = json.load(f)

        pending = [t for t in tasks if t.get("status") == "pending"]
        reviewed = [t for t in tasks if t.get("status") != "pending"]

        by_priority = {"high": 0, "medium": 0, "low": 0}
        for task in pending:
            priority = task.get("priority", "low")
            by_priority[priority] = by_priority.get(priority, 0) + 1

        return {
            "total": len(tasks),
            "pending": len(pending),
            "reviewed": len(reviewed),
            "by_priority": by_priority,
        }


def route_extraction_to_review(
    entities: list[dict],
    text: str,
    source_file: str = "",
) -> list[ReviewTask]:
    router = ReviewRouter()
    return router.route_entities(entities, text, source_file)
