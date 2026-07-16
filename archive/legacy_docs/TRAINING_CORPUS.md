# Training Corpus — Honest Assessment

**Date:** 2026-06-09

## What We Have

### Gold Annotations (20 documents)
Source: `data/real_rfqs/annotations/gold_annotations.json`

Domains covered:
- Road (4): RFQ9740, RFQ5098, RFQ7995, RFQ6835
- Building (6): RFQ5521, RFQ6053, RFQ6591, RFQ1697, RFQ1138, RFQ8237
- Bridge (6): RFQ1904, RFQ7102, RFQ2351, RFQ7605, RFQ6090, RFQ3574
- Plumbing (2): RFQ2916, RFQ7457
- Electrical (2): RFQ6187, RFQ1955

**No SWA files. No leakage.** Verified by audit.

### Unannotated Real RFQs (68 PDFs)
Source: `data/real_rfqs/additional_real/`

- Building (15), Road (6), Bridge (11), Plumbing (9), Electrical (9)
- Government docs (17): CPWD, EPI, NHAI, IREPS, PWD
- HVAC adjacent (10): Plumbing files with pumps/valves

**These are NOT annotated.** They can be used for:
1. Generalization testing (Phase 4)
2. Semi-supervised training (after auto-labeling via table extraction)
3. Future human annotation (if budget allows)

### Synthetic Data
Source: `data/annotations/` (if available)

Legacy synthetic annotations exist but quality is questionable. Used only if real gold is insufficient.

## Split Strategy

Since only 20 gold docs exist, we use a **conservative split**:

| Split | Count | Source |
|-------|-------|--------|
| Train | 14 | 70% of gold (14 docs) |
| Validation | 3 | 15% of gold (3 docs) |
| Test | 3 | 15% of gold (3 docs) |

**Bootstrap for larger corpus:**
1. Use table extraction + regex on 68 unannotated PDFs to generate "silver" labels
2. Combine silver + gold for training
3. Keep 3 gold docs strictly held-out for honest evaluation

## Honest Limitation

With only 20 annotated documents, the NER model will have **limited coverage**:
- Good at: Common materials (cement, steel, concrete, pipe, cable)
- Weak at: Unseen domains (insulation, specialized HVAC, custom composites)
- False positives: Generic words tagged as entities ("and", "of", "mm")

**Mitigation:** Heavy reliance on table extraction + regex fallback for production.

## Path to Scale

To reach the 80-file insulation corpus the original plan envisioned:
1. Source real insulation tenders from SWA business
2. Annotate 50-100 documents using `docs/ANNOTATION_GUIDELINES.md`
3. Retrain from scratch on the expanded corpus
4. Expected timeline: 2-3 weeks with 2 annotators
