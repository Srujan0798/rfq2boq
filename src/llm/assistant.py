"""AI Assistant Integration for ambiguous entity resolution.

Provides LLM-assisted resolution when BERT confidence < 0.5:
- Claude/GPT second opinion for low-confidence entities
- Resolve ambiguous entities with domain knowledge
- Auto-generate human-readable summaries
- Q&A over extracted BOQ
- Caching to control costs
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CACHE_DIR = Path(".llm_cache")
CACHE_DIR.mkdir(exist_ok=True)


@dataclass
class Resolution:
    entity_text: str
    resolved_type: str
    confidence: float
    reasoning: str
    source: str = "llm"


@dataclass
class BOQSummary:
    total_items: int
    total_quantity: float
    materials_by_category: dict[str, list[str]]
    risk_items: list[dict[str, Any]]
    recommendations: list[str]


class LLMAssistant:
    def __init__(
        self,
        provider: str = "claude",
        cache_enabled: bool = True,
        temperature: float = 0.3,
    ):
        self.provider = provider
        self.cache_enabled = cache_enabled
        self.temperature = temperature
        self._cache: dict[str, Resolution] = {}

    def resolve_entity(self, entity_text: str, context: str, current_type: str) -> Resolution | None:
        cache_key = f"{entity_text}|{current_type}"
        if self.cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        try:
            if self.provider == "claude":
                result = self._query_claude(entity_text, context, current_type)
            elif self.provider == "openai":
                result = self._query_openai(entity_text, context, current_type)
            else:
                return None

            if result and self.cache_enabled:
                self._cache[cache_key] = result
            return result
        except Exception as e:
            logger.warning(f"LLM resolution failed: {e}")
            return None

    def _query_claude(self, entity_text: str, context: str, current_type: str) -> Resolution | None:
        try:
            import anthropic
        except ImportError:
            logger.warning("anthropic not installed")
            return None

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": f"""Given this entity from a construction RFQ: "{entity_text}"
Context: {context[:500]}
Current type: {current_type}

What is the correct entity type? Choose from: MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE

Return JSON: {{"type": "...", "confidence": 0.0-1.0, "reasoning": "..."}}
Only return valid JSON.""",
                }],
            )
            text = response.content[0].text.strip()
            data = json.loads(text)
            return Resolution(
                entity_text=entity_text,
                resolved_type=data.get("type", current_type),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                source="claude",
            )
        except Exception as e:
            logger.warning(f"Claude API error: {e}")
            return None

    def _query_openai(self, entity_text: str, context: str, current_type: str) -> Resolution | None:
        try:
            from openai import OpenAI
        except ImportError:
            logger.warning("openai not installed")
            return None

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None

        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=self.temperature,
                messages=[{
                    "role": "user",
                    "content": f"""Given this entity from a construction RFQ: "{entity_text}"
Context: {context[:500]}
Current type: {current_type}

What is the correct entity type? Choose from: MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE

Return JSON: {{"type": "...", "confidence": 0.0-1.0, "reasoning": "..."}}
Only return valid JSON.""",
                }],
            )
            text = response.choices[0].message.content.strip()
            data = json.loads(text)
            return Resolution(
                entity_text=entity_text,
                resolved_type=data.get("type", current_type),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                source="openai",
            )
        except Exception as e:
            logger.warning(f"OpenAI API error: {e}")
            return None

    def summarize_boq(self, boq_items: list[dict[str, Any]], risk_report: dict | None = None) -> BOQSummary:
        total_qty = sum(float(item.get("quantity", 0)) for item in boq_items)
        materials_by_cat: dict[str, list[str]] = {}
        for item in boq_items:
            mat = item.get("material", "")
            cat = self._categorize(mat)
            if cat not in materials_by_cat:
                materials_by_cat[cat] = []
            materials_by_cat[cat].append(mat)

        risk_items = []
        if risk_report and isinstance(risk_report, dict):
            for score in risk_report.get("item_scores", []):
                if score.get("total_risk_score", 0) > 0.6:
                    risk_items.append({
                        "item_no": score.get("item_no"),
                        "material": score.get("material"),
                        "risk_score": score.get("total_risk_score"),
                        "flags": [f.flag_type for f in score.get("flags", [])],
                    })

        recommendations = []
        if len(boq_items) > 100:
            recommendations.append("Consider splitting into multiple BOQ documents")
        if risk_report and risk_report.get("aggregate_risk_score", 0) > 0.6:
            recommendations.append("Review high-risk items before proceeding")
        if not any(cat in materials_by_cat for cat in ["structure", "electrical", "plumbing"]):
            recommendations.append("Coverage incomplete - missing major work categories")

        return BOQSummary(
            total_items=len(boq_items),
            total_quantity=total_qty,
            materials_by_category=materials_by_cat,
            risk_items=risk_items,
            recommendations=recommendations,
        )

    def answer_question(self, question: str, boq_items: list[dict[str, Any]]) -> str:
        total_steel = sum(
            float(item.get("quantity", 0))
            for item in boq_items
            if "steel" in item.get("material", "").lower() or "tmt" in item.get("material", "").lower()
        )
        total_cement = sum(
            float(item.get("quantity", 0))
            for item in boq_items
            if "cement" in item.get("material", "").lower()
        )

        q_lower = question.lower()
        if "steel" in q_lower:
            return f"Total steel quantity: {total_steel:.2f} units"
        elif "cement" in q_lower:
            return f"Total cement quantity: {total_cement:.2f} units"
        elif "total" in q_lower and "item" in q_lower:
            return f"Total BOQ items: {len(boq_items)}"
        else:
            return f"BOQ contains {len(boq_items)} items with {total_steel:.2f} total steel and {total_cement:.2f} total cement"

    def _categorize(self, material: str) -> str:
        mat = material.lower()
        if any(t in mat for t in ["concrete", "cement", "steel", "brick", "block", "sand", "aggregate"]):
            return "structural"
        elif any(t in mat for t in ["paint", "tile", "flooring", "putty", "plaster", "wood", "plywood"]):
            return "finishing"
        elif any(t in mat for t in ["pipe", "pvc", "cpvc", "upvc", "gi", "plumb"]):
            return "plumbing"
        elif any(t in mat for t in ["cable", "conduit", "wire", "switch", "socket", "electrical"]):
            return "electrical"
        elif any(t in mat for t in ["duct", "ac", "air", "ventil", "hvac", "chiller"]):
            return "hvac"
        return "general"

    def resolve_low_confidence_entities(
        self,
        entities: list[dict[str, Any]],
        threshold: float = 0.5,
    ) -> list[Resolution]:
        resolved = []
        for entity in entities:
            conf = entity.get("confidence", 0.0)
            if conf < threshold:
                resolution = self.resolve_entity(
                    entity.get("text", ""),
                    entity.get("context", ""),
                    entity.get("type", "MATERIAL"),
                )
                if resolution:
                    resolved.append(resolution)
        return resolved
