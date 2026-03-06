"""缓存模块"""

from .redis import redis_client, cache_aside, invalidate_cache_by_pattern, cached
from .warmup import cache_warmup, CacheWarmup
from .metrics import cache_metrics, get_cache_stats

__all__ = [
    "redis_client",
    "cache_aside",
    "invalidate_cache_by_pattern",
    "cached",
    "cache_warmup",
    "CacheWarmup",
    "cache_metrics",
    "get_cache_stats",
]
