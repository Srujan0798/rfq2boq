"""Dictionary lookup for entity extraction."""

import json
import re
from pathlib import Path


class DictionaryLookup:
    def __init__(self, ontology_dir: str | None = None, load_defaults: bool = False):
        self.materials: dict[str, list[str]] = {}
        self.standards: dict[str, list[str]] = {}
        self.units: dict[str, str] = {}
        self.locations: dict[str, str] = {}
        self.actions: dict[str, str] = {}
        self.grades: dict[str, str] = {}

        if ontology_dir:
            self.load_from_dir(Path(ontology_dir))
        elif load_defaults:
            self._load_default_entries()

    def _load_default_entries(self):
        self.add_material("cement", alias="OPC")
        self.add_material("concrete", alias="RCC")
        self.add_material("concrete", alias="PCC")
        self.add_material("steel", alias="MS")
        self.add_material("steel", alias="TMT")
        self.add_material("steel", alias="rebar")
        self.add_material("brick", alias="brickwork")
        self.add_material("aggregate", alias="coarse aggregate")
        self.add_material("sand", alias="fine aggregate")
        self.add_material("tile", alias="floor tile")
        self.add_material("paint", alias="distemper")
        self.add_material("wood", alias="timber")
        self.add_material("pipe", alias="GI pipe")

        self.add_standard("IS 456", alias="IS456")
        self.add_standard("IS 383", alias="IS383")
        self.add_standard("IS 2062", alias="IS2062")
        self.add_standard("IS 1077", alias="IS1077")
        self.add_standard("ASTM A615", alias="ASTM-A615")
        self.add_standard("BS EN 197", alias="BSEN197")

        self.add_location("ground floor", alias="GF")
        self.add_location("first floor", alias="FF")
        self.add_location("basement", alias="cellar")
        self.add_location("terrace", alias="roof terrace")
        self.add_location("external walls", alias="exterior walls")

        self.add_unit("m³", alias="cum")
        self.add_unit("m²", alias="sqm")
        self.add_unit("kg", alias="kgs")
        self.add_unit("no.", alias="nos")
        self.add_unit("m", alias="rmt")
        self.add_unit("t", alias="tonne")
        self.add_unit("L", alias="ltr")

        self.add_grade("M20", alias="M-20")
        self.add_grade("M25", alias="M-25")
        self.add_grade("M30", alias="M-30")
        self.add_grade("Fe500", alias="Fe-500")
        self.add_grade("Fe415", alias="Fe-415")

        self.add_action("supply", alias="supply and install")
        self.add_action("install", alias="fix")
        self.add_action("lay", alias="place")
        self.add_action("apply", alias="paint")
        self.add_action("fabricate", alias="manufacture")

    def load_from_dir(self, ontology_dir: Path):
        materials_file = ontology_dir / "materials.json"
        if materials_file.exists():
            with open(materials_file, encoding="utf-8") as f:
                data = json.load(f)
                for mat in data.get("materials", data if isinstance(data, list) else []):
                    self.add_material(mat.get("name", ""))
                    for alias in mat.get("aliases", []):
                        self.add_material(mat.get("name", ""), alias=alias)

        standards_file = ontology_dir / "standards.json"
        if standards_file.exists():
            with open(standards_file, encoding="utf-8") as f:
                data = json.load(f)
                for std in data.get("standards", data if isinstance(data, list) else []):
                    self.add_standard(std.get("code", ""))
                    for alias in std.get("aliases", []):
                        self.add_standard(std.get("code", ""), alias=alias)

        units_file = ontology_dir / "units.json"
        if units_file.exists():
            with open(units_file, encoding="utf-8") as f:
                data = json.load(f)
                for unit in data.get("units", data if isinstance(data, list) else []):
                    symbol = unit.get("symbol", "")
                    self.add_unit(symbol)
                    for alias in unit.get("aliases", []):
                        self.add_unit(symbol, alias=alias)

        locations_file = ontology_dir / "locations.json"
        if locations_file.exists():
            with open(locations_file, encoding="utf-8") as f:
                data = json.load(f)
                for location in data.get("locations", data if isinstance(data, list) else []):
                    name = location.get("name", "")
                    self.add_location(name)
                    for alias in location.get("aliases", []):
                        self.add_location(name, alias=alias)

    def add_material(self, name: str, alias: str | None = None):
        if name.lower() not in self.materials:
            self.materials[name.lower()] = []
        self.materials[name.lower()].append(name.lower())
        if alias:
            self.materials[name.lower()].append(alias.lower())

    def add_standard(self, code: str, alias: str | None = None):
        if code.lower() not in self.standards:
            self.standards[code.lower()] = []
        self.standards[code.lower()].append(code.lower())
        if alias:
            self.standards[code.lower()].append(alias.lower())

    def add_unit(self, canonical: str, alias: str | None = None):
        self.units[canonical.lower()] = canonical
        if alias:
            self.units[alias.lower()] = canonical

    def add_location(self, name: str, alias: str | None = None):
        if name:
            self.locations[name.lower()] = name
        if alias:
            self.locations[alias.lower()] = name

    def add_action(self, name: str, alias: str | None = None):
        self.actions[name.lower()] = name
        if alias:
            self.actions[alias.lower()] = name

    def add_grade(self, name: str, alias: str | None = None):
        self.grades[name.lower()] = name
        if alias:
            self.grades[alias.lower()] = name

    def lookup(self, text: str) -> list[dict]:
        results = []
        text_lower = text.lower()
        seen: set[tuple[int, int, str]] = set()

        def add_result(entry_text: str, entity_type: str, start: int, end: int, confidence: float) -> None:
            key = (start, end, entity_type)
            if key in seen:
                return
            seen.add(key)
            results.append({
                "text": text[start:end],
                "type": entity_type,
                "start": start,
                "end": end,
                "confidence": confidence,
                "source": "dictionary",
            })

        def iter_matches(term: str):
            if not term or len(term.strip()) < 2:
                return []
            escaped = re.escape(term.lower())
            return list(re.finditer(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", text_lower))

        for entries in self.materials.values():
            for entry in entries:
                for match in iter_matches(entry):
                    add_result(entry, "MATERIAL", match.start(), match.end(), 0.9)

        for entries in self.standards.values():
            for entry in entries:
                for match in iter_matches(entry):
                    add_result(entry, "STANDARD", match.start(), match.end(), 0.92)

        for canonical in self.units:
            for match in iter_matches(canonical):
                if self._has_nearby_quantity(text, match.start(), match.end()):
                    add_result(canonical, "UNIT", match.start(), match.end(), 0.88)

        for canonical in self.grades:
            for match in iter_matches(canonical):
                add_result(canonical, "GRADE", match.start(), match.end(), 0.91)

        for canonical in self.locations:
            for match in iter_matches(canonical):
                add_result(canonical, "LOCATION", match.start(), match.end(), 0.87)

        for canonical in self.actions:
            for match in iter_matches(canonical):
                add_result(canonical, "ACTION", match.start(), match.end(), 0.85)

        results.sort(key=lambda x: x["start"])
        return results

    def _has_nearby_quantity(self, text: str, start: int, end: int) -> bool:
        before = text[max(0, start - 14):start]
        after = text[end:end + 14]
        return bool(re.search(r"\d[\d,.]*\s*$", before) or re.search(r"^\s*\d[\d,.]*", after))
