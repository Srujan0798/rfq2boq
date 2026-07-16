"""Annotation UI for creating human-verified BOQ gold data.

Run: streamlit run ui/annotate_gold.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="RFQ2BOQ Gold Annotator",
    page_icon="✏️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Tender definitions
# ---------------------------------------------------------------------------

TENDERS = {
    "01_gsecl": {
        "name": "01 GSECL Wanakbori TMD-8",
        "files": ["data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf"],
    },
    "02_isro": {
        "name": "02 ISRO VSSC",
        "files": ["data/real_rfqs/swa_enquiries/02_isro_vssc/VSSC_BOQ_with_qty.xlsx"],
    },
    "03_zydus_matoda": {
        "name": "03 Zydus Matoda OSD",
        "files": ["data/real_rfqs/swa_enquiries/03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx"],
    },
    "04_adani": {
        "name": "04 Adani",
        "files": [
            "data/real_rfqs/swa_enquiries/04_adani/BOQ PAGEadani proj.pdf",
            "data/real_rfqs/swa_enquiries/04_adani/BOQ PAGE2adani proj.pdf",
        ],
    },
    "05_zydus_animal": {
        "name": "05 Zydus Animal Pharmez",
        "files": [
            "data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx"
        ],
    },
    "06_avante": {
        "name": "06 Avante Kirloskar Pune",
        "files": ["data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Boq_132.pdf"],
    },
    "07_grew": {
        "name": "07 Grew Solar Narmadapuram",
        "files": ["data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf"],
    },
    "08_sael": {
        "name": "08 SAEL",
        "files": ["data/real_rfqs/swa_enquiries/08_sael/Copy of Insulation Enquiry - SAEL.xlsx"],
    },
    "09_gem": {
        "name": "09 GeM Bid 7439924",
        "files": ["data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf"],
    },
    "10_gem": {
        "name": "10 GeM Bid 7552777",
        "files": ["data/real_rfqs/swa_enquiries/10_gem_bid_7552777/GeM-Bidding-9343469.pdf"],
    },
}

ROWGOLD_DIR = Path("data/real_rfqs/gold/rows")


def get_rowgold_path(tender_id: str) -> Path:
    return ROWGOLD_DIR / f"{tender_id}.rowgold.json"


def load_existing_rowgold(tender_id: str) -> dict | None:
    path = get_rowgold_path(tender_id)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def run_pipeline(file_path: str):
    from src.pipeline import Pipeline

    pipeline = Pipeline()
    return pipeline.run(file_path)


def extract_all_items(tender_id: str) -> list[dict]:
    """Extract items from all source files for a tender."""
    tender = TENDERS[tender_id]
    all_items = []
    for fpath in tender["files"]:
        p = Path(fpath)
        if not p.exists():
            st.warning(f"File not found: {fpath}")
            continue
        with st.spinner(f"Extracting {p.name}..."):
            result = run_pipeline(str(p))
            for item in result.boq_items:
                all_items.append(
                    {
                        "item_no": len(all_items) + 1,
                        "material": item.material,
                        "quantity": str(item.quantity),
                        "unit": item.unit,
                        "grade": item.grade,
                        "source_file": p.name,
                    }
                )
    return all_items


def save_rowgold(tender_id: str, items: list[dict]):
    ROWGOLD_DIR.mkdir(parents=True, exist_ok=True)
    rowgold = {
        "doc_id": tender_id,
        "source_file": TENDERS[tender_id]["files"][0],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "human_verified": True,
        "method": "human-annotated-ui",
        "entries": [
            {
                "item_no": i + 1,
                "material": row["material"],
                "quantity": row["quantity"],
                "unit": row["unit"],
                "grade": row.get("grade", ""),
                "action": "supply",
                "dimensions": [],
                "standard": [],
                "location": "",
                "source_file": row.get("source_file", ""),
                "source_sheet": "",
                "source_row": 0,
                "human_verified": True,
                "notes": "",
            }
            for i, row in enumerate(items)
        ],
    }
    path = get_rowgold_path(tender_id)
    with open(path, "w") as f:
        json.dump(rowgold, f, indent=2)
    return path


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.title("✏️ RFQ2BOQ Gold Annotator")
st.markdown("Create human-verified BOQ rowgold for each tender. Edit, add, or delete rows as needed.")

selected_tender = st.selectbox(
    "Select Tender",
    options=list(TENDERS.keys()),
    format_func=lambda k: TENDERS[k]["name"],
)

# Load or extract
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🔄 Extract from Source Files"):
        items = extract_all_items(selected_tender)
        st.session_state[f"items_{selected_tender}"] = items
        st.success(f"Extracted {len(items)} items")

with col2:
    if st.button("📂 Load Existing Rowgold"):
        existing = load_existing_rowgold(selected_tender)
        if existing:
            items = [
                {
                    "item_no": e.get("item_no", i + 1),
                    "material": e["material"],
                    "quantity": str(e["quantity"]),
                    "unit": e["unit"],
                    "grade": e.get("grade", ""),
                    "source_file": e.get("source_file", ""),
                }
                for i, e in enumerate(existing["entries"])
            ]
            st.session_state[f"items_{selected_tender}"] = items
            st.success(f"Loaded {len(items)} items from existing gold")
        else:
            st.info("No existing rowgold found for this tender")

# Display editable table
key = f"items_{selected_tender}"
if key in st.session_state:
    items = st.session_state[key]
    st.subheader(f"Editing {len(items)} items")

    # Build dataframe for editing
    df = pd.DataFrame(items)
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        column_config={
            "item_no": st.column_config.NumberColumn("Item #", disabled=True),
            "material": st.column_config.TextColumn("Material / Description", width="large"),
            "quantity": st.column_config.TextColumn("Quantity"),
            "unit": st.column_config.TextColumn("Unit"),
            "grade": st.column_config.TextColumn("Grade"),
            "source_file": st.column_config.TextColumn("Source", disabled=True),
        },
        use_container_width=True,
    )

    # Update item numbers after edits
    edited_items = []
    for i, row in edited_df.iterrows():
        edited_items.append(
            {
                "item_no": i + 1,
                "material": str(row.get("material", "")),
                "quantity": str(row.get("quantity", "")),
                "unit": str(row.get("unit", "")),
                "grade": str(row.get("grade", "")),
                "source_file": str(row.get("source_file", "")),
            }
        )

    st.session_state[key] = edited_items

    if st.button("💾 Save Rowgold"):
        path = save_rowgold(selected_tender, edited_items)
        st.success(f"Saved to {path}")
else:
    st.info("Click 'Extract from Source Files' or 'Load Existing Rowgold' to start annotating.")
