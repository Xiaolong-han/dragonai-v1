import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.monitoring import record_tool_call
from app.schemas.message import MessageCreate
from app.services.repositories.message_repository import MessageRepository
from app.services.stream.stream_processor import StreamProcessor

logger = logging.getLogger(__name__)


class SSEEmitter:
    """SSE 输出器，负责生成 SSE 格式的流式响应"""

    def __init__(
        self,
        stream_processor: StreamProcessor | None = None,
        message_repository: MessageRepository | None = None
    ):
        self.stream_processor = stream_processor or StreamProcessor()
        self.message_repository = message_repository or MessageRepository()

    @staticmethod
    def make_sse_event(event_type: str, content: str = "") -> str:
        """生成 SSE 格式的事件"""
        return f"data: {json.dumps({'type': event_type, 'data': {'content': content}}, ensure_ascii=False)}\n\n"

    async def generate_sse_stream(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        content: str,
        is_expert: bool = False,
        enable_thinking: bool = False,
        attachments: list[str] | None = None
    ) -> AsyncGenerator[str, None]:
        """生成 SSE 格式的流式响应

        封装了完整的 SSE 流式响应逻辑，包括：
        - 调用 StreamProcessor 获取原始流
        - 转换为 SSE 格式
        - 累积响应并保存到数据库
        """
        full_response = ""
        thinking_content = ""
        chunk_count = 0
        tool_calls = []

        try:
            async for event in self.stream_processor.process_message(
                conversation_id=conversation_id,
                content=content,
                attachments=attachments,
                is_expert=is_expert,
                enable_thinking=enable_thinking,
                user_id=user_id
            ):
                if isinstance(event, dict):
                    event_type = event.get("type")
                    logger.debug(f"[SSE] Processing event: type={event_type}")

                    if event_type == "thinking":
                        thinking_chunk = event.get("data", {}).get("content", "")
                        thinking_content += thinking_chunk
                        logger.debug(f"[SSE] Sending thinking chunk: {len(thinking_chunk)} chars")
                        yield self.make_sse_event("thinking", thinking_chunk)

                    elif event_type == "thinking_end":
                        logger.debug("[SSE] Sending thinking_end")
                        yield self.make_sse_event("thinking_end")

                    elif event_type == "token":
                        token_content = event.get("data", {}).get("content", "")
                        if token_content:
                            full_response += token_content
                            chunk_count += 1
                            logger.debug(f"[SSE] Sending chunk {chunk_count}: {len(token_content)} chars")
                            yield self.make_sse_event("content", token_content)

                    elif event_type == "tool_call":
                        calls = event.get("data", {}).get("calls", [])
                        for call in calls:
                            tool_id = call.get("id", "")
                            tool_name = call.get("name", "unknown")
                            if tool_id:
                                placeholder = f"[TOOL_CALL:{tool_id}]"
                                full_response += placeholder
                                yield self.make_sse_event("content", placeholder)
                            # 记录工具调用开始时间
                            tool_calls.append({
                                "id": call.get("id", ""),
                                "name": tool_name,
                                "status": "pending",
                                "_start_time": time.time()  # 内部使用，用于计算延迟
                            })
                        yield self.make_sse_event("tool_call", json.dumps({"calls": calls}, ensure_ascii=False))

                    elif event_type == "tool_result":
                        data = event.get("data", {})
                        tool_call_id = data.get("tool_call_id")
                        for tc in tool_calls:
                            if tc.get("id") == tool_call_id:
                                # 计算工具执行延迟
                                start_time = tc.pop("_start_time", None)
                                latency = time.time() - start_time if start_time else None

                                # 判断状态
                                status = "success" if not data.get("error") else "error"
                                tc["status"] = status
                                tc["summary"] = data.get("summary", "")
                                tc["links"] = data.get("links", [])
                                tc["details"] = data.get("details", "")

                                # 记录指标
                                record_tool_call(
                                    tool=tc.get("name", "unknown"),
                                    status=status,
                                    latency_seconds=latency
                                )
                                break
                        yield self.make_sse_event("tool_result", json.dumps(data, ensure_ascii=False))

                    elif event_type == "error":
                        yield self.make_sse_event("error", event.get("data", {}).get("message", ""))

                else:
                    full_response += event
                    chunk_count += 1
                    logger.debug(f"[SSE] Sending chunk {chunk_count}: {len(event)} chars")
                    yield self.make_sse_event("content", event)
                # 移除不必要的 sleep，流式处理本身就是异步的

            logger.info(f"[SSE] Stream complete, total chunks: {chunk_count}, response length: {len(full_response)}")

            if thinking_content:
                logger.debug(f"[SSE] Sending thinking_end, total thinking: {len(thinking_content)} chars")
                yield self.make_sse_event("thinking_end")

            extra_data = {"model": "expert" if is_expert else "fast"}
            if thinking_content:
                extra_data["thinking_content"] = thinking_content
            if tool_calls:
                extra_data["tool_calls"] = tool_calls

            # 使用 try/finally 确保即使保存失败也能通知客户端
            # 但需要在 yield "data: [DONE]\n\n" 之前保存，以避免数据丢失
            save_success = True
            save_error = None
            try:
                await self.message_repository.create_message(
                    db,
                    conversation_id=conversation_id,
                    message_create=MessageCreate(
                        role="assistant",
                        content=full_response,
                        extra_data=extra_data
                    ),
                    user_id=user_id
                )
            except Exception as save_err:
                save_success = False
                save_error = save_err
                logger.error(f"[SSE] Failed to save message to DB: {save_err}", exc_info=True)

            yield "data: [DONE]\n\n"

            # 如果保存失败，记录错误但不影响客户端
            if not save_success:
                logger.warning(f"[SSE] Message not persisted to DB, conversation_id={conversation_id}, "
                             f"response_length={len(full_response)}, error={save_error}")
        except asyncio.CancelledError:
            logger.info(f"[SSE] Request cancelled, conversation_id={conversation_id}")
            raise
