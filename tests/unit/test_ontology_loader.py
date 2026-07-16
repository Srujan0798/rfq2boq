"""Tests for ontology loader."""

import tempfile
from pathlib import Path

from src.ontology.loader import ConstructionOntology, OntologyLoader


class TestOntologyLoader:
    def test_initialization_default(self):
        loader = OntologyLoader()
        assert loader.ontology_dir is not None

    def test_initialization_custom_dir(self):
        loader = OntologyLoader(ontology_dir="/custom/path")
        assert str(loader.ontology_dir) == "/custom/path"

    def test_alias_is_construction_ontology(self):
        assert OntologyLoader is ConstructionOntology

    def test_lookup_material_from_real_ontology(self):
        onto = ConstructionOntology(ontology_dir="src/ontology")
        result = onto.lookup_material("cement")
        # May or may not find it depending on data, but should not crash
        assert result is None or isinstance(result, dict)

    def test_lookup_standard(self):
        onto = ConstructionOntology(ontology_dir="src/ontology")
        result = onto.lookup_standard("IS 456")
        assert result is None or isinstance(result, dict)

    def test_get_default_unit(self):
        onto = ConstructionOntology(ontology_dir="src/ontology")
        unit = onto.get_default_unit("nonexistent_material")
        assert unit == "nos"  # fallback

    def test_resolve_unit_symbol(self):
        onto = ConstructionOntology(ontology_dir="src/ontology")
        result = onto.resolve_unit_symbol("unknown_unit")
        assert result == "unknown_unit"  # returns as-is if not found

    def test_ontology_dir_pathlib(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = OntologyLoader(ontology_dir=tmpdir)
            assert loader.ontology_dir == Path(tmpdir)

    def test_load_from_nonexistent_dir(self):
        loader = OntologyLoader(ontology_dir="/nonexistent/path")
        # Should not crash, just have empty data
        assert loader.materials == {}
        assert loader.standards == {}

    def test_get_all_materials(self):
        onto = ConstructionOntology(ontology_dir="src/ontology")
        materials = onto.get_all_materials()
        assert isinstance(materials, list)

    def test_get_all_standards(self):
        onto = ConstructionOntology(ontology_dir="src/ontology")
        standards = onto.get_all_standards()
        assert isinstance(standards, list)

    def test_properties_return_dicts(self):
        onto = ConstructionOntology(ontology_dir="src/ontology")
        assert isinstance(onto.materials, dict)
        assert isinstance(onto.standards, dict)
        assert isinstance(onto.units, dict)
        assert isinstance(onto.locations, dict)

    def test_insulation_materials_property(self):
        onto = ConstructionOntology(ontology_dir="src/ontology")
        assert isinstance(onto.insulation_materials, dict)
        assert len(onto.insulation_materials) >= 30

    def test_insulation_standards_property(self):
        onto = ConstructionOntology(ontology_dir="src/ontology")
        assert isinstance(onto.insulation_standards, dict)
        assert len(onto.insulation_standards) >= 10

    def test_insulation_units_property(self):
        onto = ConstructionOntology(ontology_dir="src/ontology")
        assert isinstance(onto.insulation_units, dict)
        assert len(onto.insulation_units) >= 12

    def test_lookup_insulation_material(self):
        onto = ConstructionOntology(ontology_dir="src/ontology")
        result = onto.lookup_insulation_material("mineral wool")
        assert result is not None
        assert result["name"] == "mineral wool"
        assert result["category"] == "thermal"

    def test_lookup_insulation_standard(self):
        onto = ConstructionOntology(ontology_dir="src/ontology")
        result = onto.lookup_insulation_standard("IS 8183")
        assert result is not None
        assert result["code"] == "IS 8183"
        assert "applies_to" in result

    def test_get_all_insulation_materials(self):
        onto = ConstructionOntology(ontology_dir="src/ontology")
        materials = onto.get_all_insulation_materials()
        assert isinstance(materials, list)
        assert len(materials) >= 22
        assert all("name" in m for m in materials)

    def test_get_all_insulation_standards(self):
        onto = ConstructionOntology(ontology_dir="src/ontology")
        standards = onto.get_all_insulation_standards()
        assert isinstance(standards, list)
        assert len(standards) >= 10
        assert all("code" in s for s in standards)
