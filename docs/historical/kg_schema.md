# RFQ2BOQ Knowledge Graph Schema

## Nodes

### Material
```
(:Material {
  name: string,           -- Primary name e.g., "galvanized steel"
  category: string,        -- e.g., "structural steel", "cement"
  density: float,          -- kg/m³ (if applicable)
  aliases: list[string],   -- e.g., ["GI steel", "galv steel"]
  common_units: list[string] -- e.g., ["kg", "sqm", "cum"]
})
```

### Standard
```
(:Standard {
  code: string,            -- e.g., "IS 2062", "ASTM A615"
  body: string,           -- e.g., "BIS", "ASTM", "BS"
  year: int,              -- e.g., 2011
  title: string,          -- Full title of standard
  aliases: list[string]   -- e.g., ["IS2062", "IS:2062"]
})
```

### Unit
```
(:Unit {
  symbol: string,         -- e.g., "kg", "m³", "sqm"
  dimension: string,      -- e.g., "mass", "volume", "area"
  canonical: string       -- e.g., "kg", "m^3", "m^2"
})
```

### Grade
```
(:Grade {
  code: string,           -- e.g., "Fe 500", "M20", "Grade 43"
  applies_to_material: string, -- e.g., "steel", "concrete"
  properties: dict       -- Additional grade-specific properties
})
```

### Location
```
(:Location {
  name: string,           -- e.g., "ground floor", "basement"
  type: string,           -- e.g., "floor", "wall", "structural"
  aliases: list[string]   -- e.g., ["GF", "ground level"]
})
```

### Region
```
(:Region {
  name: string,           -- e.g., "India", "USA", "Europe"
  country: string         -- ISO country code
})
```

### ProjectType
```
(:ProjectType {
  name: string             -- e.g., "residential", "commercial", "road", "bridge"
})
```

## Relationships

### Material - Standard
```
(Material)-[:COMPLIES_WITH {confidence: float}]->(Standard)
-- confidence: how strongly this material must comply with this standard
-- e.g., (cement)-[:COMPLIES_WITH {confidence: 1.0}]->(IS 456)
```

### Material - Unit
```
(Material)-[:MEASURED_IN {is_default: bool}]->(Unit)
-- is_default: typical unit for this material
-- e.g., (steel)-[:MEASURED_IN {is_default: true}]->(kg)
```

### Material - Grade
```
(Material)-[:HAS_GRADE]->(Grade)
-- e.g., (concrete)-[:HAS_GRADE]->(M20)
```

### Standard - Standard (hierarchy)
```
(Standard)-[:SUPERSEDES {since: int}]->(Standard)
-- e.g., (IS 456:2016)-[:SUPERSEDES {since: 2000}]->(IS 456:2000)
```

### Standard - Standard (equivalence)
```
(Standard)-[:EQUIVALENT_TO {region: string}]->(Standard)
-- e.g., (IS 2062)-[:EQUIVALENT_TO {region: "India/International"}]->(ASTM A36)
-- e.g., (IS 456)-[:EQUIVALENT_TO {region: "India/International"}]->(BS EN 206)
```

### Unit - Unit (conversion)
```
(Unit)-[:CONVERTS_TO {factor: float}]->(Unit)
-- factor: multiply value in source unit to get target unit
-- e.g., (kg)-[:CONVERTS_TO {factor: 0.001}]->(tonne)
-- e.g., (m)-[:CONVERTS_TO {factor: 1000}]->(mm)
```

### Material - ProjectType
```
(Material)-[:USED_IN]->(ProjectType)
-- e.g., (bridgeSteel)-[:USED_IN]->(bridge)
```

## Indexes

```cypher
CREATE INDEX material_name FOR (m:Material) ON (m.name);
CREATE INDEX standard_code FOR (s:Standard) ON (s.code);
CREATE INDEX unit_symbol FOR (u:Unit) ON (u.symbol);
CREATE INDEX grade_code FOR (g:Grade) ON (g.code);
CREATE INDEX location_name FOR (l:Location) ON (l.name);
```

## Constraints

```cypher
CREATE CONSTRAINT material_name_unique FOR (m:Material) REQUIRE m.name IS UNIQUE;
CREATE CONSTRAINT standard_code_unique FOR (s:Standard) REQUIRE s.code IS UNIQUE;
CREATE CONSTRAINT unit_symbol_unique FOR (u:Unit) REQUIRE u.symbol IS UNIQUE;
CREATE CONSTRAINT grade_code_unique FOR (g:Grade) REQUIRE g.code IS UNIQUE;
```

## Cross-Reference Examples

### Steel Standards
- IS 2062 ↔ ASTM A36 (structural steel)
- IS 2062 ↔ BS EN 10025 (hot rolled steel)
- ASTM A615 ↔ IS 1786 (rebar)

### Cement Standards
- IS 456 ↔ ASTM C150 (Portland cement)
- IS 1489 ↔ BS EN 197 (Portland pozzolana cement)

### Concrete Standards
- IS 456 ↔ BS EN 206 (concrete specification)
- M20 ↔ C20 (grade equivalence)

### Unit Conversions
- 1 tonne = 1000 kg
- 1 m³ = 1000 liters
- 1 sqm = 10.764 sq ft
- 1 m = 1000 mm = 100 cm