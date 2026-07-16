"""Reusable Streamlit UI components for RFQ2BOQ."""

import pandas as pd
import streamlit as st


def confidence_pill(confidence: float) -> str:
    """Return emoji + label for a confidence value."""
    if confidence >= 0.85:
        return "🟢 Good"
    if confidence >= 0.50:
        return "🟡 Check"
    return "🔴 Verify"


def confidence_color(confidence: float) -> str:
    """Return CSS color for a confidence value."""
    if confidence >= 0.85:
        return "#d4edda"
    if confidence >= 0.50:
        return "#fff3cd"
    return "#f8d7da"


def boq_row_style() -> str:
    """Custom CSS for BOQ table rows."""
    return """
    <style>
    .boq-quality-good { background-color: #d4edda !important; }
    .boq-quality-check { background-color: #fff3cd !important; }
    .boq-quality-verify { background-color: #f8d7da !important; }
    .stDataframe tbody tr:nth-child(even) { background-color: #f9f9f9; }
    </style>
    """


def render_confidence_guide() -> None:
    """Show color-coded confidence legend."""
    st.markdown("**Quality Guide:**")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("🟢 **Good** — High confidence (≥85%)", unsafe_allow_html=True)
    with c2:
        st.markdown("🟡 **Check** — Medium confidence (50-84%)", unsafe_allow_html=True)
    with c3:
        st.markdown("🔴 **Verify** — Low confidence (<50%)", unsafe_allow_html=True)


def render_boq_table(df: pd.DataFrame, *, editable: bool = True) -> None:
    """Render BOQ dataframe with color-coded confidence column."""
    if df.empty:
        st.warning("No BOQ items found in this document.")
        return

    st.markdown(f"**Total Items: {len(df)}**")

    column_config = {
        "S.No": st.column_config.NumberColumn(width="small"),
        "Description": st.column_config.TextColumn(width="large"),
        "Quantity": st.column_config.NumberColumn(format="%.2f", width="small"),
        "Unit": st.column_config.TextColumn(width="small"),
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

    if editable:
        st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
            num_rows="dynamic",
        )
    else:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
        )


def render_downloads_strip(result, project_name: str) -> None:
    """Render three download buttons: Excel, JSON, CSV."""
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_base = f"boq_{project_name.replace(' ', '_')}_{timestamp}"

    c1, c2, c3 = st.columns(3)

    excel_data = _generate_excel_bytes(result)
    with c1:
        st.download_button(
            "📥 Download Excel",
            data=excel_data,
            file_name=f"{filename_base}.xlsx",
            mime="application/vnd.ms-excel",
            type="primary",
        )

    json_data = _generate_json_bytes(result)
    with c2:
        st.download_button(
            "📋 Download JSON",
            data=json_data,
            file_name=f"{filename_base}.json",
            mime="application/json",
        )

    csv_data = _generate_csv_bytes(result)
    with c3:
        st.download_button(
            "📊 Download CSV",
            data=csv_data,
            file_name=f"{filename_base}.csv",
            mime="text/csv",
        )


def _generate_excel_bytes(result) -> bytes:
    try:
        import io

        from src.export.excel_generator import CPWDExcelGenerator

        gen = CPWDExcelGenerator()
        buffer = io.BytesIO()
        gen.export(
            result.boq_items,
            buffer,
            project_metadata={
                "project": getattr(result, "project_name", None) or "Untitled",
                "location": "N/A",
                "reference": getattr(result, "doc_id", None) or "N/A",
            },
        )
        buffer.seek(0)
        return buffer.getvalue()
    except Exception:
        return b""


def _generate_json_bytes(result) -> bytes:
    try:
        from src.export.json_formatter import JSONFormatter

        formatter = JSONFormatter()
        return formatter.format_to_string(result).encode("utf-8")
    except Exception:
        return b"{}"


def _generate_csv_bytes(result) -> bytes:
    df = _result_to_dataframe(result)
    return df.to_csv(index=False).encode("utf-8")


def _result_to_dataframe(result) -> pd.DataFrame:
    items = []
    for item in result.boq_items:
        qty = float(item.quantity) if item.quantity else 0
        conf = getattr(item, "confidence", 0.5) or 0.5
        if conf >= 0.85:
            quality = "Good"
        elif conf >= 0.50:
            quality = "Check"
        else:
            quality = "Verify"
        standard = ", ".join(item.standard) if getattr(item, "standard", None) else ""
        items.append(
            {
                "S.No": getattr(item, "item_no", len(items) + 1) or len(items) + 1,
                "Description": getattr(item, "material", None)
                or getattr(item, "description_raw", "Unknown")
                or "Unknown",
                "Quantity": qty,
                "Unit": getattr(item, "unit", "nos") or "nos",
                "Standard": standard,
                "Grade": getattr(item, "grade", "") or "",
                "Confidence": conf,
                "Quality": quality,
            }
        )
    return pd.DataFrame(items)


def build_boq_dataframe(result) -> pd.DataFrame:
    return _result_to_dataframe(result)


def header_strip(title: str = "📋 RFQ to BOQ Extractor") -> None:
    """Render app header with title and repo link."""
    st.title(title)
    st.markdown(
        "Upload a construction tender PDF to extract Bill of Quantities items automatically. "
        "[View on GitHub](https://github.com/srujan-sai/rfq2boq)"
    )


def sidebar_settings() -> dict:
    """Render sidebar settings, return values as dict."""
    st.sidebar.markdown("### 🏷️ RFQ2BOQ")
    st.sidebar.markdown("Construction tender PDF → BOQ extractor")
    st.sidebar.divider()
    st.sidebar.markdown("#### ⚙️ Project Settings")

    project_name = st.sidebar.text_input("Project Name", value="Untitled Project")
    region = st.sidebar.selectbox(
        "Region",
        ["Delhi", "Mumbai", "Bangalore", "Chennai", "Hyderabad", "Kolkata", "Other"],
    )

    st.sidebar.divider()
    if st.sidebar.button("🔄 Reset Session"):
        st.rerun()

    st.sidebar.caption("For help, see the Help tab or contact your administrator.")
    return {"project_name": project_name, "region": region}
