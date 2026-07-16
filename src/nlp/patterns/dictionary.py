"""Dictionary lookup for entity extraction."""

import json
import logging
import re
from pathlib import Path

from .gem_catalog import DEFAULT_GEM_CATALOG

logger = logging.getLogger(__name__)


def _get_insulation_ontology_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent / "data" / "ontology"


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
            self._load_insulation_ontology()
        elif load_defaults:
            self._load_default_entries()
            self._load_insulation_ontology()

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

        # Insulation materials (SWA domain)
        self.add_material("mineral wool", alias="mineral fibre")
        self.add_material("mineral wool", alias="stone wool")
        self.add_material("rock wool", alias="rockwool")
        self.add_material("fiberglass", alias="glass wool")
        self.add_material("fiberglass", alias="glass fibre")
        self.add_material("calcium silicate", alias="calcium silicate insulation")
        self.add_material("polyurethane foam", alias="PUF")
        self.add_material("polyurethane foam", alias="PU foam")
        self.add_material("elastomeric foam", alias="nitrile rubber")
        self.add_material("elastomeric foam", alias="NBR foam")
        self.add_material("ceramic fiber", alias="ceramic fibre")
        self.add_material("ceramic fiber", alias="refractory ceramic fibre")
        self.add_material("cellular glass", alias="foam glass")
        self.add_material("phenolic foam", alias="phenolic insulation")
        self.add_material("insulation", alias="thermal insulation")
        self.add_material("insulation", alias="acoustic insulation")
        self.add_material("insulation", alias="pipe insulation")
        self.add_material("insulation", alias="duct insulation")
        self.add_material("insulation", alias="tank insulation")
        self.add_material("insulation", alias="vessel insulation")
        self.add_material("insulation", alias="equipment insulation")
        self.add_material("insulation", alias="cold insulation")
        self.add_material("insulation", alias="hot insulation")
        self.add_material("bonded mineral wool", alias="bonded mineral wool mattress")
        self.add_material("bonded mineral wool", alias="rock wool mattress")
        self.add_material("loose mineral wool", alias="loose wool")
        self.add_material("resin bonded wool", alias="RBW")
        self.add_material("aluminium sheet", alias="aluminum sheet")
        self.add_material("aluminium sheet", alias="AL sheet")
        self.add_material("GI wire mesh", alias="galvanized wire mesh")
        self.add_material("SS wire mesh", alias="stainless steel wire mesh")
        self.add_material("waterproofing", alias="water proofing")
        self.add_material("waterproofing", alias="water-proofing")
        self.add_material("cladding", alias="aluminium cladding")
        self.add_material("cladding", alias="metal cladding")
        self.add_material("joint sealant", alias="sealant")
        self.add_material("adhesive", alias="glue")
        self.add_material("tape", alias="insulation tape")
        self.add_material("tape", alias="aluminum foil tape")
        self.add_material("saddles", alias="pipe saddles")
        self.add_material("supports", alias="pipe supports")
        self.add_material("hangers", alias="pipe hangers")

        self._load_gem_catalog()

        self.add_standard("IS 456", alias="IS456")
        self.add_standard("IS 383", alias="IS383")
        self.add_standard("IS 2062", alias="IS2062")
        self.add_standard("IS 1077", alias="IS1077")
        self.add_standard("ASTM A615", alias="ASTM-A615")
        self.add_standard("BS EN 197", alias="BSEN197")
        # Insulation standards
        self.add_standard("IS 8183", alias="IS8183")
        self.add_standard("IS 4671", alias="IS4671")
        self.add_standard("IS 9842", alias="IS9842")
        self.add_standard("IS 11433", alias="IS11433")
        self.add_standard("IS 15462", alias="IS15462")
        self.add_standard("ASTM C553", alias="ASTMC553")
        self.add_standard("ASTM C612", alias="ASTMC612")
        self.add_standard("BS 3958", alias="BS3958")
        self.add_standard("BS 5422", alias="BS5422")

        self.add_location("ground floor", alias="GF")
        self.add_location("first floor", alias="FF")
        self.add_location("basement", alias="cellar")
        self.add_location("terrace", alias="roof terrace")
        self.add_location("external walls", alias="exterior walls")
        self.add_location("pipe", alias="piping")
        self.add_location("pipe", alias="pipeline")
        self.add_location("duct", alias="ducting")
        self.add_location("tank", alias="storage tank")
        self.add_location("vessel", alias="pressure vessel")
        self.add_location("equipment", alias="machinery")
        self.add_location("boiler", alias="steam boiler")
        self.add_location("turbine", alias="steam turbine")
        self.add_location("flange", alias="pipe flange")
        self.add_location("valve", alias="control valve")

        self.add_unit("m³", alias="cum")
        self.add_unit("m²", alias="sqm")
        self.add_unit("kg", alias="kgs")
        self.add_unit("no.", alias="nos")
        self.add_unit("m", alias="rmt")
        self.add_unit("t", alias="tonne")
        self.add_unit("L", alias="ltr")
        self.add_unit("m", alias="running meter")
        self.add_unit("m", alias="running metre")
        self.add_unit("m", alias="rm")
        self.add_unit("m", alias="r.mtr")
        self.add_unit("m²", alias="square meter")
        self.add_unit("m²", alias="square metre")
        self.add_unit("m²", alias="sq.m")
        self.add_unit("m²", alias="sq m")
        self.add_unit("m³", alias="cubic meter")
        self.add_unit("m³", alias="cubic metre")
        self.add_unit("m³", alias="cu.m")
        self.add_unit("m³", alias="cu m")
        self.add_unit("mm", alias="millimeter")
        self.add_unit("mm", alias="millimetre")
        self.add_unit("kg/m³", alias="kg per cum")
        self.add_unit("kg/m³", alias="density")

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
        self.add_action("insulate", alias="thermal insulation")
        self.add_action("insulate", alias="acoustic insulation")
        self.add_action("wrap", alias="pipe wrapping")
        self.add_action("clad", alias="cladding")
        self.add_action("seal", alias="joint sealing")

    def _load_gem_catalog(self):
        for name in DEFAULT_GEM_CATALOG:
            self.add_material(name)

    def _load_insulation_ontology(self) -> None:
        insulation_path = _get_insulation_ontology_path()
        if not insulation_path.exists():
            return

        insulation_materials_file = insulation_path / "insulation_materials.json"
        if insulation_materials_file.exists():
            with open(insulation_materials_file, encoding="utf-8") as f:
                data = json.load(f)
                for mat in data.get("materials", []):
                    name = mat.get("name", "")
                    if name:
                        self.add_material(name)
                        for alias in mat.get("aliases", []):
                            self.add_material(name, alias=alias)
                for _category, materials in data.get("categories", {}).items():
                    for mat_name in materials:
                        self.add_material(mat_name)

        # Load terms genuinely mined + cleaned from client-provided specification PDFs.
        # No SWA sacred files or BOQ gold used. Only client specs for gazetteer expansion.
        mined = insulation_path / "insulation_gazetteer_mined.json"
        if mined.exists():
            try:
                with open(mined, encoding="utf-8") as f:
                    m = json.load(f)
                for raw in m.get("materials", []):
                    # Strict canonical filter (post-cleaning in mined file)
                    s = raw.strip().lower()
                    if 3 < len(s) < 40 and not s.endswith(("-", ".", "/", ",")):
                        self.add_material(s)
                # Also load cleaned standards/units from the same client-mined source
                for raw_std in m.get("standards", []):
                    s = raw_std.strip()
                    if s and 4 < len(s) < 16:
                        self.add_standard(s)
                for raw_u in m.get("units", []):
                    if isinstance(raw_u, str):
                        s = raw_u.strip()
                        if s:
                            self.add_unit(s)
                    else:
                        logger.warning("Skipping non-string unit entry in gazetteer: %r", raw_u)
            except Exception:
                logger.warning("Failed to load mined insulation gazetteer", exc_info=True)

        insulation_standards_file = insulation_path / "insulation_standards.json"
        if insulation_standards_file.exists():
            with open(insulation_standards_file, encoding="utf-8") as f:
                data = json.load(f)
                for std in data.get("standards", []):
                    code = std.get("code", "")
                    if code:
                        self.add_standard(code)
                        for alias in std.get("aliases", []):
                            self.add_standard(code, alias=alias)

        insulation_units_file = insulation_path / "insulation_units.json"
        if insulation_units_file.exists():
            with open(insulation_units_file, encoding="utf-8") as f:
                data = json.load(f)
                for unit in data.get("units", []):
                    symbol = unit.get("symbol", "")
                    if symbol:
                        self.add_unit(symbol)
                        for alias in unit.get("aliases", []):
                            self.add_unit(symbol, alias=alias)

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
            results.append(
                {
                    "text": text[start:end],
                    "type": entity_type,
                    "start": start,
                    "end": end,
                    "confidence": confidence,
                    "source": "dictionary",
                }
            )

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

        def _start_key(x: dict) -> int:
            s = x.get("start", 0)
            return int(s) if isinstance(s, (int, float, str)) else 0

        results.sort(key=_start_key)
        return results

    def _has_nearby_quantity(self, text: str, start: int, end: int) -> bool:
        before = text[max(0, start - 14) : start]
        after = text[end : end + 14]
        return bool(re.search(r"\d[\d,.]*\s*$", before) or re.search(r"^\s*\d[\d,.]*", after))
