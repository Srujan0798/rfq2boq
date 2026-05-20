"""RFQ2BOQ Streamlit UI — Polished for non-technical construction estimators."""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="RFQ2BOQ — Tender BOQ Extractor",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

MAX_FILE_SIZE_MB = 10
SAMPLE_PDF = Path("data/samples/sample_rfq_simple.pdf")


@st.cache_resource
def load_pipeline():
    """Load extraction pipeline once and cache it."""
    try:
        from src.pipeline import Pipeline
        p = Pipeline()
        return p
    except Exception as e:
        st.error(f"Could not load extraction engine: {e}")
        return None


def check_file_size(uploaded_file) -> str | None:
    """Check if file exceeds size limit."""
    size_mb = uploaded_file.size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return f"File too large ({size_mb:.1f}MB). Maximum allowed: {MAX_FILE_SIZE_MB}MB."
    return None


def extract_boq(pipeline, pdf_path: Path):
    """Extract BOQ from PDF using main pipeline."""
    if pipeline is None:
        return None, "Extraction engine not loaded"
    try:
        result = pipeline.run(str(pdf_path))
        return result, None
    except Exception as e:
        return None, str(e)


def build_boq_dataframe(result) -> pd.DataFrame:
    """Convert ExtractionResult to displayable DataFrame."""
    items = []
    for item in result.boq_items:
        qty = float(item.quantity) if item.quantity else 0
        rate = float(item.rate) if item.rate else 0
        amount = float(item.amount) if item.amount else qty * rate

        conf = item.confidence if hasattr(item, "confidence") else 0.5
        if conf >= 0.8:
            quality = "Good"
        elif conf >= 0.5:
            quality = "Check"
        else:
            quality = "Verify"

        standard = ", ".join(item.standard) if item.standard else ""

        items.append({
            "S.No": item.item_no if hasattr(item, "item_no") and item.item_no else len(items) + 1,
            "Description": item.material or item.description_raw or "Unknown",
            "Quantity": qty,
            "Unit": item.unit or "nos",
            "Rate (₹)": rate,
            "Amount (₹)": amount,
            "Standard": standard,
            "Grade": item.grade or "",
            "Confidence": conf,
            "Quality": quality,
        })
    return pd.DataFrame(items)


def render_boq_table(df: pd.DataFrame):
    """Render editable BOQ dataframe with color-coded confidence."""
    if df.empty:
        st.warning("No BOQ items found in this document.")
        return

    st.markdown(f"**Total Items: {len(df)}**")

    column_config = {
        "S.No": st.column_config.NumberColumn(width="small"),
        "Description": st.column_config.TextColumn(width="large"),
        "Quantity": st.column_config.NumberColumn(format="%.2f", width="small"),
        "Unit": st.column_config.TextColumn(width="small"),
        "Rate (₹)": st.column_config.NumberColumn(format="₹%.2f", width="small"),
        "Amount (₹)": st.column_config.NumberColumn(format="₹%.2f", width="small"),
        "Standard": st.column_config.TextColumn(width="medium"),
        "Grade": st.column_config.TextColumn(width="small"),
        "Confidence": st.column_config.ProgressColumn(
            format="%.0f%%",
            min_value=0,
            max_value=100,
            width="small",
        ),
        "Quality": st.column_config.TextColumn(width="small"),
    }

    st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        num_rows="dynamic",
    )


def render_confidence_guide():
    """Show color-coded confidence legend."""
    st.markdown("**Quality Guide:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🟢 **Good** — High confidence extraction", unsafe_allow_html=True)
    with col2:
        st.markdown("🟡 **Check** — Medium confidence, review recommended", unsafe_allow_html=True)
    with col3:
        st.markdown("🔴 **Verify** — Low confidence, please check manually", unsafe_allow_html=True)


def generate_excel_bytes(result):
    """Generate CPWD Excel bytes from result."""
    import io

    try:
        from src.export.excel_generator import CPWDExcelGenerator

        gen = CPWDExcelGenerator()
        buffer = io.BytesIO()
        gen.export(
            result.boq_items,
            buffer,
            project_metadata={
                "project": result.project_name or "Untitled",
                "location": "N/A",
                "reference": result.doc_id or "N/A",
            },
        )
        buffer.seek(0)
        return buffer.getvalue()
    except Exception:
        st.error("Could not generate Excel file. Try a different format or contact support.")
        return b""


def generate_json_bytes(result):
    """Generate JSON bytes from result."""
    try:
        from src.export.json_formatter import JSONFormatter

        formatter = JSONFormatter()
        json_str = formatter.format_to_string(result)
        return json_str.encode("utf-8")
    except Exception:
        return b"{}"


def generate_csv_bytes(result):
    """Generate CSV bytes from result."""
    df = build_boq_dataframe(result)
    return df.to_csv(index=False).encode("utf-8")


def render_downloads(result, project_name: str):
    """Render download buttons for Excel, JSON, CSV."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_base = f"boq_{project_name.replace(' ', '_')}_{timestamp}"

    col1, col2, col3 = st.columns(3)

    with col1:
        excel_data = generate_excel_bytes(result)
        st.download_button(
            "📥 Download Excel",
            data=excel_data,
            file_name=f"{filename_base}.xlsx",
            mime="application/vnd.ms-excel",
            type="primary",
        )

    with col2:
        json_data = generate_json_bytes(result)
        st.download_button(
            "📋 Download JSON",
            data=json_data,
            file_name=f"{filename_base}.json",
            mime="application/json",
        )

    with col3:
        csv_data = generate_csv_bytes(result)
        st.download_button(
            "📊 Download CSV",
            data=csv_data,
            file_name=f"{filename_base}.csv",
            mime="text/csv",
        )


def render_warnings(result):
    """Render warning for low-confidence items."""
    low_conf_items = [i for i in result.boq_items if (i.confidence or 0) < 0.5]
    if low_conf_items:
        st.warning(
            f"⚠️ {len(low_conf_items)} item(s) need manual verification. "
            "Please review them before finalizing your BOQ."
        )


def main():
    st.title("📋 RFQ to BOQ Extractor")
    st.markdown("Upload a construction tender PDF to extract Bill of Quantities items automatically.")

    pipeline = load_pipeline()

    with st.sidebar:
        st.markdown("### 🏷️ RFQ2BOQ")
        st.markdown("Construction tender PDF → BOQ extractor")

        st.divider()

        st.markdown("#### ⚙️ Project Settings")

        project_name = st.text_input("Project Name", value="Untitled Project")

        region = st.selectbox(  # noqa: F841
            "Region",
            ["Delhi", "Mumbai", "Bangalore", "Chennai", "Hyderabad", "Kolkata", "Other"],
        )

        st.divider()

        if st.button("🔄 Reset Session"):
            st.rerun()

        st.caption("For help, see the Help tab or contact your administrator.")

    tab1, tab2 = st.tabs(["📄 Extract BOQ", "ℹ️ Help"])

    with tab1:
        col_upload, col_sample = st.columns([2, 1])

        with col_upload:
            st.markdown("#### 📂 Upload Tender PDF")
            uploaded_file = st.file_uploader(
                "Drag and drop or click to upload your RFQ PDF",
                type=["pdf"],
                help=f"Supported: PDF files up to {MAX_FILE_SIZE_MB}MB",
            )

        with col_sample:
            st.markdown("#### 📄 Try Sample")
            if SAMPLE_PDF.exists():
                sample_bytes = SAMPLE_PDF.read_bytes()
                st.download_button(
                    "📥 Download Sample PDF",
                    sample_bytes,
                    file_name="sample_rfq.pdf",
                    help="Use the sample tender document to try the extractor",
                )
            else:
                st.info("Sample PDF not available.")

        use_sample = st.button(
            "🚀 Try Sample Now",
            type="primary",
            disabled=not SAMPLE_PDF.exists(),
        )

        if uploaded_file:
            size_error = check_file_size(uploaded_file)
            if size_error:
                st.error(size_error)
                st.info("💡 Try compressing the PDF or splitting it into smaller files.")
                return

        if uploaded_file or use_sample:
            if use_sample and SAMPLE_PDF.exists():
                pdf_path = SAMPLE_PDF
            elif uploaded_file:
                import tempfile

                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    pdf_path = Path(tmp.name)
            else:
                return

            with st.spinner("🔍 Extracting BOQ items... This may take 30-60 seconds."):
                result, error_msg = extract_boq(pipeline, pdf_path)

            if error_msg:
                st.error("❌ Could not read this PDF. Try a different file or contact support.")
                return

            if not result or not result.boq_items:
                st.warning("No BOQ items found. The PDF may not contain standard tender data.")
                return

            st.success(f"✅ Extraction complete — {len(result.boq_items)} items found")

            st.divider()

            render_confidence_guide()

            st.divider()

            st.markdown("#### 📊 Bill of Quantities")

            df = build_boq_dataframe(result)
            render_boq_table(df)

            render_warnings(result)

            st.divider()

            st.markdown("#### 💾 Download Results")
            render_downloads(result, project_name)

    with tab2:
        st.markdown("""
        ### How to Use

        1. **Upload** a construction tender PDF (Request for Quotation)
        2. **Wait** for extraction to complete (30-60 seconds)
        3. **Review** the extracted items in the table — click cells to edit
        4. **Download** in your preferred format (Excel/JSON/CSV)

        ### Quality Labels

        - 🟢 **Good** — High confidence extraction (≥80%)
        - 🟡 **Check** — Medium confidence, review recommended (50-79%)
        - 🔴 **Verify** — Low confidence, please check manually (<50%)

        ### Need Help?

        Contact your system administrator with the document name and description of the problem.
        """)


if __name__ == "__main__":
    main()
