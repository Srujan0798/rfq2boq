"""JSON output formatter."""

import json as json_module

from src.domain.models import ExtractionResult


class JSONFormatter:
    def format(self, result: ExtractionResult) -> str:
        return json_module.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False)

    def format_to_string(self, result: ExtractionResult) -> str:
        return self.format(result)
