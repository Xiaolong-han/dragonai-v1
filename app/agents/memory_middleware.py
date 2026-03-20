"""记忆管理中间件

提供自动记忆加载和提取功能：
- abefore_agent: 会话开始时加载用户相关记忆
- aafter_agent: 会话结束后提取用户偏好和重要事实

存储格式与 StoreBackend 兼容：
- 虚拟路径: /memories/preferences.txt, /memories/facts/*.txt
- Agent 可通过 read_file("/memories/xxx") 读取自动提取的记忆

注意：
- 使用异步钩子（abefore_agent/aafter_agent）因为涉及异步 I/O 操作
- LangGraph Store 需要实现 asearch/aput 异步方法
- LLM 模型需要实现 ainvoke 异步方法
"""

import json
import logging
from typing import Any, Optional
from datetime import datetime

from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)


# 记忆提取提示词
MEMORY_EXTRACTION_PROMPT = """分析以下对话，提取用户的偏好和重要事实。

对话内容：
{conversation}

请提取以下信息（如果没有相关内容，对应字段为空）：
1. 用户偏好（如语言偏好、专业领域、回复风格等）
2. 重要事实（如职业、技能、兴趣等）
3. 其他值得记住的信息

以 JSON 格式返回：
{{
    "preferences": [
        {{"key": "语言", "value": "中文"}},
        {{"key": "专业领域", "value": "编程"}}
    ],
    "facts": [
        {{"key": "职业", "value": "软件工程师"}},
        {{"key": "技能", "value": "Python, TypeScript"}}
    ],
    "notes": "其他备注"
}}

只返回 JSON，不要有其他内容。"""


class MemoryMiddleware(AgentMiddleware):
    """记忆管理中间件

    功能：
    1. 会话开始时加载用户记忆（abefore_agent 异步钩子）
    2. 会话结束后自动提取用户偏好和重要事实（aafter_agent 异步钩子）

    存储路径（虚拟路径，与 StoreBackend 兼容）：
    - /memories/preferences.txt - 用户偏好
    - /memories/facts/{topic}.txt - 用户相关事实

    Agent 可通过 read_file("/memories/xxx") 读取自动提取的记忆。

    Args:
        store: LangGraph Store 实例（支持向量检索，需要实现 asearch/aput）
        model: 用于记忆提取的模型（需要实现 ainvoke）
        max_memories_to_load: 会话开始时最多加载的记忆数量
        enable_extraction: 是否启用自动提取
        enable_semantic_search: 是否启用语义检索
    """

    def __init__(
        self,
        *,
        store,
        model=None,
        max_memories_to_load: int = 5,
        enable_extraction: bool = True,
        enable_semantic_search: bool = True,
    ):
        self.store = store
        self.model = model
        self.max_memories_to_load = max_memories_to_load
        self.enable_extraction = enable_extraction
        self.enable_semantic_search = enable_semantic_search

    def _get_user_namespace(self, runtime) -> tuple:
        """获取用户命名空间

        Args:
            runtime: LangGraph runtime 实例

        Returns:
            用户命名空间元组 (user_id, "memories")
        """
        context = getattr(runtime, "context", None)
        user_id = "default"
        if context is not None:
            user_id = getattr(context, "user_id", "default")
        return (user_id, "memories")

    def _get_last_user_message(self, state: AgentState) -> Optional[str]:
        """获取最后一条用户消息"""
        messages = state.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                return msg.content
        return None

    def _get_conversation_summary(self, state: AgentState) -> str:
        """获取对话摘要（最后几轮）"""
        messages = state.get("messages", [])
        recent_messages = messages[-10:]  # 最近 10 条消息

        summary_parts = []
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                summary_parts.append(f"用户: {msg.content[:200]}")
            elif isinstance(msg, AIMessage):
                content = msg.content[:200] if isinstance(msg.content, str) else str(msg.content)[:200]
                summary_parts.append(f"助手: {content}")

        return "\n".join(summary_parts)

    async def abefore_agent(self, state: AgentState, runtime) -> dict[str, Any] | None:
        """会话开始时加载相关记忆（异步钩子）

        使用异步钩子因为 Store.search 可能涉及：
        - 数据库查询
        - 向量计算
        - 网络请求

        Args:
            state: Agent 状态
            runtime: LangGraph runtime

        Returns:
            更新状态的字典或 None
        """
        namespace = self._get_user_namespace(runtime)
        user_message = self._get_last_user_message(state)

        if not user_message:
            return None

        try:
            # Store.asearch 是异步操作
            if self.enable_semantic_search:
                memories = await self.store.asearch(
                    namespace,
                    query=user_message,
                    limit=self.max_memories_to_load,
                )
            else:
                memories = await self.store.asearch(
                    namespace,
                    limit=self.max_memories_to_load
                )

            if memories:
                # 构建记忆上下文
                memory_context = self._format_memories(memories)
                logger.info(f"[MEMORY] Loaded {len(memories)} memories for user")

                # 将记忆注入到消息开头
                memory_message = HumanMessage(
                    content=f"[用户记忆上下文]\n{memory_context}\n[/用户记忆上下文]",
                    additional_kwargs={"lc_source": "memory_loader"}
                )

                return {"messages": [memory_message] + state.get("messages", [])}

        except Exception as e:
            logger.warning(f"[MEMORY] Failed to load memories: {e}")

        return None

    async def aafter_agent(self, state: AgentState, runtime) -> dict[str, Any] | None:
        """会话结束后提取记忆（异步钩子）

        使用异步钩子因为：
        - LLM 调用是异步的
        - Store 写入可能涉及数据库

        Args:
            state: Agent 状态
            runtime: LangGraph runtime

        Returns:
            None (记忆保存在后台完成)
        """
        if not self.enable_extraction or not self.model:
            return None

        namespace = self._get_user_namespace(runtime)
        conversation = self._get_conversation_summary(state)

        if not conversation or len(conversation) < 50:
            return None

        try:
            # 使用模型提取记忆（异步调用）
            extraction_prompt = MEMORY_EXTRACTION_PROMPT.format(conversation=conversation)
            response = await self.model.ainvoke([HumanMessage(content=extraction_prompt)])

            # 解析提取结果
            extraction_result = self._parse_extraction(response.content)
            if extraction_result:
                # 保存记忆（异步）
                await self._save_memories(namespace, extraction_result)
                logger.info(f"[MEMORY] Saved {len(extraction_result.get('preferences', []))} preferences, "
                           f"{len(extraction_result.get('facts', []))} facts")

        except Exception as e:
            logger.warning(f"[MEMORY] Failed to extract memories: {e}")

        return None

    def _format_memories(self, memories: list) -> str:
        """格式化记忆为上下文字符串

        支持 StoreBackend 格式：
        - content: ["line1", "line2", ...] 列表形式
        - 或 content: "string" 字符串形式（兼容）
        """
        parts = []
        for item in memories:
            value = item.value
            if isinstance(value, dict):
                content = value.get("content", "")
                # StoreBackend 格式: content 是列表
                if isinstance(content, list):
                    content = "\n".join(content)
                elif not isinstance(content, str):
                    content = json.dumps(content, ensure_ascii=False)
            else:
                content = str(value)
            parts.append(f"- {content}")

        return "\n".join(parts)

    def _parse_extraction(self, content: str) -> Optional[dict]:
        """解析模型输出的 JSON"""
        try:
            # 尝试提取 JSON 块
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end]
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end]

            result = json.loads(content.strip())

            # 验证结果结构
            if not isinstance(result, dict):
                return None

            return {
                "preferences": result.get("preferences", []),
                "facts": result.get("facts", []),
                "notes": result.get("notes", ""),
            }
        except json.JSONDecodeError:
            return None

    async def _save_memories(self, namespace: tuple, extraction: dict) -> None:
        """保存提取的记忆到 Store（异步）

        使用 StoreBackend 兼容格式，Agent 可通过 read_file("/memories/xxx") 读取。
        """
        timestamp = datetime.now().isoformat()

        # 保存偏好到 preferences.txt
        preferences = extraction.get("preferences", [])
        if preferences:
            # 格式化为 Markdown 文本
            content_lines = ["# 用户偏好", ""]
            for pref in preferences:
                key = pref.get("key", "未知")
                value = pref.get("value", "")
                content_lines.append(f"- **{key}**: {value}")

            await self._write_memory_file(
                namespace, "preferences.txt", content_lines, timestamp
            )

        # 保存事实到 facts/general.txt
        facts = extraction.get("facts", [])
        if facts:
            content_lines = ["# 用户相关事实", ""]
            for fact in facts:
                key = fact.get("key", "未知")
                value = fact.get("value", "")
                content_lines.append(f"- **{key}**: {value}")

            await self._write_memory_file(
                namespace, "facts/general.txt", content_lines, timestamp
            )

        # 保存备注到 notes.txt
        notes = extraction.get("notes", "")
        if notes:
            content_lines = ["# 备注", "", notes]
            await self._write_memory_file(
                namespace, "notes.txt", content_lines, timestamp
            )

    async def _write_memory_file(
        self,
        namespace: tuple,
        file_path: str,
        content_lines: list[str],
        timestamp: str
    ) -> None:
        """写入单个记忆文件（StoreBackend 格式）"""
        # StoreBackend 格式: content 是列表，包含 created_at/modified_at
        store_value = {
            "content": content_lines,
            "created_at": timestamp,
            "modified_at": timestamp,
        }
        await self.store.aput(namespace, file_path, store_value)
        logger.debug(f"[MEMORY] Saved {file_path}")