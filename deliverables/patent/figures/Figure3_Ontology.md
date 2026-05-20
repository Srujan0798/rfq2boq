# Figure 3: Construction Material Ontology Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ONTOLOGY STRUCTURE (249+ Materials)                      │
└─────────────────────────────────────────────────────────────────────────────┘

                           ┌──────────────┐
                           │ CONSTRUCTION  │
                           │   MATERIALS   │
                           │   (Root)      │
                           └───────┬──────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
   ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
   │ STRUCTURAL  │          │   FINISHING │          │  SERVICES   │
   │ MATERIALS   │          │   MATERIALS │          │  MATERIALS  │
   └──────┬──────┘          └──────┬──────┘          └──────┬──────┘
          │                        │                        │
    ┌─────┼─────┐            ┌─────┼─────┐            ┌─────┼─────┐
    │     │     │            │     │     │            │     │     │
    ▼     ▼     ▼            ▼     ▼     ▼            ▼     ▼     ▼
 ┌────┐┌────┐┌────┐     ┌────┐┌────┐┌────┐     ┌────┐┌────┐┌────┐
 │Cem ││Stl ││Cncr│     │Pls ││Pnt ││Til │     │Pip ││Wre ││Swt │
 │ent ││eel ││ete │     │tic ││    ││e   │     │ing ││    ││ch  │
 └────┘└────┘└────┘     └────┘└────┘└────┘     └────┘└────┘└────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        MATERIAL ATTRIBUTES                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CEMENT                                                                  │
│  ├── typical_units: ["bags", "tonnes"]                                     │
│  ├── grade_ranges: ["M15", "M20", "M25", "M30", "M35", "M40", "M45", "M50"]│
│  ├── standards: ["IS 269", "IS 8112", "IS 12269"]                          │
│  ├── co_occurrence: ["aggregate", "sand", "water", "admixture"]            │
│  └── default_rate_per_unit: ₹350/bag (varies by region)                   │
│                                                                             │
│  STEEL                                                                    │
│  ├── typical_units: ["kg", "tonnes"]                                       │
│  ├── grade_ranges: ["Fe250", "Fe415", "Fe500", "Fe550"]                    │
│  ├── standards: ["IS 2062", "IS 432 Part 1"]                               │
│  ├── co_occurrence: ["cement", "sand", "aggregate"]                        │
│  └── default_rate_per_unit: ₹65/kg (varies by grade)                      │
│                                                                             │
│  CONCRETE                                                                 │
│  ├── typical_units: ["m^3", "cum"]                                         │
│  ├── grade_ranges: ["M15", "M20", "M25", "M30", "M35"]                    │
│  ├── standards: ["IS 456"]                                                │
│  ├── composition: ["cement", "sand", "aggregate", "water"]               │
│  └── default_rate_per_unit: ₹5500/m³ (varies by grade)                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        ONTOLOGY QUERY EXAMPLES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Query: "OPC 53 grade cement"                                               │
│  → Match: cement → grade "M53" (IS 8112) → normalized to "OPC 53"         │
│                                                                             │
│  Query: "Supply 500 bags PPC"                                              │
│  → Match: cement → type "PPC" (Portland Pozzolana Cement)                  │
│  → Rate: ₹320/bag                                                          │
│                                                                             │
│  Query: "Fe500 steel TMT"                                                  │
│  → Match: steel → grade "Fe500" → type "TMT"                              │
│  → Rate: ₹68/kg                                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        VALIDATION RULES                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. GRADE VALIDATION:                                                       │
│     IF material.grade NOT IN material.grade_ranges THEN warning            │
│                                                                             │
│  2. UNIT VALIDATION:                                                        │
│     IF extracted_unit NOT IN material.typical_units THEN propose_canonical │
│                                                                             │
│  3. QUANTITY SANITY:                                                        │
│     IF quantity > material.quantity_threshold THEN flag_review             │
│                                                                             │
│  4. CO-OCCURRENCE RULES:                                                    │
│     IF material_A present AND material_B NOT IN co_occurrence THEN warn   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```