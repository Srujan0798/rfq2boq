"""Small file-backed result store for API jobs."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from config.settings import settings
from src.domain.models import ExtractionResult


class ResultStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (settings.DATA_DIR / "jobs")
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, result: ExtractionResult) -> None:
        path = self.root / f"{result.doc_id}.json"
        path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    def get(self, job_id: str) -> ExtractionResult | None:
        path = self.root / f"{job_id}.json"
        if not path.exists():
            return None
        return ExtractionResult.model_validate_json(path.read_text(encoding="utf-8"))

    def save_job_status(self, job_id: str, status: str, result: ExtractionResult | None = None) -> None:
        job_path = self.root / f"{job_id}.json"
        data = {
            "job_id": job_id,
            "status": status,
            "created_at": datetime.now(UTC).isoformat(),
        }
        if result:
            data["result"] = json.loads(result.model_dump_json())
        job_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_job(self, job_id: str) -> dict | None:
        path = self.root / f"{job_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def cleanup_old_jobs(self, hours: int = 24) -> int:
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        count = 0
        for job_file in self.root.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(job_file.stat().st_mtime, tz=UTC)
                if mtime < cutoff:
                    job_file.unlink()
                    count += 1
            except Exception:
                pass
        return count


result_store = ResultStore()
