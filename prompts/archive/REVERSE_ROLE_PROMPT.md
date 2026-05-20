# REVERSE ROLE PROMPT — Criticism Simulation (RFQ2BOQ)
## Pretend You're the Harshest Critic

```
You are the REVERSE ROLE critic.
Your job: Find every possible way this project can fail.
Think like:
- A professor who wants to fail lazy students
- A competitor who wants to show your work is inferior
- A user who expects perfection and will blame you for every bug
- A reviewer at a top conference who rejects 95% of papers

Be brutal. Be specific. Be unfair if it helps find real issues.
```

---

## ATTACK VECTORS

### 1. TECHNICAL ATTACKS

**"Your NER model is just pattern matching, not real ML"**
- Real NER uses contextual embeddings
- Pattern matching fails on novel data
- How do you handle typos, abbreviations, non-standard terms?

**"PDF extraction is a solved problem — you're not adding anything"**
- pdfplumber does this out of the box
- Why do you need a custom pipeline?
- What's your unique contribution?

**"Relation extraction is just proximity matching"**
- That's not ML, that's string processing
- How do you handle long-range dependencies?
- What about entities in different sentences?

### 2. DOMAIN ATTACKS

**"Construction domain has infinite variation"**
- Every contractor uses different terminology
- "20mm marble" vs "20 mm marble" vs "2cm marble" vs "marble 20mm"
- Your system will fail on real RFQs

**"BOQ standards vary by country/region"**
- Indian BOQ vs UK BOQ vs US BOQ
- Different unit systems (metric vs imperial)
- Different standard codes (IS vs BS vs ASTM)

**"Tables in RFQs are nightmares"**
- Merged cells
- Nested tables
- Tables spanning pages
- Handwritten annotations

### 3. EVALUATION ATTACKS

**"Your F1 scores are on synthetic data"**
- Real RFQs are messier
- How do you know it works on real documents?
- Show me a blind test on unseen RFQs

**"You're not comparing to baselines"**
- What if I just used spaCy out of the box?
- What if I used Claude/GPT for extraction?
- Why is your approach better?

**"Self-evaluated metrics are worthless"**
- You need independent evaluation
- Who verified your F1 scores?
- Show me the confusion matrix

### 4. DEPLOYMENT ATTACKS

**"This will fail in production"**
- What happens when the PDF is corrupted?
- What if the OCR quality is poor?
- How do you handle 500-page documents?

**"No error handling"**
- What if the NER model returns no entities?
- What if relations form a cycle?
- What if the BOQ generator gets malformed input?

**"Performance is terrible"**
- 30 seconds per page?
- Real users won't wait
- How do you scale to 1000 RFQs/day?

---

## DEFENSE QUESTIONS

For each attack, you MUST be able to answer:

1. **What's your evidence?** (Not speculation, proof)
2. **What's your fallback?** (When primary approach fails)
3. **What's your limit?** (When does your approach break?)
4. **What's your improvement plan?** (How will you fix it?)

---

## SELF-ATTACK CHECKLIST

Before submission, attack your own work:

### PDF Processing
- [ ] Test on 10 real RFQs (not samples)
- [ ] Try scanned documents with poor quality
- [ ] Test on multi-language RFQs
- [ ] Try encrypted/password-protected PDFs
- [ ] Test on PDFs with 100+ pages

### NER Model
- [ ] Test on unseen entity types
- [ ] Try with deliberate typos
- [ ] Test with mixed case (UPPERCASE, lowercase, MiXeD)
- [ ] Try with non-standard abbreviations
- [ ] Measure actual vs predicted confidence

### Relation Extraction
- [ ] Test with entities 10+ sentences apart
- [ ] Try with contradictory relations
- [ ] Test with circular dependencies
- [ ] Try with missing context

### BOQ Output
- [ ] Generate 100 BOQs, count failures
- [ ] Validate JSON schema strictly
- [ ] Open Excel in different versions
- [ ] Check for encoding issues (₹, €, special chars)

---

## HOW TO USE THIS

When you think you're done:

1. Run this reverse role attack
2. For each question you can't answer → FIX IT
3. For each limitation you discover → DOCUMENT IT
4. For each failure mode → ADD ERROR HANDLING

Then attack again. Repeat until you're genuinely unattackable.

---

## EXAMPLE EXCHANGE

**Attack:** "What if the RFQ says 'Supply and install 50 sq.m of 20mm marble flooring' and your NER only extracts 'marble' and '50' but misses '20mm' and 'sq.m'?"

**Defense:** "Our model has DIMENSION as a primary entity type with F1=0.87. The dimension '20mm' will be extracted. For units, we normalize 'sq.m' to 'm²' which is in our unit dictionary. If both are somehow missed, our validation layer catches 'missing unit' and 'missing dimension' flags for manual review."

**Verdict:** DEFENDED (with evidence)

---

## SCORING

After reverse role attack:

| Score | Description |
|-------|-------------|
| 9-10 | A+ — Truly unattackable |
| 7-8 | A — Minor vulnerabilities, acceptable |
| 5-6 | B — Significant gaps, needs work |
| 3-4 | C — Major issues, not ready |
| 1-2 | D/F — Fundamental problems |

**Goal: Score ≥8 before submission**