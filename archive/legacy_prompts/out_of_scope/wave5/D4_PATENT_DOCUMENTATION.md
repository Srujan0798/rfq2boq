# TASK: Patent Documentation — Owner (Srujan) + University IP Office

**Wave:** 5 | **Tier:** D | **Priority:** P3

## 1. GOAL
Document patent-worthy contributions for provisional patent filing through Srujan's university IP office.

## 2. CONTEXT
Read first:
- `report/technical_report.md` — technical contributions
- `docs/architecture.md`
- Wave 1-5 deliverables (novel patterns)
- [docs/conventions.md](../../../../docs/conventions.md)

This task is mostly a research + legal coordination task, not coding.

## 3. DELIVERABLES
- [ ] `patent/contributions.md` — novel contributions list with technical detail
- [ ] `patent/prior_art_search.md` — USPTO + Google Patents search results
- [ ] `patent/claims_draft.md` — draft independent + dependent claims
- [ ] `patent/figures/` — diagrams supporting claims
- [ ] `patent/SUBMISSION_README.md` — how to submit via university IP office
- [ ] `patent/INVENTORS.md` — list of named inventors with contributions

## 4. STEPS
1. Identify novel contributions:
   - Hybrid ML + rule conflict resolution algorithm (Section: src/rules/conflict.py logic)
   - Construction-specific BIOES synthetic data generator with bilingual support
   - Active learning loop with uncertainty-driven review queue
   - Knowledge graph + JSON ontology dual-source approach with cache layer
   - Layout-aware extraction with confidence-aware routing
2. Prior art search:
   - USPTO Patent Public Search
   - Google Patents
   - Espacenet (European)
   - WIPO PatentScope
   - Document closest 10-15 prior art with distinctions
3. Draft claims:
   - 1-3 independent claims (system, method, computer-readable medium)
   - 10-20 dependent claims
4. Diagrams: flowcharts, architecture diagrams from technical report
5. Submission packet: README explaining how to assemble for university IP office
6. Inventor list with contribution percentages

## 5. VERIFICATION
```bash
$ test -f patent/contributions.md && wc -l patent/contributions.md
EXPECT: ≥100 lines

$ test -f patent/prior_art_search.md && wc -l patent/prior_art_search.md
EXPECT: ≥50 lines (10-15 prior art entries)

$ test -f patent/claims_draft.md
EXPECT: exit 0

$ ls patent/figures/*.pdf 2>/dev/null | wc -l
EXPECT: ≥5
```

## 6. ACCEPTANCE CRITERIA
- [ ] Novel contributions clearly distinguished from prior art
- [ ] Claims are technically specific (avoid "an apparatus comprising")
- [ ] Figures support claims
- [ ] University IP office contact identified
- [ ] Inventor list approved by all named parties

## 7. CONSTRAINTS
- Honesty: only claim what's actually novel
- Avoid disclosure: do NOT publish or present until provisional filed
- 12-month deadline: provisional buys 12 months for full filing
- Cost: typically ~$300-3000 depending on jurisdiction + attorney

## 8. DEPENDENCIES
- **Blocked by:** All previous waves (need final implementation to claim)
- **Blocks:** Public dataset release (D1) and paper (D2) — both are PUBLIC DISCLOSURE that can bar patenting in some jurisdictions
- **Parallel-safe with:** None — this should be done BEFORE D1/D2

## 9. GOTCHAS
- ORDER MATTERS: file provisional BEFORE publishing dataset or paper, or you lose patent rights in many countries (US has 1-year grace; EU does not)
- University IP office may have priority claim on inventions
- "Novel" must be measured against worldwide prior art, not just local
- Claims drafting is a specialized skill — engage patent attorney
- Software patents face heightened scrutiny — emphasize technical implementation
- Some inventions may not be patentable (abstract algorithms) — focus on the system integration

**Important:** This task involves legal/IP consequences. Coordinate with Srujan's university IP office BEFORE filing. Public disclosure (paper, dataset, GitHub repo) may bar patenting in non-US jurisdictions.
