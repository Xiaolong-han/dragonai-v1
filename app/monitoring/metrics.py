"""Prometheus 指标定义

提供 LLM 调用、工具调用、SSE 连接等核心指标的收集能力。
所有指标使用 prometheus_client 库，支持 /metrics 端点暴露。

使用方式:
    from app.monitoring import record_llm_call, record_tool_call

    # 记录 LLM 调用
    record_llm_call(model="glm-5", status="success", latency_ms=2300,
                    input_tokens=100, output_tokens=50)

    # 记录工具调用
    record_tool_call(tool="web_search", status="success")
"""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from prometheus_client import REGISTRY, Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


# ============ 指标定义 ============

# LLM 调用次数
LLM_CALLS = Counter(
    'llm_calls_total',
    'LLM调用总次数',
    ['model', 'status'],
    registry=REGISTRY
)

# LLM Token 消耗
LLM_TOKENS = Counter(
    'llm_tokens_total',
    'LLM Token消耗总数',
    ['model', 'type'],  # label values: input/output
    registry=REGISTRY
)

# LLM 响应延迟 (秒)
LLM_LATENCY = Histogram(
    'llm_latency_seconds',
    'LLM响应延迟分布',
    ['model'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
    registry=REGISTRY
)

# 工具调用次数
TOOL_CALLS = Counter(
    'tool_calls_total',
    '工具调用总次数',
    ['tool', 'status'],
    registry=REGISTRY
)

# 工具执行延迟 (秒)
TOOL_LATENCY = Histogram(
    'tool_latency_seconds',
    '工具执行延迟分布',
    ['tool'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
    registry=REGISTRY
)

# 活跃 SSE 连接数
SSE_CONNECTIONS = Gauge(
    'sse_connections_active',
    '当前活跃的SSE连接数',
    registry=REGISTRY
)

# 活跃对话数
ACTIVE_CONVERSATIONS = Gauge(
    'active_conversations',
    '当前活跃的对话数',
    registry=REGISTRY
)

# 缓存操作
CACHE_OPERATIONS = Counter(
    'cache_operations_total',
    '缓存操作次数',
    ['operation', 'result'],  # operation: get/set/delete, result: hit/miss/success/error
    registry=REGISTRY
)

# Agent 执行次数
AGENT_EXECUTIONS = Counter(
    'agent_executions_total',
    'Agent执行总次数',
    ['type', 'status'],  # agent type: expert/fast, status: success/error/timeout
    registry=REGISTRY
)

# Agent 执行延迟
AGENT_LATENCY = Histogram(
    'agent_latency_seconds',
    'Agent执行延迟分布',
    ['type'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
    registry=REGISTRY
)


# ============ 便捷函数 ============

def record_llm_call(
    model: str,
    status: str,
    latency_seconds: float | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
):
    """记录 LLM 调用

    Args:
        model: 模型名称
        status: 状态 (success/error/timeout)
        latency_seconds: 延迟秒数
        input_tokens: 输入 token 数
        output_tokens: 输出 token 数
    """
    LLM_CALLS.labels(model=model, status=status).inc()

    if latency_seconds is not None:
        LLM_LATENCY.labels(model=model).observe(latency_seconds)

    if input_tokens is not None:
        LLM_TOKENS.labels(model=model, type='input').inc(input_tokens)

    if output_tokens is not None:
        LLM_TOKENS.labels(model=model, type='output').inc(output_tokens)


def record_tool_call(
    tool: str,
    status: str,
    latency_seconds: float | None = None,
):
    """记录工具调用

    Args:
        tool: 工具名称
        status: 状态 (success/error)
        latency_seconds: 延迟秒数
    """
    TOOL_CALLS.labels(tool=tool, status=status).inc()

    if latency_seconds is not None:
        TOOL_LATENCY.labels(tool=tool).observe(latency_seconds)


def record_cache_operation(operation: str, result: str):
    """记录缓存操作

    Args:
        operation: 操作类型 (get/set/delete)
        result: 结果 (hit/miss/success/error)
    """
    CACHE_OPERATIONS.labels(operation=operation, result=result).inc()


def record_agent_execution(
    agent_type: str,
    status: str,
    latency_seconds: float | None = None,
):
    """记录 Agent 执行

    Args:
        agent_type: Agent 类型 (expert/fast)
        status: 状态 (success/error/timeout)
        latency_seconds: 延迟秒数
    """
    AGENT_EXECUTIONS.labels(type=agent_type, status=status).inc()

    if latency_seconds is not None:
        AGENT_LATENCY.labels(type=agent_type).observe(latency_seconds)


# ============ 装饰器 ============

def track_llm_call(model_name: str):
    """LLM 调用追踪装饰器

    使用方式:
        @track_llm_call("glm-5")
        async def my_llm_function(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                latency = time.time() - start
                record_llm_call(model=model_name, status="success", latency_seconds=latency)
                return result
            except Exception:
                latency = time.time() - start
                record_llm_call(model=model_name, status="error", latency_seconds=latency)
                raise
        return wrapper
    return decorator


def track_tool_call(tool_name: str):
    """工具调用追踪装饰器

    使用方式:
        @track_tool_call("web_search")
        async def my_tool(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                latency = time.time() - start
                record_tool_call(tool=tool_name, status="success", latency_seconds=latency)
                return result
            except Exception:
                latency = time.time() - start
                record_tool_call(tool=tool_name, status="error", latency_seconds=latency)
                raise
        return wrapper
    return decorator
