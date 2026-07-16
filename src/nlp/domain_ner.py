"""Domain-specific NER for specialized construction types."""


class BuildingNER:
    """NER specialized for building construction."""

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path

    def extract(self, text: str) -> list[dict]:
        """Extract entities for building construction."""
        from src.nlp.pipeline import NLPPipeline

        pipeline = NLPPipeline(model_dir=self.model_path)
        result = pipeline.process(text)
        return result.entities


class RoadNER:
    """NER specialized for road/highway construction."""

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path

    def extract(self, text: str) -> list[dict]:
        """Extract entities for road construction."""
        from src.nlp.pipeline import NLPPipeline

        pipeline = NLPPipeline(model_dir=self.model_path)
        result = pipeline.process(text)

        entities = []
        for ent in result.entities:
            if ent.get("type") in ["MATERIAL", "QUANTITY", "UNIT", "DIMENSION", "GRADE", "STANDARD"]:
                entities.append(ent)

        return entities


class ElectricalNER:
    """NER specialized for electrical construction."""

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path

    def extract(self, text: str) -> list[dict]:
        """Extract entities for electrical construction."""
        from src.nlp.pipeline import NLPPipeline

        pipeline = NLPPipeline(model_dir=self.model_path)
        result = pipeline.process(text)

        entities = []
        for ent in result.entities:
            if ent.get("type") in ["MATERIAL", "QUANTITY", "UNIT", "DIMENSION", "GRADE", "STANDARD", "ACTION"]:
                entities.append(ent)

        return entities
