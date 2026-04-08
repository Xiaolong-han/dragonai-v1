import asyncio
import logging
from collections.abc import Callable
from typing import TypeVar

from sqlalchemy import select

from app.cache.redis import cache_aside
from app.core.database import get_db_session
from app.models.conversation import Conversation
from app.models.user import User

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheWarmup:
    """缓存预热服务 - 并发优化版本"""

    # 并发限制
    MAX_CONCURRENT_WARMUPS = 10

    @staticmethod
    async def _warmup_cache_entry(
        cache_key: str,
        data_func: Callable,
        ttl: int = 3600,
    ) -> bool:
        """通用的缓存预热方法

        Args:
            cache_key: 缓存键
            data_func: 数据获取函数
            ttl: 缓存过期时间

        Returns:
            是否预热成功
        """
        try:
            await cache_aside(
                key=cache_key,
                ttl=ttl,
                data_func=data_func,
                enable_null_cache=True,
                enable_lock=True,
                enable_random_ttl=True
            )
            return True
        except Exception as e:
            logger.warning(f"[CACHE WARMUP] 预热缓存失败 key={cache_key}: {e}")
            return False

    @staticmethod
    async def warmup_conversations(limit: int = 100):
        """预热会话列表缓存 - 并发优化版本

        预热策略：
        1. 一次性获取所有活跃用户
        2. 使用信号量控制并发数
        3. 并发预热所有用户的会话列表
        """
        logger.debug(f"[CACHE WARMUP] 开始预热会话列表缓存，限制 {limit} 条")

        async with get_db_session() as db:
            # 一次性获取所有活跃用户
            result = await db.execute(select(User).limit(50))
            active_users = result.scalars().all()

            if not active_users:
                logger.info("[CACHE WARMUP] 没有活跃用户需要预热")
                return

            # 并发预热信号量
            semaphore = asyncio.Semaphore(CacheWarmup.MAX_CONCURRENT_WARMUPS)

            async def warmup_user(user_id: int) -> bool:
                """预热单个用户的会话列表"""
                async with semaphore:
                    cache_key = f"conversations:user:{user_id}:skip:0:limit:100"

                    async def fetch_conversations():
                        result = await db.execute(
                            select(Conversation)
                            .where(Conversation.user_id == user_id)
                            .order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc())
                            .offset(0)
                            .limit(100)
                        )
                        return result.scalars().all()

                    return await CacheWarmup._warmup_cache_entry(cache_key, fetch_conversations)

            # 并发预热所有用户
            results = await asyncio.gather(
                *[warmup_user(user.id) for user in active_users],
                return_exceptions=True
            )

            warmed_count = sum(1 for r in results if r is True)
            logger.info(f"[CACHE WARMUP] 会话列表缓存预热完成，预热了 {warmed_count}/{len(active_users)} 个用户")

    @staticmethod
    async def warmup_pinned_conversations():
        """预热置顶会话详情缓存 - 并发优化版本"""
        logger.debug("[CACHE WARMUP] 开始预热置顶会话详情缓存")

        async with get_db_session() as db:
            result = await db.execute(
                select(Conversation).where(Conversation.is_pinned)
            )
            pinned_conversations = result.scalars().all()

            if not pinned_conversations:
                logger.info("[CACHE WARMUP] 没有置顶会话需要预热")
                return

            semaphore = asyncio.Semaphore(CacheWarmup.MAX_CONCURRENT_WARMUPS)

            async def warmup_conv(conv_id: int, conv_user_id: int) -> bool:
                """预热单个会话"""
                async with semaphore:
                    cache_key = f"conversation:{conv_id}:{conv_user_id}"

                    async def fetch_conversation():
                        result = await db.execute(
                            select(Conversation)
                            .where(
                                Conversation.id == conv_id,
                                Conversation.user_id == conv_user_id
                            )
                        )
                        return result.scalar_one_or_none()

                    return await CacheWarmup._warmup_cache_entry(cache_key, fetch_conversation)

            # 并发预热
            results = await asyncio.gather(
                *[warmup_conv(conv.id, conv.user_id) for conv in pinned_conversations],
                return_exceptions=True
            )

            warmed_count = sum(1 for r in results if r is True)
            logger.info(f"[CACHE WARMUP] 置顶会话详情缓存预热完成，预热了 {warmed_count}/{len(pinned_conversations)} 个会话")

    @staticmethod
    async def warmup_recent_conversations(hours: int = 24):
        """预热最近活跃的会话 - 并发优化版本

        Args:
            hours: 预热最近多少小时内有更新的会话
        """
        from datetime import datetime, timedelta

        logger.debug(f"[CACHE WARMUP] 开始预热最近 {hours} 小时活跃的会话")

        async with get_db_session() as db:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            result = await db.execute(
                select(Conversation)
                .where(Conversation.updated_at >= cutoff_time)
                .limit(200)
            )
            recent_conversations = result.scalars().all()

            if not recent_conversations:
                logger.info("[CACHE WARMUP] 没有最近活跃的会话需要预热")
                return

            semaphore = asyncio.Semaphore(CacheWarmup.MAX_CONCURRENT_WARMUPS)

            async def warmup_conv(conv_id: int, conv_user_id: int) -> bool:
                """预热单个会话"""
                async with semaphore:
                    cache_key = f"conversation:{conv_id}:{conv_user_id}"

                    async def fetch_conversation():
                        result = await db.execute(
                            select(Conversation)
                            .where(
                                Conversation.id == conv_id,
                                Conversation.user_id == conv_user_id
                            )
                        )
                        return result.scalar_one_or_none()

                    return await CacheWarmup._warmup_cache_entry(cache_key, fetch_conversation)

            # 并发预热
            results = await asyncio.gather(
                *[warmup_conv(conv.id, conv.user_id) for conv in recent_conversations],
                return_exceptions=True
            )

            warmed_count = sum(1 for r in results if r is True)
            logger.info(f"[CACHE WARMUP] 最近活跃会话缓存预热完成，预热了 {warmed_count}/{len(recent_conversations)} 个会话")

    @staticmethod
    async def warmup_all():
        """执行所有缓存预热 - 并发优化版本"""
        logger.info("[CACHE WARMUP] 开始缓存预热")

        # 并发执行所有预热任务
        results = await asyncio.gather(
            CacheWarmup.warmup_conversations(limit=100),
            CacheWarmup.warmup_pinned_conversations(),
            CacheWarmup.warmup_recent_conversations(hours=24),
            return_exceptions=True
        )

        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            logger.warning(f"[CACHE WARMUP] 部分预热任务失败: {len(errors)} 个")

        logger.info("[CACHE WARMUP] 缓存预热完成")


cache_warmup = CacheWarmup()
