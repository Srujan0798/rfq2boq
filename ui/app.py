"""RFQ2BOQ Streamlit UI — Polished for non-technical construction estimators.

P5_01: makes R1 visible to the user.

- Flagged rows in the BOQ table are visually distinct (severity color
  via the new ``flags`` column + a legend).
- The **Flag Review** panel surfaces every Flag grouped by severity
  (error / review / info) with the original code + message + row ref.
- Non-BOQ documents (compliance checklists, blank tenders) show a
  document-type banner ("0 line items, classified as COMPLIANCE_CHECKLIST")
  instead of a bare error / empty table.
- The footer carries the model version + pipeline commit so a
  user can quote the build that produced the file.
- All pipeline calls go through the same entry point the CLI uses
  (``src.pipeline.Pipeline.run`` for PDFs, ``src.pipeline_xlsx.XLSXRowPipeline.run``
  for XLSX).  No UI-only code paths.
- Extraction results are cached in ``st.session_state`` keyed by
  ``sha256(file)`` so widget re-renders don't re-run a 60s extraction
  (P5_01 §9 gotcha).
"""

from __future__ import annotations

import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="RFQ2BOQ — Tender BOQ Extractor",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --rfq-bg: #0a1420;
        --rfq-panel: #101d2e;
        --rfq-border: #22344a;
        --rfq-gold: #c9a24b;
        --rfq-blue: #5b9bd5;
        --rfq-text: #eef2f6;
        --rfq-text-dim: #93a5b8;
    }
    div[data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 85% 8%, rgba(91,155,213,0.08), transparent 45%),
            radial-gradient(circle at 8% 92%, rgba(201,162,75,0.06), transparent 40%),
            linear-gradient(180deg, var(--rfq-bg) 0%, #0d1b2c 100%) !important;
        color: var(--rfq-text) !important;
    }
    div[data-testid="stHeader"] { background: transparent; }
    h1 { color: var(--rfq-text) !important; font-weight: 800 !important; letter-spacing: -0.5px; }
    h2, h3, h4 { color: var(--rfq-text) !important; }
    p, span, label, li, div[data-testid="stMarkdownContainer"] { color: var(--rfq-text) !important; }
    .stCaption, small { color: var(--rfq-text-dim) !important; }

    div[data-testid="stMetric"] {
        background: var(--rfq-panel);
        border: 1px solid var(--rfq-border);
        border-left: 4px solid var(--rfq-gold);
        border-radius: 8px;
        padding: 14px 16px 10px 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricValue"] { color: var(--rfq-text) !important; }
    div[data-testid="stMetricLabel"] { color: var(--rfq-text-dim) !important; }

    .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--rfq-gold), #a8823a) !important;
        color: #0a1420 !important;
        border: none !important;
        font-weight: 700 !important;
    }
    .stButton > button, .stDownloadButton > button {
        background: var(--rfq-panel) !important;
        color: var(--rfq-text) !important;
        border: 1px solid var(--rfq-border) !important;
    }

    div[data-testid="stFileUploaderDropzone"] {
        border: 2px dashed var(--rfq-border) !important;
        border-radius: 10px !important;
        background: var(--rfq-panel) !important;
    }
    section[data-testid="stFileUploaderDropzone"] * { color: var(--rfq-text-dim) !important; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--rfq-bg) 0%, #0d1b2c 100%);
        border-right: 1px solid var(--rfq-border);
    }
    section[data-testid="stSidebar"] * { color: var(--rfq-text) !important; }
    section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] select {
        background: var(--rfq-panel) !important;
        color: var(--rfq-text) !important;
    }

    div[data-testid="stExpander"] {
        background: var(--rfq-panel) !important;
        border: 1px solid var(--rfq-border) !important;
        border-radius: 8px !important;
    }
    div[data-testid="stStatusWidget"], div[data-testid="stAlert"] {
        background: var(--rfq-panel) !important;
        border: 1px solid var(--rfq-border) !important;
        color: var(--rfq-text) !important;
    }
    div[data-testid="stDataFrame"], div[data-testid="stTable"] {
        background: var(--rfq-panel) !important;
    }
    hr { border-color: var(--rfq-border) !important; }
    div[data-testid="stTabs"] button { color: var(--rfq-text-dim) !important; }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--rfq-gold) !important;
        border-bottom-color: var(--rfq-gold) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

from config.settings import settings  # noqa: E402

MAX_FILE_SIZE_MB = settings.MAX_FILE_SIZE_MB
# SAMPLE_PDF removed (S2_PURGE_DEMO_SAMPLE - only real tenders)


# ---------------------------------------------------------------------------
# Provenance: model version + pipeline commit (footer)
# ---------------------------------------------------------------------------


def _pipeline_version_string() -> str:
    """Return ``v{short_commit}`` for the footer.

    Reads from git (best-effort, never raises) and falls back to
    ``vunknown`` so the footer always renders something.
    """
    try:
        import subprocess

        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        commit = (out.stdout or "").strip()
        if commit:
            return f"v{commit}"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return "vunknown"


# ---------------------------------------------------------------------------
# Pipeline loading + extraction (the same entry points the CLI uses)
# ---------------------------------------------------------------------------


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


def render_uploaded_pdf_preview(uploaded_file) -> None:
    """Inline PDF preview + an 'open in new tab' link, so the reviewer can
    cross-check extracted rows against the source document without leaving
    the app. No poppler/pdf2image dependency: the browser's native PDF
    viewer renders the base64-embedded bytes directly.
    """
    import base64

    pdf_bytes = uploaded_file.getbuffer()
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    data_uri = f"data:application/pdf;base64,{b64}"

    with st.expander(f"📄 Preview source PDF — {uploaded_file.name}", expanded=False):
        st.markdown(
            f'<a href="{data_uri}" target="_blank" rel="noopener noreferrer">'
            f"↗ Open full PDF in a new browser tab</a>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<iframe src="{data_uri}" width="100%" height="600" '
            f'style="border:1px solid #ddd; border-radius:4px;"></iframe>',
            unsafe_allow_html=True,
        )


def get_temp_file_path(uploaded_file) -> Path:
    """Save uploaded file to temporary location and return path."""
    import tempfile

    suffix = Path(uploaded_file.name).suffix if hasattr(uploaded_file, "name") else ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        return Path(tmp.name)


def _file_hash(file_path: Path) -> str:
    """Return sha256 hex of a file's bytes (used as session cache key)."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _file_hash_for_upload(uploaded_file) -> str:
    """sha256 of an in-memory upload (Streamlit's UploadedFile)."""
    try:
        return hashlib.sha256(uploaded_file.getbuffer()).hexdigest()
    except Exception:
        # Fallback: write to a temp file and hash it.
        tmp = get_temp_file_path(uploaded_file)
        try:
            return _file_hash(tmp)
        finally:
            tmp.unlink(missing_ok=True)


def extract_boq_pdf(pipeline, file_path: Path):
    """Extract BOQ from PDF using main pipeline."""
    if pipeline is None:
        return None, "Extraction engine not loaded"
    try:
        result = pipeline.run(str(file_path))
        return result, None
    except Exception as e:
        return None, str(e)


def extract_boq_xlsx(file_path: Path):
    """Extract BOQ from Excel using XLSX pipeline."""
    try:
        from src.pipeline_xlsx import XLSXRowPipeline

        xp = XLSXRowPipeline()
        items = xp.run(str(file_path))
        # Wrap in a compatible result object
        from src.pipeline import ExtractionResult

        result = ExtractionResult(
            boq_items=items,
            project_name=file_path.stem,
            doc_id=file_path.stem,
        )
        return result, None
    except Exception as e:
        return None, str(e)


def extract_boq_with_timeout(pipeline, file_path: Path, timeout_sec: float = 60.0) -> tuple:
    """Extract BOQ with timeout guard."""
    from concurrent.futures import ThreadPoolExecutor, TimeoutError

    suffix = file_path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(extract_boq_xlsx, file_path)
            try:
                return future.result(timeout=timeout_sec)
            except TimeoutError:
                return None, f"Extraction timed out after {timeout_sec}s"
            except Exception as e:
                return None, str(e)
    else:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(extract_boq_pdf, pipeline, file_path)
            try:
                return future.result(timeout=timeout_sec)
            except TimeoutError:
                return None, f"Extraction timed out after {timeout_sec}s"
            except Exception as e:
                return None, str(e)


# ---------------------------------------------------------------------------
# Flag helpers
# ---------------------------------------------------------------------------


def _flag_value(flag: Any, *keys: str, default: Any = None) -> Any:
    """Read a key from a Flag (dataclass or dict)."""
    if flag is None:
        return default
    if isinstance(flag, dict):
        d = flag
    else:
        to_dict = getattr(flag, "to_dict", None)
        d = to_dict() if callable(to_dict) else dict(getattr(flag, "__dict__", {}))
    for k in keys:
        v = d.get(k)
        if v is not None:
            return v
    return default


def _row_flags(item: Any) -> list[Any]:
    """Return the list of Flags attached to a BOQ row (any form)."""
    flags = getattr(item, "flags", None)
    if flags is None and isinstance(item, dict):
        flags = item.get("flags")
    if not flags:
        # Backward-compat: turn legacy string warnings into info-level
        # Flags so the user still sees them surfaced.
        warnings = getattr(item, "warnings", None)
        if warnings is None and isinstance(item, dict):
            warnings = item.get("warnings")
        if warnings:
            item_no = (
                getattr(item, "item_no", None) or (item.get("item_no") if isinstance(item, dict) else None) or "?"
            )
            return [
                {
                    "code": "LEGACY_WARNING",
                    "severity": "review",
                    "stage": "assembly",
                    "message": str(w),
                    "row_ref": str(item_no),
                }
                for w in warnings
            ]
    return list(flags or [])


def _row_severity(item: Any) -> str | None:
    """Most severe flag severity on a row, or None if no flags."""
    rank = {"error": 3, "review": 2, "info": 1}
    best: str | None = None
    for f in _row_flags(item):
        sev = str(_flag_value(f, "severity", default="")).lower()
        if not sev:
            continue
        if best is None or rank.get(sev, 0) > rank.get(best, 0):
            best = sev
    return best


def _row_flag_codes(item: Any) -> list[str]:
    """Sorted unique flag codes on a row."""
    return sorted({str(_flag_value(f, "code", default="")) for f in _row_flags(item) if _flag_value(f, "code", default="")})


def _result_flag_summary(result) -> dict[str, int]:
    """Tally flags by severity across the result (rows + metadata)."""
    counts: dict[str, int] = {"error": 0, "review": 0, "info": 0}
    for item in getattr(result, "boq_items", []) or []:
        for f in _row_flags(item):
            sev = str(_flag_value(f, "severity", default="")).lower()
            if sev in counts:
                counts[sev] += 1
    metadata = getattr(result, "metadata", None)
    if metadata is not None:
        meta_flags = getattr(metadata, "flags", None) or []
        for f in meta_flags:
            sev = str(_flag_value(f, "severity", default="")).lower()
            if sev in counts:
                counts[sev] += 1
    return counts


def _classify_document_type(result) -> str | None:
    """Return the document's classified table_type, if any.

    The pipeline emits a ``TABLE_TYPE_NOT_BOQ`` Flag with the type
    in the message (e.g. "classified table is 'COMPLIANCE_CHECKLIST'").
    Returns the type string (e.g. ``"COMPLIANCE_CHECKLIST"``) or None.
    """
    if result is None:
        return None
    metadata = getattr(result, "metadata", None)
    if metadata is None:
        return None
    for f in getattr(metadata, "flags", None) or []:
        code = str(_flag_value(f, "code", default=""))
        if code == "TABLE_TYPE_NOT_BOQ":
            msg = str(_flag_value(f, "message", default=""))
            # message is e.g. "classified table is 'COMPLIANCE_CHECKLIST', not BOQ — 0 rows emitted; document not skippable"
            if "'" in msg:
                return msg.split("'", 2)[1] if "'" in msg else None
            return msg or "NON_BOQ"
    return None


# ---------------------------------------------------------------------------
# DataFrame construction (adds Flags column for severity-coloring)
# ---------------------------------------------------------------------------


def build_boq_dataframe(result) -> pd.DataFrame:
    """Convert ExtractionResult to displayable DataFrame (unpriced BOQ)."""
    items = []
    for item in result.boq_items:
        qty = float(item.quantity) if item.quantity else 0

        conf = item.confidence if hasattr(item, "confidence") else 0.5
        if conf >= 0.8:
            quality = "Good"
        elif conf >= 0.5:
            quality = "Check"
        else:
            quality = "Verify"

        standard = ", ".join(item.standard) if item.standard else ""

        # P5_01: row-level severity from typed Flags.  The
        # `flags` column is the trigger the UI uses to apply
        # color (via st.data_editor row styling is limited, so
        # we render the severity as a pill in its own column).
        severity = _row_severity(item) or ""
        flag_codes = _row_flag_codes(item)

        items.append(
            {
                "S.No": item.item_no if hasattr(item, "item_no") and item.item_no else len(items) + 1,
                "Description": item.material or item.description_raw or "Unknown",
                "Quantity": qty,
                "Unit": item.unit or "nos",
                "Standard": standard,
                "Grade": item.grade or "",
                "Confidence": conf,
                "Quality": quality,
                "Flags": ", ".join(flag_codes) if flag_codes else "",
                "Severity": severity,
            }
        )
    return pd.DataFrame(items)


def render_boq_table(df: pd.DataFrame) -> None:
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
        "Standard": st.column_config.TextColumn(width="medium"),
        "Grade": st.column_config.TextColumn(width="small"),
        "Confidence": st.column_config.ProgressColumn(
            format="%.0f%%",
            min_value=0,
            max_value=100,
            width="small",
        ),
        "Quality": st.column_config.TextColumn(width="small"),
        "Flags": st.column_config.TextColumn(width="medium"),
        "Severity": st.column_config.TextColumn(width="small"),
    }

    st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        num_rows="dynamic",
        disabled=["Flags", "Severity"],  # read-only — derived from typed Flags
    )


def render_confidence_guide() -> None:
    """Show color-coded confidence + severity legend."""
    st.markdown("**Confidence guide:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🟢 **Good** — High confidence extraction (≥80%)", unsafe_allow_html=True)
    with col2:
        st.markdown("🟡 **Check** — Medium confidence, review recommended (50–79%)", unsafe_allow_html=True)
    with col3:
        st.markdown("🔴 **Verify** — Low confidence, please check manually (<50%)", unsafe_allow_html=True)
    st.markdown("**Severity guide (typed flags, R1):**")
    scol1, scol2, scol3 = st.columns(3)
    with scol1:
        st.markdown("🔴 **Error** — capture failed or suspect", unsafe_allow_html=True)
    with scol2:
        st.markdown("🟠 **Review** — needs human check", unsafe_allow_html=True)
    with scol3:
        st.markdown("⚪ **Info** — observation, not blocking", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Entity highlight helpers (NER span coloring for text preview)
# ---------------------------------------------------------------------------

# Stable colors for the 8 ontology entity types (config.constants.ENTITY_LABELS).
_ENTITY_COLORS: dict[str, str] = {
    "MATERIAL": "#5b9bd5",
    "QUANTITY": "#70ad47",
    "UNIT": "#ed7d31",
    "LOCATION": "#9e480e",
    "DIMENSION": "#7030a0",
    "STANDARD": "#00b0f0",
    "ACTION": "#c00000",
    "GRADE": "#c9a24b",
}


def highlight_entities(text: str, entities: list[dict[str, Any]] | list[Any]) -> str:
    """Wrap entity spans in colored HTML ``<span>`` tags.

    ``entities`` entries are dicts (or objects) with ``start``, ``end``,
    and ``type`` (optionally ``confidence``). Empty entity list returns
    ``text`` unchanged. Non-entity text is HTML-escaped; entity type names
    appear in the span markup (class / data attr / title).
    """
    import html as _html

    if not entities:
        return text

    spans: list[tuple[int, int, str, float]] = []
    for ent in entities:
        if isinstance(ent, dict):
            start = int(ent.get("start", 0) or 0)
            end = int(ent.get("end", start) or start)
            etype = str(ent.get("type", "ENTITY") or "ENTITY")
            conf = float(ent.get("confidence", 0.0) or 0.0)
        else:
            start = int(getattr(ent, "start", 0) or 0)
            end = int(getattr(ent, "end", start) or start)
            etype = str(getattr(ent, "type", "ENTITY") or "ENTITY")
            conf = float(getattr(ent, "confidence", 0.0) or 0.0)
        if end <= start or start < 0 or end > len(text):
            continue
        spans.append((start, end, etype, conf))

    if not spans:
        return text

    spans.sort(key=lambda s: s[0])
    parts: list[str] = []
    cursor = 0
    for start, end, etype, conf in spans:
        if start < cursor:
            continue  # skip overlapping span
        if start > cursor:
            parts.append(_html.escape(text[cursor:start]))
        color = _ENTITY_COLORS.get(etype.upper(), "#888888")
        fragment = _html.escape(text[start:end])
        title = f"{etype} ({conf:.0%})" if conf else etype
        parts.append(
            f'<span class="entity-span entity-{_html.escape(etype.lower())}" '
            f'style="background-color:{color}33;border-bottom:2px solid {color};'
            f'border-radius:2px;padding:0 2px;" '
            f'title="{_html.escape(title)}" '
            f'data-entity-type="{_html.escape(etype)}">'
            f"{fragment}</span>"
        )
        cursor = end
    if cursor < len(text):
        parts.append(_html.escape(text[cursor:]))
    return "".join(parts)


def render_entity_legend() -> None:
    """Render a one-row color legend for the 8 ontology entity types."""
    from config.constants import ENTITY_LABELS

    st.markdown("**Entity types:**")
    cols = st.columns(len(ENTITY_LABELS))
    for col, label in zip(cols, ENTITY_LABELS, strict=False):
        color = _ENTITY_COLORS.get(label, "#888888")
        with col:
            st.markdown(
                f'<span style="display:inline-block;width:10px;height:10px;'
                f"background:{color};border-radius:2px;margin-right:4px;"
                f'vertical-align:middle;"></span>'
                f"**{label}**",
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# P5_01: Flag review panel (R1 made visible to the user)
# ---------------------------------------------------------------------------


def render_flag_review_panel(result) -> None:
    """Group every Flag by severity, render a clear panel.

    P5_01 §3 deliverable: the user must be able to see exactly what
    was flagged and why.  The Review sheet in Excel has the same
    data; the UI panel is the live, in-browser equivalent.
    """
    counts = _result_flag_summary(result)
    total = sum(counts.values())
    if total == 0:
        st.markdown("#### 🚩 Flag Review")
        st.success("No flags — every extracted row passed review.")
        return

    st.markdown(f"#### 🚩 Flag Review — {total} flag(s) raised")

    by_sev: dict[str, list[tuple[Any, str]]] = {"error": [], "review": [], "info": []}
    for item in getattr(result, "boq_items", []) or []:
        item_no = (
            getattr(item, "item_no", None) or (item.get("item_no") if isinstance(item, dict) else None) or "?"
        )
        for f in _row_flags(item):
            sev = str(_flag_value(f, "severity", default="")).lower()
            if sev not in by_sev:
                by_sev[sev] = []
            by_sev[sev].append((f, str(item_no)))
    # Document-level flags
    metadata = getattr(result, "metadata", None)
    if metadata is not None:
        for f in getattr(metadata, "flags", None) or []:
            sev = str(_flag_value(f, "severity", default="")).lower()
            if sev not in by_sev:
                by_sev[sev] = []
            by_sev[sev].append((f, "—"))

    sev_label = {
        "error": "🔴 Error",
        "review": "🟠 Review",
        "info": "⚪ Info",
    }

    for sev in ("error", "review", "info"):
        items = by_sev.get(sev) or []
        if not items:
            continue
        with st.expander(
            f"{sev_label[sev]} — {len(items)} flag(s)",
            expanded=(sev == "error"),
        ):
            rows = []
            for f, row_ref in items:
                rows.append(
                    {
                        "Row": row_ref,
                        "Stage": str(_flag_value(f, "stage", default="")),
                        "Code": str(_flag_value(f, "code", default="")),
                        "Message": str(_flag_value(f, "message", default="")),
                        "Original": str(_flag_value(f, "original", default="") or ""),
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# P5_01: document-type banner for non-BOQ docs
# ---------------------------------------------------------------------------


def render_document_type_banner(result) -> None:
    """Show a non-BOQ document-type banner when applicable.

    P5_01 §3 deliverable: non-BOQ uploads (compliance checklists,
    blank tenders, etc.) should show a clear classification banner
    instead of an error / empty table.
    """
    if result is None:
        return
    doc_type = _classify_document_type(result)
    items = getattr(result, "boq_items", None) or []
    n_items = len(items)
    if doc_type and n_items == 0:
        st.info(
            f"📄 **0 line items extracted** — document classified as `{doc_type}`.  "
            "This is not a Bill of Quantities; the PDF/Excel contains a different "
            "table type (e.g. compliance checklist, schedule, or specifications)."
        )
    elif doc_type and n_items > 0:
        # Mixed: some BOQ rows + a non-BOQ table elsewhere.
        st.warning(
            f"📄 Document also contains a `{doc_type}` table — {n_items} BOQ row(s) "
            "extracted.  Other tables were classified as non-BOQ and not extracted."
        )


# ---------------------------------------------------------------------------
# Downloads
# ---------------------------------------------------------------------------


def generate_excel_bytes(result):
    """Generate CPWD Excel bytes from result (with P5_01 Review + Provenance sheets)."""
    import tempfile

    try:
        from src.export.excel_generator import CPWDExcelGenerator

        gen = CPWDExcelGenerator()
        # CPWDExcelGenerator.export() expects a real filesystem path
        # (it calls Path(output_path).parent.mkdir() and writes via
        # openpyxl.save()).  Use a temp file, read the bytes back,
        # then clean up.  Fixed in P3_02.
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            source_file = ""
            sha = ""
            try:
                source_file = getattr(result, "source_file", "") or ""
            except Exception:
                source_file = ""
            gen.export(
                result.boq_items,
                str(tmp_path),
                project_metadata={
                    "project": result.project_name or "Untitled",
                    "location": "N/A",
                    "reference": result.doc_id or "N/A",
                },
                provenance={
                    "source_file": source_file,
                    "source_sha256": sha,
                    "pipeline_version": "rfq2boq-phase9",
                },
            )
            return tmp_path.read_bytes()
        finally:
            tmp_path.unlink(missing_ok=True)
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
            f"⚠️ {len(low_conf_items)} item(s) need manual verification. Please review them before finalizing your BOQ."
        )


# ---------------------------------------------------------------------------
# Footer (P5_01 §3: model version + pipeline commit)
# ---------------------------------------------------------------------------


def render_footer() -> None:
    """Footer with model version + pipeline commit + schema version."""
    version = _pipeline_version_string()
    st.markdown("---")
    st.markdown(
        f"<div style='text-align:center; color:#888; font-size:0.85em;'>"
        f"RFQ2BOQ {version} · SWA Consultancy · BOQ JSON schema v1.1.0 · "
        f"unpriced BOQ (no Rate/Amount/cost columns per scope)"
        f"</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    st.title("📋 RFQ to BOQ Extractor")
    st.markdown("Upload a construction tender PDF or Excel to extract Bill of Quantities items automatically.")

    pipeline = load_pipeline()

    with st.sidebar:
        st.markdown("### 🏷️ RFQ2BOQ")
        st.markdown("Construction tender PDF/Excel → BOQ extractor")

        st.divider()

        st.markdown("#### ⚙️ Project Settings")

        project_name = st.text_input("Project Name", value="Untitled Project")

        region = st.selectbox(  # noqa: F841
            "Region",
            ["Delhi", "Mumbai", "Bangalore", "Chennai", "Hyderabad", "Kolkata", "Other"],
        )

        st.divider()

        if st.button("🔄 Reset Session"):
            st.session_state.pop("extraction_cache", None)
            st.rerun()

        st.caption("For help, see the Help tab or contact your administrator.")

    tab1, tab2 = st.tabs(["📄 Extract BOQ", "ℹ️ Help"])

    with tab1:
        st.markdown("#### 📂 Upload Tender PDF or Excel (real tenders only)")
        uploaded_file = st.file_uploader(
            "Drag and drop or click to upload your RFQ (PDF or Excel)",
            type=["pdf", "xlsx", "xls"],
            help=f"Supported: PDF and Excel files up to {MAX_FILE_SIZE_MB}MB",
        )

        if uploaded_file:
            size_error = check_file_size(uploaded_file)
            if size_error:
                st.error(size_error)
                st.info("💡 Try compressing the PDF or splitting it into smaller files.")
                return

        if uploaded_file and Path(uploaded_file.name).suffix.lower() == ".pdf":
            render_uploaded_pdf_preview(uploaded_file)

        if uploaded_file:
            # P5_01 §9: cache extraction in session_state keyed by file
            # hash so widget re-renders don't re-run a 60s extraction.
            file_hash = _file_hash_for_upload(uploaded_file)
            cache = st.session_state.setdefault("extraction_cache", {})
            cached = cache.get(file_hash)
            if cached is not None:
                result, error_msg, elapsed = cached
            else:
                import time as _time

                suffix = Path(uploaded_file.name).suffix if hasattr(uploaded_file, "name") else ".pdf"
                file_path = get_temp_file_path(uploaded_file)
                is_excel = suffix.lower() in (".xlsx", ".xls")

                with st.status("Processing tender document...", expanded=True) as status:
                    st.write("📖 Reading document structure...")
                    t0 = _time.time()
                    if not is_excel:
                        st.write("🧭 Routing to BOQ-likely sections (structure-first)...")
                    st.write("🔎 Extracting entities (material, quantity, unit, standard)...")
                    st.write("📚 Validating against GeM catalog...")
                    result, error_msg = extract_boq_with_timeout(pipeline, file_path)
                    elapsed = _time.time() - t0
                    if error_msg:
                        status.update(label="Extraction failed", state="error", expanded=True)
                    else:
                        n_items = len(result.boq_items) if result else 0
                        status.update(
                            label=f"Done — {n_items} item(s) extracted in {elapsed:.1f}s",
                            state="complete",
                            expanded=False,
                        )
                # Persist in session cache (elapsed time included for the dashboard).
                cache[file_hash] = (result, error_msg, elapsed)

            if error_msg:
                st.error(f"❌ Could not read this file. {error_msg}")
                return

            # P5_01: document-type banner for non-BOQ docs.
            render_document_type_banner(result)

            if not result or not result.boq_items:
                # The banner already told the user; just return so we
                # don't render an empty BOQ table.
                if _classify_document_type(result):
                    return
                st.warning("No BOQ items found. The file may not contain standard tender data.")
                return

            st.success(f"✅ Extraction complete — {len(result.boq_items)} items found")

            # Real, computed metrics dashboard — no fabricated numbers.
            n_items = len(result.boq_items)
            confidences = [float(i.confidence or 0) for i in result.boq_items]
            avg_conf = (sum(confidences) / len(confidences) * 100) if confidences else 0.0
            flag_counts = _result_flag_summary(result)
            total_flags = sum(flag_counts.values())

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("BOQ Items Extracted", n_items)
            m2.metric("Avg. Confidence", f"{avg_conf:.0f}%")
            m3.metric("Flags Raised", total_flags, delta=None if total_flags == 0 else "review recommended", delta_color="off")
            m4.metric("Extraction Time", f"{elapsed:.1f}s")

            st.divider()

            render_confidence_guide()

            st.divider()

            st.markdown("#### 📊 Bill of Quantities")

            df = build_boq_dataframe(result)
            render_boq_table(df)

            render_warnings(result)

            st.divider()

            # P5_01: Flag review panel — the centerpiece of "R1 visible".
            render_flag_review_panel(result)

            st.divider()

            st.markdown("#### 💾 Download Results")
            render_downloads(result, project_name)

    with tab2:
        st.markdown("""
        ### How to Use

        1. **Upload** a construction tender PDF or Excel (Request for Quotation)
        2. **Wait** for extraction to complete (Excel: instant, PDF: 30-60 seconds)
        3. **Review** the extracted items in the table — click cells to edit
        4. **Check the Flag Review panel** — every uncertainty the pipeline
           raised is grouped by severity (error / review / info) with the
           original code + message + row reference.
        5. **Download** in your preferred format (Excel/JSON/CSV)

        ### Flag Review

        Every typed flag from the pipeline is surfaced:

        - 🔴 **Error** — capture failed or suspect; the row is included
          but should be checked.
        - 🟠 **Review** — needs a human sanity check (low confidence,
          unknown unit, non-catalog material, fallback used, etc.).
        - ⚪ **Info** — observation, not blocking.

        The same data is on the **Review** sheet of the downloaded Excel
        file.  The **Provenance** sheet shows source file, sha256, and
        pipeline commit.

        ### Document-type banner

        Non-BOQ documents (compliance checklists, specifications, etc.)
        are detected and a banner explains "0 line items, classified as
        COMPLIANCE_CHECKLIST" instead of a bare empty table.

        ### Quality Labels (confidence)

        - 🟢 **Good** — High confidence extraction (≥80%)
        - 🟡 **Check** — Medium confidence, review recommended (50-79%)
        - 🔴 **Verify** — Low confidence, please check manually (<50%)

        ### Need Help?

        Contact your system administrator with the document name and description of the problem.
        """)

    # P5_01 §3: footer with model version + pipeline commit.
    render_footer()


if __name__ == "__main__":
    main()
