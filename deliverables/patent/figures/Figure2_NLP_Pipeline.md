# Figure 2: NLP Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NLP PIPELINE DETAILED FLOW                           │
└─────────────────────────────────────────────────────────────────────────────┘

 INPUT TEXT
     │
     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                    PREPROCESSING STAGE                                    │
 │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
 │  │ Text Cleaning│  │Language Det │  │Tokenization │  │ Sentence Split   │  │
 │  │ & Normalize │→ │(en/hi)      │→ │             │→ │                 │  │
 │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘  │
 └─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                    NER STAGE (BIOES Tagging)                             │
 │                                                                          │
 │  Input: "Supply 500 bags of cement M25 at site"                          │
 │                                                                          │
 │  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐          │
 │  │ BERT Tokenizer│ →   │  BiLSTM-CRF   │ →   │  BIOES Tags   │          │
 │  │              │     │    Encoder    │     │              │          │
 │  └───────────────┘     └───────────────┘     └───────────────┘          │
 │       │                    │                      │                     │
 │       ▼                    ▼                      ▼                     │
 │   "Supply"           [O, O, O, O]        ACTION = Supply               │
 │   "500"             [B-QTY, E-QTY]       QUANTITY = 500                │
 │   "bags"            [O, O]               UNIT = bags → no.             │
 │   "cement"          [B-MAT]              MATERIAL = cement              │
 │   "M25"             [B-GRD]              GRADE = M25                   │
 │   "at"              [O, O]                                               │
 │   "site"            [B-LOC, E-LOC]       LOCATION = site                │
 │                                                                          │
 └─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                 RELATION EXTRACTION STAGE                                │
 │                                                                          │
 │  Entities:                                                               │
 │    - MATERIAL: cement (start=15, end=21)                                 │
 │    - QUANTITY: 500 (start=6, end=9)                                      │
 │    - UNIT: bags (start=10, end=14)                                      │
 │    - GRADE: M25 (start=22, end=25)                                      │
 │    - LOCATION: site (start=28, end=32)                                  │
 │                                                                          │
 │  ┌─────────────────────────────────────────────────────────────┐       │
 │  │              RELATION CLASSIFICATION                         │       │
 │  │                                                              │       │
 │  │  HAS_QUANTITY:  cement → 500                                  │       │
 │  │  HAS_UNIT:      500 → bags                                    │       │
 │  │  OF_GRADE:      cement → M25                                 │       │
 │  │  AT_LOCATION:   cement → site                                │       │
 │  └─────────────────────────────────────────────────────────────┘       │
 └─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                 AMBIGUITY RESOLUTION STAGE                               │
 │                                                                          │
 │  if confidence < 0.5:                                                    │
 │     send_to_LLM(text, entity, context)                                    │
 │     get_verification()                                                   │
 │                                                                          │
 │  Example: "IS 456" could be STANDARD or LOCATION                        │
 │           BERT: conf=0.3 → LLM → STANDARD (95% conf)                    │
 └─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              EXTRACTED ENTITIES + RELATIONS
                    (Ready for BOQ Assembly)
```

## Tag Set (BIOES)

| Tag    | Meaning                | Example           |
|--------|------------------------|-------------------|
| B-MAT  | Begin Material         | cement            |
| I-MAT  | Inside Material        | -                 |
| E-MAT  | End Material           | -                 |
| S-MAT  | Single Material        | cement            |
| B-QTY  | Begin Quantity         | 500               |
| E-QTY  | End Quantity           | -                 |
| B-UNIT | Begin Unit             | bags              |
| E-UNIT | End Unit               | -                 |
| B-GRD  | Begin Grade            | M25               |
| E-GRD  | End Grade              | -                 |
| B-LOC  | Begin Location         | site              |
| E-LOC  | End Location           | -                 |
| O      | Outside (no entity)    | the, at, to       |