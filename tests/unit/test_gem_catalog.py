"""Tests for the GeM catalog integration (R2 — authoritative NER reference).

These tests verify the regenerated, JSON-backed catalog:
  * load + provenance block
  * exact match
  * normalized match (case / whitespace / OCR 0-O artifact)
  * negative match (non-catalog text)
  * validation flags (non-catalog material on a GeM doc -> red flag, never drop)
  * gazetteer wiring (no hard-coded product strings in the module)
"""

from __future__ import annotations

import json
from pathlib import Path

from src.nlp.patterns.gem_catalog import (
    DEFAULT_GEM_CATALOG,
    GeMCatalogGazetteer,
    get_gem_materials,
    get_gem_products_in_order,
    get_provenance,
    is_gem_material,
)
from src.rules.gem_validation import (
    GemFlag,
    detect_gem_document,
    validate_gem_extraction,
)

CATALOG_JSON = Path(__file__).resolve().parent.parent.parent / "data" / "ontology" / "gem_catalog.json"


class TestGeMCatalogLoad:
    def test_catalog_json_exists_with_provenance(self):
        """The ingested catalog JSON exists and carries a full provenance block."""
        assert CATALOG_JSON.exists(), f"Catalog JSON missing at {CATALOG_JSON}"
        doc = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
        assert "_provenance" in doc, "Missing _provenance block"
        prov = doc["_provenance"]
        for key in ("source_file", "source_sha256", "ingest_date_utc", "row_count"):
            assert key in prov, f"provenance missing {key}"
        assert prov["row_count"] == len(doc["products"]), "row_count mismatch"
        assert prov["source_sha256"], "empty sha256"
        assert prov["source_file"], "empty source_file"

    def test_get_gem_materials_loads_from_json(self):
        """get_gem_materials returns the catalog keyed by product name (no hard-coded lists)."""
        materials = get_gem_materials()
        assert isinstance(materials, dict)
        # 19 rows in the source XLSX, 13 unique product names.
        assert len(materials) >= 13
        # Every value carries the verbatim name + product_id.
        for name, product in materials.items():
            assert isinstance(name, str) and name
            assert hasattr(product, "name") and product.name == name
            assert hasattr(product, "product_id") and product.product_id

    def test_row_count_matches_source(self):
        """All 19 source rows are present (no dedup at the row level)."""
        rows = get_gem_products_in_order()
        assert len(rows) == 19, f"Expected 19 product rows, got {len(rows)}"
        prov = get_provenance()
        assert prov["row_count"] == 19


class TestExactAndNormalizedMatch:
    def test_exact_match_known_products(self):
        """Verbatim catalog names match."""
        assert is_gem_material("THERMO ACOUSTIC INSULATION") is True
        assert is_gem_material("Aluminum Tape") is True
        assert is_gem_material("Ceramic Fibre Blanket Insulation") is True
        assert is_gem_material("Preformed Fibrous Pipe Sections For Thermal Insulation-IS: 9842") is True

    def test_normalized_match_case_and_whitespace(self):
        """Case folding + whitespace collapse still match (OCR-artifact cleanup)."""
        assert is_gem_material("thermo acoustic insulation") is True
        assert is_gem_material("  THERMO   ACOUSTIC   INSULATION  ") is True
        # Trailing form-feed (OCR artifact) collapses to whitespace.
        assert is_gem_material("THERMO ACOUSTIC INSULATION\x0c") is True
        # Doubled spaces inside the name.
        assert is_gem_material("Foam  Tape") is True

    def test_normalized_match_ocr_zero_oh_swap(self):
        """A '0' inside an alphabetic token is treated as 'o' (common OCR artifact)."""
        assert is_gem_material("F0AM TAPE") is True  # '0' -> 'o'

    def test_negative_match(self):
        """Non-catalog text never matches (no fuzzy expansion)."""
        assert is_gem_material("Bogus Product") is False
        assert is_gem_material("Mineral Wool") is False  # not in the GeM catalog
        assert is_gem_material("") is False
        assert is_gem_material("   ") is False


class TestGazetteerWiring:
    def test_no_hardcoded_product_strings_in_module(self):
        """The module must not contain hard-coded product name literals."""
        module_path = Path("src/nlp/patterns/gem_catalog.py")
        text = module_path.read_text(encoding="utf-8")
        # A representative sample of strings that USED to be hard-coded and
        # must now come only from the JSON catalog.
        forbidden = [
            '"Mineral Wool"',
            '"Cement"',
            '"Ready Mix Concrete"',
            '"TMT Bars"',
            '"Ball Valve"',
        ]
        for lit in forbidden:
            assert lit not in text, f"hard-coded product string still present: {lit}"

    def test_default_catalog_proxy_loads_from_json(self):
        """DEFAULT_GEM_CATALOG (back-compat list) is populated from the JSON, not hard-coded."""
        names = list(DEFAULT_GEM_CATALOG)
        assert len(names) == 19
        assert "THERMO ACOUSTIC INSULATION" in names
        assert "Mineral Wool" not in names  # the old hard-coded default is gone

    def test_gazetteer_extract_finds_catalog_phrases(self):
        """GeMCatalogGazetteer extracts catalog materials from text (exact-after-norm)."""
        gazetteer = GeMCatalogGazetteer()
        text = "Supply THERMO ACOUSTIC INSULATION and Foam Tape for the project."
        entities = gazetteer.extract_materials(text)
        texts = {e["text"] for e in entities}
        assert "THERMO ACOUSTIC INSULATION" in texts
        assert "Foam Tape" in texts
        for e in entities:
            assert e["type"] == "MATERIAL"
            assert e["source"] == "swa_gem_catalog"

    def test_gazetteer_is_in_catalog(self):
        """is_in_catalog uses normalized exact match."""
        gazetteer = GeMCatalogGazetteer()
        assert gazetteer.is_in_catalog("THERMO ACOUSTIC INSULATION") is True
        assert gazetteer.is_in_catalog("Aluminum Tape") is True
        assert gazetteer.is_in_catalog("Non-existent Product") is False


class TestGemValidation:
    def test_detect_gem_document_requires_two_signals(self):
        """≥2 signals (filename + header) required; one alone is insufficient."""
        assert detect_gem_document("GeM-Bidding-9218026.pdf", header_text="GeM Bid 7439924") is True
        assert detect_gem_document("GeM-Bidding-9218026.pdf", header_text="random boilerplate") is False
        assert detect_gem_document("random.pdf", header_text="GeM Bid 7439924") is False
        assert detect_gem_document("random.pdf", header_text="random") is False

    def test_validate_flags_non_catalog_on_gem_doc(self):
        """Non-catalog material on a GeM doc -> red flag (never dropped)."""
        flags = validate_gem_extraction(
            doc_is_gem=True,
            materials=["THERMO ACOUSTIC INSULATION", "Bogus Material X", "Foam Tape", "Another Bogus"],
        )
        assert len(flags) == 2
        flagged_texts = {f.material for f in flags}
        assert flagged_texts == {"Bogus Material X", "Another Bogus"}
        for f in flags:
            assert isinstance(f, GemFlag)
            assert f.severity == "red"
            assert "non-catalog" in f.reason

    def test_validate_no_flags_for_non_gem_doc(self):
        """Non-GeM docs may legitimately use any vocabulary -> no flags."""
        flags = validate_gem_extraction(doc_is_gem=False, materials=["Bogus Material X", "Mineral Wool"])
        assert flags == []

    def test_validate_no_flags_when_all_match_catalog(self):
        """A GeM doc where every material is in the catalog -> no flags."""
        flags = validate_gem_extraction(
            doc_is_gem=True,
            materials=["THERMO ACOUSTIC INSULATION", "Foam Tape", "Aluminum Tape"],
        )
        assert flags == []
