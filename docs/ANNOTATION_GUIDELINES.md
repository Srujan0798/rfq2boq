# Annotation Guidelines — RFQ2BOQ NER

**Version:** 1.0
**Date:** 2026-06-09
**Scope:** Construction tender documents (PDF, XLSX) → BOQ item extraction

---

## Entity Types (8)

### 1. MATERIAL
The physical item or work being procured.

**Examples:**
- "Portland cement", "TMT steel bars", "HDPE pipe", "ceramic floor tiles"
- "brickwork in cement mortar", "plastering 12mm thick"
- "supply and installation of fire alarm call point"

**Rules:**
- Include action verbs at start if they describe the work item ("supply of cement", "installation of pipes")
- Include dimensions/grades if part of the material phrase ("100mm dia HDPE pipe", "M25 concrete")
- Do NOT include standalone quantities or units
- Do NOT include location phrases unless they're part of the material name

### 2. QUANTITY
The numeric amount.

**Examples:**
- "500", "1500.5", "2,500", "10,000"
- "½" (only if clearly a quantity)

**Rules:**
- Must be purely numeric (may contain commas or decimals)
- Do NOT tag page numbers, item numbers, or rates as quantities
- If a number is part of a dimension ("100mm"), tag it as DIMENSION not QUANTITY

### 3. UNIT
The unit of measurement.

**Examples:**
- "cum", "sqm", "rmt", "kg", "nos", "bags", "tonnes"
- "m³", "m²", "m", "no.", "pcs", "sets"

**Rules:**
- Normalize to standard forms when annotating
- "cubic meters" → tag as "cum"
- "running meters" → tag as "rmt"
- Do NOT tag currency units (INR, ₹) or time units unless they're BOQ units

### 4. LOCATION
Where the work/material is applied.

**Examples:**
- "ground floor", "basement", "roof slab", "external walls"
- "Zone A", "Building 1", "at site"

**Rules:**
- Only tag if it specifies a physical location
- Do NOT tag generic terms like "at project" or "as per drawing"

### 5. DIMENSION
Physical size specifications.

**Examples:**
- "100mm dia", "12mm thick", "600x600 mm", "Ø25mm"
- "25 mm diameter", "50 mm width"

**Rules:**
- Always include the unit (mm, cm, m, inch)
- "100mm" alone → DIMENSION
- "100mm dia HDPE pipe" → "100mm dia" = DIMENSION, "HDPE pipe" = MATERIAL

### 6. STANDARD
Code or standard reference.

**Examples:**
- "IS 456", "IS 1786", "ASTM C553", "BS EN 14303"
- "M20" (when referring to concrete grade standard)
- "Fe500" (when referring to steel grade standard)

**Rules:**
- Tag the full code including prefix
- "IS" + space + number is one STANDARD entity

### 7. GRADE
Quality/grade specification.

**Examples:**
- "OPC 53", "Grade A", "Class B", "Type II"
- "premium", "commercial" (when explicitly specified as grade)

**Rules:**
- Distinguish from STANDARD: "M25" is STANDARD (concrete mix), "Fe500" is STANDARD (steel grade)
- "Grade A insulation" → "Grade A" = GRADE

### 8. ACTION
What is being done to the material.

**Examples:**
- "supply", "installation", "testing", "commissioning"
- "supply and installation of"
- "apply", "fix", "erect", "construct"

**Rules:**
- Usually at the start of a BOQ line
- Often combined: "supply, installation, testing and commissioning"

---

## Tagging Scheme: BIOES

| Prefix | Meaning | Example |
|--------|---------|---------|
| B- | Begin | B-MATERIAL |
| I- | Inside | I-MATERIAL |
| E- | End | E-MATERIAL |
| S- | Single token | S-QUANTITY |
| O | Outside | O |

**Example:**

Tokens: `Supply` `and` `installation` `of` `100mm` `dia` `HDPE` `pipe` `-` `500` `RMT`

Tags: `B-ACTION` `I-ACTION` `E-ACTION` `O` `B-DIMENSION` `E-DIMENSION` `B-MATERIAL` `E-MATERIAL` `O` `S-QUANTITY` `S-UNIT`

---

## Relation Types (6)

| Relation | Head | Tail | Example |
|----------|------|------|---------|
| HAS_QUANTITY | MATERIAL | QUANTITY | "HDPE pipe" → "500" |
| HAS_UNIT | QUANTITY | UNIT | "500" → "RMT" |
| AT_LOCATION | MATERIAL | LOCATION | "tiles" → "ground floor" |
| OF_GRADE | MATERIAL | GRADE | "cement" → "OPC 53" |
| COMPLIES_WITH | MATERIAL | STANDARD | "steel" → "IS 1786" |
| HAS_DIMENSION | MATERIAL | DIMENSION | "pipe" → "100mm dia" |

---

## Quality Rules

1. **Every MATERIAL must have a QUANTITY** (if visible in the document)
2. **Every QUANTITY must have a UNIT** (if visible)
3. **No overlapping entities** of the same type
4. **Prefer longer spans** for MATERIAL (include dimensions/grades if adjacent)
5. **When uncertain, tag as O** rather than guessing

---

## Domain-Specific Notes

### Insulation Tenders
- Common materials: "mineral wool", "elastomeric foam", "nitrile rubber", "XLPE insulation"
- Common units: "sqm" (surface), "rmt" (pipe length), "kg" (weight)
- Standards: "IS 8183", "IS 9842", "ASTM C553", "ASTM C612"

### Civil/Structural Tenders
- Common materials: "concrete", "steel", "brickwork", "plastering"
- Common units: "cum", "kg", "sqm", "nos"
- Standards: "IS 456", "IS 1786", "M20", "M25", "Fe415", "Fe500"

### Electrical Tenders
- Common materials: "cable", "wire", "conduit", "switch", "DB box"
- Common units: "rmt", "nos", "sets"
- Standards: "IS 694", "IS 1554"

---

## Annotation Tool

Use `scripts/annotate_gold.py` or Label Studio.

**Output format:** JSON with `tokens` and `ner_tags` arrays.

```json
{
  "doc_id": "rfq_building_001",
  "source_file": "tender.pdf",
  "tokens": ["Supply", "and", "installation", "of", "100mm", "dia", "HDPE", "pipe", "-", "500", "RMT"],
  "ner_tags": ["B-ACTION", "I-ACTION", "E-ACTION", "O", "B-DIMENSION", "E-DIMENSION", "B-MATERIAL", "E-MATERIAL", "O", "S-QUANTITY", "S-UNIT"]
}
```

---

## Review Checklist

Before submitting annotations:
- [ ] All MATERIALs have corresponding QUANTITY tags
- [ ] All QUANTITYs have corresponding UNIT tags
- [ ] No standalone numbers are untagged (should be QUANTITY or O)
- [ ] BIOES tags are consistent (no I- without B-, no E- without B-/I-)
- [ ] Relations connect valid entity pairs
- [ ] Document source_file is recorded
