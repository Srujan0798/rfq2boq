"""GeM extraction validator (R2).

Validates that MATERIAL strings extracted from a GeM tender document all
belong to the authoritative GeM catalog. Non-catalog materials are FLAGGED
(never dropped — R1) so reviewers can decide.

GeM-document detection (required before flagging) uses the ≥2-signals rule
defined in the SWA requirements: a document is treated as a GeM tender only
when BOTH of the following hold:

  1. A filename / manifest signal: the filename (or ``source_batch`` from the
     corpus manifest) contains a GeM marker (``gem`` / ``GeM-Bidding``).
  2. A document-header text signal: the first few pages of extracted text
     contain a GeM bid header such as ``GeM Bid`` or the ``GEM/`` portal marker.

A single signal alone does NOT trigger flagging — this prevents false
positives on non-GeM docs that merely mention "GeM" in boilerplate.

The validator is pure: it takes ``doc_is_gem`` and a list of material strings
and returns ``list[GemFlag]``. The caller (pipeline) is responsible for
computing ``doc_is_gem`` via :func:`detect_gem_document`.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from src.nlp.patterns.gem_catalog import is_gem_material


@dataclass(frozen=True)
class GemFlag:
    """One validation finding for a non-catalog material on a GeM document.

    The flagged material is NEVER dropped (R1) — the flag is advisory only.
    """

    material: str
    reason: str
    severity: str = "red"  # non-catalog material on a GeM doc -> red flag

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


_GEM_FILENAME_RE = re.compile(r"(gem[-_]?bid|gem-bidding|gem_bid|\bgem\b)", re.IGNORECASE)
_GEM_HEADER_RE = re.compile(r"(GeM\s*Bid|GEM/|Government\s+e[\s-]?Marketplace)", re.IGNORECASE)
# Inspect at most this many leading pages for the header signal.
_HEADER_SCAN_PAGES = 5


def detect_gem_document(filename: str | Path, header_text: str = "", manifest_batch: str = "") -> bool:
    """Return True iff ≥2 independent signals indicate a GeM tender.

    Signals:
      * filename / manifest marker (signal A)
      * document header text marker (signal B)

    Both A and B must be present to flag. A single signal alone is insufficient
    (prevents false positives on docs that merely mention "GeM" in boilerplate).
    """
    name = Path(filename).name if str(filename) else ""
    batch = (manifest_batch or "").lower()
    signal_a = bool(_GEM_FILENAME_RE.search(name)) or ("gem" in batch)
    # Only scan the leading portion of the header text (cheap + safe).
    head = (header_text or "")[: 200 * _HEADER_SCAN_PAGES]
    signal_b = bool(_GEM_HEADER_RE.search(head))
    return signal_a and signal_b


def validate_gem_extraction(doc_is_gem: bool, materials: list[str]) -> list[GemFlag]:
    """Validate a list of extracted material strings against the GeM catalog.

    - If ``doc_is_gem`` is False, no flags are produced (the catalog is only
      authoritative for GeM tenders — non-GeM docs may legitimately use any
      vocabulary).
    - If ``doc_is_gem`` is True, every material that does NOT exactly match
      (after normalization) a GeM catalog product is flagged red. The material
      is NEVER dropped (R1): the flag is advisory.

    Returns a list of :class:`GemFlag` (possibly empty). The order matches the
    input order; duplicate materials each produce their own flag (preserving
    row context for the reviewer).
    """
    if not doc_is_gem:
        return []
    flags: list[GemFlag] = []
    for material in materials:
        if not material or not material.strip():
            continue
        if not is_gem_material(material):
            flags.append(
                GemFlag(
                    material=material,
                    reason="non-catalog material on a GeM tender (R2 violation candidate)",
                    severity="red",
                )
            )
    return flags
