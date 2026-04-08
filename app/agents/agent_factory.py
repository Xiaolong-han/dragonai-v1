"""Agent工厂 - 使用LangChain Deep Agent"""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ModelFallbackMiddleware,
    SummarizationMiddleware,
    TodoListMiddleware,
    ToolCallLimitMiddleware,
    ToolRetryMiddleware,
)
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.memory import BaseStore, InMemoryStore

from app.agents.middleware import CustomSkillsMiddleware, MemoryMiddleware
from app.agents.prompts import (
    FILESYSTEM_SYSTEM_PROMPT_CN,
    FILESYSTEM_TOOL_DESCRIPTIONS_CN,
    SKILLS_SYSTEM_PROMPT_CN,
    SYSTEM_PROMPT,
    WRITE_TODOS_SYSTEM_PROMPT_CN,
    WRITE_TODOS_TOOL_DESCRIPTION_CN,
)
from app.config import settings
from app.llm.model_factory import ModelFactory

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Agent 运行时上下文 - 用于 LangChain 1.0 的 context_schema"""
    user_id: str


class AgentFactory:
    """Agent工厂类 - 使用LangChain 1.0+推荐的create_agent"""

    _checkpointer: AsyncPostgresSaver | InMemorySaver | None = None
    _context_manager: object | None = None
    _initialized: bool = False
    _agent_cache: dict[str, Any] = {}
    _skills_backend: FilesystemBackend | None = None
    _store: BaseStore | None = None
    _store_context: object | None = None

    @classmethod
    async def init_checkpointer(cls) -> bool:
        """初始化 checkpointer (异步版本)

        在应用启动时调用，创建数据库连接并初始化表结构。

        Returns:
            bool: 是否成功使用 PostgreSQL
        """
        try:
            if settings.database_url:
                cls._context_manager = AsyncPostgresSaver.from_conn_string(settings.database_url)
                cls._checkpointer = await cls._context_manager.__aenter__()
                if not cls._initialized:
                    await cls._checkpointer.setup()
                    cls._initialized = True
                logger.info("[AGENT] AsyncPostgresSaver initialized")
                return True
        except Exception as e:
            logger.warning(f"[AGENT] AsyncPostgresSaver init failed, fallback to InMemorySaver: {e}")

        cls._checkpointer = InMemorySaver()
        cls._context_manager = None
        return False

    @classmethod
    async def close_checkpointer(cls) -> None:
        """关闭 checkpointer 连接 (异步版本)

        在应用关闭时调用，清理数据库连接和缓存。
        """
        if cls._context_manager and hasattr(cls._context_manager, '__aexit__'):
            try:
                await cls._context_manager.__aexit__(None, None, None)
                logger.info("[AGENT] AsyncPostgresSaver connection closed")
            except Exception as e:
                logger.error(f"[AGENT] Failed to close AsyncPostgresSaver connection: {e}")
        cls._checkpointer = None
        cls._context_manager = None
        cls._agent_cache.clear()
        cls._skills_backend = None
        logger.info("[AGENT] Cache cleared")

    @classmethod
    def get_checkpointer(cls) -> AsyncPostgresSaver | InMemorySaver:
        """获取 checkpointer 实例

        如果尚未初始化，会自动初始化。

        Returns:
            AsyncPostgresSaver 或 InMemorySaver 实例
        """
        if cls._checkpointer is None:
            raise RuntimeError("Checkpointer not initialized. Call init_checkpointer() first.")
        return cls._checkpointer

    @classmethod
    def _get_store_index_config(cls):
        """获取 Store 向量索引配置

        Returns:
            IndexConfig 用于启用向量检索
        """
        from langgraph.store.base import IndexConfig

        # 使用项目配置的 Embedding 模型
        embedding = ModelFactory.get_embedding()

        # text-embedding-v4 维度为 1024
        # 参考: https://help.aliyun.com/zh/model-studio/getting-started/models
        embedding_dims = 1024

        return IndexConfig(
            embed=embedding,
            dims=embedding_dims,
            fields=["content", "$"],  # 嵌入 content 字段和整个文档
        )

    @classmethod
    async def init_store(cls) -> bool:
        """初始化长期记忆存储 (BaseStore)

        用于 StoreBackend 持久化跨线程记忆。
        启用向量检索支持语义相似度搜索。

        Returns:
            bool: 是否成功使用 PostgreSQL
        """
        try:
            if settings.database_url:
                import asyncpg
                from langgraph.store.postgres.aio import AsyncPostgresStore

                # 先确保 pgvector 扩展已安装
                conn = await asyncpg.connect(settings.database_url)
                try:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    logger.info("[AGENT] pgvector extension ensured")
                except Exception as e:
                    logger.warning(f"[AGENT] Could not create vector extension: {e}")
                finally:
                    await conn.close()

                index_config = cls._get_store_index_config()
                cls._store_context = AsyncPostgresStore.from_conn_string(
                    settings.database_url,
                    index=index_config,
                )
                cls._store = await cls._store_context.__aenter__()
                await cls._store.setup()
                logger.info("[AGENT] AsyncPostgresStore initialized with vector search enabled")
                return True
        except Exception as e:
            logger.warning(f"[AGENT] AsyncPostgresStore init failed, fallback to InMemoryStore: {e}")

        # InMemoryStore 也支持向量检索
        index_config = cls._get_store_index_config()
        cls._store = InMemoryStore(index=index_config)
        cls._store_context = None
        logger.info("[AGENT] InMemoryStore initialized with vector search enabled")
        return False

    @classmethod
    async def close_store(cls) -> None:
        """关闭长期记忆存储"""
        if cls._store_context and hasattr(cls._store_context, '__aexit__'):
            try:
                await cls._store_context.__aexit__(None, None, None)
                logger.info("[AGENT] AsyncPostgresStore connection closed")
            except Exception as e:
                logger.error(f"[AGENT] Failed to close AsyncPostgresStore: {e}")
        cls._store = None
        cls._store_context = None

    @classmethod
    def get_store(cls) -> BaseStore:
        """获取长期记忆存储实例

        Returns:
            BaseStore 实例
        """
        if cls._store is None:
            raise RuntimeError("Store not initialized. Call init_store() first.")
        return cls._store

    @classmethod
    def _make_backend(cls, runtime) -> CompositeBackend:
        """创建复合后端 - 路由持久化路径到 StoreBackend

        路径规划：
        - /memories/     → StoreBackend (跨会话持久化)
        - /skills/       → FilesystemBackend (本地技能文件)
        - 其他           → StateBackend (临时存储)
        """
        def get_user_id(ctx) -> str:
            context = getattr(ctx.runtime, "context", None)
            if context is not None:
                return getattr(context, "user_id", "default")
            return "default"

        memories_backend = StoreBackend(
            runtime,
            namespace=lambda ctx: (
                get_user_id(ctx),
                "memories"
            )
        )

        skills_dir = str(Path(settings.storage_dir).resolve() / "skills")
        skills_file_backend = FilesystemBackend(
            root_dir=skills_dir,
            virtual_mode=True,
        )

        return CompositeBackend(
            default=StateBackend(runtime),
            routes={
                "/memories/": memories_backend,
                "/skills/": skills_file_backend,
            }
        )

    @classmethod
    def _get_or_create_backend(cls, runtime) -> CompositeBackend:
        """获取或创建复合后端 - 每次创建新实例避免上下文混淆

        注意：不再使用类级别缓存，因为 runtime 包含用户上下文，
        共享 backend 会导致不同用户的上下文混淆。

        Args:
            runtime: LangChain runtime 实例

        Returns:
            CompositeBackend 实例
        """
        return cls._make_backend(runtime)

    @classmethod
    def create_chat_agent(
        cls,
        is_expert: bool = False,
        enable_thinking: bool = False
    ):
        """创建聊天Agent (LangChain 1.0+ 推荐方式)

        使用create_agent创建ReAct模式的Agent，无需AgentExecutor。
        内部基于LangGraph构建，支持持久化、流式输出等特性。

        使用缓存机制，相同配置的agent只创建一次，通过thread_id区分不同对话。

        集成中间件: TodoListMiddleware, SkillsMiddleware, PatchToolCallsMiddleware,
        LLMToolSelectorMiddleware, ContextEditingMiddleware,
        SummarizationMiddleware, ToolCallLimitMiddleware,
        ModelCallLimitMiddleware, ToolRetryMiddleware, ModelFallbackMiddleware

        Args:
            is_expert: 是否使用专家模型
            enable_thinking: 是否启用深度思考

        Returns:
            Agent实例，可直接调用invoke或stream
        """
        # 缓存键包含中间件配置，确保配置变化时重新创建 Agent
        middleware_settings = settings.agent_middleware
        middleware_hash = hash((
            middleware_settings.enable_todo_list,
            middleware_settings.enable_tool_retry,
            middleware_settings.enable_model_fallback,
            middleware_settings.enable_filesystem,
            middleware_settings.enable_skills,
            middleware_settings.enable_summarization,
            middleware_settings.enable_tool_call_limit,
            middleware_settings.enable_model_call_limit,
            middleware_settings.enable_memory,
            middleware_settings.tool_retry_max_retries,
            middleware_settings.summarization_max_tokens,
            middleware_settings.model_call_limit,
            middleware_settings.memory_max_to_load,
            middleware_settings.memory_enable_extraction,
            middleware_settings.memory_enable_semantic_search,
        ))
        cache_key = f"expert_{is_expert}_thinking_{enable_thinking}_mw_{middleware_hash}"

        if cache_key in cls._agent_cache:
            logger.debug(f"[AGENT] Using cached agent: {cache_key}")
            return cls._agent_cache[cache_key]

        main_model = ModelFactory.get_general_model(
            is_expert=is_expert,
            enable_thinking=enable_thinking
        )

        middleware = cls._build_middleware()

        checkpointer = cls.get_checkpointer()
        store = cls.get_store()

        from app.agents.tools import ALL_TOOLS

        agent = create_agent(
            model=main_model,
            tools=ALL_TOOLS,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,
            store=store,
            middleware=middleware,
            context_schema=AgentContext,
        )

        cls._agent_cache[cache_key] = agent
        logger.debug(f"[AGENT] Created and cached agent: {cache_key}")

        return agent

    @classmethod
    def _build_middleware(cls) -> list:
        """构建Agent中间件列表"""
        middleware_settings = settings.agent_middleware
        fallback_model = ModelFactory.get_general_model(is_expert=False, enable_thinking=False, streaming=True)
        summary_model = ModelFactory.get_general_model(is_expert=False, enable_thinking=False, streaming=False)
        extraction_model = ModelFactory.get_general_model(is_expert=False, enable_thinking=False, streaming=False)

        middleware = []

        # 记忆中间件 - 放在最前面，确保其他中间件可以看到记忆上下文
        if middleware_settings.enable_memory:
            middleware.append(MemoryMiddleware(
                store=cls.get_store(),
                model=extraction_model,
                max_memories_to_load=middleware_settings.memory_max_to_load,
                enable_extraction=middleware_settings.memory_enable_extraction,
                enable_semantic_search=middleware_settings.memory_enable_semantic_search,
                extraction_interval=middleware_settings.memory_extraction_interval,
            ))

        if middleware_settings.enable_todo_list:
            middleware.append(TodoListMiddleware(
                system_prompt=WRITE_TODOS_SYSTEM_PROMPT_CN,
                tool_description=WRITE_TODOS_TOOL_DESCRIPTION_CN,
            ))

        middleware.append(PatchToolCallsMiddleware())

        if middleware_settings.enable_tool_retry:
            middleware.append(ToolRetryMiddleware(
                max_retries=middleware_settings.tool_retry_max_retries,
                backoff_factor=middleware_settings.tool_retry_backoff_factor,
            ))

        if middleware_settings.enable_model_fallback:
            middleware.append(ModelFallbackMiddleware(fallback_model))

        if middleware_settings.enable_filesystem:
            middleware.append(FilesystemMiddleware(
                backend=cls._get_or_create_backend,
                system_prompt=FILESYSTEM_SYSTEM_PROMPT_CN,
                custom_tool_descriptions=FILESYSTEM_TOOL_DESCRIPTIONS_CN,
                tool_token_limit_before_evict=middleware_settings.filesystem_tool_token_limit,
            ))

        if middleware_settings.enable_skills:
            middleware.append(CustomSkillsMiddleware(
                backend=cls._get_or_create_backend,
                sources=["/skills/"],
                system_prompt_template=SKILLS_SYSTEM_PROMPT_CN,
            ))

        if middleware_settings.enable_summarization:
            middleware.append(SummarizationMiddleware(
                model=summary_model,
                max_tokens_before_summary=middleware_settings.summarization_max_tokens,
                messages_to_keep=middleware_settings.summarization_messages_to_keep,
            ))

        if middleware_settings.enable_tool_call_limit:
            middleware.append(ToolCallLimitMiddleware(
                run_limit=settings.agent_tool_call_limit,
                exit_behavior="end"
            ))

        if middleware_settings.enable_model_call_limit:
            middleware.append(ModelCallLimitMiddleware(
                run_limit=middleware_settings.model_call_limit,
                exit_behavior="end"
            ))

        return middleware

    @classmethod
    async def warmup(cls):
        """启动预热：并发创建全部 4 种配置

        在应用启动时调用，避免首次请求延迟。
        使用 asyncio.gather 并发创建，减少启动时间。
        """
        configs = [
            (False, False),
            (True, False),
            (False, True),
            (True, True),
        ]

        logger.info("[AGENT] Starting concurrent warmup...")

        async def create_agent_safe(is_expert: bool, thinking: bool) -> str | None:
            """安全创建 Agent，返回缓存键或 None"""
            try:
                cls.create_chat_agent(is_expert, thinking)
                return f"expert_{is_expert}_thinking_{thinking}"
            except Exception as e:
                logger.warning(f"[AGENT] Warmup failed for expert={is_expert}, thinking={thinking}: {e}")
                return None

        results = await asyncio.gather(
            *[create_agent_safe(is_expert, thinking) for is_expert, thinking in configs]
        )

        successful = [r for r in results if r is not None]
        logger.info(f"[AGENT] Warmup completed, cached: {len(successful)}/{len(configs)}")

    @classmethod
    def get_cache_stats(cls) -> dict:
        """获取缓存状态

        Returns:
            包含缓存信息的字典
        """
        return {
            "cached_agents": list(cls._agent_cache.keys()),
            "total": len(cls._agent_cache),
            "max": 4,
        }

    @classmethod
    def get_agent_config(cls, conversation_id: str, user_id: int | None = None) -> tuple[dict, "AgentContext | None"]:
        """获取Agent配置 - 用于区分不同对话线程

        Args:
            conversation_id: 对话ID
            user_id: 用户ID，用于长期记忆的 namespace 隔离

        Returns:
            (config, context) 元组，config 包含 thread_id，context 包含 user_id
        """
        config = {
            "configurable": {
                "thread_id": f"conversation_{conversation_id}"
            }
        }

        context = None
        if user_id is not None:
            context = AgentContext(user_id=str(user_id))

        return config, context


class AgentLifecycle:
    """Agent 生命周期管理类 - 统一初始化和关闭流程

    提供单一入口来管理 Agent 系统的完整生命周期，
    包括 checkpointer、store 和 agent 预热的初始化，
    以及对应的资源清理。

    使用方式::

        # 启动时
        await AgentLifecycle.initialize()

        # 关闭时
        await AgentLifecycle.shutdown()
    """

    @classmethod
    async def initialize(cls) -> None:
        """统一初始化 Agent 系统所有资源

        初始化顺序:
        1. Checkpointer (PostgreSQL 或 InMemory)
        2. Store (长期记忆存储)
        3. Agent 预热 (4 种配置并发创建)

        Raises:
            Exception: 初始化失败时仅记录警告，不阻止启动
        """
        logger.info("[AGENT] Initializing Agent system...")

        await AgentFactory.init_checkpointer()
        logger.info("[AGENT] Checkpointer initialized")

        await AgentFactory.init_store()
        logger.info("[AGENT] Store initialized")

        try:
            await AgentFactory.warmup()
            logger.info("[AGENT] Agent warmup completed")
        except Exception as e:
            logger.warning(f"[AGENT] Warmup failed, will create agents on-demand: {e}")

    @classmethod
    async def shutdown(cls) -> None:
        """统一关闭 Agent 系统所有资源

        关闭顺序:
        1. Checkpointer 连接
        2. Store 连接
        3. 缓存清理
        """
        logger.info("[AGENT] Shutting down Agent system...")

        await AgentFactory.close_checkpointer()
        logger.info("[AGENT] Checkpointer closed")

        await AgentFactory.close_store()
        logger.info("[AGENT] Store closed")

        logger.info("[AGENT] Agent system shutdown completed")
