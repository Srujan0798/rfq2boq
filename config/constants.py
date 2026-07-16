"""Entity taxonomy, relation schema, and BIOES tag definitions.

Authoritative source: plan/04_ENTITY_ONTOLOGY.md
Frozen at project start. Changes require ADR.
"""

from enum import StrEnum

# ---------------------------------------------------------------------------
# Entity types (8) — aligned to IFC ontology
# ---------------------------------------------------------------------------


class EntityType(StrEnum):
    MATERIAL = "MATERIAL"  # "M20 concrete", "TMT steel bars", "Class-A brick"
    QUANTITY = "QUANTITY"  # "150.5", "1,200", "2.5"
    UNIT = "UNIT"  # "m³", "kg", "no.", "lm", "ls"
    LOCATION = "LOCATION"  # "ground floor", "Block A", "external walls"
    DIMENSION = "DIMENSION"  # "230 mm thick", "Ø12 mm", "1.5 × 3.0 m"
    STANDARD = "STANDARD"  # "IS 456", "ASTM A615", "BS EN 197-1"
    ACTION = "ACTION"  # "supply", "install", "lay", "cast", "plaster"
    GRADE = "GRADE"  # "Fe500", "M20", "Class A"


ENTITY_LABELS: list[str] = [e.value for e in EntityType]

# ---------------------------------------------------------------------------
# BIOES tagging scheme
# B = Beginning, I = Inside, O = Outside, E = End, S = Single-token entity
# ---------------------------------------------------------------------------

BIOES_PREFIXES = ["B", "I", "O", "E", "S"]

BIOES_LABELS: list[str] = ["O"] + [f"{prefix}-{label}" for label in ENTITY_LABELS for prefix in ["B", "I", "E", "S"]]

LABEL2ID: dict[str, int] = {label: i for i, label in enumerate(BIOES_LABELS)}
ID2LABEL: dict[int, str] = {i: label for label, i in LABEL2ID.items()}

NUM_LABELS: int = len(BIOES_LABELS)

# ---------------------------------------------------------------------------
# Relation types (6) — typed against CTO ontology
# ---------------------------------------------------------------------------


class RelationType(StrEnum):
    HAS_QUANTITY = "HAS_QUANTITY"  # MATERIAL → QUANTITY
    HAS_UNIT = "HAS_UNIT"  # QUANTITY → UNIT
    AT_LOCATION = "AT_LOCATION"  # MATERIAL → LOCATION
    OF_GRADE = "OF_GRADE"  # MATERIAL → GRADE
    COMPLIES_WITH = "COMPLIES_WITH"  # MATERIAL → STANDARD
    HAS_DIMENSION = "HAS_DIMENSION"  # MATERIAL → DIMENSION


RELATION_LABELS: list[str] = [r.value for r in RelationType]

# Head → Tail type constraints for each relation
RELATION_SCHEMA: dict[str, tuple[str, str]] = {
    "HAS_QUANTITY": ("MATERIAL", "QUANTITY"),
    "HAS_UNIT": ("QUANTITY", "UNIT"),
    "AT_LOCATION": ("MATERIAL", "LOCATION"),
    "OF_GRADE": ("MATERIAL", "GRADE"),
    "COMPLIES_WITH": ("MATERIAL", "STANDARD"),
    "HAS_DIMENSION": ("MATERIAL", "DIMENSION"),
}

# ---------------------------------------------------------------------------
# Section types for document layout classification
# ---------------------------------------------------------------------------


class SectionType(StrEnum):
    PREAMBLE = "preamble"
    SCOPE = "scope"
    SCHEDULE_OF_ITEMS = "schedule_of_items"
    SPECIFICATIONS = "specifications"
    DRAWINGS_LIST = "drawings_list"
    COMMERCIAL = "commercial"
    GENERAL = "general"


# ---------------------------------------------------------------------------
# Flag codes (P3_04) — the closed enum of every typed flag in the system.
#
# Mirrored in src.domain.flags (which imports it via a try/except so the
# flags module is importable even before this enum was added here).
# Codes are stable identifiers — every flag emitted anywhere in the
# pipeline uses one of these.  Adding a new code requires an ADR.
# ---------------------------------------------------------------------------


class FlagCode(StrEnum):
    """Closed set of flag codes (R1: flag, never drop)."""

    # --- Extraction shape (row-level) ---
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    QUANTITY_MISSING = "QUANTITY_MISSING"
    MATERIAL_FRAGMENT = "MATERIAL_FRAGMENT"

    # --- Unit / normalization (row-level) ---
    UNKNOWN_UNIT = "UNKNOWN_UNIT"
    AMBIGUOUS_UNIT = "AMBIGUOUS_UNIT"
    UNIT_DIMENSION_MISMATCH = "UNIT_DIMENSION_MISMATCH"

    # --- Document structure (doc-level) ---
    STRUCTURE_FALLBACK = "STRUCTURE_FALLBACK"
    NO_BOQ_SECTION_FOUND = "NO_BOQ_SECTION_FOUND"
    COLUMN_FALLBACK = "COLUMN_FALLBACK"
    NO_TEXT_EXTRACTED = "NO_TEXT_EXTRACTED"

    # --- Table classification (doc-level) ---
    TABLE_TYPE_NOT_BOQ = "TABLE_TYPE_NOT_BOQ"

    # --- GeM catalog (R2) ---
    GEM_NON_CATALOG = "GEM_NON_CATALOG"

    # --- Pipeline errors (doc-level) ---
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    EMPTY_FILE = "EMPTY_FILE"
    PIPELINE_ERROR = "PIPELINE_ERROR"

    # --- Misc (row-level) ---
    RATE_ONLY = "RATE_ONLY"



SECTION_LABELS: list[str] = [s.value for s in SectionType]

# ---------------------------------------------------------------------------
# Warning types emitted by the validation layer
# ---------------------------------------------------------------------------


class WarningType(StrEnum):
    SCOPE_GAP = "SCOPE_GAP_WARNING"
    UNIT_AMBIGUOUS = "UNIT_AMBIGUOUS"
    STANDARD_UNKNOWN = "STANDARD_UNKNOWN"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    QUANTITY_MISSING = "QUANTITY_MISSING"
    OCR_LOW_QUALITY = "OCR_LOW_QUALITY"


# ---------------------------------------------------------------------------
# Unit normalization canonical forms
# ---------------------------------------------------------------------------

CANONICAL_UNITS: dict[str, str] = {
    # Volume
    "cu.m": "m^3",
    "cum": "m^3",
    "m3": "m^3",
    "m³": "m^3",
    "cu m": "m^3",
    "cu.m.": "m^3",
    "cubic meter": "m^3",
    "cubic metre": "m^3",
    "cubic meters": "m^3",
    "cubic metres": "m^3",
    "cft": "ft^3",
    "ft3": "ft^3",
    "cubic foot": "ft^3",
    "cubic feet": "ft^3",
    # Area
    "sq.m": "m^2",
    "sqm": "m^2",
    "m2": "m^2",
    "m²": "m^2",
    "sq m": "m^2",
    "sq.m.": "m^2",
    "square meter": "m^2",
    "square metre": "m^2",
    "square meters": "m^2",
    "square metres": "m^2",
    "sft": "ft^2",
    "sq.ft": "ft^2",
    "sq ft": "ft^2",
    "ft2": "ft^2",
    "square foot": "ft^2",
    "square feet": "ft^2",
    "hectare": "ha",
    "hectares": "ha",
    "acre": "acre",
    "acres": "acre",
    # Length
    "R.m": "lm",
    "Rm": "lm",
    "rm": "lm",
    "lm": "lm",
    "r.m.": "lm",
    "running meter": "lm",
    "running metre": "lm",
    "running meters": "lm",
    "running metres": "lm",
    "linear meter": "lm",
    "linear metre": "lm",
    "lineal meter": "lm",
    "lineal metre": "lm",
    # Mass
    "MT": "t",
    "Tonne": "t",
    "tonne": "t",
    "ton": "t",
    "metric ton": "t",
    "metric tonne": "t",
    "tons": "t",
    "tonnes": "t",
    "kg": "kg",
    "Kg": "kg",
    "KG": "kg",
    "kgs": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "g": "g",
    "gram": "g",
    "grams": "g",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "pounds": "lb",
    # Count
    "Nos": "no.",
    "nos": "no.",
    "no.": "no.",
    "nr": "no.",
    "no": "no.",
    "number": "no.",
    "numbers": "no.",
    "each": "no.",
    "ea": "no.",
    "nos.": "no.",
    "piece": "no.",
    "pieces": "no.",
    "pc": "no.",
    "pcs": "no.",
    "set": "set",
    "sets": "set",
    "pair": "pair",
    "pairs": "pair",
    "point": "point",
    "points": "point",
    # Lump sum
    "LS": "ls",
    "Lump-sum": "ls",
    "l.s.": "ls",
    "lumpsum": "ls",
    "lump sum": "ls",
    "lot": "lot",
    "job": "job",
    # Linear
    "m": "m",
    "meter": "m",
    "metre": "m",
    "meters": "m",
    "metres": "m",
    "cm": "cm",
    "centimeter": "cm",
    "centimetre": "cm",
    "centimeters": "cm",
    "centimetres": "cm",
    "mm": "mm",
    "millimeter": "mm",
    "millimetre": "mm",
    "millimeters": "mm",
    "millimetres": "mm",
    "ft": "ft",
    "foot": "ft",
    "feet": "ft",
    "inch": "in",
    "inches": "in",
    "in": "in",
    # Capacity
    "ltr": "ltr",
    "liter": "ltr",
    "litre": "ltr",
    "liters": "ltr",
    "litres": "ltr",
    "l": "ltr",
    "L": "ltr",
    "ml": "ml",
    "milliliter": "ml",
    "millilitre": "ml",
    "kl": "kl",
    "kiloliter": "kl",
    "kilolitre": "kl",
    # Packaging
    "bag": "bag",
    "bags": "bag",
    "sack": "bag",
    "sacks": "bag",
    "drum": "drum",
    "drums": "drum",
    "roll": "roll",
    "rolls": "roll",
    "coil": "coil",
    "coils": "coil",
    "bundle": "bundle",
    "bundles": "bundle",
    "box": "box",
    "boxes": "box",
    "carton": "carton",
    "cartons": "carton",
    # MEP and electrical
    "kw": "kW",
    "kilowatt": "kW",
    "w": "W",
    "watt": "W",
    "hp": "hp",
    "kva": "kVA",
    "va": "VA",
    "v": "V",
    "volt": "V",
    "amp": "A",
    "amps": "A",
    "a": "A",
    "bar": "bar",
    "psi": "psi",
    "pa": "Pa",
    "kpa": "kPa",
}

# ---------------------------------------------------------------------------
# NER model defaults
# ---------------------------------------------------------------------------

DEFAULT_MODEL_NAME = "bert-base-cased"
MAX_SEQ_LENGTH = 512

MULTILINGUAL_MODEL = "xlm-roberta-base"

SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "code": "en", "model": "bert-base-cased"},
    "hi": {"name": "Hindi", "code": "hi", "model": "xlm-roberta-base"},
}
