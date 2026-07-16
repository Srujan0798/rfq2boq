"""LLM client with Claude API, OpenRouter, caching, and local fallback."""

import hashlib
import json
import os
from dataclasses import dataclass

try:
    from anthropic import Anthropic

    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from openai import AsyncOpenAI

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from src.cache.redis_cache import RedisCache
except ImportError:
    # Cache module is optional / archived in slim build
    RedisCache = None  # type: ignore[assignment, misc]

from config.settings import settings


@dataclass
class LLMResponse:
    """Response from LLM."""

    text: str
    model: str
    usage: dict
    cached: bool = False


class LLMClient:
    """Client for LLM inference with caching and fallback."""

    def __init__(self):
        self.anthropic = Anthropic() if HAS_ANTHROPIC else None
        self.openrouter = (
            AsyncOpenAI(
                api_key=settings.OPENROUTER_API_KEY,
                base_url=settings.OPENROUTER_BASE_URL,
            )
            if HAS_OPENAI and settings.OPENROUTER_API_KEY
            else None
        )
        self.cache = RedisCache() if RedisCache is not None else None
        self.local_fallback = None
        self._setup_local_fallback()

    def _setup_local_fallback(self):
        """Setup local Llama fallback if available."""
        if os.getenv("LLM_CLIENT_SKIP_SETUP"):
            return
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            model_name = os.getenv("LLAMA_MODEL", "meta-llama/Llama-2-7b-chat-hf")
            self.local_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.local_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto" if os.getenv("CUDA_VISIBLE_DEVICES") else "cpu",
            )
            self.local_fallback = "llama"
        except Exception:
            self.local_fallback = None

    def _get_cache_key(self, prompt: str, model: str) -> str:
        """Generate cache key for prompt."""
        content = json.dumps({"prompt": prompt, "model": model}, sort_keys=True)
        return f"llm:{hashlib.sha256(content.encode()).hexdigest()}"

    async def query(
        self,
        prompt: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """Query LLM with caching."""
        cache_key = self._get_cache_key(prompt, model)

        cached = self.cache.get(cache_key) if self.cache is not None else None
        if cached:
            return LLMResponse(
                text=cached["text"],
                model=model,
                usage=cached.get("usage", {}),
                cached=True,
            )

        try:
            if self.anthropic and model.startswith("claude"):
                response = await self._query_claude(prompt, model, max_tokens, temperature)
            elif self.openrouter and (
                model.startswith("openrouter/") or ":" in model or model in settings.OPENROUTER_MODEL
            ):
                response = await self._query_openrouter(prompt, model, max_tokens, temperature)
            elif self.local_fallback:
                response = await self._query_llama(prompt, max_tokens, temperature)
            else:
                raise RuntimeError("No LLM provider available")
        except Exception as e:
            if self.local_fallback and model.startswith("claude"):
                response = await self._query_llama(prompt, max_tokens, temperature)
            else:
                raise RuntimeError(f"LLM query failed: {e}") from e

        if self.cache is not None:
            self.cache.set(
                cache_key,
                {
                    "text": response.text,
                    "model": response.model,
                    "usage": response.usage,
                },
                ttl=3600,
            )

        return response

    async def _query_claude(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Query Claude API."""
        message = self.anthropic.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return LLMResponse(
            text=message.content[0].text,
            model=model,
            usage={"input_tokens": message.usage.input_tokens, "output_tokens": message.usage.output_tokens},
        )

    async def _query_openrouter(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Query OpenRouter API (OpenAI-compatible)."""
        # Use default model from settings if "openrouter/free" or similar router is specified
        actual_model = model
        if model == "openrouter/free" or model == "openrouter/auto":
            actual_model = settings.OPENROUTER_MODEL

        response = await self.openrouter.chat.completions.create(
            model=actual_model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return LLMResponse(
            text=response.choices[0].message.content or "",
            model=actual_model,
            usage={
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        )

    async def _query_llama(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Query local Llama model."""
        inputs = self.local_tokenizer(prompt, return_tensors="pt")
        outputs = self.local_model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
        )
        text = self.local_tokenizer.decode(outputs[0], skip_special_tokens=True)
        return LLMResponse(
            text=text,
            model=self.local_fallback,
            usage={},
            cached=False,
        )


class AmbiguityResolver:
    """Resolve entity ambiguities using LLM."""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()
        self.agreement_count = 0
        self.total_resolutions = 0

    def _build_resolve_prompt(self, sentence: str, entity: str, context: str) -> str:
        """Build prompt for ambiguity resolution."""
        return f"""Given the following construction RFQ sentence:

"{sentence}"

The entity "{entity}" appears in this context: "{context}"

Is this entity a MATERIAL, QUANTITY, LOCATION, ACTION, GRADE, or STANDARD?

Rules:
- MATERIAL: Physical construction materials like cement, steel, brick, concrete
- QUANTITY: Numbers, measurements, counts
- LOCATION: Places, floors, rooms, areas
- ACTION: Verbs like supply, install, lay, cast, erect
- GRADE: Quality levels like M25, Fe500, Class A
- STANDARD: Reference standards like IS code, ASTM

Respond with ONLY the category name in uppercase, nothing else."""

    async def resolve(
        self,
        sentence: str,
        entity: str,
        context: str,
        current_type: str,
        confidence: float,
    ) -> str | None:
        """Resolve entity type ambiguity when confidence is low."""
        if confidence >= 0.5:
            return current_type

        prompt = self._build_resolve_prompt(sentence, entity, context)

        try:
            response = await self.llm.query(prompt, temperature=0.1)
            resolved_type = response.text.strip().upper()

            valid_types = ["MATERIAL", "QUANTITY", "LOCATION", "ACTION", "GRADE", "STANDARD"]
            if resolved_type in valid_types:
                self.total_resolutions += 1
                if resolved_type == current_type:
                    self.agreement_count += 1
                return resolved_type
        except Exception:
            pass

        return current_type

    def get_agreement_rate(self) -> float:
        """Get LLM agreement rate with BERT."""
        if self.total_resolutions == 0:
            return 0.0
        return self.agreement_count / self.total_resolutions


class SummaryGenerator:
    """Generate human-readable BOQ summaries."""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()

    async def generate_summary(self, boq_items: list[dict], doc_name: str = "document") -> str:
        """Generate executive summary of BOQ."""
        if not boq_items:
            return "No items found in BOQ."

        total_items = len(boq_items)
        total_value = sum(float(item.get("quantity", 0)) for item in boq_items)
        high_confidence = sum(1 for item in boq_items if item.get("confidence", 0) >= 0.8)
        low_confidence = sum(1 for item in boq_items if item.get("confidence", 0) < 0.6)

        materials: dict[str, int] = {}
        for item in boq_items:
            mat = item.get("material", "Unknown")
            materials[mat] = materials.get(mat, 0) + 1

        top_materials = sorted(materials.items(), key=lambda x: x[1], reverse=True)[:5]

        prompt = f"""Generate a 2-3 paragraph executive summary for a Bill of Quantities (BOQ) from construction RFQ "{doc_name}".

Key Statistics:
- Total line items: {total_items}
- Total quantity: {total_value:.2f}
- High confidence items (≥80%): {high_confidence}
- Low confidence items (<60%): {high_confidence}

Top Materials:
{", ".join([f"{m} ({c} items)" for m, c in top_materials])}

Provide:
1. Overview of document scope
2. Key items and any anomalies detected
3. Quality assessment (confidence levels)

Keep it professional and concise. 2-3 paragraphs only."""

        try:
            response = await self.llm.query(prompt, max_tokens=512, temperature=0.3)
            return response.text
        except Exception:
            return f"BOQ Summary: {total_items} items, {high_confidence} high confidence, {low_confidence} need review."


class BOQQA:
    """Q&A over BOQ data."""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()

    def _build_query_prompt(self, question: str, boq_data: list[dict]) -> str:
        """Build prompt for Q&A over BOQ."""
        boq_json = json.dumps(boq_data[:100], indent=2)  # Limit to first 100 items

        return f"""Given the following BOQ data as JSON:

{boq_json}

Answer the question: "{question}"

If the question asks about totals, compute from the data.
If asking about specific items, cite item numbers.
If information is not available, say so.

Format your answer clearly and cite specific item numbers when relevant."""

    async def ask(self, question: str, boq_data: list[dict]) -> dict:
        """Answer question about BOQ."""
        prompt = self._build_query_prompt(question, boq_data)

        try:
            response = await self.llm.query(prompt, max_tokens=512, temperature=0.1)

            return {
                "question": question,
                "answer": response.text,
                "model": response.model,
                "cached": response.cached,
            }
        except Exception as e:
            return {
                "question": question,
                "answer": f"Error processing question: {e}",
                "model": None,
                "cached": False,
            }

    def _parse_nl_to_query(self, question: str) -> dict | None:
        """Parse natural language question to structured query."""
        question_lower = question.lower()

        if "total" in question_lower and "reinforcement" in question_lower:
            return {"type": "aggregate", "field": "quantity", "material": "reinforcement"}
        elif "floor" in question_lower and "concrete" in question_lower:
            return {"type": "filter", "material": "concrete", "group_by": "location"}
        elif "item" in question_lower:
            import re

            match = re.search(r"item\s*(\d+)", question_lower)
            if match:
                return {"type": "item", "item_no": int(match.group(1))}

        return None
