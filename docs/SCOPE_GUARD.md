# Scope Guard — How to Avoid the Drift That Already Happened

Auto-loaded reference for Claude (and any AI agent) working on this project. Read with `CLAUDE.md`.

This project has been corrected from scope drift **three times** (paper/patent/SaaS, then a second time, then a full sweep). Each time, work happened that was never asked for. This document codifies the patterns so they stop repeating.

---

## 1. The single test for any new work

Before generating any task prompt, ask **one question**:

> "Does this directly help turn a construction RFQ PDF into a structured BOQ that an estimator can use?"

If **yes** → in scope, write the prompt.
If **no** → out of scope, refuse.
If **maybe** → ask Srujan before writing anything.

---

## 2. Drift patterns to refuse on sight

When you see ANY of these phrases or implied requests, **stop, name the pattern, and ask Srujan**:

### 2.1 Publication / academic drift

- "Write a paper / journal / conference submission"
- "Prepare for publication"
- "Draft a research paper"
- "Generate ITcon / ASCE / IEEE formatting"
- "Co-author / reviewer response"
- "Bibtex / references / citations"

### 2.2 IP / patent drift

- "File a patent / provisional"
- "Patent claims / prior art search"
- "Inventor list / patent attorney"
- "IP disclosure to university or company"

### 2.3 Marketing / business drift

- "Pitch deck / sales deck (beyond demo)"
- "Business case / ROI analysis"
- "Pricing tiers / billing"
- "Customer outreach / cold email"
- "Landing page / marketing site"
- "Portfolio summary for jobs"

### 2.4 SaaS / multi-tenant drift

- "Multi-tenant architecture"
- "Stripe / billing / subscriptions / plans"
- "Team roles / RBAC / permissions"
- "Tenant isolation / row-level security"
- "User signup flow / email verification"

### 2.5 Public release drift

- "Open-source the dataset"
- "Upload to HuggingFace Hub / Papers With Code"
- "Public benchmark / leaderboard"
- "Submission system / auto-eval workflow"

### 2.6 Enterprise infra drift

- "Observability stack" (Prometheus + Grafana + Loki + Tempo + Sentry)
- "Distributed tracing"
- "MLflow tracking server" / "model registry promotion"
- "A/B testing infrastructure"
- "Drift detection daemons"

### 2.7 Security theatre drift

- "OWASP Top 10 audit"
- "Penetration test"
- "MFA TOTP / refresh tokens / JWT rotation"
- "ClamAV file scanning"
- "Audit log integrity (HMAC-signed)"

### 2.8 Test-engineering drift

- "Mutation testing (mutmut)"
- "Property-based tests at scale"
- "Chaos engineering"
- "Load testing scenarios"
- "Performance regression CI"

### 2.9 Modality drift

- "Voice input / Whisper transcription"
- "Drawing / blueprint / CAD analysis"
- "Symbol detection (YOLOv8)"
- "Multi-modal extraction"

### 2.10 Modeling drift

- "Per-domain specialized models" (one good model > five fragile ones)
- "SpERT / joint NER+RE" (current pipeline is enough)
- "Custom domain-pretrain BERT from 50k corpus" (use ARCBERT/SciBERT directly)
- "Custom knowledge graph schema" (use OmniClass + ifcOWL)
- "Active learning + uncertainty + conformal prediction" (overkill for one model)

### 2.11 Integration drift

- "SAP MM / IDoc / Primavera P6 XER / IFC export / CostX adapters"
- "Revit / ArchiCAD plugins"
- "ERP integrations"
- (Excel + JSON + CSV is enough)

### 2.12 Communication automation drift

- "Email / Slack / Notion automation"
- "Notification to SWA / company"
- "Submission to the company"
- (Srujan handles all company comms himself)

---

## 3. What's actually in scope

Only these tasks count. Anything else needs explicit approval.

### Core pipeline
- PDF ingestion (text + tables + OCR for scanned)
- Preprocessing (tokenization, sentence split, sections)
- NER (BERT-BiLSTM-CRF, 8 entities, BIOES)
- Relation extraction (6 relations, rule-based or learned)
- Rule engine (units, standards, scope-gap, conflict resolution)
- BOQ assembly (entities → rows)
- Validation + confidence scoring
- Cost lookup (CPWD DSR rates)

### Surfaces
- FastAPI (one or two routes — extract + upload)
- Streamlit UI (one page — upload → extract → table → download)
- Typer CLI (one or two commands)
- Excel output (CPWD-format)
- JSON output
- CSV output

### Data
- Synthetic training corpus (already exists)
- BIOES annotations (already exists)
- 50 real RFQ PDFs (P1T5 — pending)
- 20 gold annotations on real PDFs (P1T5 — pending)
- CPWD DSR rate library (P1T4 — pending)

### Quality
- Unit + integration + golden tests
- Real-world F1 measurement (honest, not synthetic)
- Documentation: README, USER_GUIDE, ONBOARDING, deployment

### Optional (only if directly asked)
- Hindi support via IndicBERT (P1T2)
- ARCBERT base swap (P1T3)
- OmniClass mapping table (P1T1, for BIM export)
- LLM ambiguity resolver (B2, already DONE)
- Risk engine (B1, already DONE)

---

## 4. The active-prompt allowlist

Anything outside this list requires Srujan's explicit "yes, do this":

| Folder | Status |
|--------|--------|
| `prompts/hybrid/phase1/` | Active (P1T1–P1T5) |
| `prompts/hybrid/phase2/` | Active (slim codebase) |
| `prompts/hybrid/phase3/` | Active (final polish + demo) |
| `prompts/wave2/` | Active subset (A0, A3, A4, A6, A8) |
| `prompts/wave3/` | Active subset (B1, B2) |
| `prompts/archive/out_of_scope/` | **READ-ONLY** — never dispatch from here |

Out-of-scope prompts under `archive/` exist for traceability. Do not dispatch them; do not auto-port them into active folders.

---

## 5. Refusal template

When asked for out-of-scope work, respond like this:

> That looks like [pattern X from §2.Y above] — not part of the internship scope (RFQ→BOQ extraction). The archived prompt for it is at `prompts/archive/out_of_scope/[FILE].md` if you want to restore it, but I'd recommend not. Do you want me to:
> 1. Move on to an in-scope task (suggest one), or
> 2. Restore the archived prompt anyway (and accept the timeline cost), or
> 3. Add it as a parking lot item for after the internship?

Never silently generate the out-of-scope prompt. Always make the trade-off explicit.

---

## 6. Auto-recovery

If you (Claude) notice that a previous session generated out-of-scope code or docs that are still active, **proactively flag and propose archival** — don't wait to be asked. Example:

> I see `src/billing/` is still active even though SaaS is out of scope (per CLAUDE.md §1). Move it to `attic/`? (Y/n)

---

**Last updated:** 2026-05-17 — after the third scope-drift cleanup. If you find yourself drafting something outside §3, stop and re-read §2.
