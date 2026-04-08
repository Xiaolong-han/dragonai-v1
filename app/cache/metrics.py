"""缓存监控模块"""

import logging
from datetime import datetime
from typing import Any

from app.monitoring.metrics import CACHE_OPERATIONS

logger = logging.getLogger(__name__)


class CacheMetrics:
    """缓存指标收集器"""

    def __init__(self):
        self._hits = 0
        self._misses = 0
        self._null_hits = 0
        self._errors = 0
        self._start_time = datetime.now()

    def record_hit(self):
        self._hits += 1
        # 同步到 Prometheus
        CACHE_OPERATIONS.labels(operation="get", result="hit").inc()

    def record_miss(self):
        self._misses += 1
        # 同步到 Prometheus
        CACHE_OPERATIONS.labels(operation="get", result="miss").inc()

    def record_null_hit(self):
        self._null_hits += 1
        # 空值命中也算命中
        CACHE_OPERATIONS.labels(operation="get", result="hit").inc()

    def record_error(self):
        self._errors += 1
        # 同步到 Prometheus
        CACHE_OPERATIONS.labels(operation="get", result="error").inc()

    def record_set(self, success: bool = True):
        """记录缓存写入"""
        result = "success" if success else "error"
        CACHE_OPERATIONS.labels(operation="set", result=result).inc()

    def record_delete(self, success: bool = True):
        """记录缓存删除"""
        result = "success" if success else "error"
        CACHE_OPERATIONS.labels(operation="delete", result=result).inc()

    def get_stats(self) -> dict[str, Any]:
        total = self._hits + self._misses + self._null_hits
        hit_rate = (self._hits + self._null_hits) / total * 100 if total > 0 else 0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "null_hits": self._null_hits,
            "errors": self._errors,
            "total_requests": total,
            "hit_rate": round(hit_rate, 2),
            "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
        }

    def reset(self):
        self._hits = 0
        self._misses = 0
        self._null_hits = 0
        self._errors = 0
        self._start_time = datetime.now()


cache_metrics = CacheMetrics()


async def get_cache_stats() -> dict[str, Any]:
    """获取缓存统计信息"""
    from app.cache.redis import redis_client

    stats = cache_metrics.get_stats()

    try:
        info = await redis_client.client.info("memory")
        stats["redis_memory_used"] = info.get("used_memory_human", "unknown")
        stats["redis_memory_peak"] = info.get("used_memory_peak_human", "unknown")

        info_stats = await redis_client.client.info("stats")
        stats["redis_total_commands"] = info_stats.get("total_commands_processed", 0)
        stats["redis_connections_received"] = info_stats.get("total_connections_received", 0)

        dbsize = await redis_client.client.dbsize()
        stats["redis_key_count"] = dbsize
    except Exception as e:
        logger.debug(f"[CACHE METRICS] Cannot get Redis info: {e}")
        stats["redis_error"] = str(e)

    return stats
