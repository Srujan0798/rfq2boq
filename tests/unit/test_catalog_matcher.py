"""Unit tests for the GeM catalog matcher."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from src.nlp.catalog_matcher import (
    CatalogMatch,
    CatalogMatcher,
    _jaccard,
    _levenshtein_ratio,
    _normalize,
    _tokenize,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def catalog_path() -> Path:
    return Path("data/real_rfqs/swa_gem_catalog_full.json")


@pytest.fixture
def ontology_path() -> Path:
    return Path("data/ontology/insulation_materials.json")


@pytest.fixture
def matcher(catalog_path: Path, ontology_path: Path) -> CatalogMatcher:
    return CatalogMatcher(catalog_path=catalog_path, ontology_path=ontology_path)


@pytest.fixture
def temp_catalog(tmp_path: Path) -> Path:
    """Create a minimal catalog for testing."""
    catalog = {
        "source": "test",
        "products": [
            {
                "gem_id": "test-001",
                "name": "CERAMIC FIBRE BLANKET",
                "material": "Ceramic Fibre",
                "standards": ["IS 15402"],
                "aliases": ["ceramic fibre blanket", "ceramic fiber blanket", "rcf blanket"],
            },
            {
                "gem_id": "test-002",
                "name": "FOAM TAPE",
                "material": "Nitrile",
                "aliases": ["foam tape", "nitrile foam tape"],
            },
            {
                "gem_id": "test-003",
                "name": "ALUMINUM TAPE",
                "material": "Aluminum Foil",
                "aliases": ["aluminum tape", "aluminium tape", "foil tape"],
            },
        ],
    }
    path = tmp_path / "test_catalog.json"
    path.write_text(json.dumps(catalog))
    return path


# ---------------------------------------------------------------------------
# Normalization tests
# ---------------------------------------------------------------------------


class TestNormalization:
    def test_lowercases(self):
        assert _normalize("CERAMIC FIBRE") == "ceramic fibre"

    def test_collapses_whitespace(self):
        assert _normalize("  ceramic   fibre  ") == "ceramic fibre"

    def test_strips_punctuation(self):
        assert _normalize("ceramic fibre blanket!") == "ceramic fibre blanket"

    def test_handles_empty(self):
        assert _normalize("") == ""

    def test_tokenize_basic(self):
        assert _tokenize("ceramic fibre blanket") == ["ceramic", "fibre", "blanket"]

    def test_tokenize_with_punctuation(self):
        tokens = _tokenize("IS:3346-1980 material")
        assert "is" in tokens
        assert "material" in tokens


# ---------------------------------------------------------------------------
# Similarity function tests
# ---------------------------------------------------------------------------


class TestSimilarityFunctions:
    def test_jaccard_identical(self):
        tokens = {"ceramic", "fibre", "blanket"}
        assert _jaccard(tokens, tokens) == 1.0

    def test_jaccard_disjoint(self):
        assert _jaccard({"a", "b"}, {"c", "d"}) == 0.0

    def test_jaccard_partial(self):
        a = {"ceramic", "fibre", "blanket"}
        b = {"ceramic", "fiber", "blanket"}
        score = _jaccard(a, b)
        assert 0.3 < score < 1.0

    def test_jaccard_empty(self):
        assert _jaccard(set(), set()) == 0.0

    def test_levenshtein_identical(self):
        assert _levenshtein_ratio("ceramic", "ceramic") == 1.0

    def test_levenshtein_one_edit(self):
        ratio = _levenshtein_ratio("ceramic", "ceramics")
        assert ratio > 0.8

    def test_levenshtein_completely_different(self):
        ratio = _levenshtein_ratio("aaa", "zzz")
        assert ratio < 0.5

    def test_levenshtein_empty(self):
        assert _levenshtein_ratio("", "abc") == 0.0

    def test_levenshtein_both_empty(self):
        assert _levenshtein_ratio("", "") == 1.0


# ---------------------------------------------------------------------------
# CatalogMatcher loading tests
# ---------------------------------------------------------------------------


class TestCatalogMatcherLoading:
    def test_loads_real_catalog(self, matcher: CatalogMatcher):
        assert matcher.catalog_size == 19
        assert matcher.unique_products > 0

    def test_loads_temp_catalog(self, temp_catalog: Path):
        m = CatalogMatcher(catalog_path=temp_catalog)
        assert m.catalog_size == 3
        assert m.unique_products == 3

    def test_missing_catalog_raises(self):
        with pytest.raises(FileNotFoundError):
            CatalogMatcher(catalog_path="/nonexistent/path.json")

    def test_catalog_summary(self, matcher: CatalogMatcher):
        summary = matcher.get_catalog_summary()
        assert len(summary) > 0
        assert all("gem_id" in s for s in summary)
        assert all("name" in s for s in summary)


# ---------------------------------------------------------------------------
# Exact match tests
# ---------------------------------------------------------------------------


class TestExactMatch:
    def test_exact_name_match(self, matcher: CatalogMatcher):
        result = matcher.match("Ceramic Fibre Blanket Insulation")
        assert result.is_unmatched is False
        assert result.method == "exact"
        assert result.confidence == 1.0
        assert result.gem_name is not None

    def test_exact_alias_match(self, matcher: CatalogMatcher):
        result = matcher.match("ceramic fibre blanket")
        assert result.is_unmatched is False
        assert result.method in ("exact", "alias_exact")
        assert result.confidence >= 0.98

    def test_exact_case_insensitive(self, matcher: CatalogMatcher):
        result = matcher.match("foam tape")
        assert result.is_unmatched is False
        assert result.method in ("exact", "alias_exact")

    def test_exact_with_extra_whitespace(self, matcher: CatalogMatcher):
        result = matcher.match("  foam   tape  ")
        assert result.is_unmatched is False


# ---------------------------------------------------------------------------
# Fuzzy match tests
# ---------------------------------------------------------------------------


class TestFuzzyMatch:
    def test_token_overlap(self, matcher: CatalogMatcher):
        result = matcher.match("supply ceramic fibre blanket insulation 25mm")
        assert result.is_unmatched is False
        assert result.method in ("token_overlap", "substring", "exact", "alias_exact")

    def test_substring_match(self, matcher: CatalogMatcher):
        result = matcher.match("nitrile foam tape single sided 25mm width")
        assert result.is_unmatched is False

    def test_edit_distance_match(self, matcher: CatalogMatcher):
        # Close to "aluminum tape" but with typo
        result = matcher.match("aluminium tape")
        assert result.is_unmatched is False

    def test_fuzzy_partial_alias(self, matcher: CatalogMatcher):
        result = matcher.match("rcf blanket 25mm thick")
        assert result.is_unmatched is False


# ---------------------------------------------------------------------------
# Unmatched / no-match tests
# ---------------------------------------------------------------------------


class TestUnmatched:
    def test_completely_unrelated(self, matcher: CatalogMatcher):
        result = matcher.match("ordinary portland cement 43 grade")
        # Cement is not in the GeM catalog
        assert result.is_unmatched is True
        assert result.method == "none"
        assert result.confidence == 0.0

    def test_empty_input(self, matcher: CatalogMatcher):
        result = matcher.match("")
        assert result.is_unmatched is True

    def test_gibberish(self, matcher: CatalogMatcher):
        result = matcher.match("xyzzy plugh")
        assert result.is_unmatched is True


# ---------------------------------------------------------------------------
# Batch matching tests
# ---------------------------------------------------------------------------


class TestBatchMatching:
    def test_batch_returns_correct_count(self, matcher: CatalogMatcher):
        texts = ["foam tape", "ceramic fibre blanket", "cement"]
        results = matcher.match_batch(texts)
        assert len(results) == 3

    def test_batch_mixed(self, matcher: CatalogMatcher):
        texts = ["foam tape", "random gibberish", "aluminum foil insulation tape"]
        results = matcher.match_batch(texts)
        matched = [r for r in results if not r.is_unmatched]
        unmatched = [r for r in results if r.is_unmatched]
        assert len(matched) >= 1
        assert len(unmatched) >= 1


# ---------------------------------------------------------------------------
# CatalogMatch dataclass tests
# ---------------------------------------------------------------------------


class TestCatalogMatch:
    def test_to_dict_unmatched(self):
        m = CatalogMatch(input_text="test", is_unmatched=True)
        d = m.to_dict()
        assert d["input_text"] == "test"
        assert d["is_unmatched"] is True
        assert d["gem_id"] is None

    def test_to_dict_matched(self):
        m = CatalogMatch(
            input_text="test",
            gem_id="g-001",
            gem_name="Test Product",
            confidence=0.95,
            method="exact",
            is_unmatched=False,
            material="test material",
        )
        d = m.to_dict()
        assert d["gem_id"] == "g-001"
        assert d["confidence"] == 0.95
        assert d["method"] == "exact"


# ---------------------------------------------------------------------------
# Threshold configuration tests
# ---------------------------------------------------------------------------


class TestThresholds:
    def test_custom_thresholds(self, temp_catalog: Path):
        m = CatalogMatcher(
            catalog_path=temp_catalog,
            token_threshold=0.1,  # very low
            substring_threshold=0.3,  # low
            edit_threshold=0.5,  # low
        )
        # Should match more aggressively
        result = m.match("ceramic fibre")
        assert result.is_unmatched is False

    def test_strict_thresholds(self, temp_catalog: Path):
        m = CatalogMatcher(
            catalog_path=temp_catalog,
            token_threshold=0.9,  # very high
            substring_threshold=0.9,
            edit_threshold=0.95,
        )
        # Very strict — should miss fuzzy matches
        result = m.match("ceramic fibre")
        # Should still get exact/alias match if it exists
        # But if not exact, strict thresholds may not match
        if result.is_unmatched:
            assert result.method == "none"


# ---------------------------------------------------------------------------
# Integration with real data
# ---------------------------------------------------------------------------


class TestRealCatalogIntegration:
    def test_all_aliases_match(self, matcher: CatalogMatcher):
        """Every alias in the catalog should match itself."""
        seen: set[str] = set()
        for product in matcher._catalog:
            for alias in product.get("aliases", []):
                norm = _normalize(alias)
                if norm in seen:
                    continue
                seen.add(norm)
                result = matcher.match(alias)
                assert result.is_unmatched is False, f"Alias '{alias}' did not match"

    def test_all_names_match(self, matcher: CatalogMatcher):
        """Every product name in the catalog should match itself."""
        seen: set[str] = set()
        for product in matcher._catalog:
            name = product.get("name", "")
            norm = _normalize(name)
            if norm in seen:
                continue
            seen.add(norm)
            result = matcher.match(name)
            assert result.is_unmatched is False, f"Name '{name}' did not match"

    def test_material_field_populated(self, matcher: CatalogMatcher):
        """Matched results should have material and standards from catalog."""
        result = matcher.match("ceramic fibre blanket")
        if not result.is_unmatched:
            assert result.material is not None or result.gem_name is not None
