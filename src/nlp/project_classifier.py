"""Project type classifier for RFQ routing to specialized models."""

from typing import Any

PROJECT_TYPES = [
    "building",
    "road",
    "bridge",
    "electrical",
    "plumbing",
    "water_treatment",
    "industrial",
    "unknown",
]

KEYWORDS = {
    "building": [
        "building",
        "residential",
        "commercial",
        "apartment",
        "office",
        "school",
        "hospital",
        "rcc",
        "foundation",
        "floor",
        "ceiling",
        "wall",
        "plaster",
    ],
    "road": [
        "road",
        "highway",
        "pavement",
        "carriageway",
        "embankment",
        "subgrade",
        "wbm",
        "bm",
        "dbc",
        "pc",
        "km",
        "stone",
        "aggregate",
    ],
    "bridge": ["bridge", "girder", "pier", "abutment", "deck", "span", "prestress", "psc", "box"],
    "electrical": [
        "electrical",
        "wiring",
        "cable",
        "conduit",
        "switch",
        "fixture",
        "load",
        "ampere",
        "voltage",
        "transformer",
    ],
    "plumbing": ["plumbing", "pipe", "gi", "pvc", "cistern", "faucet", "drain", "sewage", "water supply", "sanitary"],
    "water_treatment": ["wtp", "sewage", "treatment", "filter", "pump", "tank", "clarifier", "stp"],
    "industrial": ["industrial", "factory", "warehouse", "plant", "machinery", "crane", "hoist"],
}


def classify_project_type(text: str) -> str:
    """Classify project type from RFQ text."""
    text_lower = text.lower()
    scores = {}

    for ptype, keywords in KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[ptype] = score

    if max(scores.values()) == 0:
        return "unknown"

    return max(scores, key=lambda k: scores.get(k, 0))


class ProjectTypeClassifier:
    """Classify RFQ into project types for routing to specialized models."""

    def __init__(self):
        self._history: list[dict[str, Any]] = []

    def classify(self, text: str) -> dict[str, Any]:
        """Classify project type with confidence."""
        ptype = classify_project_type(text)

        text_lower = text.lower()
        scores = {}
        for p, keywords in KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[p] = score

        total = sum(scores.values())
        confidence = scores.get(ptype, 0) / max(total, 1)

        result = {
            "project_type": ptype,
            "confidence": confidence,
            "all_scores": scores,
        }

        self._history.append(result)
        return result

    @property
    def history(self) -> list[dict]:
        return self._history
