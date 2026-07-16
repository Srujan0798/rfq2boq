"""PDF rendering helper for Streamlit split-view."""

from pathlib import Path

import streamlit as st


@st.cache_data(ttl=3600, show_spinner=False)
def render_pdf_pages(pdf_path: str, dpi: int = 100, max_pages: int = 5) -> list[bytes]:
    """Render PDF pages as PNG images.

    Args:
        pdf_path: Path to PDF file
        dpi: Resolution for rendering (default 100 for speed)
        max_pages: Maximum pages to render (default 5, large PDFs capped)

    Returns:
        List of PNG image bytes, one per page
    """
    try:
        from pdf2image import convert_from_path
    except ImportError:
        return []

    try:
        pages = convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=1,
            last_page=max_pages,
            fmt="png",
        )
        return [page.tobytes() for page in pages]
    except Exception:
        return []


def count_pdf_pages(pdf_path: str) -> int:
    """Get total page count of a PDF."""
    try:
        from pdf2image import convert_from_path

        pages = convert_from_path(pdf_path, dpi=50, first_page=1, last_page=1, fmt="png")
        return max(1, len(pages))
    except Exception:
        return 1


def render_pdf_viewer(pdf_path: Path, *, max_pages: int = 5) -> None:
    """Render PDF pages in Streamlit with page captions."""
    pages = render_pdf_pages(str(pdf_path), dpi=100, max_pages=max_pages)

    if not pages:
        st.warning("Could not render PDF. Install poppler: `brew install poppler`")
        return

    total = len(pages)
    for i, page_bytes in enumerate(pages, start=1):
        st.image(page_bytes, caption=f"Page {i} of {total}", use_container_width=True)
        st.divider()
