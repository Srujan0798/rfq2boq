"""Sub-domain NER model router - building, road, bridge, electrical, plumbing."""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class ProjectType(StrEnum):
    BUILDING = "building"
    ROAD = "road"
    BRIDGE = "bridge"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    GENERAL = "general"


PROJECT_TYPE_KEYWORDS = {
    ProjectType.BUILDING: [
        "building",
        "residential",
        "commercial",
        "apartment",
        "office",
        "hospital",
        "school",
        "hospital",
        "floor",
        "column",
        "beam",
        "slab",
        "wall",
        "foundation",
    ],
    ProjectType.ROAD: [
        "road",
        "highway",
        "pavement",
        "asphalt",
        "bitumen",
        "crusher",
        "granular",
        "subgrade",
        "pavement",
        "lane",
        "carriageway",
        "shoulder",
        "median",
    ],
    ProjectType.BRIDGE: [
        "bridge",
        "flyover",
        "culvert",
        "abutment",
        "pier",
        "girder",
        "span",
        "foundation",
        "pile",
        "precast",
        "launching",
        "segmental",
    ],
    ProjectType.ELECTRICAL: [
        "electrical",
        "cable",
        "wire",
        "conduit",
        "switch",
        "socket",
        "db",
        "panel",
        "transformer",
        "generator",
        "lighting",
        "earthing",
        "mcb",
        "mccb",
    ],
    ProjectType.PLUMBING: [
        "plumbing",
        "pipe",
        "pvc",
        "cpvc",
        "gi",
        "water",
        "drain",
        "sewage",
        "sanitary",
        "fixture",
        "tap",
        "valve",
        "pump",
        "tank",
        "cistern",
    ],
}


class ProjectTypeClassifier:
    def __init__(self):
        self._model = None

    def classify(self, text: str) -> tuple[ProjectType, float]:
        text_lower = text.lower()

        scores: dict[ProjectType, float] = {pt: 0.0 for pt in ProjectType}

        for pt, keywords in PROJECT_TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    scores[pt] += 1

        if max(scores.values()) == 0:
            return ProjectType.GENERAL, 0.5

        best_type = max(scores, key=lambda k: scores.get(k, 0))
        total_kw = sum(scores.values())
        confidence = scores[best_type] / max(total_kw, 1)

        return best_type, float(confidence)

    def classify_batch(self, texts: list[str]) -> list[tuple[ProjectType, float]]:
        return [self.classify(text) for text in texts]


MODEL_DIRS = {
    ProjectType.BUILDING: "models/building-ner",
    ProjectType.ROAD: "models/roads-highways-ner",
    ProjectType.BRIDGE: "models/bridges-ner",
    ProjectType.ELECTRICAL: "models/electrical-ner",
    ProjectType.PLUMBING: "models/plumbing-ner",
    ProjectType.GENERAL: "models/ner-bert-bilstm-crf-v1",
}


class DomainModelRouter:
    def __init__(self, use_subdomain: bool = True):
        self.use_subdomain = use_subdomain
        self.classifier = ProjectTypeClassifier()
        self._models: dict[ProjectType, Any] = {}
        self._fallback_model = None

    def get_model_for_project(self, project_text: str | None = None) -> str:
        if not self.use_subdomain or not project_text:
            return MODEL_DIRS[ProjectType.GENERAL]

        project_type, confidence = self.classifier.classify(project_text)

        if confidence < 0.3:
            return MODEL_DIRS[ProjectType.GENERAL]

        return MODEL_DIRS.get(project_type, MODEL_DIRS[ProjectType.GENERAL])

    def get_model_for_type(self, project_type: ProjectType) -> str:
        return MODEL_DIRS.get(project_type, MODEL_DIRS[ProjectType.GENERAL])

    def route_extraction(
        self,
        text: str,
        model_path: str | None = None,
    ) -> dict[str, Any]:
        if model_path is None:
            model_path = self.get_model_for_project(text)

        return {
            "project_type": self.classifier.classify(text)[0].value,
            "model_path": model_path,
            "confidence": self.classifier.classify(text)[1],
        }

    def preload_models(self) -> None:
        for project_type, model_dir in MODEL_DIRS.items():
            path = model_dir
            if path and path != MODEL_DIRS[ProjectType.GENERAL]:
                from pathlib import Path

                if Path(model_dir).exists():
                    logger.info(f"Preloading model for {project_type}: {model_dir}")


class DomainRouter:
    """Router to direct input to appropriate specialized model."""

    def __init__(self):
        self._classifier = None
        self._domain_models: dict[str, str] = {}

    def set_classifier(self, classifier):
        self._classifier = classifier

    def register_domain_model(self, project_type: str, model_path: str):
        """Register a specialized model for a project type."""
        self._domain_models[project_type] = model_path

    def route(self, text: str) -> dict[str, Any]:
        """Route text to appropriate model and return result."""
        if self._classifier is None:
            from src.nlp.project_classifier import ProjectTypeClassifier

            self._classifier = ProjectTypeClassifier()

        classification = self._classifier.classify(text)
        project_type = classification["project_type"]

        model_path = self._domain_models.get(project_type)

        return {
            "project_type": project_type,
            "confidence": classification["confidence"],
            "model_path": model_path,
            "routing": "specialized" if model_path else "general",
        }

    def get_model_for_type(self, project_type: str) -> str | None:
        """Get model path for project type."""
        return self._domain_models.get(project_type)

    def list_available_domains(self) -> list[str]:
        """List all registered domain models."""
        return list(self._domain_models.keys())


def get_best_model(text: str) -> str:
    router = DomainModelRouter()
    return router.get_model_for_project(text)


def classify_project(text: str) -> ProjectType:
    classifier = ProjectTypeClassifier()
    return classifier.classify(text)[0]
