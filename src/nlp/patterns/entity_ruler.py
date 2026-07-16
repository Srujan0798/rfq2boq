"""spaCy EntityRuler for structured entity patterns."""

import json
from pathlib import Path

import spacy
from spacy.pipeline import EntityRuler


class ConstructionEntityRuler:
    def __init__(self, ontology_dir: str | None = None):
        self.ontology_dir = Path(ontology_dir) if ontology_dir else None
        self.nlp = spacy.blank("en")
        self.ruler: EntityRuler | None = None
        self._patterns: list[dict] = []

    def build_patterns(self) -> list[dict]:
        patterns = []

        if self.ontology_dir and self.ontology_dir.exists():
            materials_file = self.ontology_dir / "materials.json"
            if materials_file.exists():
                with open(materials_file, encoding="utf-8") as f:
                    data = json.load(f)
                    materials = data.get("materials", data if isinstance(data, list) else [])
                    for mat in materials:
                        if mat.get("name"):
                            patterns.append(
                                {
                                    "label": "MATERIAL",
                                    "pattern": mat["name"],
                                }
                            )
                        for alias in mat.get("aliases", []):
                            patterns.append({"label": "MATERIAL", "pattern": alias})

            standards_file = self.ontology_dir / "standards.json"
            if standards_file.exists():
                with open(standards_file, encoding="utf-8") as f:
                    data = json.load(f)
                    standards = data.get("standards", data if isinstance(data, list) else [])
                    for std in standards:
                        if std.get("code"):
                            patterns.append({"label": "STANDARD", "pattern": std["code"]})
                        for alias in std.get("aliases", []):
                            patterns.append({"label": "STANDARD", "pattern": alias})

        standard_patterns = [
            {"label": "STANDARD", "pattern": [{"TEXT": {"REGEX": r"IS\s*\d+"}}]},
            {"label": "STANDARD", "pattern": [{"TEXT": {"REGEX": r"ASTM\s+[A-Z]\d+"}}]},
            {"label": "STANDARD", "pattern": [{"TEXT": {"REGEX": r"BS\s*EN\s*\d+"}}]},
            {"label": "STANDARD", "pattern": [{"TEXT": {"REGEX": r"ACI\s*\d+"}}]},
        ]
        patterns.extend(standard_patterns)

        unit_patterns = [
            {"label": "UNIT", "pattern": [{"TEXT": {"REGEX": r"m³|cu\.m|m3"}}]},
            {"label": "UNIT", "pattern": [{"TEXT": {"REGEX": r"m²|sq\.m|m2"}}]},
            {"label": "UNIT", "pattern": [{"TEXT": {"REGEX": r"kg|nos?|no\.|lm|mm|cm|m"}}]},
        ]
        patterns.extend(unit_patterns)

        dimension_patterns = [
            {"label": "DIMENSION", "pattern": [{"TEXT": {"REGEX": r"\d+\s*mm"}}]},
            {"label": "DIMENSION", "pattern": [{"TEXT": {"REGEX": r"\d+\s*cm"}}]},
            {"label": "DIMENSION", "pattern": [{"TEXT": {"REGEX": r"\d+\s*m\s*x\s*\d+\s*m"}}]},
        ]
        patterns.extend(dimension_patterns)

        grade_patterns = [
            {"label": "GRADE", "pattern": [{"TEXT": {"REGEX": r"M\d{1,2}"}}]},
            {"label": "GRADE", "pattern": [{"TEXT": {"REGEX": r"Fe\d{3}"}}]},
            {"label": "GRADE", "pattern": [{"TEXT": {"REGEX": r"Class\s+[A-Z]"}}]},
        ]
        patterns.extend(grade_patterns)

        action_patterns = [
            {
                "label": "ACTION",
                "pattern": [
                    {
                        "TEXT": {
                            "REGEX": r"Supply|Install|Provide|Lay|Erect|Apply|Fix|Construct|Build|Pour|Cast|Fabricate"
                        }
                    }
                ],
            },
        ]
        patterns.extend(action_patterns)

        return patterns

    def create_ruler(self, nlp: spacy.Language | None = None) -> EntityRuler:
        if nlp is None:
            nlp = self.nlp

        from spacy.pipeline import EntityRuler as _EntityRuler

        nlp.add_pipe("entity_ruler", name="construction_ruler")
        ruler = nlp.get_pipe("construction_ruler")
        if not isinstance(ruler, _EntityRuler):
            raise RuntimeError("Failed to create entity_ruler")
        self.ruler = ruler
        self._patterns = self.build_patterns()
        self.ruler.add_patterns(self._patterns)

        return self.ruler

    def extract(self, text: str) -> list[dict]:
        if self.ruler is None:
            self.create_ruler()

        doc = self.nlp(text)
        entities = []

        for ent in doc.ents:
            entities.append(
                {
                    "text": ent.text,
                    "label": ent.label_,
                    "type": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": 0.9,
                    "source": "entity_ruler",
                }
            )

        return entities
