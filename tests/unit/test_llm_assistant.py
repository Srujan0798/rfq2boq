"""Tests for LLM Assistant integration."""

import os

os.environ["LLM_CLIENT_SKIP_SETUP"] = "1"

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestLLMClient:
    def test_init(self):
        from src.llm.client import LLMClient

        client = LLMClient()
        assert client is not None

    def test_get_cache_key(self):
        from src.llm.client import LLMClient

        client = LLMClient()
        key1 = client._get_cache_key("test prompt", "claude")
        key2 = client._get_cache_key("test prompt", "claude")
        key3 = client._get_cache_key("different prompt", "claude")
        assert key1 == key2
        assert key1 != key3
        assert key1.startswith("llm:")

    @patch("src.llm.client.RedisCache")
    @pytest.mark.asyncio
    async def test_cache_hit(self, mock_cache_cls):
        mock_cache = MagicMock()
        mock_cache.get.return_value = {"text": "cached response", "model": "claude", "usage": {}}
        mock_cache_cls.return_value = mock_cache

        from src.llm.client import LLMClient

        client = LLMClient()
        response = await client.query("test prompt", "claude")
        assert response.cached is True
        assert response.text == "cached response"


class TestAmbiguityResolver:
    def test_init(self):
        from src.llm.client import AmbiguityResolver

        resolver = AmbiguityResolver()
        assert resolver is not None
        assert resolver.agreement_count == 0
        assert resolver.total_resolutions == 0

    def test_agreement_rate_no_resolutions(self):
        from src.llm.client import AmbiguityResolver

        resolver = AmbiguityResolver()
        assert resolver.get_agreement_rate() == 0.0

    def test_build_resolve_prompt(self):
        from src.llm.client import AmbiguityResolver

        resolver = AmbiguityResolver()
        prompt = resolver._build_resolve_prompt(
            "Supply 500 kg cement",
            "cement",
            "material context",
        )
        assert "cement" in prompt
        assert "MATERIAL" in prompt
        assert len(prompt) > 100

    @pytest.mark.asyncio
    async def test_resolve_high_confidence_unchanged(self):
        from src.llm.client import AmbiguityResolver

        resolver = AmbiguityResolver()
        result = await resolver.resolve(
            sentence="Supply cement",
            entity="cement",
            context="material context",
            current_type="MATERIAL",
            confidence=0.8,
        )
        assert result is None or result == "MATERIAL"

    @pytest.mark.asyncio
    async def test_resolve_low_confidence_calls_llm(self):
        from src.llm.client import AmbiguityResolver

        resolver = AmbiguityResolver()
        resolver.llm.query = AsyncMock(return_value=MagicMock(text="MATERIAL", model="claude", usage={}, cached=False))

        result = await resolver.resolve(
            sentence="Supply cement",
            entity="cement",
            context="material context",
            current_type="MATERIAL",
            confidence=0.3,
        )
        assert result in ["MATERIAL", "QUANTITY", "LOCATION", "ACTION", "GRADE", "STANDARD"]


class TestSummaryGenerator:
    def test_init(self):
        from src.llm.client import SummaryGenerator

        gen = SummaryGenerator()
        assert gen is not None

    @pytest.mark.asyncio
    async def test_generate_summary_empty_items(self):
        from src.llm.client import SummaryGenerator

        gen = SummaryGenerator()
        result = await gen.generate_summary([], "test.pdf")
        assert "No items" in result

    @pytest.mark.asyncio
    async def test_generate_summary_calls_llm(self):
        from src.llm.client import SummaryGenerator

        gen = SummaryGenerator()
        gen.llm.query = AsyncMock(
            return_value=MagicMock(text="Executive summary of BOQ.", model="claude", usage={}, cached=False)
        )

        items = [
            {"material": "cement", "quantity": 500, "unit": "kg", "confidence": 0.9},
            {"material": "steel", "quantity": 100, "unit": "kg", "confidence": 0.8},
        ]
        result = await gen.generate_summary(items, "test.pdf")
        assert isinstance(result, str)
        assert len(result) > 0


class TestBOQQA:
    def test_init(self):
        from src.llm.client import BOQQA

        qa = BOQQA()
        assert qa is not None

    def test_build_query_prompt(self):
        from src.llm.client import BOQQA

        qa = BOQQA()
        prompt = qa._build_query_prompt(
            "What is the total cement quantity?",
            [{"material": "cement", "quantity": 500}],
        )
        assert "cement" in prompt
        assert "total" in prompt.lower()

    @pytest.mark.asyncio
    async def test_ask(self):
        from src.llm.client import BOQQA

        qa = BOQQA()
        qa.llm.query = AsyncMock(
            return_value=MagicMock(text="Total cement is 500 kg.", model="claude", usage={}, cached=False)
        )

        result = await qa.ask(
            "What is total cement?",
            [{"material": "cement", "quantity": 500}],
        )
        assert "question" in result
        assert "answer" in result
        assert result["cached"] is False

    def test_parse_nl_to_query_total_reinforcement(self):
        from src.llm.client import BOQQA

        qa = BOQQA()
        query = qa._parse_nl_to_query("What is the total reinforcement quantity?")
        assert query is not None
        assert query["type"] == "aggregate"

    def test_parse_nl_to_query_floor_concrete(self):
        from src.llm.client import BOQQA

        qa = BOQQA()
        query = qa._parse_nl_to_query("How much concrete on first floor?")
        assert query is not None

    def test_parse_nl_to_query_item_number(self):
        from src.llm.client import BOQQA

        qa = BOQQA()
        query = qa._parse_nl_to_query("Tell me about item 5")
        assert query is not None
        assert query["type"] == "item"
        assert query["item_no"] == 5

    def test_parse_nl_to_query_unknown(self):
        from src.llm.client import BOQQA

        qa = BOQQA()
        query = qa._parse_nl_to_query("Random question")
        assert query is None
