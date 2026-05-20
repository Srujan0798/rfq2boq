# CPWD DSR 2023 Rate Reference

## Source

**CPWD Delhi Schedule of Rates 2023 (Vol 1 Civil)**
- Published by: Central Public Works Department, Government of India
- Region: Delhi
- Year: 2023
- License: Public Domain under NDSAP (National Data Sharing and Accessibility Policy) / RTI Act

## Official Sources

1. **Primary:** CPWD website (https://cpwd.gov.in) — may have SSL issues
2. **Mirror 1:** https://helptheengineer.com/cpwd-publication/
3. **Mirror 2:** https://civilenggascent.com/cpwd-sor-schedule-of-rates-2023-pdf-download/
4. **Mirror 3:** https://www.scribd.com/document/777526980/DSR-Vol-1-Civil-2023-Compressed-2

## Data Description

- **Total items:** 501 line items
- **Chapters:** 31 chapters covering all major construction work types
- **Scope:** Earthwork, Concrete, RCC, Reinforcement, Brickwork, Flooring, Woodwork, Steel Work, Plumbing, Electrical, Road Work, Painting, Waterproofing, etc.

## How to Update

1. Download the latest CPWD DSR PDF from one of the mirror links
2. Run `python scripts/parse_dsr_pdf.py --input <pdf_path> --output data/rates/cpwd_dsr_2023.json`
3. The script extracts table data and normalizes to the standard schema
4. If new DSR has corrections, update the JSON manually or re-run extraction

## Rate Structure

Each item includes:
- `code`: DSR item code
- `description`: Work description
- `chapter`: DSR chapter name
- `material`: Material category
- `grade`: Material grade (if applicable)
- `unit`: Standard unit (m³, m², kg, nos, etc.)
- `rate_inr`: Rate in Indian Rupees

## State SOR Alternatives

For state-specific rates, consider:
- **Maharashtra:** MSRTC / PWD SOR
- **Karnataka:** PWD SOR
- **Tamil Nadu:** TN PWD SOR
- **Uttar Pradesh:** UP PWD SOR

The rate lookup follows this priority:
1. Exact match (material + grade + unit)
2. Fuzzy match (Levenshtein < 3 on material name)
3. Hardcoded fallback rates

## Usage in CostEstimator

```python
from src.domain.cost_estimator import CostEstimator
ce = CostEstimator()
rate = ce.lookup_rate('cement', 'OPC 43', 'bag', 'delhi')
# Returns: {'rate': 350, 'source': 'DSR 2023', ...}
```

## Citation

CPWD Delhi Schedule of Rates 2023, Central Public Works Department, Government of India. Public domain under NDSAP/RTI Act.