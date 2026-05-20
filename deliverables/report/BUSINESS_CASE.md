# Business Case: RFQ2BOQ

## Problem Statement

Construction tender estimation requires manually extracting Bill of Quantities (BOQ) from Request for Quotation (RFQ) documents. This process:

- **Takes 2-4 hours** per tender for a trained estimator
- **Requires domain expertise** (IS codes, construction terminology)
- **Contains errors** leading to cost overruns or missed items

## Solution Value

RFQ2BOQ automates this extraction, reducing time from hours to minutes.

| Metric | Manual Process | RFQ2BOQ | Improvement |
|--------|----------------|---------|-------------|
| Time per tender | 2-4 hours | 2-5 minutes | **90-95% faster** |
| Errors | 5-15% miss rate | ~2% (with human review) | **70% reduction** |
| Cost per extraction | ₹500-1500 | ₹50-100 (compute) | **80-90% cheaper** |

## Market Context

### India Construction Tender Market

| Segment | Annual Value | Tender Count |
|---------|-------------|--------------|
| CPWD | ₹80,000+ Crore | 50,000+ |
| State PWDs | ₹1,20,000+ Crore | 1,00,000+ |
| Smart Cities | ₹20,000 Crore | 5,000+ |
| Railways | ₹40,000 Crore | 10,000+ |

**Assumption**: 20% of tenders require BOQ extraction = 33,000+ tenders/year in India alone.

### ROI Calculation

| Cost Element | Manual | With RFQ2BOQ |
|--------------|--------|--------------|
| Estimator time | ₹800/tender (4 hrs × ₹200/hr) | ₹100/tender (15 min + review) |
| Error correction | ₹5,000/tender (average) | ₹500/tender |
| **Total cost** | **₹5,800/tender** | **₹600/tender** |

**Annual savings per estimator**: ₹5,200 × 50 tenders/year = **₹2,60,000**

**If deployed for 100 estimators**: ₹2.6 Crore/year savings

## Competitive Advantage

1. **First-mover** in Indian construction NLP
2. **Domain-optimized** for IS codes and CPWD formats
3. **Open-source** foundation enables customization
4. **Transferable** to other markets (Southeast Asia, Middle East)

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Real-world F1 lower than expected | High | Medium | Retrain on real data (P0 priority) |
| Limited adoption by estimators | Medium | High | Partner with PWD training institutes |
| Competition from established players | Low | High | Focus on Indian standards specificity |

## Implementation Path

| Phase | Duration | Investment | Expected Outcome |
|-------|-----------|------------|-------------------|
| Pilot | 1 month | ₹50,000 | 10 RFQs processed, validated |
| Beta | 3 months | ₹2,00,000 | 100 RFQs, 20% efficiency gain |
| Production | 6 months | ₹10,00,000 | 1000+ RFQs, commercially viable |

## Recommendation

**Immediate (Next 30 days)**:
1. Collect 20 real CPWD/PWD RFQs for validation
2. Retrain model on real annotated data
3. Demonstrate pilot to 2-3 construction firms

**Medium-term (3-6 months)**:
1. Deploy as SaaS for construction firms
2. Add Hindi/regional language support
3. Build integration with existing BOQ software

**Long-term (1 year)**:
1. Expand to Southeast Asian markets
2. Add supplier quotation comparison
3. Develop predictive pricing models