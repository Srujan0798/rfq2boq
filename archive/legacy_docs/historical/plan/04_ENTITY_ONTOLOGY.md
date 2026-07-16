# ENTITY TAXONOMY + RELATION SCHEMA + IFC ALIGNMENT
## "What we extract and what we mean by it"

Frozen at start of Step 2. Versioned (`v1`). Changes go through ADR.

---

## A. ENTITY TYPES (8) — BIOES tags = `B-X / I-X / O / E-X / S-X` for X in:

| # | Tag | Definition | Examples | IFC alignment | Cardinality per item |
|---|---|---|---|---|---|
| 1 | `MATERIAL` | The substance / product being supplied or used | "M20 concrete", "TMT steel bars", "Class-A brick" | IfcMaterial / IfcProduct | 1 per row |
| 2 | `QUANTITY` | The numeric value | "150.5", "1,200", "2.5" | IfcQuantityCount/Volume/Area/Length | 1 per row |
| 3 | `UNIT` | The measurement unit | "m³", "kg", "no.", "lm", "ls" | IfcUnit | 1 per row |
| 4 | `LOCATION` | Where in the building/project | "ground floor", "Block A", "external walls" | IfcSpatialStructureElement | 0-1 per row |
| 5 | `DIMENSION` | Physical size/spec | "230 mm thick", "Ø12 mm", "1.5 × 3.0 m" | IfcQuantityLength + composite | 0-3 per row |
| 6 | `STANDARD` | Code / standard the item must meet | "IS 456", "ASTM A615", "BS EN 197-1" | reference (custom) | 0-n per row |
| 7 | `ACTION` | Verb describing the work | "supply", "install", "lay", "cast", "plaster" | IfcTask.PredefinedType | 0-1 per row |
| 8 | `GRADE` | Quality grade / class | "Fe500", "M20", "Class A" | IfcMaterialProperty | 0-1 per row |

**Why 8 and not more.** Smaller taxonomy = higher κ, easier annotation, faster training. ALL OTHER concepts (e.g., color, supplier, contractor) are stored as `attributes` on the canonical row, not as separate entity types.

---

## B. RELATION TYPES (6)

| # | Relation | Head → Tail | Example |
|---|---|---|---|
| 1 | `HAS_QUANTITY`  | MATERIAL → QUANTITY  | concrete → 150.5 |
| 2 | `HAS_UNIT`      | QUANTITY → UNIT      | 150.5 → m³ |
| 3 | `AT_LOCATION`   | MATERIAL → LOCATION  | brickwork → ground floor |
| 4 | `OF_GRADE`      | MATERIAL → GRADE     | concrete → M20 |
| 5 | `COMPLIES_WITH` | MATERIAL → STANDARD  | TMT → IS 1786 |
| 6 | `HAS_DIMENSION` | MATERIAL → DIMENSION | wall → 230 mm thick |

`ACTION` attaches to MATERIAL via implicit relation captured in canonical row (`row.action = "supply"`), not as an explicit RE label — reduces RE noise.

---

## C. BIOES TAGGING — examples

```
Supply  O
and     O
lay     B-ACTION
M20     B-GRADE
concrete S-MATERIAL
of      O
150     B-QUANTITY
cu.m    S-UNIT
in      O
ground  B-LOCATION
floor   E-LOCATION
slab    O
conforming O
to      O
IS      B-STANDARD
:       I-STANDARD
456     E-STANDARD
.       O
```

Note: `M20 concrete` is split — `M20` is `GRADE`, `concrete` is `MATERIAL`. This lets us reuse the same MATERIAL across grades.

---

## D. CANONICAL BOQ ROW (target output)

```json
{
  "item_no": 14,
  "action": "lay",
  "material": "concrete",
  "grade": "M20",
  "dimensions": [{"value": 0.23, "unit": "m", "axis": "thickness"}],
  "quantity": 150.5,
  "unit": "m^3",
  "location": "ground floor slab",
  "standard": ["IS 456"],
  "description_raw": "Supply and lay M20 concrete of 150 cu.m in ground floor slab...",
  "source_pages": [3],
  "source_spans": [{"start": 41200, "end": 41345}],
  "confidence": 0.91,
  "warnings": []
}
```

---

## E. ONTOLOGIES — files we ship

```
ontology/
├── cto.ttl            # Construction Terms Ontology (custom)
│                       — 500+ concepts: materials, grades, units, standards, actions
├── ifcOWL_subset.ttl  # IFC 4.0 subset (IfcMaterial, IfcUnit, IfcSpatial..., IfcTask)
├── mappings.yaml      # CTO concept → IFC class mapping
└── validators.py      # SHACL-light or rdflib SPARQL queries enforcing typing
```

CTO is bootstrapped from:
- ISO 12006-3 dictionary terms (open subset)
- IS codes term index (open)
- Sousa et al. 2024 — task taxonomy
- Manual additions from corpus EDA

---

## F. UNIT NORMALIZATION TABLE (excerpt)

| Surface form | Canonical | Notes |
|---|---|---|
| `cu.m`, `cum`, `m^3`, `m3`, `cubic meter`, `cubic metre` | `m^3` | volume |
| `sq.m`, `sqm`, `m^2`, `m2`, `square meter`           | `m^2` | area |
| `R.m`, `Rm`, `rm`, `lm`, `r.m.`, `running meter`     | `lm`  | length |
| `MT`, `Tonne`, `tonne`, `ton`                        | `t`   | mass; **`ton` ≠ US short-ton in this domain** |
| `Nos`, `nos`, `no.`, `nr`, `each`, `ea`              | `no.` | count |
| `LS`, `Lump-sum`, `l.s.`, `lumpsum`                  | `ls`  | non-quantified |
| `kg`, `Kg`, `KG`                                     | `kg`  | mass |

Full table lives at `rules/units_table.csv` and is unit-tested.

---

## G. STANDARDS REGISTRY (excerpt)

| Body | Regex | Example |
|---|---|---|
| IS (Indian Standard) | `IS\s*[:\-]?\s*\d{1,5}(\s*Part\s*\d+)?(\s*[-:]\s*\d{4})?` | `IS 456`, `IS 1786:1985`, `IS 13920 Part 1` |
| BS (British)         | `BS\s*(EN\s*)?\d{1,5}([\-:]\d{1,4})?` | `BS 5950`, `BS EN 197-1` |
| EN (European)        | `EN\s*\d{1,5}` | `EN 206` |
| ASTM (US)            | `ASTM\s*[A-Z]\d{1,4}(\/[A-Z]\d{1,4}M)?(\s*[-:]\s*\d{2,4})?` | `ASTM A615/A615M-20` |
| ACI                  | `ACI\s*\d{3}[A-Z]?(\.\d)?(\-\d{2})?` | `ACI 318-19` |

Standards mentioned but not matched go to `STANDARD_UNKNOWN_WARNING`.

---

## H. ANNOTATION POLICY

1. **Span minimality** — annotate the shortest meaningful span. "M20 concrete" → two spans.
2. **Numeric inclusion** — include sign and decimals: `-12.5` is one QUANTITY.
3. **Compound units** — `kg/m²` is one UNIT.
4. **Standards punctuation** — include the colon: `IS 456:2000` is one STANDARD.
5. **Locations** — include hierarchy: `Block A, ground floor` = single LOCATION span (it carries semantic unity).
6. **Negative cases** — phrases like "specifications below" or "as per drawing" are NOT entities (they're references; handled separately).

Examples doc: `docs/annotation_guide.md` (50 adjudicated examples covering 14 tricky cases).

---

## I. METRICS WE REPORT PER ENTITY TYPE

| Type | Why we care | Floor |
|---|---|---|
| MATERIAL | most-frequent; drives cost-DB join | F1 ≥ 0.90 |
| QUANTITY | wrong number = wrong contract | F1 ≥ 0.92 |
| UNIT     | wrong unit = wrong contract     | F1 ≥ 0.92 |
| LOCATION | important for partial scope     | F1 ≥ 0.80 |
| DIMENSION| nice-to-have                    | F1 ≥ 0.75 |
| STANDARD | regulatory compliance           | F1 ≥ 0.85 |
| ACTION   | classifies row type             | F1 ≥ 0.80 |
| GRADE    | discriminates material variants | F1 ≥ 0.80 |

Micro-F1 over all = target 0.85.

---

**Status:** ✅ Ontology v1 frozen. ADR required to add/remove entity or relation types.
