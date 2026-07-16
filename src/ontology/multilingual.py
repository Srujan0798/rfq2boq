"""Multilingual ontology for Hindi, Tamil, Marathi support.

Provides translations for materials, standards, and units per language.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


MATERIAL_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {},
    "hi": {
        "cement": "सीमेंट",
        "concrete": "कंक्रीट",
        "steel": "इस्पात",
        "brick": "ईंट",
        "sand": "रेत",
        "aggregate": "aggregate",
        "paint": "पेंट",
        "tile": "टाइल",
        "pipe": "पाइप",
    },
    "ta": {
        "cement": "சement",
        "concrete": "கான்கிரீட்",
        "steel": "இரும்பு",
        "brick": "ச Brick",
        "sand": "மணல்",
        "aggregate": "aggregate",
        "paint": "வண்ணம்",
        "tile": "டைல்",
        "pipe": "குழாய்",
    },
    "mr": {
        "cement": "सीमेंट",
        "concrete": "काँक्रीट",
        "steel": "स्टील",
        "brick": "विस्तू",
        "sand": "विट",
        "aggregate": "aggregate",
        "paint": "रंग",
        "tile": "टाइल",
        "pipe": "पाइप",
    },
}

STANDARD_TRANSLATIONS: dict[str, dict[str, str]] = {
    "hi": {
        "IS 456": "आईएस 456",
        "IS 516": "आईएस 516",
        "IS 800": "आईएस 800",
    },
    "ta": {
        "IS 456": "ஐஎஸ் 456",
        "IS 516": "ஐஎஸ் 516",
        "IS 800": "ஐஎஸ் 800",
    },
    "mr": {
        "IS 456": "आयएस 456",
        "IS 516": "आयएस 516",
        "IS 800": "आयएस 800",
    },
}

UNIT_TRANSLATIONS: dict[str, dict[str, str]] = {
    "hi": {
        "m³": "घन मीटर",
        "m²": "वर्ग मीटर",
        "kg": "किलोग्राम",
        "no.": "संख्या",
    },
    "ta": {
        "m³": "கன மீட்டர்",
        "m²": "சதுர மீட்டர்",
        "kg": "கிலோகிராம்",
        "no.": "எண்",
    },
    "mr": {
        "m³": "घन मीटर",
        "m²": "चौरस मीटर",
        "kg": "किलोग्राम",
        "no.": "संख्या",
    },
}


class MultilingualOntology:
    def __init__(self, ontology_dir: str | Path | None = None):
        self.ontology_dir = Path(ontology_dir) if ontology_dir else None
        self._materials: dict[str, list[dict[str, Any]]] = {}
        self._standards: dict[str, list[dict[str, Any]]] = {}
        self._units: dict[str, list[dict[str, Any]]] = {}
        self._load_ontologies()

    def _load_ontologies(self) -> None:
        if self.ontology_dir and self.ontology_dir.exists():
            for lang in ["hi", "ta", "mr"]:
                materials_file = self.ontology_dir / f"materials_{lang}.json"
                if materials_file.exists():
                    try:
                        with open(materials_file, encoding="utf-8") as f:
                            self._materials[lang] = json.load(f).get("materials", [])
                    except Exception:
                        self._materials[lang] = []
        else:
            self._materials = {lang: [] for lang in ["hi", "ta", "mr"]}

    def translate_material(self, material: str, target_lang: str) -> str:
        if target_lang == "en":
            return material

        mat_lower = material.lower()
        if target_lang in MATERIAL_TRANSLATIONS and mat_lower in MATERIAL_TRANSLATIONS[target_lang]:
            return MATERIAL_TRANSLATIONS[target_lang][mat_lower]
        return material

    def translate_standard(self, standard: str, target_lang: str) -> str:
        if target_lang == "en":
            return standard

        if target_lang in STANDARD_TRANSLATIONS and standard in STANDARD_TRANSLATIONS[target_lang]:
            return STANDARD_TRANSLATIONS[target_lang][standard]
        return standard

    def translate_unit(self, unit: str, target_lang: str) -> str:
        if target_lang == "en":
            return unit

        if target_lang in UNIT_TRANSLATIONS and unit in UNIT_TRANSLATIONS[target_lang]:
            return UNIT_TRANSLATIONS[target_lang][unit]
        return unit

    def get_materials_for_lang(self, lang: str) -> list[dict[str, Any]]:
        return self._materials.get(lang, [])

    def find_material_alias(self, query: str, lang: str) -> str | None:
        if lang == "en":
            return None

        query_lower = query.lower()
        materials = self._materials.get(lang, [])

        for material in materials:
            if material.get("name", "").lower() == query_lower:
                return material.get("name")
            for alias in material.get("aliases", []):
                if alias.lower() == query_lower:
                    return material.get("name")

        return None


def translate_boq_to_lang(boq_items: list[dict[str, Any]], target_lang: str) -> list[dict[str, Any]]:
    ontology = MultilingualOntology()
    translated = []

    for item in boq_items:
        new_item = item.copy()

        if target_lang != "en":
            new_item["material"] = ontology.translate_material(item.get("material", ""), target_lang)
            new_item["grade"] = ontology.translate_standard(item.get("grade", ""), target_lang)
            new_item["unit"] = ontology.translate_unit(item.get("unit", ""), target_lang)
            if item.get("description_raw"):
                new_item["description_raw"] = ontology.translate_material(item.get("description_raw", ""), target_lang)

        translated.append(new_item)

    return translated
