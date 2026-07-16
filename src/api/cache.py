"""Redis caching layer for RFQ2BOQ."""

import json
from collections.abc import Callable
from datetime import timedelta
from functools import wraps
from typing import Any

import redis


class RFQCache:
    """Redis-based caching for RFQ2BOQ extraction results."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.ttl = timedelta(hours=1)

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        try:
            value = self.client.get(key)
            if value and isinstance(value, str):
                return json.loads(value)
            return None
        except redis.RedisError:
            return None

    def set(self, key: str, value: Any, ttl: timedelta | None = None) -> bool:
        """Set value in cache."""
        try:
            ttl = ttl or self.ttl
            self.client.setex(key, int(ttl.total_seconds()), json.dumps(value))
            return True
        except redis.RedisError:
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            self.client.delete(key)
            return True
        except redis.RedisError:
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        try:
            keys = self.client.keys(pattern)
            if keys and isinstance(keys, list):
                result = self.client.delete(*keys)
                if isinstance(result, int):
                    return result
                return 0
            return 0
        except redis.RedisError:
            return 0

    def cached(self, key_prefix: str, ttl: timedelta | None = None):
        """Decorator for caching function results."""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = f"{key_prefix}:{hash(str(args))}:{hash(str(kwargs))}"
                cached = self.get(cache_key)
                if cached is not None:
                    return cached
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result

            return wrapper

        return decorator


_cache: RFQCache | None = None


def get_cache() -> RFQCache:
    """Get global cache instance."""
    global _cache
    if _cache is None:
        _cache = RFQCache()
    return _cache


def invalidate_extraction_cache(extraction_id: str) -> bool:
    """Invalidate cache for a specific extraction."""
    return get_cache().delete(f"extraction:{extraction_id}")
