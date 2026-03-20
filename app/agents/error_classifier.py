import asyncio
from enum import Enum


class AgentErrorType(Enum):
    """Agent 错误类型枚举"""
    TOOL_CALL_INVALID = "tool_call_invalid"
    TOOL_NOT_FOUND = "tool_not_found"
    TIMEOUT = "timeout"
    STATE_ERROR = "state_error"
    RATE_LIMIT = "rate_limit"
    MODEL_ERROR = "model_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


class AgentErrorClassifier:
    """Agent 错误分类器"""

    TOOL_CALL_PATTERNS = [
        "tool_calls",
        "must be followed by tool messages",
    ]

    TOOL_NOT_FOUND_PATTERNS = [
        "tool not found",
        "unknown tool",
        "invalid tool name",
    ]

    STATE_ERROR_PATTERNS = [
        "checkpointer",
        "thread_id",
        "conversation state",
    ]

    RATE_LIMIT_PATTERNS = [
        "rate limit",
        "too many requests",
        "quota exceeded",
        "requests per minute",
    ]

    MODEL_ERROR_PATTERNS = [
        "model not found",
        "invalid model",
        "model overloaded",
        "context length exceeded",
        "token limit",
    ]

    NETWORK_ERROR_PATTERNS = [
        "connection refused",
        "connection timeout",
        "network error",
        "dns error",
        "socket error",
    ]

    @classmethod
    def classify(cls, error: Exception) -> AgentErrorType:
        """分类错误类型

        Args:
            error: 捕获的异常

        Returns:
            AgentErrorType 枚举值
        """
        if isinstance(error, asyncio.TimeoutError):
            return AgentErrorType.TIMEOUT

        error_msg = str(error).lower()

        if any(pattern in error_msg for pattern in cls.RATE_LIMIT_PATTERNS):
            return AgentErrorType.RATE_LIMIT

        if any(pattern in error_msg for pattern in cls.MODEL_ERROR_PATTERNS):
            return AgentErrorType.MODEL_ERROR

        if any(pattern in error_msg for pattern in cls.NETWORK_ERROR_PATTERNS):
            return AgentErrorType.NETWORK_ERROR

        if all(pattern in error_msg for pattern in cls.TOOL_CALL_PATTERNS):
            return AgentErrorType.TOOL_CALL_INVALID

        if any(pattern in error_msg for pattern in cls.TOOL_NOT_FOUND_PATTERNS):
            return AgentErrorType.TOOL_NOT_FOUND

        if any(pattern in error_msg for pattern in cls.STATE_ERROR_PATTERNS):
            return AgentErrorType.STATE_ERROR

        return AgentErrorType.UNKNOWN

    @classmethod
    def is_retryable(cls, error_type: AgentErrorType) -> bool:
        """判断错误是否可重试"""
        return error_type in (
            AgentErrorType.TOOL_CALL_INVALID,
            AgentErrorType.NETWORK_ERROR,
            AgentErrorType.RATE_LIMIT,
        )

    @classmethod
    def get_user_message(cls, error_type: AgentErrorType, is_production: bool = True) -> str:
        """获取用户友好的错误消息

        Args:
            error_type: 错误类型
            is_production: 是否生产环境（生产环境隐藏详细信息）
        """
        messages = {
            AgentErrorType.TIMEOUT: "请求处理超时，请稍后重试",
            AgentErrorType.TOOL_CALL_INVALID: "工具调用异常，正在重试..." if not is_production else "处理请求时遇到问题，请重试",
            AgentErrorType.TOOL_NOT_FOUND: "工具调用失败，请重试",
            AgentErrorType.STATE_ERROR: "会话状态异常，请刷新页面重试",
            AgentErrorType.RATE_LIMIT: "请求过于频繁，请稍后再试",
            AgentErrorType.MODEL_ERROR: "模型服务暂时不可用，请稍后重试",
            AgentErrorType.NETWORK_ERROR: "网络连接异常，请检查网络后重试",
            AgentErrorType.UNKNOWN: "处理请求时出错，请稍后重试",
        }
        return messages.get(error_type, "未知错误")
