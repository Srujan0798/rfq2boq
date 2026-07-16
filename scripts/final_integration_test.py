#!/usr/bin/env python3
"""Final integration smoke on the 10 SWA enquiries (held-out validation set).

Honest: uses independent gold/rowgold, reports real numbers.
No cheating.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.pipeline import Pipeline

BASE = Path("data/real_rfqs/swa_enquiries")
GOLD_BASE = Path("data/real_rfqs/gold")

ENQUIRIES = [
    ("01_gsecl", "01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf", "pdf"),
    ("02_isro", "02_isro_vssc/VSSC_BOQ_with_qty.xlsx", "xlsx"),
    ("03_zydus_matoda", "03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx", "xlsx"),
    ("04_adani", "04_adani/BOQ PAGE2adani proj.pdf", "pdf"),
    (
        "05_zydus_animal",
        "05_zydus_animal_pharmez/Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx",
        "xlsx",
    ),
    ("06_avante", "06_avante_kirloskar_pune/Insulation Boq_132.pdf", "pdf"),
    ("07_grew", "07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf", "pdf"),
    ("08_sael", "08_sael/Copy of Insulation Enquiry - SAEL.xlsx", "xlsx"),
    ("09_gem", "09_gem_bid_7439924/GeM-Bidding-9218026.pdf", "pdf"),
    ("10_gem", "10_gem_bid_7552777/GeM-Bidding-9343469.pdf", "pdf"),
]


def main():
    p = Pipeline()
    print("Final integration smoke on 10 SWA (held-out)")
    print("=" * 60)
    for eid, rel, typ in ENQUIRIES:
        path = BASE / rel
        if not path.exists():
            print(f"{eid}: MISSING {path}")
            continue
        t0 = time.time()
        try:
            r = p.run(str(path))
            dt = time.time() - t0
            print(f"{eid}: {len(r.boq_items)} items in {dt:.1f}s [{typ}]")
        except Exception as e:
            print(f"{eid}: ERROR {type(e).__name__}: {e}")
    print("=" * 60)
    print("Done. Check row counts vs user table expectations for the 10.")


if __name__ == "__main__":
    main()
