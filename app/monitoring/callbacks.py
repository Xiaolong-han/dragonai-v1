"""LangChain 回调处理器 - 用于监控 LLM 调用

提供自定义回调处理器，用于监控 ChatTongyi 等 LangChain 模型的调用。
"""

import logging
import time
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from app.monitoring.metrics import LLM_TOKENS, record_llm_call

logger = logging.getLogger(__name__)


class MetricsCallbackHandler(BaseCallbackHandler):
    """指标收集回调处理器

    用于收集 LLM 调用的指标，包括：
    - 调用次数
    - 响应延迟
    - Token 消耗
    - 错误统计

    使用方式:
        from app.monitoring.callbacks import MetricsCallbackHandler

        model = ChatTongyi(...)
        model.callbacks = [MetricsCallbackHandler()]
    """

    def __init__(self):
        self._start_times: dict[UUID, float] = {}

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """LLM 调用开始时记录时间"""
        self._start_times[run_id] = time.time()
        model_name = kwargs.get("invocation_params", {}).get("model_name", "unknown")
        logger.debug(f"[CALLBACK] LLM start: model={model_name}, run_id={run_id}")

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """LLM 调用结束时记录指标"""
        start_time = self._start_times.pop(run_id, None)
        latency = time.time() - start_time if start_time else 0

        # 获取模型名称
        model_name = "unknown"
        if response.llm_output and "model_name" in response.llm_output:
            model_name = response.llm_output["model_name"]
        elif kwargs.get("invocation_params"):
            model_name = kwargs["invocation_params"].get("model_name", "unknown")

        # 记录成功调用
        record_llm_call(model=model_name, status="success", latency_seconds=latency)

        # 记录 Token 消耗
        if response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})
            if token_usage:
                input_tokens = token_usage.get("prompt_tokens", 0) or token_usage.get("input_tokens", 0)
                output_tokens = token_usage.get("completion_tokens", 0) or token_usage.get("output_tokens", 0)
                if input_tokens:
                    LLM_TOKENS.labels(model=model_name, type="input").inc(input_tokens)
                if output_tokens:
                    LLM_TOKENS.labels(model=model_name, type="output").inc(output_tokens)

        logger.debug(f"[CALLBACK] LLM end: model={model_name}, latency={latency:.2f}s")

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """LLM 调用出错时记录错误"""
        start_time = self._start_times.pop(run_id, None)
        latency = time.time() - start_time if start_time else 0

        # 获取模型名称
        model_name = kwargs.get("invocation_params", {}).get("model_name", "unknown")

        # 记录错误调用
        record_llm_call(model=model_name, status="error", latency_seconds=latency)

        logger.error(f"[CALLBACK] LLM error: model={model_name}, error={error}")


# 全局单例
_metrics_callback_handler = MetricsCallbackHandler()


def get_metrics_callback_handler() -> MetricsCallbackHandler:
    """获取全局指标回调处理器"""
    return _metrics_callback_handler
