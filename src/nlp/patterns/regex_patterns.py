"""Regex patterns for entity extraction."""

import re

STANDARD_PATTERNS = [
    (r"IS\s*\d+(?::\d+)?", "STANDARD"),
    (r"ASTM\s+[A-Z]?\d+(?:\s*\([^)]+\))?", "STANDARD"),
    (r"BS\s*EN\s*\d+(?::\d+)?", "STANDARD"),
    (r"ACI\s*\d+", "STANDARD"),
    (r"EN\s*\d+(?::\d+)?", "STANDARD"),
    # Additional patterns from client insulation specs
    (r"ASTM\s*C?\d+(?:\s*\d*)?", "STANDARD"),
    (r"IS\s*\d+", "STANDARD"),
]

QUANTITY_PATTERNS = [
    (r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", "QUANTITY"),
    (r"\d+\.\d+", "QUANTITY"),
    (r"\b\d+\b", "QUANTITY"),
]

DIMENSION_PATTERNS = [
    (r"\b\d{2,}\s*mm\b", "DIMENSION"),
    (r"\b\d{2,}\s*cm\b", "DIMENSION"),
    (r"\b\d{2,}\s*m\b", "DIMENSION"),
    (r"\d+\s*mm\s*(?:dia|diameter)\b", "DIMENSION"),
    (r"\d+\s*cm\s*(?:dia|diameter)\b", "DIMENSION"),
    (r"\d+\s*m\s*(?:x\s*\d+\s*m)?(?:\s*(?:long|wide|high))?", "DIMENSION"),
    (r"Ø\s*\d+\s*mm", "DIMENSION"),
    (r"\d+\s*mm\s*x\s*\d+\s*mm", "DIMENSION"),
]

GRADE_PATTERNS = [
    (r"M\d{1,2}\b", "GRADE"),
    (r"Fe\d{3}\b", "GRADE"),
    (r"Grade\s+[A-C]\b", "GRADE"),
    (r"Grade\s+\d+\b", "GRADE"),
    (r"Class\s+[A-C]\b", "GRADE"),
    (r"Class\s+\d+\b", "GRADE"),
]

ACTION_PATTERNS = [
    (r"\b(supply|install|provide|lay|erect|apply|fix|construct|build|pour|cast|fabricate)\b", "ACTION"),
]

MATERIAL_PATTERNS = [
    (r"\bwet mix macadam\b", "MATERIAL"),
    (r"\btack coat\b", "MATERIAL"),
    (r"\bbituminous concrete\b", "MATERIAL"),
    (r"\bgranular sub[- ]base(?:\s+type\s+[A-Z])?\b", "MATERIAL"),
    (r"\bprime coat\b", "MATERIAL"),
    (r"\baggregate base course\b", "MATERIAL"),
    (r"\bdry lean concrete\b", "MATERIAL"),
    (r"\belastomeric bearing[sd]?\b", "MATERIAL"),
    (r"\bpre[- ]stressed steel\b", "MATERIAL"),
    (r"\breinforcement steel\b", "MATERIAL"),
    (r"\bms structural steel\b", "MATERIAL"),
    (r"\bshotcrete\b", "MATERIAL"),
    (r"\bexpansion joint[sd]?\b", "MATERIAL"),
    (r"\brock anchor\b", "MATERIAL"),
    (r"\brcc pipe\b", "MATERIAL"),
    (r"\bfirst class brickwork\b", "MATERIAL"),
    (r"\bgranite flooring\b", "MATERIAL"),
    (r"\bplywood flush door\b", "MATERIAL"),
    (r"\bceramic floor tile[sd]?\b", "MATERIAL"),
    (r"\bcpvc pipe[sd]?\b", "MATERIAL"),
    (r"\bg[i]? pipe[sd]?\b", "MATERIAL"),
    (r"\bpvc conduit\b", "MATERIAL"),
    (r"\bupvc pipe[sd]?\b", "MATERIAL"),
    (r"\bgi conduit\b", "MATERIAL"),
    (r"\belectric wire\b", "MATERIAL"),
    (r"\bcopper cable\b", "MATERIAL"),
    (r"\baluminium cable\b", "MATERIAL"),
    (r"\bball valve\b", "MATERIAL"),
    (r"\bwater meter\b", "MATERIAL"),
    (r"\bdb box\b", "MATERIAL"),
    (r"\bair breaker\b", "MATERIAL"),
    (r"\bfire alarm call point\b", "MATERIAL"),
    (r"\bsanitary ware\b", "MATERIAL"),
    (r"\bsewage pump\b", "MATERIAL"),
    (r"\bpressure boosting\b", "MATERIAL"),
    (r"\bfrp tank\b", "MATERIAL"),
    (r"\bled panel light\b", "MATERIAL"),
    (r"\bceiling fan\b", "MATERIAL"),
    (r"\baluminum window[sd]?\b", "MATERIAL"),
    (r"\bearth electrode\b", "MATERIAL"),
    (r"\btmt (?:steel )?bar[sd]?\b", "MATERIAL"),
    (r"\btmt steel\b", "MATERIAL"),
    (r"\btmt bar[sd]?\b", "MATERIAL"),
    (r"\bstructural steel\b", "MATERIAL"),
    (r"\bstainless steel\b", "MATERIAL"),
    (r"\bmild steel\b", "MATERIAL"),
    (r"\bgalvanized steel\b", "MATERIAL"),
    (r"\bbeam\b", "MATERIAL"),
    (r"\bcolumn\b", "MATERIAL"),
    (r"\bslab\b", "MATERIAL"),
    # Road construction (additional patterns beyond top section)
    (r"\bseal coat\b", "MATERIAL"),
    (r"\broller compacted concrete\b", "MATERIAL"),
    (r"\bshoulder\b", "MATERIAL"),
    (r"\bkerb\b", "MATERIAL"),
    (r"\bpavement\b", "MATERIAL"),
    (r"\basphalt\b", "MATERIAL"),
    (r"\btar\b", "MATERIAL"),
    (r"\broad marking\b", "MATERIAL"),
    # Electrical
    (r"\bpower cable\b", "MATERIAL"),
    (r"\bcontrol cable\b", "MATERIAL"),
    (r"\bdata cable\b", "MATERIAL"),
    (r"\bcoaxial cable\b", "MATERIAL"),
    (r"\bfiber optic\b", "MATERIAL"),
    (r"\boptical fiber\b", "MATERIAL"),
    (r"\brj45\b", "MATERIAL"),
    (r"\bcat6\b", "MATERIAL"),
    (r"\bswitch board\b", "MATERIAL"),
    (r"\bdistribution board\b", "MATERIAL"),
    (r"\bmcb\b", "MATERIAL"),
    (r"\bmccb\b", "MATERIAL"),
    (r"\bcontactor\b", "MATERIAL"),
    (r"\brelay\b", "MATERIAL"),
    (r"\btimer\b", "MATERIAL"),
    (r"\bsensor\b", "MATERIAL"),
    (r"\bphotocell\b", "MATERIAL"),
    (r"\bstreet light\b", "MATERIAL"),
    (r"\bflood light\b", "MATERIAL"),
    (r"\bexit sign\b", "MATERIAL"),
    (r"\bups\b", "MATERIAL"),
    (r"\binverter\b", "MATERIAL"),
    (r"\bsolar panel\b", "MATERIAL"),
    (r"\bearth bus\b", "MATERIAL"),
    (r"\bearth pit\b", "MATERIAL"),
    # Plumbing
    (r"\bwater supply pipe\b", "MATERIAL"),
    (r"\bdrainage pipe\b", "MATERIAL"),
    (r"\bsewer pipe\b", "MATERIAL"),
    (r"\bstp pipe\b", "MATERIAL"),
    (r"\bhdpe pipe\b", "MATERIAL"),
    (r"\bmdpe pipe\b", "MATERIAL"),
    (r"\bldpe pipe\b", "MATERIAL"),
    (r"\bpp-r pipe\b", "MATERIAL"),
    (r"\babs pipe\b", "MATERIAL"),
    (r"\bcast iron pipe\b", "MATERIAL"),
    (r"\bductile iron pipe\b", "MATERIAL"),
    (r"\basbestos pipe\b", "MATERIAL"),
    (r"\bfrp pipe\b", "MATERIAL"),
    (r"\bgrp pipe\b", "MATERIAL"),
    (r"\bwash basin\b", "MATERIAL"),
    (r"\bwater closet\b", "MATERIAL"),
    (r"\burinal\b", "MATERIAL"),
    (r"\bshower\b", "MATERIAL"),
    (r"\bbathtub\b", "MATERIAL"),
    (r"\bkitchen sink\b", "MATERIAL"),
    (r"\bfaucet\b", "MATERIAL"),
    (r"\btap\b", "MATERIAL"),
    (r"\bstop cock\b", "MATERIAL"),
    (r"\bnon[- ]return valve\b", "MATERIAL"),
    (r"\bcheck valve\b", "MATERIAL"),
    (r"\bgate valve\b", "MATERIAL"),
    (r"\bglobe valve\b", "MATERIAL"),
    (r"\b butterfly valve\b", "MATERIAL"),
    (r"\bfloat valve\b", "MATERIAL"),
    (r"\bpressure reducing valve\b", "MATERIAL"),
    (r"\bpressure relief valve\b", "MATERIAL"),
    (r"\bair valve\b", "MATERIAL"),
    (r"\bfoot valve\b", "MATERIAL"),
    (r"\bsluice valve\b", "MATERIAL"),
    (r"\bhydrant\b", "MATERIAL"),
    (r"\bsprinkler head\b", "MATERIAL"),
    (r"\bfire hose\b", "MATERIAL"),
    (r"\bfire extinguisher\b", "MATERIAL"),
    (r"\bmanhole cover\b", "MATERIAL"),
    (r"\bgully trap\b", "MATERIAL"),
    (r"\bfloor trap\b", "MATERIAL"),
    (r"\broof drain\b", "MATERIAL"),
    (r"\bgrease trap\b", "MATERIAL"),
    (r"\b septic tank\b", "MATERIAL"),
    (r"\bbio[- ]digester\b", "MATERIAL"),
    # Building materials
    (r"\bportland cement\b", "MATERIAL"),
    (r"\bwhite cement\b", "MATERIAL"),
    (r"\bwall putty\b", "MATERIAL"),
    (r"\bpop\b", "MATERIAL"),
    (r"\bgypsum plaster\b", "MATERIAL"),
    (r"\blime plaster\b", "MATERIAL"),
    (r"\b cement plaster\b", "MATERIAL"),
    (r"\bneeru\b", "MATERIAL"),
    (r"\bwhite wash\b", "MATERIAL"),
    (r"\bdistemper\b", "MATERIAL"),
    (r"\btexture paint\b", "MATERIAL"),
    (r"\bweather coat\b", "MATERIAL"),
    (r"\bwaterproofing\b", "MATERIAL"),
    (r"\bdamp proof\b", "MATERIAL"),
    (r"\btermite proof\b", "MATERIAL"),
    (r"\btermite treatment\b", "MATERIAL"),
    (r"\banti[- ]termite\b", "MATERIAL"),
    (r"\bwood primer\b", "MATERIAL"),
    (r"\bmetal primer\b", "MATERIAL"),
    (r"\bred oxide\b", "MATERIAL"),
    (r"\bzinc chromate\b", "MATERIAL"),
    (r"\bbitumen paint\b", "MATERIAL"),
    (r"\bepoxy paint\b", "MATERIAL"),
    (r"\bpolyurethane paint\b", "MATERIAL"),
    (r"\banti[- ]corrosive\b", "MATERIAL"),
    (r"\bglass\b", "MATERIAL"),
    (r"\btoughened glass\b", "MATERIAL"),
    (r"\blaminated glass\b", "MATERIAL"),
    (r"\bfloat glass\b", "MATERIAL"),
    (r"\bwire mesh glass\b", "MATERIAL"),
    (r"\bmirror\b", "MATERIAL"),
    (r"\baluminium section\b", "MATERIAL"),
    (r"\baluminium composite panel\b", "MATERIAL"),
    (r"\bacp\b", "MATERIAL"),
    (r"\bupvc window\b", "MATERIAL"),
    (r"\bupvc door\b", "MATERIAL"),
    (r"\bwooden door\b", "MATERIAL"),
    (r"\bflush door\b", "MATERIAL"),
    (r"\bpanel door\b", "MATERIAL"),
    (r"\brolling shutter\b", "MATERIAL"),
    (r"\bcollapsible gate\b", "MATERIAL"),
    (r"\bms grill\b", "MATERIAL"),
    (r"\bms railing\b", "MATERIAL"),
    (r"\bss railing\b", "MATERIAL"),
    (r"\bhandrail\b", "MATERIAL"),
    (r"\bbalustrade\b", "MATERIAL"),
    (r"\bstaircase\b", "MATERIAL"),
    (r"\blift\b", "MATERIAL"),
    (r"\belevator\b", "MATERIAL"),
    (r"\bescalator\b", "MATERIAL"),
    (r"\bfalse ceiling\b", "MATERIAL"),
    (r"\bgypsum board ceiling\b", "MATERIAL"),
    (r"\bgrid ceiling\b", "MATERIAL"),
    (r"\bacoustic ceiling\b", "MATERIAL"),
    (r"\bmetal ceiling\b", "MATERIAL"),
    (r"\bpvc panel\b", "MATERIAL"),
    (r"\bpartition\b", "MATERIAL"),
    (r"\bcubicle\b", "MATERIAL"),
    (r"\bfurniture\b", "MATERIAL"),
    (r"\bworkstation\b", "MATERIAL"),
    (r"\bcabinet\b", "MATERIAL"),
    (r"\blocker\b", "MATERIAL"),
    (r"\bpartition wall\b", "MATERIAL"),
    (r"\bcurtain wall\b", "MATERIAL"),
    (r"\bspider fitting\b", "MATERIAL"),
    (r"\bcanopy\b", "MATERIAL"),
    (r"\bawning\b", "MATERIAL"),
    (r"\bshade\b", "MATERIAL"),
    (r"\bfabrication\b", "MATERIAL"),
    (r"\berection\b", "MATERIAL"),
    # Insulation materials (from insulation_materials.json + GeM catalog)
    (r"\bmineral wool\b", "MATERIAL"),
    (r"\bmineral fibre\b", "MATERIAL"),
    (r"\bstone wool\b", "MATERIAL"),
    (r"\brock wool\b", "MATERIAL"),
    (r"\brockwool\b", "MATERIAL"),
    (r"\bfiberglass\b", "MATERIAL"),
    (r"\bglass wool\b", "MATERIAL"),
    (r"\bglass fibre\b", "MATERIAL"),
    (r"\bfibreglass\b", "MATERIAL"),
    (r"\bcalcium silicate\b", "MATERIAL"),
    (r"\bpolyurethane foam\b", "MATERIAL"),
    (r"\bPUF\b", "MATERIAL"),
    (r"\bPU foam\b", "MATERIAL"),
    (r"\bpolyfoam\b", "MATERIAL"),
    (r"\bpolyisocyanurate\b", "MATERIAL"),
    (r"\bPIR\b", "MATERIAL"),
    (r"\belastomeric foam\b", "MATERIAL"),
    (r"\belastomeric insulation\b", "MATERIAL"),
    (r"\bnitrile rubber\b", "MATERIAL"),
    (r"\bNBR\b", "MATERIAL"),
    (r"\bclosed cell elastomeric\b", "MATERIAL"),
    (r"\bceramic fiber\b", "MATERIAL"),
    (r"\bceramic fibre\b", "MATERIAL"),
    (r"\bthermal insulation board\b", "MATERIAL"),
    (r"\bcellular glass\b", "MATERIAL"),
    (r"\bfoam glass\b", "MATERIAL"),
    (r"\bacoustic foam\b", "MATERIAL"),
    (r"\bmass loaded vinyl\b", "MATERIAL"),
    (r"\bfiberglass batt\b", "MATERIAL"),
    (r"\brock wool batt\b", "MATERIAL"),
    (r"\bacoustic insulation\b", "MATERIAL"),
    (r"\bsoundproofing\b", "MATERIAL"),
    (r"\bpipe insulation\b", "MATERIAL"),
    (r"\bduct insulation\b", "MATERIAL"),
    (r"\btank insulation\b", "MATERIAL"),
    (r"\bvessel insulation\b", "MATERIAL"),
    (r"\bthermal insulation\b", "MATERIAL"),
    (r"\bequipment insulation\b", "MATERIAL"),
    (r"\bcold insulation\b", "MATERIAL"),
    (r"\bhot insulation\b", "MATERIAL"),
    (r"\bduct liner\b", "MATERIAL"),
    (r"\bfiberglass duct wrap\b", "MATERIAL"),
    (r"\bflexible insulation\b", "MATERIAL"),
    (r"\bbonded mineral wool\b", "MATERIAL"),
    (r"\bresin bonded rock wool\b", "MATERIAL"),
    (r"\bLRB mattress(?:es)?\b", "MATERIAL"),
    (r"\bResin Bonded Rock Wool\b", "MATERIAL"),
    (r"\bClass O Insulation\b", "MATERIAL"),
    (r"\barmaflex\b", "MATERIAL"),
    (r"\bk-flex\b", "MATERIAL"),
    (r"\bnomaco\b", "MATERIAL"),
    (r"\btrocellen\b", "MATERIAL"),
    (r"\bkaiflex\b", "MATERIAL"),
    (r"\bisonor\b", "MATERIAL"),
    (r"\bphenolic foam\b", "MATERIAL"),
    (r"\bphenolic insulation\b", "MATERIAL"),
    (r"\bperlite\b", "MATERIAL"),
    (r"\bvermiculite\b", "MATERIAL"),
    (r"\bmagnesia\b", "MATERIAL"),
    # Additional from client specs mined (cleaned canonicals + common variants) for insulation domain
    (r"\bclosed cell nitrile(?: rubber)?\b", "MATERIAL"),
    (r"\bopen cell nitrile(?: rubber)?\b", "MATERIAL"),
    (r"\bnitrile rubber insulation\b", "MATERIAL"),
    (r"\belastomeric nitrile(?: rubber)?\b", "MATERIAL"),
    (r"\belastomeric insulation\b", "MATERIAL"),
    (r"\brock wool mattress\b", "MATERIAL"),
    (r"\bmineral wool mattress\b", "MATERIAL"),
    (r"\bxlpe insulation\b", "MATERIAL"),
    (r"\bclass [oO0] insulation\b", "MATERIAL"),
    (r"\bclass [oO0] nitrile\b", "MATERIAL"),
    (r"\bthermal insulation\b", "MATERIAL"),
    (r"\bduct insulation\b", "MATERIAL"),
    (r"\bpipe insulation\b", "MATERIAL"),
]


def extract_regex_entities(text: str) -> list[dict]:
    """Extract entities using regex patterns."""
    entities: list[dict] = []

    def add_entity(ent: dict):
        for existing in entities:
            overlaps = (
                existing["start"] <= ent["start"] < existing["end"] or existing["start"] < ent["end"] <= existing["end"]
            )
            if overlaps and existing["type"] == ent["type"]:
                if ent["text"] in existing["text"]:
                    return
                if existing["text"] in ent["text"]:
                    existing["text"] = ent["text"]
                    existing["start"] = ent["start"]
                    existing["end"] = ent["end"]
                    return
        entities.append(ent)

    for pattern, label in STANDARD_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            add_entity(
                {
                    "text": match.group(0),
                    "type": label,
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.95,
                    "source": "regex",
                }
            )

    for pattern, label in QUANTITY_PATTERNS:
        for match in re.finditer(pattern, text):
            text_val = match.group(0)
            if text_val and len(text_val) > 1:
                existing_in_range = [
                    e
                    for e in entities
                    if (e["start"] <= match.start() < e["end"] or e["start"] < match.end() <= e["end"])
                ]
                blocked_types = {"STANDARD", "GRADE", "DIMENSION"}
                if not any(e.get("type") in blocked_types | {label} for e in existing_in_range):
                    add_entity(
                        {
                            "text": text_val,
                            "type": label,
                            "start": match.start(),
                            "end": match.end(),
                            "confidence": 0.90,
                            "source": "regex",
                        }
                    )

    for pattern, label in DIMENSION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            match_text = match.group(0)
            existing_in_range = [
                e for e in entities if (e["start"] <= match.start() < e["end"] or e["start"] < match.end() <= e["end"])
            ]
            if not any(e.get("type") == label for e in existing_in_range):
                add_entity(
                    {
                        "text": match_text,
                        "type": label,
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.92,
                        "source": "regex",
                    }
                )

    for pattern, label in GRADE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            match_text = match.group(0)
            existing_in_range = [
                e for e in entities if (e["start"] <= match.start() < e["end"] or e["start"] < match.end() <= e["end"])
            ]
            if not any(e.get("type") == label for e in existing_in_range):
                add_entity(
                    {
                        "text": match_text,
                        "type": label,
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.93,
                        "source": "regex",
                    }
                )

    for pattern, label in ACTION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            match_text = match.group(0)
            existing_in_range = [
                e for e in entities if (e["start"] <= match.start() < e["end"] or e["start"] < match.end() <= e["end"])
            ]
            if not any(e.get("type") == label for e in existing_in_range):
                add_entity(
                    {
                        "text": match_text,
                        "type": label,
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.94,
                        "source": "regex",
                    }
                )

    entities.sort(key=lambda x: x["start"])
    return entities
