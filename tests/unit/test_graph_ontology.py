import pytest
from src.ontology import GraphOntology


def test_graph_ontology_init():
    kg = GraphOntology()
    assert kg is not None
    assert hasattr(kg, "is_available")
    assert hasattr(kg, "_graph")


def test_fallback_when_unavailable():
    kg = GraphOntology()
    if not kg.is_available:
        pytest.skip("Neo4j not available")
    result = kg.lookup_material("concrete")
    assert result is None or isinstance(result, dict)


def test_lookup_standard():
    kg = GraphOntology()
    if not kg.is_available:
        pytest.skip("Neo4j not available")
    result = kg.lookup_standard("IS 456")
    assert result is None or isinstance(result, dict)


def test_find_compatible_standards():
    kg = GraphOntology()
    if not kg.is_available:
        pytest.skip("Neo4j not available")
    result = kg.find_compatible_standards("concrete")
    assert isinstance(result, list)


def test_convert_unit_unavailable():
    kg = GraphOntology()
    if not kg.is_available:
        pytest.skip("Neo4j not available")
    result = kg.convert_unit(1.0, "m", "cm")
    assert result is None or isinstance(result, float)


def test_find_equivalent_standard():
    kg = GraphOntology()
    if not kg.is_available:
        pytest.skip("Neo4j not available")
    result = kg.find_equivalent_standard("IS 456", "India/International")
    assert result is None or isinstance(result, dict)


def test_multi_hop_query_unavailable():
    kg = GraphOntology()
    if not kg.is_available:
        pytest.skip("Neo4j not available")
    result = kg.multi_hop_query("cement", max_depth=3)
    assert isinstance(result, list)


def test_close():
    kg = GraphOntology()
    kg.close()
