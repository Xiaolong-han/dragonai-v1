"""Agent工厂 - 使用LangChain Deep Agent"""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, Dict, Any

from langchain.agents import create_agent
from langchain.agents.middleware import (
    SummarizationMiddleware,
    ContextEditingMiddleware,
    ClearToolUsesEdit,
    LLMToolSelectorMiddleware,
    ToolCallLimitMiddleware,
    ToolRetryMiddleware,
    ModelCallLimitMiddleware,
    ModelFallbackMiddleware,
    TodoListMiddleware,
)
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

from langgraph.store.memory import InMemoryStore, BaseStore

from app.config import settings
from app.llm.model_factory import ModelFactory
from app.agents.prompts import (
    SYSTEM_PROMPT,
    WRITE_TODOS_SYSTEM_PROMPT_CN,
    WRITE_TODOS_TOOL_DESCRIPTION_CN,
    FILESYSTEM_SYSTEM_PROMPT_CN,
    FILESYSTEM_TOOL_DESCRIPTIONS_CN,
    SKILLS_SYSTEM_PROMPT_CN,
)
from app.agents.middleware_custom import CustomSkillsMiddleware

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Agent 运行时上下文 - 用于 LangChain 1.0 的 context_schema"""
    user_id: str


class AgentFactory:
    """Agent工厂类 - 使用LangChain 1.0+推荐的create_agent"""

    _checkpointer: Optional[Union[AsyncPostgresSaver, InMemorySaver]] = None
    _context_manager: Optional[object] = None
    _initialized: bool = False
    _agent_cache: Dict[str, Any] = {}
    _skills_backend: Optional[FilesystemBackend] = None
    _store: Optional[BaseStore] = None
    _store_context: Optional[object] = None

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
    def get_checkpointer(cls) -> Union[AsyncPostgresSaver, InMemorySaver]:
        """获取 checkpointer 实例
        
        如果尚未初始化，会自动初始化。
        
        Returns:
            AsyncPostgresSaver 或 InMemorySaver 实例
        """
        if cls._checkpointer is None:
            raise RuntimeError("Checkpointer not initialized. Call init_checkpointer() first.")
        return cls._checkpointer

    @classmethod
    async def init_store(cls) -> bool:
        """初始化长期记忆存储 (BaseStore)
        
        用于 StoreBackend 持久化跨线程记忆。
        
        Returns:
            bool: 是否成功使用 PostgreSQL
        """
        try:
            if settings.database_url:
                from langgraph.store.postgres import PostgresStore
                cls._store_context = PostgresStore.from_conn_string(settings.database_url)
                cls._store = cls._store_context.__enter__()
                cls._store.setup()
                logger.info("[AGENT] PostgresStore initialized for long-term memory")
                return True
        except Exception as e:
            logger.warning(f"[AGENT] PostgresStore init failed, fallback to InMemoryStore: {e}")
        
        cls._store = InMemoryStore()
        cls._store_context = None
        return False

    @classmethod
    async def close_store(cls) -> None:
        """关闭长期记忆存储"""
        if cls._store_context and hasattr(cls._store_context, '__exit__'):
            try:
                cls._store_context.__exit__(None, None, None)
                logger.info("[AGENT] PostgresStore connection closed")
            except Exception as e:
                logger.error(f"[AGENT] Failed to close PostgresStore: {e}")
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
        
        skills_dir = str((Path(settings.storage_dir).resolve() / "skills"))
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
    def _get_skills_backend(cls) -> FilesystemBackend:
        """获取技能文件系统后端 (用于 SkillsMiddleware 扫描)
        
        Returns:
            FilesystemBackend 实例
        """
        if cls._skills_backend is None:
            storage_dir = Path(settings.storage_dir).resolve()
            if not storage_dir.exists():
                storage_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"[AGENT] Created storage directory: {storage_dir}")
            
            skills_dir = storage_dir / "skills"
            if not skills_dir.exists():
                skills_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"[AGENT] Created skills directory: {skills_dir}")
            
            cls._skills_backend = FilesystemBackend(
                root_dir=str(storage_dir),
                virtual_mode=True,
            )
            logger.debug(f"[AGENT] Initialized skills backend with root: {storage_dir}")
        return cls._skills_backend

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
        cache_key = f"expert_{is_expert}_thinking_{enable_thinking}"
        
        if cache_key in cls._agent_cache:
            logger.debug(f"[AGENT] Using cached agent: {cache_key}")
            return cls._agent_cache[cache_key]
        
        main_model = ModelFactory.get_general_model(
            is_expert=is_expert,
            enable_thinking=enable_thinking
        )
        
        middleware = cls._build_middleware()
        
        # 获取 store，如果 BackendManager 未初始化则使用 None
        checkpointer = cls.get_checkpointer()
        store = cls.get_store()

        # 延迟导入避免循环导入
        from app.tools import ALL_TOOLS

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
        fallback_model = ModelFactory.get_general_model(is_expert=False, enable_thinking=False, streaming=True)
        summary_model = ModelFactory.get_general_model(is_expert=False, enable_thinking=False, streaming=False)

        return [
            TodoListMiddleware(
                system_prompt=WRITE_TODOS_SYSTEM_PROMPT_CN,
                tool_description=WRITE_TODOS_TOOL_DESCRIPTION_CN,
            ),  # 任务规划和跟踪
            PatchToolCallsMiddleware(),  # 工具调用修复
            ToolRetryMiddleware(max_retries=1, backoff_factor=2.0),
            ModelFallbackMiddleware(fallback_model),
            FilesystemMiddleware(
                backend=cls._make_backend,
                system_prompt=FILESYSTEM_SYSTEM_PROMPT_CN,
                custom_tool_descriptions=FILESYSTEM_TOOL_DESCRIPTIONS_CN,
                tool_token_limit_before_evict=8000,
            ),
            CustomSkillsMiddleware(
                backend=cls._make_backend,
                sources=["/skills/"],
                system_prompt_template=SKILLS_SYSTEM_PROMPT_CN,
            ),
            SummarizationMiddleware(model=summary_model, max_tokens_before_summary=10000, messages_to_keep=6),
            ToolCallLimitMiddleware(run_limit=settings.agent_tool_call_limit, exit_behavior="end"),
            ModelCallLimitMiddleware(run_limit=50, exit_behavior="end"),
        ]

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
        
        async def create_agent_safe(is_expert: bool, thinking: bool) -> Optional[str]:
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

