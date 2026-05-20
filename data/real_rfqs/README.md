# Collecting Real RFQs for Training

This guide helps you collect real RFQ PDFs from Indian government tender portals.

## Target Sources

### 1. CPWD e-Tenders (Primary)
- Portal: https://etenders.gov.in
- Contains all CPWD construction tenders
- Search: "BOQ" or "Bill of Quantities"
- Filter: Construction works, Buildings

### 2. State PWD Portals
| State | Portal |
|-------|--------|
| Tamil Nadu | https://tntenders.gov.in |
| Karnataka | https://kptcl.com/tenders |
| Maharashtra | https://mahatenders.gov.in |
| Gujarat | https://gujarattenders.gov.in |
| Uttar Pradesh | https://etender.up.nic.in |

### 3. Other Sources
- Indian Railways: https://ireps.gov.in
- Smart Cities: https://smartcityapplication.gov.in
- Metro Rail: Various per city

## Download Procedure (Manual)

### CPWD e-Tenders:
1. Go to https://etenders.gov.in
2. Search keyword: "BOQ" or "construction"
3. Select date range (last 6 months)
4. Open tender details
5. Download "Tender Document" PDF
6. Save to `data/real_rfqs/raw/TN_2024_001.pdf`

### Naming Convention:
```
{State}_{Year}_{SerialNo}.pdf
Examples:
  CPWD_2024_001.pdf
  TN_PWD_2024_023.pdf
  MH_Railways_2024_045.pdf
```

## Automated Collection (Optional)

### Using web scraping:
```bash
pip install requests beautifulsoup4 pdfplumber

python3 << 'EOF'
import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "https://etenders.gov.in"
SEARCH_URL = f"{BASE_URL}/eproc tenderness"

# Search for BOQ-related tenders
params = {
    'search': 'BOQ construction',
    'status': 'live',
    'date_from': '2024-01-01'
}

response = requests.get(SEARCH_URL, params=params)
soup = BeautifulSoup(response.text, 'html.parser')

# Extract tender links
tender_links = []
for link in soup.find_all('a', href=re.compile(r'tender.*details')):
    tender_links.append(link['href'])

print(f"Found {len(tender_links)} tenders")

# Download PDFs (requires authentication)
for tender_url in tender_links[:10]:
    print(f"Tender: {tender_url}")
    # Requires login — manual download recommended
EOF
```

### Using Selenium (for dynamic pages):
```bash
pip install selenium webdriver-manager

python3 << 'EOF'
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

driver = webdriver.Chrome()
driver.get("https://etenders.gov.in")

# Login (manual in browser)
input("Login to portal, then press Enter...")

# Search and collect
search_box = driver.find_element(By.ID, "search")
search_box.send_keys("BOQ construction")
driver.find_element(By.CLASS_NAME, "search-btn").click()

time.sleep(5)

# Collect tender links
tenders = driver.find_elements(By.CSS_SELECTOR, ".tender-link")
print(f"Found {len(tenders)} tenders")

driver.quit()
EOF
```

## What to Collect

### Minimum for retraining: 20 PDFs
- 5-10 CPWD standard tender format
- 5-10 State PWD format
- 2-5 Railway/Metro format

### Ideal collection: 50+ PDFs
- Different tender types (building, road, water supply, electrical)
- Different states
- Different scales (₹1Cr, ₹10Cr, ₹100Cr+)

## Annotation Priority

Not all 20 need annotation. Priority order:

| Priority | Count | Why |
|----------|-------|-----|
| P0 | 10 | CPWD standard format (most common) |
| P1 | 5 | State PWD (varied formats) |
| P2 | 5 | Other sources (validation) |

## Storage

```
data/real_rfqs/
├── raw/                    # Original PDFs
│   ├── CPWD_2024_001.pdf
│   ├── CPWD_2024_002.pdf
│   └── ...
├── annotations/            # BIOES annotated JSON
│   ├── cpwd_standard_001.json
│   └── ...
└── README.md              # This file
```

## Verification Checklist

Before annotation, verify each PDF:
- [ ] Contains BOQ items (not just general terms)
- [ ] Has quantity + unit for materials
- [ ] Has at least 3-5 extractable entities
- [ ] Text is readable (not scanned image of poor quality)
- [ ] Saved as PDF (not DOC/DOCX)