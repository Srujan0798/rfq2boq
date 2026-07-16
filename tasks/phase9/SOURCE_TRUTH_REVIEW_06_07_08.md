# SOURCE TRUTH REVIEW — 06_avante / 07_grew / 08_sael

**Author:** independent worker agent (this repo only, `phase9-final`)
**Date:** 2026-07-07
**Scope:** independently re-derive the correct source row count for the three
sacred-10 docs whose `source_truth.json` count is disputed by the sacred-10
fidelity test. Read source files directly with `openpyxl` / `pdfplumber`
(never the pipeline). Follow the D4 rule from
[`docs/GOLD_METHODOLOGY.md`](../../docs/GOLD_METHODOLOGY.md) §2 — "a row that
is a section title only — it has an item number but no real quantity and no
real unit, and exists solely to introduce child items — is NOT a BOQ line
item and is excluded from gold."

**Files inspected (raw, not via pipeline):**
- `data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Boq_132.pdf`
- `data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf`
- `data/real_rfqs/swa_enquiries/08_sael/Copy of Insulation Enquiry - SAEL.xlsx`

**Method:** raw `pdfplumber.open().pages[i].extract_tables()` and raw
`openpyxl.load_workbook(..., data_only=True).iter_rows(values_only=True)`.
D4 rule applied exactly as written: a row counts as a BOQ line item iff it
has a real quantity **and** a real unit **and** is not a section-title-only
row that exists solely to introduce children.

---

## TL;DR — honest counts vs the test's expected numbers

| doc_id | current `source_truth.json` | test expects | **my honest count (per D4)** | match? |
|---|---|---|---|---|
| 06_avante_kirloskar_pune | 36 | 31 | **36** | NO — off by 5 |
| 07_grew_solar_narmadapuram | 11 | 9 | **11** | NO — off by 2 |
| 08_sael | 19 (counts the TDS file, not the enquiry — see §4) | 16 | **14** | NO — off by 2 |

The test's "expected 31/9/16" matches the **gold files' entry counts**, not
the D4-rule count from the raw source. The gold files were produced by a
convention that is **broader than the D4 rule as written**:
- Gold **excludes** rows whose quantity is `RO`/`R/O` (Rate-Only placeholder).
  D4 as written does not — `RO` rows have a real unit (e.g. `sq.m`, `Nos.`,
  `RM`) and the rule's exclusion criterion is "no real quantity **and** no
  real unit". This explains the 06_avante and 07_grew deltas.
- Gold **keeps** parent/spec rows with `qty=None, unit=None` in the source
  as `qty=0, unit="no."` placeholders (08_sael rows at source rows 4 and 15).
  D4 as written excludes these — they are "no real quantity **and** no real
  unit, and exist solely to introduce child items". This explains the
  08_sael delta.

The orchestrator's stated correction direction (31/9/16) would align
`source_truth.json` with the gold convention. My honest D4-rule count
disagrees. Per the dispatch's explicit instruction ("an honest mismatch is a
correct outcome here"), I report the mismatch rather than reconcile it.

---

## 1. 06_avante_kirloskar_pune — `Insulation Boq_132.pdf`

**Tool:** `pdfplumber.open()` → `page.extract_tables()`
**Pages:** 2. Page 1 table = 38 raw rows (alternating content/empty separator
= 19 non-empty). Page 2 table = 47 raw rows (= 24 non-empty). 7 of those
non-empty rows are section/parent titles with **no qty and no unit** (D4
excludes). The remaining 36 non-empty rows have a real UOM column (`sq.m`,
`Sq.m.`, `Nos.`, or `RM`).

### 1.1 Section/parent titles excluded by D4 (7 rows — no qty AND no unit)

These are the "exists solely to introduce child items" rows the D4 rule
targets. I exclude them.

| Page | Table row | Item | Material (snippet) | Qty | Unit | Why excluded |
|---|---|---|---|---|---|---|
| 1 | 1 | F | `THERMAL INSULATION` | — | — | Section header; introduces 75-82 |
| 1 | 3 | `#REF!` | `Supply and installation of External Thermal insulation (Nitrile Rubber) with 7 mil thick factory laminated fibreglass cloth protective coating on ducts as per the specifications.` | — | — (col 5 = "Comply" remark) | Parent spec; introduces #REF! children r5/r7/r9/r11 |
| 1 | 15 | 76 | `Supply, installation testing and commissioning of acoustic insulation. Material shall be nitrile rubber with 140-180 Kg/m3 density and all accessories as per specification.` | — | — (col 5 = "Complies for density 180-220 Kg/m3") | Parent spec; introduces 76.1 |
| 1 | 25 | 79 | `Supplying, installing and testing of 19mm thick insulation (Nitrile Rubber) with 7 mil thick factory laminated fibreglass cloth protective coating on chilled water and condensate drain piping and fittings like valves, flanges union, etc. as per the approved shop drawings and specifications.` | — | — (col 5 = "Comply") | Parent spec; introduces 79.1-79.5 |
| 1 | 37 | 80 | `Supply, installation and testing of 25 mm thick insulation (Nitrile Rubber) with 7 mil thick factory laminated fibreglass cloth protective coating on chilled water pipes and fittings like valves, flanges and unions, etc. as per approved shop drawings and specifications.` | — | — (col 5 = "Comply") | Parent spec; introduces 80.1-80.6 |
| 2 | 13 | 81 | `Supply, installation and testing of 32mm thick insulation (Nitrile Rubber) with 7mil thick factory laminated fibreglass cloth protective coating on chilled water pipes and fittings like valves, flanges and unions, etc. as per approved shop drawings and specifications.` | — | — (col 5 = "Comply") | Parent spec; introduces 81.1-81.10 |
| 2 | 35 | 82 | `Supply, installation, testing & commissioning of 32mm thick insulation with aluminium clading and UV treatment over pipes exposed to sun & Plant room piping to be consider with Aluminium cladding.` | — | — (col 5 = "Comply with Nitrile rubber") | Parent spec; introduces 82.1-82.6 |

### 1.2 Rows that count as BOQ line items per D4 (36 rows — have a real UOM)

The D4 rule's exclusion criterion is "no real quantity **and** no real unit".
Rows with `qty=RO`/`qty=R/O` (Rate-Only placeholder) **do** have a real unit
(`sq.m`, `Nos.`, or `RM`). The rule does not exclude them. I count them.

| Page | Table row | Item | Material (snippet) | Qty | Unit |
|---|---|---|---|---|---|
| 1 | 5 | `#REF!` | `13 mm thick insulation for supply air ducts in return air path.` | 6163 | sq.m |
| 1 | 7 | `#REF!` | `19 mm thick insulation for return air ducts.` | 576 | sq.m |
| 1 | 9 | `#REF!` | `25 mm thick insulation for supply duct (not in RA path).` | RO | sq.m |
| 1 | 11 | `#REF!` | `25 mm thick insulation for supply & return air ducts exposed to weather.` | RO | sq.m |
| 1 | 13 | 75 | `25 mm thick insulation for ducts exposed to atmosphere with UV protection of thickness minimum 7 mm` | 3443 | sq.m |
| 1 | 17 | 76.1 | `15 mm thick` | 2664 | sq.m |
| 1 | 19 | 77 | `Supply and installation of acoustic lining of walls of mechanical plant room, AHU rooms, Fan rooms, etc. covered with open cell Nitrile rubber with density 140-180 kg/m3 as per the approved shop drawings & specifications. All longitudinal and transfer joint shall be covered with 22-gauge 50 mm wide GI strip with screws` | RO | Nos. |
| 1 | 21 | 77.1 | `15 mm thick acoustic lining with Nitrile Rubber` | 9351 | Sq.m. |
| 1 | 23 | 78 | `Supply, installation of acoustic enclosure for Axial flow fans. The outer panel shall be made of galvanized preplasticised sheet of 24 gage thick and internally lined with 50mm thick fibre glass having 64 Kg/cum density and covered with tissue and 28 gauge perforated aluminium inside as shown in drawings.` | RO | Nos. |
| 1 | 27 | 79.1 | `25 mm dia pipes` | 1507 | RM |
| 1 | 29 | 79.2 | `20 mm dia pipes` | 1246 | RM |
| 1 | 31 | 79.3 | `15 mm dia pipes` | RO | RM |
| 1 | 33 | 79.4 | `50 mm dia condensate drain pipes.` | 522 | RM |
| 1 | 35 | 79.5 | `25 mm dia condensate drain pipes.` | 260 | RM |
| 2 | 1 | 80.1 | `100 mm dia pipes` | 345 | RM |
| 2 | 3 | 80.2 | `80 mm dia pipes` | 902 | RM |
| 2 | 5 | 80.3 | `65 mm dia pipes` | 201 | RM |
| 2 | 7 | 80.4 | `50 mm dia pipes` | 1946 | RM |
| 2 | 9 | 80.5 | `40 mm dia pipes` | 792 | RM |
| 2 | 11 | 80.6 | `32 mm dia pipes` | 1320 | RM |
| 2 | 15 | 81.1 | `400 mm dia pipes` | 53 | RM |
| 2 | 17 | 81.2 | `300 mm dia pipes` | 45 | RM |
| 2 | 19 | 81.3 | `250 mm dia pipes` | 450 | RM |
| 2 | 21 | 81.4 | `200 mm dia pipes` | 386 | RM |
| 2 | 23 | 81.5 | `150 mm dia pipes` | 74 | RM |
| 2 | 25 | 81.6 | `125 mm dia pipes` | 273 | RM |
| 2 | 27 | 81.7 | `600 mm dia pipes` | 36 | RM |
| 2 | 29 | 81.8 | `500 mm dia pipes` | 200 | RM |
| 2 | 31 | 81.9 | `450 mm dia pipes` | 113 | RM |
| 2 | 33 | 81.10 | `350 mm dia pipes` | 41 | RM |
| 2 | 37 | 82.1 | `300 mm dia pipes` | 16 | RM |
| 2 | 39 | 82.2 | `250 mm dia pipes` | 140 | RM |
| 2 | 41 | 82.3 | `200 mm dia pipes` | 168 | RM |
| 2 | 43 | 82.4 | `150 mm dia pipes` | 176 | RM |
| 2 | 45 | 82.5 | `600 mm dia pipes` | 30 | RM |
| 2 | 47 | 82.6 | `500 mm dia pipes` | 47 | RM |

### 1.3 Final count for 06_avante_kirloskar_pune

**My honest D4 count: 36 BOQ line items.**

- 7 D4-excluded section/parent titles (no qty AND no unit).
- 36 remaining rows have a real UOM column. Of these, 5 have `qty=RO`
  (rows: p1-r9 `#REF!` 25mm, p1-r11 `#REF!` 25mm, p1-r19 item 77,
  p1-r23 item 78, p1-r31 item 79.3). Per the D4 rule as written in
  `docs/GOLD_METHODOLOGY.md` §2, these are **not** section-title-only rows
  (they have a real unit), so they are **not** excluded.
- Total: 36.
- `source_truth.json` currently says 36 ✓ (matches D4).
- Gold `06_avante_kirloskar_pune.rowgold.json` has 31 entries — it excludes
  the 5 RO rows. **That is a gold-vs-D4 discrepancy, not a D4 vs source
  discrepancy.**
- The test "expects 31" — the test's expected value is the gold's
  convention, not the D4 rule. The test reason text in
  `tests/integration/test_sacred10_fidelity.py:82` says
  `"source_row_count=36 should be 31; source_truth correction not P1_03"`.

**My honest answer: 36, not 31.** The 5-row gap is the 5 RO rows
(rows: 2× `#REF!` 25mm at p1 r9/r11, item 77, item 78, item 79.3). The
gold's 31 is the gold convention, not the D4 rule.

---

## 2. 07_grew_solar_narmadapuram — `108, BOQ compliance, Grew Energy.pdf`

**Tool:** `pdfplumber.open()` → `page.extract_tables()`
**Pages:** 1. The PDF has 5 separate tables on the page. The pdfplumber
extraction gave: Table 1 (6 rows — 11.1 thermal insulation block), Table 2
(18 rows — compliance remark column, mostly empty), Table 3 (2 rows —
12 acoustic lining), Table 4 (5 rows — 8 CHW piping block), Table 5 (2
rows — items 6 & 7 underfloor/underdeck).

### 2.1 Section/parent titles excluded by D4 (4 rows — no qty AND no unit)

| Table | Row | Item | Material (snippet) | Qty | Unit | Why excluded |
|---|---|---|---|---|---|---|
| 1 | 1 | 11 | `THERMAL INSULATION` | — | — | Section header; introduces 11.x |
| 1 | 2 | (blank) | `Supply, Installation of Insulation material. It shall be Class "O" type low fire propagation with closed cell elastomeric nitrile rubber having factory laminated glass reinforced minimum 12 microns pure aluminum foil...` | — | — (col 4 = `compliance` remark header) | Parent spec; introduces 11.1-11.4 |
| 3 | 1 | 12 | `ACOUSTIC LINING` | — | — | Section header; introduces 12.x |
| 4 | 1 | 8 | `S.I.T.C. of Thermal insulation of CHW Pipings with low fire propagation Class O & UL94(VO,HB Passed) FM Apprroved Closed Cell Nitrile Rubber... Insulation covering to be 26G aluminium cladding, coated with a special UV protection.` | — | — (col 4 = `Plain NBR to Quote` remark) | Parent spec; introduces 8.1-8.4 |

### 2.2 Rows that count as BOQ line items per D4 (11 rows — have a real UOM)

| Table | Row | Item | Material (snippet) | Qty | Unit |
|---|---|---|---|---|---|
| 1 | 3 | 11.1 | `32 mm thick for Clean Room SA Duct` | 15000 | Sqm. |
| 1 | 4 | 11.2 | `25 mm thick for Clean Room SA Duct` | 23750 | Sqm. |
| 1 | 5 | 11.3 | `19 mm thick for Comfort SA Duct` | 8500 | Sqm. |
| 1 | 6 | 11.4 | `13 mm thick for Comfort RA Duct` | 5000 | Sqm. |
| 3 | 2 | (blank) | `Supply, Installation and Testing of Accoustic lining with 10mm thick Class 1 rating Open Cell nitrile rubber insulation material with density of 140 to 180 kg /m³ along with manufacturer recommended adhesive.` | 500 | Sqm. |
| 4 | 2 | 8.1 | `75 mm thick Insulation on 1200NB to 1000NB` | 1,976.00 | Sq. Mtr. |
| 4 | 3 | 8.2 | `51 mm thick Insulation on 950NB to 500NB` | 3,600.00 | Sq. Mtr. |
| 4 | 4 | 8.3 | `38 mm thick Insulation on 450NB to 80NB` | 14,800.00 | Sq. Mtr. |
| 4 | 5 | 8.4 | `19 mm thick Insulation on 65NB / 50NB / 40NB / 32NB / 25NB / 20NB / 15NB` | 7,400.00 | Sq. Mtr. |
| 5 | 1 | 6 | `Supply & Installation of underfloor insulation as per specification. Material shall be 19mm thick Class "0" Closed cell nitrile rubber elastomeric foam insulation...` | R/O | Sqm |
| 5 | 2 | 7 | `Supply & Installation of underdeck insulation as per specification. Material shall be 19mm thick Class "0" Closed cell nitrile rubber elastomeric foam insulation...` | R/O | Sqm |

### 2.3 Final count for 07_grew_solar_narmadapuram

**My honest D4 count: 11 BOQ line items.**

- 4 D4-excluded section/parent titles (no qty AND no unit).
- 11 remaining rows have a real UOM column. Of these, 2 have `qty=R/O`
  (items 6 underfloor and 7 underdeck). Per the D4 rule as written, these
  are **not** section-title-only rows (they have a real unit, `Sqm`), so
  they are **not** excluded.
- Total: 11.
- `source_truth.json` currently says 11 ✓ (matches D4).
- Gold `07_grew_solar_narmadapuram.rowgold.json` has 9 entries — it excludes
  the 2 R/O rows (items 6 and 7). **That is a gold-vs-D4 discrepancy.**
- The test "expects 9" — the test's expected value is the gold convention.

**My honest answer: 11, not 9.** The 2-row gap is the 2 R/O rows
(items 6 underfloor, 7 underdeck). The gold's 9 is the gold convention,
not the D4 rule.

---

## 3. 08_sael — `Copy of Insulation Enquiry - SAEL.xlsx`

**Tool:** `openpyxl.load_workbook(..., data_only=True)` → `ws.iter_rows(values_only=True)`
**Sheet:** `Sheet1` (the only sheet). `ws.dimensions = A3:E22`,
`ws.max_row = 22`, `ws.max_column = 5`. Columns in the BOQ area: A=item_no,
B=material, C=unit, D=qty, E=technical-compliance (header text only).

### 3.1 Section/parent titles excluded by D4 (3 rows — no qty AND no unit)

| Sheet row | Item | Material (snippet) | Qty | Unit | Why excluded |
|---|---|---|---|---|---|
| 3 | 11 | `THERMAL INSULATION ` | None | None (col E = "Technical Compliance / Deviations to be filled" header) | Section header; introduces 11.1.x |
| 4 | 11.1 | `Supply, Installation of Insulation material. Thermal insulation of Ducts with low smoke/low fire propagating FM listed closed cell nitrile rubber insulation having ASTM E84 (25/50) ratings with Class 0 and UL94(V0 &HB) approvals...` | None | None | Parent spec; introduces 11.1.1-11.1.5 |
| 15 | 8 | `S.I.T.C. of Thermal insulation of CHW Pipings with low fire propagation Class O Closed Cell Nitrile Rubber with K value of 0.035 w/m.k at 0 Deg C Temp, and UL94 certified from UL lab. Insulation to be laminated with Grey colored 400 microns/380 gsm multiple layered laminate of polymeric material reinforced with scrim...` | None | None | Parent spec; introduces 8.1-8.7 |

### 3.2 Rows that count as BOQ line items per D4 (14 rows — have real qty AND real unit)

| Sheet row | Item | Material (snippet) | Qty | Unit |
|---|---|---|---|---|
| 5 | 11.1.1 | `50 mm thick  for Clean Room SA Duct - MAU Plenum` | 2500 | Sqm. |
| 6 | 11.1.2 | `32 mm thick  for Clean Room SA Duct - For 15 Meter from MAU` | 9000 | Sqm. |
| 7 | 11.1.3 | `25 mm thick  for Clean Room SA Duct - For After 15 Meter All Ducts` | 42000 | Sqm. |
| 8 | 11.1.4 | `19 mm thick for Comfort SA Duct` | 9500 | Sqm. |
| 9 | 11.1.5 | `13 mm thick for Comfort RA Duct` | 9500 | Sqm. |
| 11 | 11.2 | `Supply, Installation of Insulation material. Acoustic Insulation of Duct Internal linings starting from AHU Collars till 5-7 meters by Dust and Fiber free Open Cell Nitrile Rubber... Thickness - Min 25 mm` | 2500 | Sqm. |
| 13 | 6 | `Supply & Installation of underdeck insulation as per specification. Material shall be 19mm thick Class " 0 " Closed cell nitrile rubber elastomeric foam insulation laminated with chemically treated glass cloth  of 7 mil / 0.18 mm thickness...` | 300 | Sqm |
| 16 | 8.1 | `50 mm thick Insulation ` | 7500 | Sq. Mtr. |
| 17 | 8.2 | `44mm thick Insulation ` | 8500 | Sq. Mtr. |
| 18 | 8.3 | `38 mm thick Insulation` | 4000 | Sq. Mtr. |
| 19 | 8.4 | `32 mm thick Insulation` | 7000 | Sq. Mtr. |
| 20 | 8.5 | `25mm Thick Insulation` | 4500 | Sq. Mtr. |
| 21 | 8.6 | `19mm Thick Insulation` | 1500 | Sq. Mtr. |
| 22 | 8.7 | `13mm Thick Insulation` | 150 | Sq. Mtr. |

(Empty separator rows at sheet rows 1, 2, 10, 12, 14 — not counted.)

### 3.3 Final count for 08_sael

**My honest D4 count: 14 BOQ line items.**

- 3 D4-excluded rows: row 3 (section title `THERMAL INSULATION`), row 4
  (parent spec `11.1`), row 15 (parent spec `8`). All three have
  `qty=None, unit=None` in the source and exist solely to introduce child
  items.
- 14 remaining rows have a real quantity AND a real unit.
- Total: 14.
- `source_truth.json` currently says **19** — but it counts the **wrong file**
  (the TDS file `Copy of TDS - Insulation - SAEL (1).xlsx`, not the enquiry
  file `Copy of Insulation Enquiry - SAEL.xlsx`). The test reason in
  `tests/integration/test_sacred10_fidelity.py:91` names the enquiry file
  as the source, and the `08_sael.rowgold.json` gold file is also keyed to
  the enquiry file (`"source_file": "Copy of Insulation Enquiry - SAEL.xlsx"`).
  The source_truth entry's own evidence field flags this:
  `"NOTE: this is the TDS (Technical Data Sheet) file, NOT the BOQ enquiry
  file. The BOQ enquiry file (Copy of Insulation Enquiry - SAEL.xlsx) has
  16 rows per P0_02 D4."` — so the 19 there was from the TDS file, the 16
  was the orchestrator's claimed count for the enquiry file.
- Gold `08_sael.rowgold.json` has 16 entries. It excludes the section title
  (row 3) and includes the two parent spec rows (4 and 15) as `qty=0,
  unit="no."` placeholders even though the source has `None, None`. The
  gold is **inconsistent with the D4 rule**: it keeps rows that D4 says to
  exclude.
- The test "expects 16" — the test's expected value is the gold's count,
  which includes 2 rows the D4 rule excludes.

**My honest answer: 14, not 16.** The 2-row gap is exactly the 2 parent
spec rows (source rows 4 and 15) that the gold inflates to `qty=0, unit="no."`
placeholders despite the source having `None, None` for those columns. Per
the D4 rule, those rows have "no real quantity and no real unit, and exist
solely to introduce child items" — they are exactly the D4 exclusion case.

---

## 4. Cross-cutting observations (for the orchestrator's awareness)

### 4.1 The current `source_truth.json` for 08_sael points at the wrong file

The current `source_truth.json` entry for 08_sael says:

> `"NOTE: this is the TDS (Technical Data Sheet) file, NOT the BOQ enquiry
> file. The BOQ enquiry file (Copy of Insulation Enquiry - SAEL.xlsx) has
> 16 rows per P0_02 D4. The manifest classifies the TDS file as boq_bearing
> — this may be a misclassification (TDS = spec_only). OWNER-DECISION-NEEDED"`

The `d4_exclusions` listed (`11 DUCT THERMAL INSULATION`, `11.2 FINISHING
MATERIALS`, `12.01 INSULATION MATERIALS`) are **TDS-file item numbers**, not
enquiry-file item numbers. The enquiry file's section title is `11
THERMAL INSULATION` (row 3), not `11 DUCT THERMAL INSULATION`. So whoever
generated that source_truth entry transcribed the TDS file, not the enquiry
file that the test, the gold, and the `sacred10_fidelity.py` `path` field
all point at. This is a separate upstream data error that any correction
must address independently of the D4-rule count question.

### 4.2 The gold files for all three docs are inconsistent with the D4 rule as written

The D4 rule in `docs/GOLD_METHODOLOGY.md` §2 reads:

> A row that is a section title only — it has an item number but no real
> quantity and no real unit, and exists solely to introduce child items — is
> NOT a BOQ line item and is excluded from gold.

The rule uses "**and**" — both "no real quantity" and "no real unit" must
hold for exclusion. But the gold files treat:
- `RO`/`R/O` qty (with a real unit) as "no real quantity" — **excluded** by
  the gold (06_avante: 5 rows; 07_grew: 2 rows). D4 as written does not
  exclude these.
- `qty=None, unit=None` parent spec rows (08_sael rows 4, 15) as "real
  quantity = 0, real unit = no." — **included** by the gold. D4 as written
  excludes these (they have neither a real quantity nor a real unit and
  exist solely to introduce children).

This is a real inconsistency between the documented D4 rule and the gold
files. Two possible reconciliations:
- (a) Amend `docs/GOLD_METHODOLOGY.md` §2 to add the gold convention
  ("RO/R/O qty = no real quantity; parent spec rows retained as 0/'no.'
  placeholders"). This would align the rule with the existing gold.
- (b) Restore the gold files to be D4-strict (keep RO rows, drop the
  08_sael parent rows). This would change the gold counts to 36 / 11 / 14
  (matching my honest counts).

Per Rule 3, gold is owner-only. Per Rule 5, the D4 rule is part of the
documented methodology that the gold lock and `check_gold_provenance.py`
enforce. Neither reconciliation is something an agent should perform
unilaterally. The orchestrator must route this to the owner.

### 4.3 The test's "expects 31/9/16" is the gold convention, not the D4 rule

`tests/integration/test_sacred10_fidelity.py:82-94` records the test's
expected values as `31 / 9 / 16`, with reason text `"source_row_count=N
should be M; source_truth correction not P1_03"`. These M values equal
the gold file entry counts:
- `data/real_rfqs/gold/rows/06_avante_kirloskar_pune.rowgold.json` has 31
  entries.
- `data/real_rfqs/gold/rows/07_grew_solar_narmadapuram.rowgold.json` has 9
  entries.
- `data/real_rfqs/gold/rows/08_sael.rowgold.json` has 16 entries.

The test will only PASS for these three docs if `source_truth.json` is
changed to match the gold convention (31/9/16). Changing `source_truth.json`
to those values is, under my D4-rule reading, adopting the gold convention
in preference to the D4 rule. That is the orchestrator's/owner's call to
make, not the worker's.

---

## 5. Recommendation to the orchestrator

1. **Acknowledge the mismatch.** My independent D4-rule counts are
   36 / 11 / 14, not the test's expected 31 / 9 / 16. The mismatch is not a
   transcription error — it is a real divergence between the D4 rule as
   documented and the gold convention as applied. An honest source-truth
   review must report this.
2. **Route the D4 vs gold-convention question to the owner.** The owner
   must rule on which of the following is correct:
   - (a) The D4 rule as written is authoritative — gold files for
     06_avante, 07_grew, 08_sael need to be updated to 36 / 11 / 14 (and
     the test expectations updated to match).
   - (b) The gold convention is authoritative — the D4 rule text needs to
     be amended to match (explicitly covering RO/R/O exclusion and
     parent-spec retention), and `source_truth.json` updated to 31 / 9 / 16.
3. **Fix the 08_sael source-truth file pointer regardless.** The current
   `source_truth.json` entry for 08_sael counts the TDS file, not the
   enquiry file. This is a clear upstream transcription error that needs
   correction under either ruling.
4. **Do not adopt my counts as a default.** I am one worker, reading the
   source once. The orchestrator should spot-check at least 06_avante page 2
   (the densest table) and the 08_sael XLSX rows 4 and 15 to verify my
   transcription before acting.

I have NOT edited `data/real_rfqs/source_truth.json` (per dispatch rule
3/5). I have NOT edited any gold file. I have NOT modified any test, eval
script, or source code.

---

## 6. Appendix — exact commands used

```bash
# 08_sael XLSX raw dump (openpyxl)
python3.12 -c "
import openpyxl
wb = openpyxl.load_workbook(
    'data/real_rfqs/swa_enquiries/08_sael/Copy of Insulation Enquiry - SAEL.xlsx',
    data_only=True)
for sname in wb.sheetnames:
    ws = wb[sname]
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True):
        print(row)
"

# 06_avante PDF raw dump (pdfplumber)
python3.12 -c "
import pdfplumber
with pdfplumber.open('data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Boq_132.pdf') as pdf:
    for i, page in enumerate(pdf.pages, 1):
        print(f'=== PAGE {i} TEXT ===')
        print(page.extract_text())
        for ti, tbl in enumerate(page.extract_tables() or [], 1):
            print(f'=== PAGE {i} TABLE {ti} ===')
            for ri, row in enumerate(tbl, 1):
                print(ri, row)
"

# 07_grew PDF raw dump (pdfplumber)
python3.12 -c "
import pdfplumber
with pdfplumber.open('data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf') as pdf:
    for i, page in enumerate(pdf.pages, 1):
        print(f'=== PAGE {i} TEXT ===')
        print(page.extract_text())
        for ti, tbl in enumerate(page.extract_tables() or [], 1):
            print(f'=== PAGE {i} TABLE {ti} ===')
            for ri, row in enumerate(tbl, 1):
                print(ri, row)
"
```

All three runs were executed in the repo root with
`PYTHONPATH=/Users/srujansai/rfq2boq-phase9` and Python 3.12.2.
Output is fully reproduced in §1.1, §1.2, §2.1, §2.2, §3.1, §3.2 above.
