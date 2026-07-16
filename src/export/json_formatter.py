"""JSON output formatter."""

import json as json_module
import logging

from src.domain.models import ExtractionResult

logger = logging.getLogger(__name__)

# P3_04: schema version is bumped when the BOQ JSON shape changes.
# v1.1.0 adds typed ``flags`` arrays on document + rows.  v1.0.0
# (the original schema/boq.v1.json baseline) is preserved here as
# a reference — the JSONFormatter always emits v1.1.0-or-later and
# the schema_version field lets consumers detect the upgrade.
BOQ_JSON_SCHEMA_VERSION = "1.1.0"


class JSONFormatter:
    def format(self, result: ExtractionResult) -> str:
        filtered_items = []
        for item in result.boq_items:
            if hasattr(item, "validate"):
                errs = item.validate()
                if errs:
                    logger.warning("Skipping invalid BOQ row %s: %s", getattr(item, "item_no", "?"), errs)
                    continue
            filtered_items.append(item)

        result_copy = result.model_copy(update={"boq_items": filtered_items})
        payload = result_copy.model_dump(mode="json")
        # P3_04: stamp every payload with the current schema version
        # so consumers (UI, tests) can detect the v1.1.0+ shape.
        # Top-level placement matches the spec's "keep a
        # schema_version field" gotcha.
        if isinstance(payload, dict):
            payload.setdefault("schema_version", BOQ_JSON_SCHEMA_VERSION)
            # Document-level flags: hoist extraction_metadata.warnings
            # + any flags that aren't row-attached.  Row-attached
            # flags are already inside each item["flags"].
            metadata = payload.get("metadata") or {}
            if "warnings" in metadata and "flags" not in metadata:
                # Preserve the legacy warnings as a string list and
                # also expose the typed flags array (initially empty
                # until the pipeline migrates producers to attach
                # FlagStore metadata).
                metadata.setdefault("flags", [])
        return json_module.dumps(payload, indent=2, ensure_ascii=False)

    def format_to_string(self, result: ExtractionResult) -> str:
        return self.format(result)
