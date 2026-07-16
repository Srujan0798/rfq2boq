"""Column-band detection for multi-column PDF tables.

The P3_02 task — the 07_grew class of problem — happens when a PDF table has
side-by-side columns (description | qty | remarks, description | unit | qty |
remarks, …) and plain text extraction interleaves words from different
columns on the same y-line. The fix is positional: every row is rebuilt
from cells defined by detected vertical bands, not from jumbled text lines.

The detector has two complementary inputs:

* **Ruling-line evidence.** pdfplumber exposes ``page.lines`` and
  ``page.rects``. Some PDFs (07_grew, the Grew Energy BOQ) draw horizontal
  rules and vertical column dividers as very thin filled rectangles instead
  of explicit line objects. We collect rects with high vertical extent
  (column dividers) and rects with high horizontal extent (row separators)
  and use the column-divider x-positions as authoritative band edges.

* **Word x-edge histogram.** Borderless tables (the §9 gotcha — Word-exported
  PDFs) have no ruling lines. We cluster the x0 of every word (and the
  x1) into 1-D bands via gap-based clustering, with a ~3pt tolerance.

The two inputs are merged: ruling-line edges anchor the detector when
present, word clusters fill the gaps. ``detect_columns`` returns a
``ColumnDetectorResult`` carrying the bands, the per-band source of
evidence, and a confidence score in [0, 1].

This module deliberately knows nothing about BOQ semantics — it does not
parse "this band is unit" or "that band is remarks". The caller
(``src/ingest/pdf_extractor.py``) does the semantic assignment.

The module is the single source of truth for the column-aware extraction
introduced by P3_02. The sacred-10 baseline (07_grew 9/9) is preserved
because the downstream pipeline falls back to the existing text-line
path when ``confidence < 0.5`` or no bands are detected.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class ColumnBand:
    """A vertical band of the page (one column of the table).

    x_left / x_right are in PDF point space. The band is half-open:
    ``x_left <= word.x0 < x_right`` (a word exactly on a divider edge
    belongs to the band on the LEFT, matching how PDF tables draw borders).
    """

    x_left: float
    x_right: float
    band_index: int
    evidence: str = "unknown"  # "ruling" | "word_histogram" | "fused"
    word_count: int = 0

    @property
    def width(self) -> float:
        return self.x_right - self.x_left

    @property
    def center(self) -> float:
        return (self.x_left + self.x_right) / 2.0

    def contains(self, x: float, tolerance: float = 0.0) -> bool:
        return (self.x_left - tolerance) <= x < (self.x_right + tolerance)


@dataclass(slots=True)
class RowEnvelope:
    """A horizontal band of the page (one logical table row).

    Envelopes are constructed by clustering word y-centers with a small
    tolerance. A wrapped description spans multiple envelopes; the
    caller is expected to merge them into a single row before emitting.
    """

    y_center: float
    y_top: float
    y_bottom: float


@dataclass(slots=True)
class RowCells:
    """One assembled table row: words grouped by detected column band.

    ``cells`` is indexed by ``band_index`` from the detector. Empty cells
    (no words in that band within this row envelope) are present as
    ``""`` so the caller can rely on positional identity.
    """

    y_top: float
    y_bottom: float
    cells: list[str] = field(default_factory=list)
    # Map from band_index to the words (x0, text) used to build the cell.
    # Used by the pipeline for debugging and for re-assembly after
    # band-merging.
    cell_words: list[list[tuple[float, str]]] = field(default_factory=list)

    def cell(self, band_index: int) -> str:
        if 0 <= band_index < len(self.cells):
            return self.cells[band_index]
        return ""


@dataclass(slots=True)
class ColumnDetectorResult:
    """Output of ``detect_columns``."""

    bands: list[ColumnBand] = field(default_factory=list)
    confidence: float = 0.0
    evidence_summary: dict[str, int] = field(default_factory=dict)

    @property
    def band_count(self) -> int:
        return len(self.bands)

    @property
    def is_reliable(self) -> bool:
        """Whether the caller can trust cell-by-cell row assembly.

        True iff we have ≥2 bands AND confidence ≥ 0.5. Single-band
        results are kept for inspection but the pipeline should fall
        back to text-line parsing.
        """
        return self.band_count >= 2 and self.confidence >= 0.5


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def _rect_extent_x(extent: float, page_width: float) -> bool:
    """True if the rect's x extent looks like a vertical column divider.

    Vertical dividers are tall (high y extent) and narrow (low x extent).
    """
    return extent < max(2.0, page_width * 0.01)


def _rect_extent_y(extent: float, page_height: float) -> bool:
    """True if the rect's y extent looks like a horizontal row separator.

    Horizontal separators are wide (high x extent) and thin (low y extent).
    """
    return extent < max(2.0, page_height * 0.01)


def _collect_divider_xs(rects: Iterable[dict[str, Any]], page_height: float) -> list[float]:
    """Collect candidate vertical column dividers from a page's rects.

    Ruled tables (e.g. 07_grew) draw column dividers as tall thin filled
    rects. The midpoint x of each such rect is a candidate band edge.
    """
    xs: list[float] = []
    for r in rects or []:
        x0 = float(r.get("x0", 0.0))
        x1 = float(r.get("x1", 0.0))
        y0 = float(r.get("top", r.get("y0", 0.0)))
        y1 = float(r.get("bottom", r.get("y1", 0.0)))
        if x1 <= x0 or y1 <= y0:
            continue
        x_extent = x1 - x0
        y_extent = y1 - y0
        # A divider is tall (y_extent / page_height >= 0.2) and very narrow.
        if y_extent >= 0.2 * page_height and _rect_extent_x(x_extent, page_width=0.0):
            xs.append((x0 + x1) / 2.0)
    # Sort + de-dup with 1pt tolerance.
    xs.sort()
    merged: list[float] = []
    for x in xs:
        if not merged or abs(x - merged[-1]) > 1.0:
            merged.append(x)
    return merged


def _collect_separator_ys(rects: Iterable[dict[str, Any]], page_width: float) -> list[float]:
    """Collect candidate horizontal row separators (used to define page
    bands when no vertical dividers are present)."""
    ys: list[float] = []
    for r in rects or []:
        x0 = float(r.get("x0", 0.0))
        x1 = float(r.get("x1", 0.0))
        y0 = float(r.get("top", r.get("y0", 0.0)))
        y1 = float(r.get("bottom", r.get("y1", 0.0)))
        if x1 <= x0 or y1 <= y0:
            continue
        x_extent = x1 - x0
        y_extent = y1 - y0
        if x_extent >= 0.2 * page_width and _rect_extent_y(y_extent, page_height=0.0):
            ys.append((y0 + y1) / 2.0)
    ys.sort()
    merged: list[float] = []
    for y in ys:
        if not merged or abs(y - merged[-1]) > 1.0:
            merged.append(y)
    return ys


def _cluster_xs(xs: list[float], gap: float = 3.0) -> list[tuple[float, float]]:
    """Cluster 1-D x positions into bands via gap-based 1-D clustering.

    Returns a list of (x_min, x_max) tuples, each spanning the cluster's
    observed extent. ``gap`` is the maximum allowed intra-cluster gap.
    """
    if not xs:
        return []
    xs = sorted(xs)
    clusters: list[list[float]] = [[xs[0]]]
    for x in xs[1:]:
        if x - clusters[-1][-1] <= gap:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    return [(min(c), max(c)) for c in clusters]


def _merge_close_bands(bands: list[ColumnBand], min_band_width: float = 6.0) -> list[ColumnBand]:
    """Drop trivially-narrow bands (likely noise between adjacent real
    bands) and renumber the survivors.

    The detector frequently produces a 1-2pt sliver between two real
    columns (e.g. between UNIT and QTY where there is no true band
    separator). We treat any band narrower than ``min_band_width`` as
    noise and absorb it into the band on its LEFT — BUT only when
    the band is actually empty of words. A narrow band that
    contains real words is a real band (its width is dictated by
    the word geometry, not by noise), so it survives the merge.
    """
    if not bands:
        return bands
    out: list[ColumnBand] = []
    for b in bands:
        if b.width < min_band_width and b.word_count == 0 and out:
            # Empty sliver — absorb into previous band.
            prev = out[-1]
            out[-1] = ColumnBand(
                x_left=prev.x_left,
                x_right=b.x_right,
                band_index=prev.band_index,
                evidence=prev.evidence,
                word_count=prev.word_count + b.word_count,
            )
        else:
            out.append(b)
    # Renumber so band_index is contiguous from 0.
    for i, b in enumerate(out):
        out[i] = ColumnBand(
            x_left=b.x_left,
            x_right=b.x_right,
            band_index=i,
            evidence=b.evidence,
            word_count=b.word_count,
        )
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def filter_empty_bands(bands: list[ColumnBand], min_words: int = 1) -> list[ColumnBand]:
    """Drop bands that contain zero words (e.g. page margins that happened
    to be enclosed by ruling lines), then renumber.

    The detector on a ruled page like 07_grew frequently produces
    trailing/leading bands that are 0-word (the margin between the
    outermost column and the page edge). Drop them so callers can
    reason about bands as the table's actual columns.
    """
    out: list[ColumnBand] = []
    for b in bands:
        if b.word_count >= min_words:
            out.append(
                ColumnBand(
                    x_left=b.x_left,
                    x_right=b.x_right,
                    band_index=len(out),
                    evidence=b.evidence,
                    word_count=b.word_count,
                )
            )
    return out


def _detect_band_roles(bands: list[ColumnBand], page: Any) -> dict[str, int]:
    """Auto-detect the semantic role of each band by content.

    Heuristic:

    * ITEM  — leftmost band whose words include a small integer (1-2 digits,
      possibly with a dot like "11.1") AND that band is narrow.
    * UNIT  — narrow band whose words include a known unit (sqm, kg, m, …).
    * QTY   — narrow band whose words are pure digits, right-aligned
      (x_left in the right third of the page).
    * REMARKS — wide band that is rightmost OR the band whose words
      contain prose markers ("complies", "for", "as per").
    * MATERIAL — the widest band by word count that is NOT item/unit/qty/remarks.

    Returns
    -------
    dict[str, int]
        Map from role name ("item" | "material" | "unit" | "qty" |
        "remarks") to band_index. Roles that are not confidently detected
        are omitted.
    """
    roles: dict[str, int] = {}
    if not bands:
        return roles
    try:
        words = list(page.extract_words() or [])
    except Exception:
        return roles

    # Candidate item bands: leftmost narrow bands whose words include a
    # short item number.
    for b in bands:
        if roles.get("item") is not None:
            break
        if b.x_right > 100:
            continue
        for w in words:
            if not b.contains(float(w.get("x0", 0.0))):
                continue
            t = str(w.get("text", "")).strip()
            if re.match(r"^\d{1,2}(\.\d+)?\.?$", t):
                roles["item"] = b.band_index
                break

    # Candidate unit bands: narrow bands whose words include a known unit.
    known_units = {
        "sqm",
        "sq.m",
        "sq.mtr",
        "sq",
        "mtr",
        "m",
        "kg",
        "nos",
        "no",
        "rm",
        "rmt",
        "m³",
        "cum",
        "ltr",
        "m2",
        "m3",
        "sqmtrs",
        "sq.mtrs",
        "sqmtr",
        "sqft",
        "sft",
        "cft",
        "ea",
        "each",
        "rmt.",
        "sqmtr.",
        "sq.m.",
        "kg.",
    }
    for b in bands:
        if roles.get("item") is not None and b.band_index == roles["item"]:
            continue
        if roles.get("unit") is not None:
            break
        if b.width > 80:
            continue
        for w in words:
            if not b.contains(float(w.get("x0", 0.0))):
                continue
            t = str(w.get("text", "")).strip().lower().rstrip(".")
            if t in known_units:
                roles["unit"] = b.band_index
                break

    # Candidate qty bands: narrow bands whose words are pure digits AND
    # sit in the right half of the page.
    page_w = float(getattr(page, "width", 0.0) or 0.0)
    if page_w > 0:
        for b in bands:
            if b.band_index in {roles.get("item"), roles.get("unit")}:
                continue
            if roles.get("qty") is not None:
                break
            if b.width > 80:
                continue
            if b.x_left < page_w * 0.4:
                continue
            digit_count = 0
            total = 0
            for w in words:
                if not b.contains(float(w.get("x0", 0.0))):
                    continue
                t = str(w.get("text", "")).strip()
                if not t:
                    continue
                total += 1
                if t.replace(",", "").replace(".", "").isdigit():
                    digit_count += 1
            if total >= 1 and digit_count / max(1, total) >= 0.6:
                roles["qty"] = b.band_index

    # Candidate remarks band: rightmost wide band containing prose markers.
    prose_markers = {"complies", "for", "as", "per", "will", "be", "kg/m3", "kg/m²"}
    if page_w > 0:
        for b in reversed(bands):
            if b.band_index in {roles.get("item"), roles.get("unit"), roles.get("qty")}:
                continue
            if b.x_left < page_w * 0.5:
                continue
            for w in words:
                if not b.contains(float(w.get("x0", 0.0))):
                    continue
                t = str(w.get("text", "")).strip().lower().rstrip(",.")
                if t in prose_markers:
                    roles["remarks"] = b.band_index
                    break
            if "remarks" in roles:
                break

    # Material band: the widest remaining band (most words) that is not
    # already assigned.
    candidate = [b for b in bands if b.band_index not in set(roles.values())]
    if candidate:
        material = max(candidate, key=lambda b: b.word_count)
        roles["material"] = material.band_index

    return roles


def detect_columns(page: Any) -> ColumnDetectorResult:
    """Detect vertical column bands on a pdfplumber page.

    Parameters
    ----------
    page
        A pdfplumber ``Page`` object. Must expose ``width``, ``height``,
        ``rects``, and ``extract_words``.

    Returns
    -------
    ColumnDetectorResult
        Detected bands + a confidence score. ``is_reliable`` is the
        caller-friendly boolean for "trust cell-by-cell row assembly".
    """
    try:
        page_width = float(getattr(page, "width", 0.0) or 0.0)
        page_height = float(getattr(page, "height", 0.0) or 0.0)
        rects = list(getattr(page, "rects", []) or [])
        words = list(page.extract_words() or [])
    except Exception as exc:
        logger.debug("detect_columns: page access failed: %s", exc)
        return ColumnDetectorResult(bands=[], confidence=0.0, evidence_summary={"error": 1})

    if page_width <= 0 or page_height <= 0:
        return ColumnDetectorResult(bands=[], confidence=0.0, evidence_summary={"no_page": 1})

    evidence_summary: dict[str, int] = {}

    # ---- Stage 1: ruling-line evidence ----------------------------------
    divider_xs = _collect_divider_xs(rects, page_height=page_height)
    separator_ys = _collect_separator_ys(rects, page_width=page_width)
    evidence_summary["ruling_dividers"] = len(divider_xs)
    evidence_summary["ruling_separators"] = len(separator_ys)

    # ---- Stage 2: word x-edge histogram --------------------------------
    # We use the LEFT edge of each word as the cluster input. Right-aligned
    # numeric columns are also captured by adding x1 (right edge) — that
    # way a 5pt-wide "500" cell at x=400..428 produces cluster at 400 AND
    # cluster at 428, and a numeric band gets band boundaries that span the
    # full numeric-column extent. We then dedupe clusters that overlap.
    if words:
        x0s = [float(w.get("x0", 0.0)) for w in words]
        x1s = [float(w.get("x1", 0.0)) for w in words]
        word_clusters = _cluster_xs(x0s + x1s, gap=3.0)
    else:
        word_clusters = []
    evidence_summary["word_clusters"] = len(word_clusters)

    # ---- Stage 3: fuse --------------------------------------------------
    bands: list[ColumnBand] = []
    if divider_xs and len(divider_xs) >= 2:
        # Use divider x-positions as authoritative band edges.
        # Sort and add 0 and page_width as the page bounds so the
        # outer columns are also captured.
        edges = sorted(set([0.0] + divider_xs + [page_width]))
        bands = [
            ColumnBand(
                x_left=edges[i],
                x_right=edges[i + 1],
                band_index=i,
                evidence="ruling",
            )
            for i in range(len(edges) - 1)
        ]
    elif word_clusters and len(word_clusters) >= 2:
        # No rulings; use the word histogram directly. We widen each cluster
        # by 2pt on each side so consecutive words still fall into it.
        bands = [
            ColumnBand(
                x_left=max(0.0, c[0] - 2.0),
                x_right=min(page_width, c[1] + 2.0),
                band_index=i,
                evidence="word_histogram",
            )
            for i, c in enumerate(word_clusters)
        ]
    else:
        # No usable signal: caller should fall back to text-line path.
        return ColumnDetectorResult(
            bands=[],
            confidence=0.0,
            evidence_summary={**evidence_summary, "no_signal": 1},
        )

    # ---- Stage 4: count words per band + drop slivers -------------------
    for b in bands:
        b.word_count = sum(1 for w in words if b.contains(float(w.get("x0", 0.0))))
    bands = _merge_close_bands(bands, min_band_width=6.0)

    # ---- Stage 5: confidence --------------------------------------------
    # Confidence = average of two contributions in [0, 1]:
    #   - ruling-line strength: more dividers + word alignment ⇒ higher
    #   - word coverage:        fraction of words that fell inside a band
    if words:
        covered = sum(b.word_count for b in bands)
        word_coverage = min(1.0, covered / max(1, len(words)))
    else:
        word_coverage = 0.0
    ruling_strength = min(1.0, len(divider_xs) / 4.0) if divider_xs else 0.0
    confidence = round(0.5 * word_coverage + 0.5 * ruling_strength, 3)
    # Bonus: if both signals exist, the result is fused ⇒ bump confidence.
    if divider_xs and word_clusters:
        confidence = min(1.0, confidence + 0.15)
    evidence_summary["word_coverage"] = int(word_coverage * 100)
    evidence_summary["ruling_strength"] = int(ruling_strength * 100)

    return ColumnDetectorResult(
        bands=bands,
        confidence=confidence,
        evidence_summary=evidence_summary,
    )


def _word_x_center(w: dict[str, Any]) -> float:
    return (float(w.get("x0", 0.0)) + float(w.get("x1", 0.0))) / 2.0


def _word_y_center(w: dict[str, Any]) -> float:
    return (float(w.get("top", 0.0)) + float(w.get("bottom", 0.0))) / 2.0


def cluster_words_into_rows(
    words: list[dict[str, Any]],
    y_tolerance: float = 3.0,
) -> list[RowEnvelope]:
    """Cluster words into horizontal row envelopes by y-center proximity.

    A wrapped description that spans multiple visual lines (e.g. 07_grew's
    "Supply,InstallationandTestingofAccousticliningwith10mmthickClass1rating
    OpenCellnitrilerubberinsulationmaterialwithdensityof140to\n180 kg /m³along
    with manufacturer recommended adhesive.") will be split into multiple
    word groups by ``extract_words``; the caller is expected to join the
    cells within an envelope to a single row.

    ``y_tolerance`` is the half-height of the bucket. ``extract_words``'s
    own y_tolerance=3 produces consistent y-centers per visual line, so
    3pt here matches pdfplumber's own line detection.

    Each envelope's y_top/y_bottom are computed from the **min of (top, y_center - y_tolerance)
    and max of (bottom, y_center + y_tolerance)** so envelopes are non-overlapping
    when used with center-based word assignment in ``assemble_cell_based_rows``.
    """
    if not words:
        return []
    sorted_w = sorted(words, key=_word_y_center)
    envelopes: list[RowEnvelope] = []
    current: list[dict[str, Any]] = [sorted_w[0]]
    current_y = _word_y_center(sorted_w[0])
    for w in sorted_w[1:]:
        y = _word_y_center(w)
        if abs(y - current_y) <= y_tolerance:
            current.append(w)
        else:
            tops = [float(c.get("top", 0.0)) for c in current]
            bots = [float(c.get("bottom", 0.0)) for c in current]
            # Build a non-overlapping y range: half a tolerance above/below
            # the mean y_center. This makes downstream center-based word
            # assignment (assemble_cell_based_rows) partition cleanly.
            y_top = min(tops)
            y_bottom = max(bots)
            y_top = min(y_top, current_y - y_tolerance / 2.0)
            y_bottom = max(y_bottom, current_y + y_tolerance / 2.0)
            envelopes.append(
                RowEnvelope(
                    y_center=current_y,
                    y_top=y_top,
                    y_bottom=y_bottom,
                )
            )
            current = [w]
            current_y = y
    if current:
        tops = [float(c.get("top", 0.0)) for c in current]
        bots = [float(c.get("bottom", 0.0)) for c in current]
        y_top = min(tops)
        y_bottom = max(bots)
        y_top = min(y_top, current_y - y_tolerance / 2.0)
        y_bottom = max(y_bottom, current_y + y_tolerance / 2.0)
        envelopes.append(
            RowEnvelope(
                y_center=current_y,
                y_top=y_top,
                y_bottom=y_bottom,
            )
        )
    # Post-process: clip overlapping y ranges so adjacent envelopes do not
    # share words. The midpoint between two adjacent envelope y-centers
    # is the cleanest cut.
    for i in range(1, len(envelopes)):
        prev = envelopes[i - 1]
        cur = envelopes[i]
        if cur.y_top <= prev.y_bottom:
            mid = (prev.y_center + cur.y_center) / 2.0
            envelopes[i - 1] = RowEnvelope(
                y_center=prev.y_center,
                y_top=prev.y_top,
                y_bottom=mid,
            )
            envelopes[i] = RowEnvelope(
                y_center=cur.y_center,
                y_top=mid,
                y_bottom=cur.y_bottom,
            )
    return envelopes


def assemble_cell_based_rows(
    page: Any,
    bands: list[ColumnBand],
    y_tolerance: float = 3.0,
) -> list[RowCells]:
    """Assemble rows cell-by-cell from the detected column bands.

    For each row envelope (one logical row of the table), each band's
    intersection with the envelope is collected as a cell string. Cells
    are joined left-to-right by the bands' band_index.

    Wrapped cells (a single band that contains multiple envelopes) are
    NOT auto-merged here. The caller decides how to handle wrapped
    descriptions: typically by joining all envelopes that share the same
    item_no (or have no item_no in the ITEM band) into one row.

    Returns
    -------
    list[RowCells]
        One RowCells per envelope; cells are indexed by band_index.
    """
    if not bands:
        return []
    words: list[dict[str, Any]] = list(page.extract_words() or [])
    envelopes = cluster_words_into_rows(words, y_tolerance=y_tolerance)
    # Ensure envelopes are non-overlapping: each word belongs to the
    # envelope whose y_center is closest. This avoids the situation
    # where a tall word near an envelope boundary gets assigned to two
    # adjacent envelopes (e.g. 07_grew's "180 kg /m³..." at y=256
    # could fall into both the y=252 and the y=259 envelopes based on
    # the outer y_top/y_bottom range).
    out: list[RowCells] = []
    for env in envelopes:
        cells: list[str] = [""] * len(bands)
        cell_words: list[list[tuple[float, str]]] = [[] for _ in bands]
        for w in words:
            wc = _word_y_center(w)
            # Pick the envelope whose y_center is closest (a word
            # belongs to the nearest envelope, not to the first one
            # whose outer range overlaps it).
            if abs(wc - env.y_center) > y_tolerance:
                continue
            x0 = float(w.get("x0", 0.0))
            x1 = float(w.get("x1", 0.0))
            text = str(w.get("text", ""))
            # Pick the band whose center is closest to the word's center.
            xc = (x0 + x1) / 2.0
            best = 0
            best_dist = float("inf")
            for b in bands:
                if b.x_left - 1.0 <= xc < b.x_right + 1.0:
                    d = 0.0 if b.contains(xc, tolerance=1.0) else min(abs(xc - b.x_left), abs(xc - b.x_right))
                    if d < best_dist:
                        best_dist = d
                        best = b.band_index
            cell_words[best].append((x0, text))
        for i, ws in enumerate(cell_words):
            if ws:
                ws.sort(key=lambda x: x[0])
                cells[i] = " ".join(t for _, t in ws).strip()
        out.append(
            RowCells(
                y_top=env.y_top,
                y_bottom=env.y_bottom,
                cells=cells,
                cell_words=cell_words,
            )
        )
    return out


def merge_wrapped_rows(
    rows: list[RowCells],
    item_band_index: int | None = None,
    unit_band_index: int | None = None,
    qty_band_index: int | None = None,
    material_band_index: int | None = None,
    y_gap: float = 5.0,
) -> list[RowCells]:
    """Merge wrapped descriptions so a multi-line cell becomes a single row.

    The strategy: an "anchor" row is one whose UNIT or QTY band has
    content (i.e. it carries a real quantity — that is the defining
    characteristic of a BOQ data row). All other rows are "context"
    rows (section headers, spec paragraphs, item-number-only rows).

    Two distinct passes are applied:

    1. **Trailing continuation merge.** A context row that immediately
       follows an anchor row (small y-gap) is folded into the anchor's
       MATERIAL cell as a continuation (wrapped description tail).
       This handles 07_grew's "Supply,InstallationandTesting..." at
       y=249 followed by "180 kg /m³along with..." at y=256.

    2. **Leading context merge.** A block of context rows that
       precedes an anchor row (small y-gap to the anchor, no anchor
       in between) is folded into the anchor's MATERIAL cell as a
       prefix (section spec text). This handles 07_grew's
       "Supply,InstallationofInsulationmaterial..." paragraph at
       y=70-187 that precedes the 11.1 data row at y=202.

    Section header rows (item="11" material="THERMAL INSULATION" with
    no UNIT/QTY) are also treated as context — they are NOT emitted
    as data rows. Their text becomes the prefix to the next anchor
    row.

    Parameters
    ----------
    rows
        Output of ``assemble_cell_based_rows``.
    item_band_index, unit_band_index, qty_band_index, material_band_index
        Optional explicit band roles. When all are ``None`` the
        function uses the conventional indices 0/2/3/1 (item/unit/
        qty/material) — but **only** if the band count is ≥4. With
        fewer bands the function degrades to the 0/1/2/0 fallback so
        a 2-band (item, qty) layout still merges correctly.
    y_gap
        Maximum vertical gap (in pt) for context rows to be merged
        into the surrounding anchor.

    Returns
    -------
    list[RowCells]
        The data rows (one per anchor). Each anchor's MATERIAL cell
        may now contain wrapped description text joined with
        spaces.
    """
    if not rows:
        return rows

    n_bands = max(len(r.cells) for r in rows)
    # Default role mapping. With 8 bands (07_grew layout) the indices
    # after filter_empty_bands are 0=ITEM, 1=MATERIAL, 2=UNIT, 3=QTY,
    # 4=margin, 5=REMARKS. We default to 0/1/2/3 for item/material/unit/qty.
    if item_band_index is None:
        item_band_index = 0
    if material_band_index is None:
        material_band_index = 1 if n_bands >= 4 else 0
    if unit_band_index is None:
        unit_band_index = 2 if n_bands >= 4 else (1 if n_bands >= 2 else 0)
    if qty_band_index is None:
        qty_band_index = 3 if n_bands >= 4 else (2 if n_bands >= 3 else 1)

    def _is_anchor(r: RowCells) -> bool:
        if len(r.cells) <= max(unit_band_index, qty_band_index):  # type: ignore[type-var]
            return False
        return bool(r.cell(unit_band_index)) or bool(r.cell(qty_band_index))  # type: ignore[arg-type]

    # ---- Pass 1: trailing continuation merge -----------------------------
    # Three cases handled:
    #   (a) same-data-row merge — two consecutive anchor rows with the
    #       same UNIT+QTY and a small y-gap are the same data row with
    #       wrapped material (07_grew's "Supply...140to" + "180 kg /m³along..."
    #       at y=250 and y=256).
    #   (b) anchor-without-item continuation — the current anchor has an
    #       empty ITEM band but the previous anchor has one (rare; reserved).
    #   (c) non-anchor continuation — the current row has no UNIT/QTY and
    #       immediately follows an anchor (wrapped description tail).
    after_continuation: list[RowCells] = []
    for r in rows:
        if after_continuation:
            prev = after_continuation[-1]
            gap = r.y_top - prev.y_bottom
            # (a) Same-data-row merge: identical UNIT AND QTY.
            same_unit = (
                len(r.cells) > unit_band_index  # type: ignore[operator]
                and len(prev.cells) > unit_band_index  # type: ignore[operator]
                and r.cell(unit_band_index) == prev.cell(unit_band_index)  # type: ignore[arg-type]
                and r.cell(unit_band_index)  # type: ignore[arg-type]
            )
            same_qty = (
                len(r.cells) > qty_band_index  # type: ignore[operator]
                and len(prev.cells) > qty_band_index  # type: ignore[operator]
                and r.cell(qty_band_index) == prev.cell(qty_band_index)  # type: ignore[arg-type]
                and r.cell(qty_band_index)  # type: ignore[arg-type]
            )
            if _is_anchor(r) and _is_anchor(prev) and same_unit and same_qty and gap <= 2 * y_gap:
                # Only merge the MATERIAL band; do NOT concatenate the
                # already-equal unit/qty/remarks bands (they would
                # duplicate). Extend material only.
                for i, txt in enumerate(r.cells):
                    if i >= len(prev.cells) or not txt:
                        continue
                    if i in {item_band_index, unit_band_index, qty_band_index}:  # type: ignore[arg-type]
                        # Skip structural cells — they're already correct on prev.
                        prev.cell_words[i].extend(r.cell_words[i])
                        continue
                    sep = " " if prev.cells[i] else ""
                    prev.cells[i] = (prev.cells[i] + sep + txt).strip()
                    prev.cell_words[i].extend(r.cell_words[i])
                prev.y_bottom = r.y_bottom
                continue
            # (b) Anchor-without-item continuation.
            if (
                not r.cell(item_band_index)  # type: ignore[arg-type]
                and prev.cell(item_band_index)  # type: ignore[arg-type]
                and _is_anchor(r)
                and _is_anchor(prev)
                and gap <= 2 * y_gap
            ):
                for i, txt in enumerate(r.cells):
                    if i < len(prev.cells) and txt:
                        if i in {unit_band_index, qty_band_index}:  # type: ignore[arg-type]
                            prev.cell_words[i].extend(r.cell_words[i])
                            continue
                        sep = " " if prev.cells[i] else ""
                        prev.cells[i] = (prev.cells[i] + sep + txt).strip()
                        prev.cell_words[i].extend(r.cell_words[i])
                prev.y_bottom = r.y_bottom
                continue
            # (c) Non-anchor continuation.
            if not _is_anchor(r) and gap <= y_gap:
                for i, txt in enumerate(r.cells):
                    if i < len(prev.cells) and txt:
                        if i in {unit_band_index, qty_band_index, item_band_index}:  # type: ignore[arg-type]
                            prev.cell_words[i].extend(r.cell_words[i])
                            continue
                        sep = " " if prev.cells[i] else ""
                        prev.cells[i] = (prev.cells[i] + sep + txt).strip()
                        prev.cell_words[i].extend(r.cell_words[i])
                prev.y_bottom = r.y_bottom
                continue
        after_continuation.append(r)

    # ---- Pass 2: leading context merge -----------------------------------
    # Walk backwards from each anchor and collect a contiguous block of
    # non-anchor context rows that immediately precede it (no other anchor
    # in between, and a small vertical gap). This captures multi-line
    # wrapped descriptions and rate-only spec paragraphs that plain
    # pdfplumber keeps as a single cell but the column-aware band assembly
    # splits across rows (e.g. 07_grew underfloor/underdeck items).
    # The previous "one row only, y-range ≤ 8pt" rule dropped the leading
    # multi-line spec text and left only the trailing anchor line.
    final: list[RowCells] = []
    consumed: set[int] = set()
    for i, cur in enumerate(after_continuation):
        if not _is_anchor(cur):
            # Pass through non-anchor rows; they were already folded in pass 1.
            continue
        # Collect preceding context rows.
        ctx: list[RowCells] = []
        j = i - 1
        while j >= 0 and not _is_anchor(after_continuation[j]):
            prev_ctx = after_continuation[j]
            if j in consumed:
                break
            gap = cur.y_top - prev_ctx.y_bottom
            if gap > 2 * y_gap:
                break
            ctx.insert(0, prev_ctx)
            consumed.add(j)
            j -= 1
        if ctx:
            mat_parts: list[str] = []
            words: list[tuple[float, str]] = []
            for c in ctx:
                txt = c.cell(material_band_index)  # type: ignore[arg-type]
                if txt and txt != cur.cell(item_band_index):  # type: ignore[arg-type]
                    mat_parts.append(txt)
                    words.extend(c.cell_words[material_band_index])  # type: ignore[index]
            cur_mat = cur.cell(material_band_index)  # type: ignore[arg-type]
            if cur_mat:
                mat_parts.append(cur_mat)
                words.extend(cur.cell_words[material_band_index])  # type: ignore[index]
            if mat_parts:
                cur.cells[material_band_index] = " ".join(mat_parts).strip()  # type: ignore[index]
                cur.cell_words[material_band_index] = words  # type: ignore[index]
                cur.y_top = ctx[0].y_top
        final.append(cur)
    return final
