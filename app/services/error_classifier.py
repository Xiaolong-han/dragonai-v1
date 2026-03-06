import asyncio
from enum import Enum


class AgentErrorType(Enum):
    """Agent 错误类型枚举"""
    TOOL_CALL_INVALID = "tool_call_invalid"
    TIMEOUT = "timeout"
    STATE_ERROR = "state_error"
    UNKNOWN = "unknown"


class AgentErrorClassifier:
    """Agent 错误分类器"""
    
    TOOL_CALL_PATTERNS = [
        "tool_calls",
        "must be followed by tool messages",
    ]
    
    STATE_ERROR_PATTERNS = [
        "checkpointer",
        "thread_id",
        "conversation state",
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
        
        if all(pattern in error_msg for pattern in cls.TOOL_CALL_PATTERNS):
            return AgentErrorType.TOOL_CALL_INVALID
        
        if any(pattern in error_msg for pattern in cls.STATE_ERROR_PATTERNS):
            return AgentErrorType.STATE_ERROR
        
        return AgentErrorType.UNKNOWN
    
    @classmethod
    def is_retryable(cls, error_type: AgentErrorType) -> bool:
        """判断错误是否可重试"""
        return error_type == AgentErrorType.TOOL_CALL_INVALID
    
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
            AgentErrorType.STATE_ERROR: "会话状态异常，请刷新页面重试",
            AgentErrorType.UNKNOWN: "处理请求时出错，请稍后重试",
        }
        return messages.get(error_type, "未知错误")
