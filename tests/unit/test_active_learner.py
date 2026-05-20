from src.labeling.active_learner import ActiveLearner


def test_entropy_score():
    al = ActiveLearner()
    preds = [{"confidence": 0.5}, {"confidence": 0.5}]
    score = al.score_uncertainty(preds, method="entropy")
    assert score > 0.6


def test_margin_score():
    al = ActiveLearner()
    preds = [{"confidence": 0.9}, {"confidence": 0.3}]
    score = al.score_uncertainty(preds, method="margin")
    assert abs(score - 0.6) < 0.01


def test_rank_documents():
    al = ActiveLearner()
    docs = {
        "doc1": [{"confidence": 0.5, "type": "MATERIAL"}],
        "doc2": [{"confidence": 0.99, "type": "MATERIAL"}],
        "doc3": [{"confidence": 0.1, "type": "MATERIAL"}],
    }
    ranked = al.rank_documents(docs)
    assert ranked[0][0] == "doc1"


def test_sample_for_review():
    al = ActiveLearner()
    docs = {
        "doc1": [{"confidence": 0.5}],
        "doc2": [{"confidence": 0.99}],
        "doc3": [{"confidence": 0.1}],
        "doc4": [{"confidence": 0.6}],
    }
    samples = al.sample_for_review(docs, n=2)
    assert len(samples) == 2
    assert "doc1" in samples
