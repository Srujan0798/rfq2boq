# Orchestration Patterns — RFQ2BOQ

This document describes how AI orchestration works on this project. It is referenced from `CLAUDE.md` and applies to Claude, Codex, MiniMax, and any other agent contributing to the project.

---

## 1. Hierarchy

```
┌────────────────────────────────────────────┐
│  Owner (Srujan)                            │
│  - Approves plans, accepts deliverables    │
│  - Assigns task prompts to external agents │
└──────────────┬─────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────┐
│  Orchestrator (Claude in this repo)        │
│  - Reads CLAUDE.md, memory, project state  │
│  - Generates task prompts (TASK_TEMPLATE)  │
│  - Audits deliverables via subagents       │
│  - Maintains docs, memory, wave status     │
│  - NEVER does implementation work itself   │
└──────────────┬─────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────┐
│  Workers (External agents: Codex, MiniMax) │
│  - Receive 9-section task prompts          │
│  - Implement, test, verify                 │
│  - Report via REPORT format                │
└────────────────────────────────────────────┘
```

The orchestrator never does worker tasks. The owner assigns. The workers build.

---

## 2. Task assignment protocol

Every task assignment uses the [9-section template](../prompts/TASK_TEMPLATE.md):

1. **GOAL** — one sentence WHY
2. **CONTEXT** — files to read first
3. **DELIVERABLES** — exact file paths
4. **STEPS** — numbered procedure with exact commands
5. **VERIFICATION** — commands + expected output
6. **ACCEPTANCE CRITERIA** — objective pass/fail
7. **CONSTRAINTS** — hard rules
8. **DEPENDENCIES** — blocks / blocked-by / parallel-safe / shared files
9. **GOTCHAS** — known pitfalls

See [EXAMPLE_FILLED_TASK.md](../prompts/EXAMPLE_FILLED_TASK.md) for a complete worked example.

Vague specs ("implement well", "use best practices") are forbidden. Every assertion must be testable via Section 5 commands.

---

## 3. Wave protocol

Work is organized into **waves of parallel-safe tasks**:

| Wave | Tier | Theme | Status |
|------|------|-------|--------|
| 0 | — | Initial scaffolding (4 agents) | DONE |
| 1 | S | Game-changers (LayoutLM, Neo4j, Cost, Active Learning, React) | DONE |
| 2 | A | High-value (SpERT, Tables, ConstructionBERT, Calibration, MLflow, Hindi, ERP/BIM) | 1/7 |
| 3 | B | Depth (Risk, LLM, Voice, Drawings, Sub-domain) | 0/5 |
| 4 | C | Polish & scale (Performance, Security, Observability, Multi-tenancy, Testing) | 0/5 |
| 5 | D | Research/moat (Dataset, Paper, Benchmark, Patent) | 0/4 |

Detailed task status: [wave_status.md](wave_status.md)

After every wave, run a **4-parallel-subagent audit** (one per external agent) before declaring the wave complete.

---

## 4. Parallel dispatch rules

When dispatching multiple tasks in parallel:

- **No shared files** — Section 3 (Deliverables) of two tasks must not overlap
- **No logical dependency** — Section 8 (Dependencies) must show no blocking relationship
- **Compatible constraints** — Section 7 must not contradict

If conflicts exist, sequence them. Otherwise, batch dispatch to maximize throughput.

---

## 5. Contract-based hand-offs

When task A's output is task B's input:

- Section 3 (Deliverables) of A = exact file paths
- Section 2 (Context) of B = same exact file paths in "Read first" list

The file paths form the contract. Hand-off failures usually mean A's Section 3 was vague.

---

## 6. Reflexion on failure

Every external agent failure must update Section 9 (Gotchas) of similar future tasks.

**Examples from past failures (already encoded):**

- All Wave 0 agents used `src/` instead of `code/` → CLAUDE.md and templates now pin `src.` explicitly
- Codex generated `test_ontology_loader.py` against an old stub API (`.load()`) instead of the new `ConstructionOntology` API → templates now require reading the actual implementation before writing tests
- Agents defaulted to BIO tagging instead of BIOES → templates explicitly cite `config.constants.BIOES_LABELS`

---

## 7. Memory continuity

State that must survive sessions:

| Location | Content | Update when |
|----------|---------|-------------|
| `CLAUDE.md` (root) | Project-wide rules, current wave state | Project rules change |
| `docs/wave_status.md` | Current task status | After each task delivery |
| `docs/conventions.md` | Code/naming conventions | Convention changes |
| `~/.claude/.../memory/` | Srujan-specific user preferences | User-specific feedback |

Memory in `~/.claude/...` is local-only. Project docs are version-controlled and shared.

---

## 8. Skill leverage

The orchestrator should invoke Claude Code skills when patterns match:

| Pattern | Skill |
|---------|-------|
| Multi-step planning | `superpowers:writing-plans` |
| 2+ independent tasks | `superpowers:dispatching-parallel-agents` |
| Before claiming done | `superpowers:verification-before-completion` |
| Test failure unclear | `superpowers:systematic-debugging` |
| New feature design | `feature-dev:feature-dev` |
| PR/code review | `pr-review-toolkit:review-pr` |

Never silently work around an obstacle. Investigate root cause.

---

## 9. Source-of-truth precedence

When documents conflict, defer in this order:

1. `config/constants.py` — schema (entity types, BIOES labels, relations) — authoritative
2. `plan/` — frozen architecture specs
3. `docs/` — operational and architectural docs
4. `prompts/` — historical and template prompts
5. External agent self-reports — least trusted, always verify

---

## 10. Audit cadence

After every wave:

1. Run 4 parallel subagents (one per agent's deliverables)
2. Each subagent reports per-file status: EXISTS+IMPLEMENTED / EXISTS+STUB / MISSING / WRONG-API
3. Run verification gates from CLAUDE.md Section 7
4. Aggregate into wave-completion report
5. File any new gotchas into CLAUDE.md Section 8

Only declare a wave complete when all gates pass.
