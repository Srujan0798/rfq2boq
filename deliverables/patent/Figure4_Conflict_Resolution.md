# Figure 4: Hybrid ML + Rule Conflict Resolution Algorithm

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 CONFLICT RESOLUTION ALGORITHM                                │
└─────────────────────────────────────────────────────────────────────────────┘

   EXTRACTED ENTITY
         │
         ▼
┌────────────────────────┐
│  CONFLICT DETECTION    │
│                        │
│  Rule-based check:     │
│  - Ontology validate  │
│  - Unit canonicalize  │
│  - Grade range check  │
│  - Quantity bounds    │
└───────────┬────────────┘
            │
            ▼
    ┌───────────────┐
    │  Conflict?   │
    └───────┬───────┘
            │
     ┌──────┴──────┐
     │             │
   YES            NO
     │             │
     ▼             ▼
┌─────────┐   ┌─────────────────────────┐
│  ML vs  │   │   ACCEPT ENTITY         │
│  Rules  │   │   (Add to BOQ)          │
└────┬────┘   └─────────────────────────┘
     │
     ▼
┌────────────────────────┐
│  GET CONTEXT          │
│                        │
│  - Surrounding text   │
│  - Page context       │
│  - Table position     │
│  - Neighboring entities│
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│  CHECK CONFIDENCE     │
│                        │
│  IF bert_conf >= 0.5: │
│     → Use BERT output │
│  ELSE:                │
│     → Escalate to LLM │
└───────────┬────────────┘
            │
     ┌──────┴──────┐
     │             │
   HIGH          LOW
     │             │
     ▼             ▼
┌─────────┐   ┌─────────────────────────┐
│ ACCEPT  │   │  LLM VERIFICATION       │
│ BERT    │   │                        │
└─────────┘   │  Prompt Template:       │
              │  "Text: {sentence}"     │
              │  "Entity: {text}"      │
              │  "Type: {type}"        │
              │  "Context: {context}"  │
              │  → Get clarification   │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │  MERGE RESULT          │
              │                        │
              │  - LLM response        │
              │  - Confidence update  │
              │  - Annotate for AL     │
              └───────────┬────────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │   ACCEPT RESOLVED       │
              │   (Add to BOQ)           │
              └─────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        DECISION MATRIX                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BERT Conf    Rule Violation    Action                                     │
│  ─────────    ──────────────    ───────                                    │
│    >= 0.7          No          Accept BERT                                 │
│    >= 0.7          Yes         Accept BERT + warn                          │
│   0.5-0.7          No          Accept BERT                                 │
│   0.5-0.7          Yes         LLM verification                            │
│    < 0.5           -           LLM verification                             │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                        LLM PROMPT EXAMPLE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  "In the sentence: 'Supply cement M25 for foundation as per IS 456',       │
│   the entity 'IS 456' was extracted as LOCATION.                            │
│   Is 'IS 456' actually a STANDARD code (Indian Standard for concrete)?      │
│   Reply with: STANDARD, LOCATION, or UNKNOWN"                              │
│                                                                             │
│  Response: "STANDARD"                                                       │
│  Confidence: 0.95 (after LLM verification)                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        STATISTICS TRACKED                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  - Total entities processed                                                 │
│  - Conflicts detected                                                       │
│  - BERT only resolutions                                                    │
│  - LLM escalation count                                                     │
│  - LLM agreement rate (BERT vs LLM)                                         │
│  - Final confidence distributions                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```