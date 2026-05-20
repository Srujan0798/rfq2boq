"""Relation extraction rules for RFQ-to-BOQ."""

RELATION_RULES = [
    {
        "type": "HAS_QUANTITY",
        "head": "MATERIAL",
        "tail": "QUANTITY",
        "max_distance": 50,
        "keywords": [],
    },
    {
        "type": "HAS_UNIT",
        "head": "QUANTITY",
        "tail": "UNIT",
        "max_distance": 10,
        "keywords": [],
    },
    {
        "type": "AT_LOCATION",
        "head": "MATERIAL",
        "tail": "LOCATION",
        "max_distance": 100,
        "keywords": ["at", "in", "for", "to"],
    },
    {
        "type": "OF_GRADE",
        "head": "MATERIAL",
        "tail": "GRADE",
        "max_distance": 30,
        "keywords": ["grade", "of"],
    },
    {
        "type": "COMPLIES_WITH",
        "head": "MATERIAL",
        "tail": "STANDARD",
        "max_distance": 80,
        "keywords": ["as per", "conforming to", "per", "according to", "complying with"],
    },
    {
        "type": "HAS_DIMENSION",
        "head": "MATERIAL",
        "tail": "DIMENSION",
        "max_distance": 40,
        "keywords": ["thick", "dia", "diameter"],
    },
]


DEFAULT_MAX_DISTANCE = 300
DEFAULT_SENTENCE_GAP = 50
