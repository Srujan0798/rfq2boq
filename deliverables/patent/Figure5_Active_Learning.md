# Figure 5: Real-Time Uncertainty-Driven Active Learning Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACTIVE LEARNING LOOP                                     │
└─────────────────────────────────────────────────────────────────────────────┘

                          ┌──────────────────┐
                          │   NEW RFQ DOCS    │
                          │   (Unprocessed)   │
                          └────────┬─────────┘
                                   │
                                   ▼
                    ┌────────────────────────────┐
                    │      NER INFERENCE          │
                    │   (Current Model v1.3)     │
                    └────────────┬───────────────┘
                                 │
                                 ▼
              ┌─────────────────────────────────────┐
              │         ENTITY EXTRACTION          │
              │                                      │
              │   - MATERIAL entities              │
              │   - QUANTITY entities              │
              │   - UNIT entities                  │
              │   - GRADE entities                 │
              │   - etc.                           │
              └──────────────┬──────────────────────┘
                             │
                             ▼
              ┌─────────────────────────────────────┐
              │      CONFIDENCE SCORING             │
              │                                       │
              │   Each entity gets confidence:       │
              │   - High (>= 0.7): Accept           │
              │   - Medium (0.5-0.7): Review        │
              │   - Low (< 0.5): Flag for AL        │
              └──────────────┬──────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
     ┌─────────────────┐           ┌─────────────────┐
     │  HIGH CONF      │           │   LOW CONF       │
     │  (>= 0.7)       │           │   (< 0.5)        │
     │  → Add to BOQ   │           │  → Review Queue │
     └─────────────────┘           └────────┬─────────┘
                                           │
                                           ▼
                              ┌─────────────────────────┐
                              │   HUMAN REVIEW          │
                              │                         │
                              │   - Verify entity      │
                              │   - Correct if needed  │
                              │   - Add to training    │
                              └────────────┬────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    │                                               │
                    ▼                                               ▼
       ┌─────────────────────────┐                   ┌─────────────────────────┐
       │  CORRECTED SAMPLES      │                   │    DRIFT DETECTION       │
       │  (Human Verified)       │                   │                         │
       │  → Training Data       │                   │  KS Test on:             │
       └───────────┬─────────────┘                   │  - Input distribution    │
                   │                                   │  - Entity frequency     │
                   │                                   │  - Quantity ranges      │
                   ▼                                   └───────────┬─────────────┘
       ┌─────────────────────────┐                               │
       │  MODEL RETRAINING       │          ┌────────────────────┘
       │                         │          │
       │  - Add verified samples│          ▼
       │  - Increment version   │   ┌─────────────────┐
       │  - Re-evaluate         │   │  Drift Detected?│
       └───────────┬───────────┘   └───────┬─────────┘
                   │                       │     │
                   │                       │    NO
                   │                       │     │
                   │                       │     ▼
                   │              ┌────────────────┐
                   │              │ Continue       │
                   │              │ Monitoring     │
                   │              └────────────────┘
                   │
                   │     ┌────────────────┐
                   └────►│  MODEL v1.4    │
                         │  (Updated)     │
                         └────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        ACTIVE LEARNING METRICS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. UNCERTAINTY SAMPLING                                                    │
│     - Select entities where model is most uncertain                        │
│     - Prioritize: low confidence + high variance                          │
│                                                                             │
│  2. DIVERSITY SAMPLING                                                      │
│     - Ensure coverage across:                                               │
│       • Material types                                                      │
│       • Document sources (CPWD, PWD, etc.)                                 │
│       • Languages (English, Hindi)                                         │
│                                                                             │
│  3. DRIFT DETECTION                                                         │
│     - Kolmogorov-Smirnov test on input distributions                       │
│     - Alert when KS > 0.15 (significant drift)                             │
│     - Trigger model retraining automatically                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        TRAINING DATA FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Initial Training:     300 synthetic + 50 real (annotated)                 │
│                                                                             │
│  After 1 month:         300 synthetic + 50 real + N corrections            │
│                                                                             │
│  After 6 months:       300 synthetic + 200 real + M corrections           │
│                                                                             │
│  Target (12 months):   500 real + 1000 corrections                         │
│                        → Real-world F1 >= 85%                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        REVIEW QUEUE PRIORITIZATION                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Priority = α × (1 - confidence) + β × entity_rarity + γ × ambiguity_score │
│                                                                             │
│  Where:                                                                    │
│    α = 0.5 (weight for uncertainty)                                        │
│    β = 0.3 (weight for rarity)                                             │
│    γ = 0.2 (weight for ambiguity)                                          │
│                                                                             │
│  High priority entities:                                                   │
│    - New material types (not seen before)                                 │
│    - Out-of-range quantities                                               │
│    - Ambiguous unit formats                                                 │
│    - Hindi-English mixed text                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```