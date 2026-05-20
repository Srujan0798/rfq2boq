"""Ontology loader for construction domain knowledge."""

from pathlib import Path
from typing import Any


class ConstructionOntology:
    def __init__(self, ontology_dir: str | Path | None = None):
        if ontology_dir:
            self.ontology_dir = Path(ontology_dir)
        else:
            from config.settings import settings
            self.ontology_dir = settings.ONTOLOGY_DIR

        self._materials: dict[str, dict] = {}
        self._standards: dict[str, dict] = {}
        self._units: dict[str, dict] = {}
        self._locations: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        self._materials = self._load_json("materials.json", "materials")
        self._standards = self._load_json("standards.json", "standards")
        self._units = self._load_json("units.json", "units")
        self._locations = self._load_json("locations.json", "locations")

    def _load_json(self, filename: str, key: str) -> dict[str, dict]:
        result = {}
        path = self.ontology_dir / filename
        if path.exists():
            import json
            with open(path) as f:
                data = json.load(f)
            for entry in data.get(key, []):
                if key == "materials":
                    name = entry["name"].lower()
                    result[name] = entry
                    for alias in entry.get("aliases", []):
                        result[alias.lower()] = entry
                elif key == "standards":
                    code = entry["code"].lower()
                    result[code] = entry
                    for alias in entry.get("aliases", []):
                        result[alias.lower()] = entry
                elif key == "units":
                    sym = entry["symbol"].lower()
                    result[sym] = entry
                    for alias in entry.get("aliases", []):
                        result[alias.lower()] = entry
                elif key == "locations":
                    name = entry["name"].lower()
                    result[name] = entry
                    for alias in entry.get("aliases", []):
                        result[alias.lower()] = entry
        return result

    def lookup_material(self, name: str) -> dict | None:
        key = name.lower().strip()
        return self._materials.get(key)

    def lookup_standard(self, code: str) -> dict | None:
        key = code.lower().strip()
        return self.standards.get(key)

    def validate_material_standard(self, material: str, standard: str) -> bool:
        mat_entry = self.lookup_material(material)
        if not mat_entry:
            return False
        std_entry = self.lookup_standard(standard)
        if not std_entry:
            return False
        applies_to = [a.lower() for a in std_entry.get("applies_to", [])]
        mat_lower = material.lower()
        return any(at in mat_lower for at in applies_to) or any(mat_lower in at for at in applies_to)

    def get_default_unit(self, material: str) -> str:
        mat_entry = self.lookup_material(material)
        if mat_entry and mat_entry.get("common_units"):
            return mat_entry["common_units"][0]
        return "nos"

    def normalize_unit(self, unit_text: str) -> str:
        entry = self._units.get(unit_text.lower().strip())
        if entry:
            return entry["symbol"]
        return unit_text.strip()

    def get_all_materials(self) -> list[dict]:
        seen = set()
        result = []
        for entry in self._materials.values():
            name = entry.get("name", "")
            if name and name not in seen:
                seen.add(name)
                result.append(entry)
        return result

    def get_all_standards(self) -> list[dict]:
        seen = set()
        result = []
        for entry in self._standards.values():
            code = entry.get("code", "")
            if code and code not in seen:
                seen.add(code)
                result.append(entry)
        return result

    @property
    def materials(self) -> dict[str, dict]:
        return self._materials

    @property
    def standards(self) -> dict[str, dict]:
        return self._standards

    @property
    def units(self) -> dict[str, dict]:
        return self._units

    @property
    def locations(self) -> dict[str, dict]:
        return self._locations


OntologyLoader = ConstructionOntology


class _GraphOntology:
    """Neo4j graph backend - wraps ConstructionOntology when Neo4j unavailable."""

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "rfq2boq_dev"):
        self.driver = None  # No Neo4j connection
        self._fallback = ConstructionOntology()

    def lookup_material(self, name: str):
        return self._fallback.lookup_material(name)

    def lookup_standard(self, code: str):
        return self._fallback.lookup_standard(code)

    def find_compatible_standards(self, material: str) -> list:
        return self._fallback.find_compatible_standards(material)

    def convert_unit(self, value: float, from_unit: str, to_unit: str) -> float | None:
        return self._fallback.convert_unit(value, from_unit, to_unit)

    def find_equivalent_standard(self, code: str, region: str = "US") -> dict | None:
        return None

    def multi_hop_query(self, start: str, max_depth: int = 3) -> list:
        return []

    def close(self):
        pass


class GraphOntology:
    """Neo4j-backed ontology - falls back to ConstructionOntology if unavailable."""

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "rfq2boq_dev",
    ):
        self._graph = _GraphOntology(uri=uri, user=user, password=password)
        self._fallback = ConstructionOntology()

    @property
    def is_available(self) -> bool:
        return self._graph.driver is not None

    def lookup_material(self, name: str) -> dict[str, Any] | None:
        result = self._graph.lookup_material(name)
        if result is not None:
            return {
                "name": result.name,
                "category": result.category,
                "density": result.density,
                "aliases": result.aliases,
                "common_units": result.common_units,
                "standards": result.standards,
                "grades": result.grades,
            }
        return self._fallback.lookup_material(name)

    def lookup_standard(self, code: str) -> dict[str, Any] | None:
        result = self._graph.lookup_standard(code)
        if result is not None:
            return {
                "code": result.code,
                "body": result.body,
                "year": result.year,
                "title": result.title,
                "aliases": result.aliases,
                "equivalents": result.equivalents,
            }
        return self._fallback.lookup_standard(code)

    def find_compatible_standards(self, material: str) -> list[dict]:
        return self._graph.find_compatible_standards(material)

    def convert_unit(self, value: float, from_unit: str, to_unit: str) -> float | None:
        return self._graph.convert_unit(value, from_unit, to_unit)

    def find_equivalent_standard(self, code: str, region: str = "US") -> dict | None:
        result = self._graph.find_equivalent_standard(code, region)
        if result:
            return {
                "code": result.code,
                "body": result.body,
                "year": result.year,
                "title": result.title,
            }
        return None

    def multi_hop_query(self, start: str, max_depth: int = 3) -> list[dict]:
        return self._graph.multi_hop_query(start, max_depth)

    def close(self):
        self._graph.close()
