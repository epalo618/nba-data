import time
from typing import Callable, TypeVar

T = TypeVar("T")


def make_cache(default_ttl: int = 3600) -> Callable:
    """Returns a `_cached(key, fn, ttl=None)` helper backed by its own private
    in-memory TTL store. Each caller gets an independent cache dict (via this
    closure) so different services never share or collide on cache entries,
    even if their cache keys happen to match."""
    _cache: dict = {}

    def _cached(key: str, fn: Callable[[], T], ttl: int | None = None) -> T:
        now = time.time()
        actual_ttl = default_ttl if ttl is None else ttl
        if key in _cache and now - _cache[key]["ts"] < actual_ttl:
            return _cache[key]["data"]
        data = fn()
        _cache[key] = {"data": data, "ts": now}
        return data

    return _cached
