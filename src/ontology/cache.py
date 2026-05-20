"""LRU cache for ontology queries."""

from functools import lru_cache


class OntologyCache:
    @staticmethod
    @lru_cache(maxsize=1000)
    def cached_lookup_material(name: str) -> tuple | None:
        return None

    @staticmethod
    @lru_cache(maxsize=500)
    def cached_lookup_standard(code: str) -> tuple | None:
        return None

    @staticmethod
    @lru_cache(maxsize=500)
    def cached_convert_unit(from_unit: str, to_unit: str) -> float | None:
        return None

    @staticmethod
    def clear():
        OntologyCache.cached_lookup_material.cache_clear()
        OntologyCache.cached_lookup_standard.cache_clear()
        OntologyCache.cached_convert_unit.cache_clear()
