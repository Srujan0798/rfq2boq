# OmniClass Mapping for RFQ2BOQ

## Overview

This document describes the bidirectional mapping between RFQ2BOQ's 8 entity types and the OmniClass classification system (OmniClass 2019).

## Why OmniClass?

OmniClass is the industry-standard classification system used by:
- Autodesk Revit (BIM)
- Graphisoft ArchiCAD
- Nemetschek Allplan
- Oracle Primavera
- SAP PM

By mapping our entities to OmniClass codes, our BOQ output becomes automatically interoperable with these tools.

## Entity-to-OmniClass Mapping

| RFQ2BOQ Entity | OmniClass Table | Description |
|----------------|-----------------|-------------|
| **MATERIAL** | Table 23 (Products) | Construction products and materials |
| **QUANTITY** | N/A | Plain numeric values have no OmniClass equivalent |
| **UNIT** | N/A | Standard SI unit symbols (kg, m, etc.) |
| **LOCATION** | Table 13 (Spaces by Function) | Spatial references and floor levels |
| **DIMENSION** | Table 49 (Properties) | Size and dimension specifications |
| **STANDARD** | Table 41 (Materials and Methods) | Reference standards and codes |
| **ACTION** | Table 22 (Work Results) | Construction activities and work results |
| **GRADE** | Table 23 (Products - specification) | Quality grades and material specifications |

## Material-Specific Codes

| Material | OmniClass Code | Description |
|----------|----------------|-------------|
| Cement | 23-13-21-13 | Portland cement products |
| Concrete | 23-13-21-19 | Ready-mixed concrete |
| Steel reinforcement | 23-13-25-11 | Steel bars for reinforcement |
| Structural steel | 23-13-25-15 | Structural steel sections |
| Brick | 23-13-23-11 | Clay bricks |
| Mortar | 23-13-21-23 | Mortar and grout |
| Plaster | 23-13-29-11 | Plaster products |
| Tile | 23-15-23-11 | Ceramic tiles |

## Action-Specific Codes

| Action | OmniClass Code | Description |
|--------|----------------|-------------|
| Supply | 22-01 | Supply of materials |
| Install | 22-03 | Installation work |
| Lay | 22-03-21 | Laying work (flooring, etc.) |
| Fix | 22-03-31 | Fixing work (fixtures, etc.) |
| Construct | 22-03 | General construction |
| Cast | 22-03-11 | Casting concrete |
| Erect | 22-03-31 | Erecting structures |
| Apply | 22-05 | Application work (paint, etc.) |

## Usage

```python
from src.ontology.omniclass import OmniClassMapper

mapper = OmniClassMapper()

# Map entity type to OmniClass
result = mapper.map_entity("MATERIAL", "cement")
print(result)
# Output: {'table': '23', 'default_code': '23-13', 'code': '23-13-21-13', 'specific': True}

# Reverse lookup
entity_type = mapper.reverse_lookup("23-13-21-13")
print(entity_type)
# Output: 'MATERIAL'

# Get material-specific code
code = mapper.get_material_code("cement")
print(code)
# Output: '23-13-21-13'
```

## Indian Construction Extensions

The mapping includes Indian-specific extensions for BIS (Bureau of Indian Standards) codes:

- **IS 456** → Concrete work (22-03-11)
- **IS 269** → OPC cement (23-13-21-13)
- **IS 2062** → Steel products (23-13-25-11)
- **M25, M30** → Concrete grades (23-13-21-19)
- **Fe415, Fe500** → Steel grades (23-13-25-11)

## Notes

1. Some entities (QUANTITY, UNIT) genuinely have no OmniClass equivalent — this is expected and handled gracefully.

2. OmniClass codes use dashes to separate hierarchy levels (e.g., 23-13-21-13), not to be parsed numerically.

3. Partial codes (e.g., "23-13") are valid and represent broader categories.

4. The mapping is stored in `data/ontology/omniclass_map.json` for easy updates without code changes.

## References

- OmniClass: https://www.csiresources.org/standards/omniclass
- buildingSMART International: https://buildingsmart.org/standards/omniclass-tables/