#!/usr/bin/env python3
import json
import os
import sys

from src.pipeline import Pipeline

gold_files = {
    "01": "data/real_rfqs/gold/swa_01_gsecl_wanakbori_tmd8.json",
    "02": "data/real_rfqs/gold/swa_02_isro_vssc.json",
    "03": "data/real_rfqs/gold/swa_03_zydus_matoda_osd.json",
    "04": "data/real_rfqs/gold/swa_04_adani.json",
    "05": "data/real_rfqs/gold/swa_05_zydus_animal_pharmez.json",
    "06": "data/real_rfqs/gold/swa_06_avante_kirloskar_pune.json",
    "07": "data/real_rfqs/gold/swa_07_grew_solar_narmadapuram.json",
    "08": "data/real_rfqs/gold/swa_08_sael.json",
    "09": "data/real_rfqs/gold/swa_09_gem_bid_7439924.json",
    "10": "data/real_rfqs/gold/swa_10_gem_bid_7552777.json",
}

source_files = {
    "01": "data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf",
    "02": "data/real_rfqs/swa_enquiries/02_isro_vssc/VSSC_BOQ_with_qty.xlsx",
    "03": "data/real_rfqs/swa_enquiries/03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx",
    "04": "data/real_rfqs/swa_enquiries/04_adani/BOQ PAGEadani proj.pdf",
    "05": "data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx",
    "06": "data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Boq_132.pdf",
    "07": "data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf",
    "08": "data/real_rfqs/swa_enquiries/08_sael/Copy of Insulation Enquiry - SAEL.xlsx",
    "09": "data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf",
    "10": "data/real_rfqs/swa_enquiries/10_gem_bid_7552777/GeM-Bidding-9343469.pdf",
}

p = Pipeline()
total_matched = 0
total_gold = 0

for id, gold_path in gold_files.items():
    if not os.path.exists(gold_path):
        print(f"{id}. GOLD FILE MISSING: {gold_path}")
        continue
    with open(gold_path) as f:
        gold = json.load(f)
    items = gold.get("items", gold.get("boq_items", gold.get("rows", [])))
    gold_rows = items if isinstance(items, list) else []

    r = p.run(source_files[id])
    pred_rows = r.boq_items

    gold_mats = set()
    for row in gold_rows:
        m = row.get("material", row.get("description", "")).lower().strip()
        if m:
            gold_mats.add(m)

    pred_mats = set()
    for row in pred_rows:
        m = row.material.lower().strip() if row.material else ""
        if m:
            pred_mats.add(m)

    matched = len(gold_mats & pred_mats)
    total_gold += len(gold_mats)
    total_matched += matched
    rate = (matched / len(gold_mats) * 100) if gold_mats else 0

    status = "OK" if rate >= 50 else "LOW"
    print(f"{id}. gold={len(gold_mats)}, pred={len(pred_rows)}, matched={matched} ({rate:.0f}%) [{status}]")
    if rate < 50:
        print(f"   gold samples: {list(gold_mats)[:3]}")
        print(f"   pred samples: {list(pred_mats)[:3]}")
    sys.stdout.flush()

print(
    f"\nOverall: {total_matched}/{total_gold} materials matched ({100*total_matched/total_gold:.1f}%)"
    if total_gold
    else "No gold data"
)
