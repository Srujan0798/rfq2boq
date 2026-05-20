---
marp: true
theme: default
paginate: true
---

# RFQ to BOQ: NLP-Based Construction Tender Analysis

**SWA Consultancy Internship — 2026**

---

## The Problem: Manual BOQ Extraction is Painful

- **Time:** 2–4 hours per 20-page tender document
- **Errors:** Scope omissions and specification mismatches lead to contractual disputes
- **Cost:** Skilled estimator time at $50–100 per extraction
- **Inconsistency:** Different extractors produce different results on the same document

*Zhang & El-Gohary (2015) showed NLP can achieve precision 0.969, recall 0.944 on construction documents.*

---

## The Solution: Automated RFQ → BOQ Pipeline

```
PDF → Ingest → Preprocess → NER → Relations → BOQ → Export
        ↓          ↓           ↓          ↓         ↓
     OCR/text   normalize   BERT-      proximity  Excel/
                units       BiLSTM-     rules      JSON
                           CRF
```

- BERT-BiLSTM-CRF NER model (8 entity types, BIOES tagging)
- Hybrid ML + rule-based extraction + ontology validation
- CPWD DSR 2023 rate lookup (507 items, 83% coverage)
- Confidence scoring per extracted item
- Processing time: ~30s for typical document

---

## Entity & Relation Schema

| Entity (8 types) | Relation (6 types) |
|------------------|-------------------|
| **MATERIAL** — cement, steel, concrete | HAS_QUANTITY |
| **QUANTITY** — 500, 150.5 | HAS_UNIT |
| **UNIT** — m³, kg, no. | AT_LOCATION |
| **LOCATION** — ground floor, Block A | OF_GRADE |
| **DIMENSION** — 230mm, Ø12mm | COMPLIES_WITH |
| **STANDARD** — IS 456, ASTM A615 | HAS_DIMENSION |
| **ACTION** — supply, install, lay | |
| **GRADE** — M20, Fe500 | |

BIOES tagging scheme: B(eginning), I(nside), E(nd), S(ingle), O(utside)
33 total labels (1 O + 8 entities × 4 BIOES prefixes)

---

## NER Architecture: BERT-BiLSTM-CRF

```
Input: "Supply 500 kg of OPC 43 cement as per IS 8112"
                 ↓
         BERT Encoder (bert-base-cased, 768 hidden, 12 heads)
                 ↓
         BiLSTM (2 × 256 hidden units, bidirectional)
                 ↓
         CRF Layer (33 BIOES labels, transition constraints)
                 ↓
Output: S-ACTION S-QUANTITY S-UNIT S-MATERIAL S-GRADE S-STANDARD
```

**Why this architecture?**
- **BERT:** Captures bidirectional context; handles ambiguous terms
- **BiLSTM:** Models sequential dependencies across tokens
- **CRF:** Enforces valid BIOES tag transitions (no I-QUANTITY without B-QUANTITY)

---

## Hybrid Approach: ML + Patterns + Ontology

| Component | Approach | Benefit |
|-----------|----------|---------|
| BERT-BiLSTM-CRF | Deep learning | Primary extraction, open vocabulary |
| spaCy EntityRuler | Pattern rules | High-precision for standards/grades |
| Regex | IS/ASTM patterns | 98% recall on standard codes |
| Aho-Corasick | Dictionary lookup | Fast material gazetteer matching |
| Ontology validation | IFC-backed rules | Catches invalid material-standard combos |

**Conflict Resolution (5 strategies):**
- `RulesFirst` — for QUANTITY, UNIT, STANDARD
- `ModelFirst` — for MATERIAL, LOCATION, ACTION
- `TypeSpecific` — per-entity threshold tuning
- `ThresholdConfidence` — requires 0.15 confidence margin
- `HybridEnsemble` — type-weighted voting

---

## Results: Honest Real-World F1 = 0.52

**Evaluation:** 31 gold-annotated real RFQ documents

| Metric | Value |
|--------|-------|
| **Micro F1** | **0.5227** |
| Macro F1 | 0.5330 |
| Precision | 0.49 |
| Recall | 0.53 |

> ⚠️ Synthetic F1 = 0.996 (inflated — template overfitting)
> Real F1 = 0.523 (honest — reflects actual tender language diversity)

---

## Per-Entity Performance Breakdown

| Entity | Precision | Recall | F1 | Analysis |
|--------|-----------|--------|-----|---------|
| **STANDARD** | 1.000 | 0.890 | **0.942** | IS/ASTM patterns highly distinctive |
| **GRADE** | 0.505 | 0.982 | 0.668 | High recall, over-generates |
| **UNIT** | 0.804 | 0.570 | 0.667 | Good precision |
| **QUANTITY** | 0.696 | 0.506 | 0.586 | Balanced |
| **ACTION** | 0.324 | 0.917 | 0.479 | High recall, low precision |
| **DIMENSION** | 0.233 | 0.688 | 0.349 | Low precision |
| **LOCATION** | 0.085 | 0.250 | 0.126 | Ambiguous terminology |
| **MATERIAL** | 0.046 | 0.031 | **0.037** | Critical bottleneck |

**MATERIAL is the key bottleneck** — span mismatch, open vocabulary, domain shift

---

## CPWD Excel Export

The system exports structured BOQ in **CPWD format**:

- **Trade grouping:** Concrete, Steel, Masonry, Flooring, etc.
- **DSR lookup:** Cross-reference to CPWD DSR 2023 (507 items, 83% coverage)
- **Rate calculation:** Base rate × quantity × GST (18%)
- **Confidence indicators:** 🟢 >0.85 🟡 0.70–0.85 🔴 <0.70

| Item | Material | Qty | Unit | DSR Rate | Confidence |
|------|----------|-----|------|----------|------------|
| 1 | RCC M20 | 150 | m³ | ₹ 7,642/m³ | 0.91 |
| 2 | TMT Fe500 | 500 | kg | ₹ 71/kg | 0.88 |
| 3 | Brickwork | 200 | m³ | ₹ 5,230/m³ | 0.72 |

---

## Streamlit UI Demo

Interactive web interface at `http://localhost:8501`:

- **PDF upload** with drag-and-drop
- **Entity visualization** with color-coded highlighting
- **BOQ table** with confidence indicators
- **JSON/Excel download** buttons
- **DSR rate display** for matched items

**Implementation:** `ui/app.py` (470 lines, 15 tests)

---

## Processing Speed

| Document Type | Processing Time |
|---------------|-----------------|
| 1-page native text PDF | 2.3s |
| 10-page native text PDF | 8.7s |
| 10-page scanned PDF | 45.2s |
| Typical 20-page RFQ | ~30s |

**OCR is the bottleneck** for scanned documents.
Native text processing is fast enough for interactive use.

---

## Limitations: Where the Pipeline Struggles

1. **MATERIAL entity (F1 0.037)** — open vocabulary, multi-word spans, domain shift
2. **Small gold training set** — only 14 of 20 gold docs used for training
3. **Training interrupted** — MPS constraints stopped at epoch 4 of 8
4. **No ARCBERT** — SciBERT fallback used (network-blocked download)
5. **English only** — Hindi support scaffolded but not deployed
6. **LOCATION ambiguity** — "floor", "slab", "wall" serve dual roles

**Root cause:** Template-based synthetic data does not capture real tender diversity.

---

## Future Work: Path to F1 ≥ 0.80

| Priority | Improvement | Expected Impact |
|----------|-------------|-----------------|
| **P1** | Expand gold annotations (30–50 more docs) | +10–15% F1 |
| **P2** | ARCBERT base model (when network available) | +5–8% F1 |
| **P3** | MATERIAL: expanded gazetteer + active learning | +5–10% F1 |
| **P4** | Full 8-epoch training (GPU cloud) | +2–5% F1 |
| **P5** | Hindi IndicBERT model | Enables Hindi RFQs |

---

## Conclusion

**RFQ2BOQ demonstrates:**
- ✅ Complete end-to-end pipeline: PDF → Excel/JSON BOQ
- ✅ Hybrid architecture: BERT-BiLSTM-CRF + patterns + ontology
- ✅ Real-world F1 0.523 on 31 gold-annotated documents
- ✅ Processing ~30s per typical document (vs 2–4 hours manual)

**Key insight:** Structured entities (STANDARD 0.942, GRADE 0.668) work well; open-vocabulary entities (MATERIAL 0.037) need more data.

**The path forward:** More gold annotations + ARCBERT + full training = F1 ≥ 0.80

---

## Thank You

**Questions?**

Contact: srujan@swa-consultancy.in

*Full report: `deliverables/report/internship_report.md`*
*Slides: `deliverables/slides/presentation.md`*