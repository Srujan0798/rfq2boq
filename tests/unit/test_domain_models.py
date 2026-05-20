from src.nlp.project_classifier import (
    KEYWORDS,
    PROJECT_TYPES,
    ProjectTypeClassifier,
    classify_project_type,
)
from src.nlp.router import DomainRouter


def test_classify_building():
    text = "RCC building construction for residential complex with foundation and flooring work"
    result = classify_project_type(text)
    assert result == "building"

def test_classify_road():
    text = "Construction of 2-lane highway with WBM base and DBM surface course"
    result = classify_project_type(text)
    assert result == "road"

def test_classify_electrical():
    text = "Electrical wiring for commercial building with conduit and cable management"
    result = classify_project_type(text)
    assert result == "electrical"

def test_classify_unknown():
    text = "Random text with no construction keywords"
    result = classify_project_type(text)
    assert result == "unknown"

def test_classifier_with_confidence():
    clf = ProjectTypeClassifier()
    text = "RCC building construction"
    result = clf.classify(text)
    assert result["project_type"] == "building"
    assert "confidence" in result
    assert "all_scores" in result

def test_classifier_history():
    clf = ProjectTypeClassifier()
    clf.classify("building construction")
    clf.classify("road construction")
    assert len(clf.history) == 2

def test_domain_router_init():
    router = DomainRouter()
    assert router is not None

def test_domain_router_list_domains():
    router = DomainRouter()
    assert isinstance(router.list_available_domains(), list)

def test_domain_router_register():
    router = DomainRouter()
    router.register_domain_model("building", "/models/ner-building")
    assert router.get_model_for_type("building") == "/models/ner-building"

def test_domain_router_route():
    router = DomainRouter()
    result = router.route("RCC building construction")
    assert "project_type" in result
    assert "routing" in result

def test_building_ner_init():
    from src.nlp.domain_ner import BuildingNER
    ner = BuildingNER()
    assert ner is not None

def test_road_ner_init():
    from src.nlp.domain_ner import RoadNER
    ner = RoadNER()
    assert ner is not None

def test_electrical_ner_init():
    from src.nlp.domain_ner import ElectricalNER
    ner = ElectricalNER()
    assert ner is not None

def test_project_types_coverage():
    for ptype in PROJECT_TYPES:
        if ptype != "unknown":
            assert ptype in KEYWORDS
            assert len(KEYWORDS[ptype]) > 0
