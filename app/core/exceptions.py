"""统一异常定义模块

异常层次结构：
- DragonAIException: 基础异常类
  - NotFoundException: 资源未找到
  - UnauthorizedException: 未授权
  - ForbiddenException: 禁止访问
  - BadRequestException: 错误请求
  - ValidationException: 验证错误
  - ConflictException: 冲突错误
  - RateLimitException: 限流异常
  - ExternalServiceException: 外部服务错误
  - LLMException: LLM 服务错误
  - AgentTimeoutException: Agent 超时
  - ToolCallLimitException: 工具调用限制
  - AgentStateException: Agent 状态错误
"""

from typing import Any

from app.schemas.response import ErrorCode


class DragonAIException(Exception):
    """DragonAI 基础异常类

    所有自定义异常都应继承此类。

    Attributes:
        message: 错误消息
        code: 错误码 (来自 ErrorCode)
        status_code: HTTP 状态码
        details: 额外详情
    """

    def __init__(
        self,
        message: str,
        code: int = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: dict[str, Any] | None = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            result["data"] = self.details
        return result


class NotFoundException(DragonAIException):
    """资源未找到异常"""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: str | None = None,
        resource_id: Any | None = None,
        details: dict[str, Any] | None = None
    ):
        _details = details or {}
        if resource_type:
            _details["resource_type"] = resource_type
        if resource_id is not None:
            _details["resource_id"] = resource_id
        super().__init__(
            message=message,
            code=ErrorCode.NOT_FOUND,
            status_code=404,
            details=_details
        )


class UnauthorizedException(DragonAIException):
    """未授权异常"""

    def __init__(
        self,
        message: str = "Unauthorized",
        details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.UNAUTHORIZED,
            status_code=401,
            details=details
        )


class ForbiddenException(DragonAIException):
    """禁止访问异常"""

    def __init__(
        self,
        message: str = "Forbidden",
        details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.FORBIDDEN,
            status_code=403,
            details=details
        )


class BadRequestException(DragonAIException):
    """错误请求异常"""

    def __init__(
        self,
        message: str = "Bad request",
        details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.BAD_REQUEST,
            status_code=400,
            details=details
        )


class ValidationException(DragonAIException):
    """验证异常"""

    def __init__(
        self,
        message: str = "Validation error",
        errors: list | None = None,
        details: dict[str, Any] | None = None
    ):
        _details = details or {}
        if errors:
            _details["errors"] = errors
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details=_details
        )


class ConflictException(DragonAIException):
    """冲突异常 (如资源已存在)"""

    def __init__(
        self,
        message: str = "Resource conflict",
        details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.USER_ALREADY_EXISTS,
            status_code=409,
            details=details
        )


class RateLimitException(DragonAIException):
    """限流异常"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        details: dict[str, Any] | None = None
    ):
        _details = details or {}
        if retry_after:
            _details["retry_after"] = retry_after
        super().__init__(
            message=message,
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details=_details
        )


class ExternalServiceException(DragonAIException):
    """外部服务异常"""

    def __init__(
        self,
        message: str = "External service error",
        service_name: str | None = None,
        details: dict[str, Any] | None = None
    ):
        _details = details or {}
        if service_name:
            _details["service"] = service_name
        super().__init__(
            message=message,
            code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            status_code=502,
            details=_details
        )


class LLMException(DragonAIException):
    """LLM 服务异常"""

    def __init__(
        self,
        message: str = "LLM service error",
        model: str | None = None,
        details: dict[str, Any] | None = None
    ):
        _details = details or {}
        if model:
            _details["model"] = model
        super().__init__(
            message=message,
            code=ErrorCode.LLM_ERROR,
            status_code=502,
            details=_details
        )


class AgentTimeoutException(DragonAIException):
    """Agent 执行超时异常"""

    def __init__(
        self,
        message: str = "Agent execution timeout",
        timeout_seconds: int | None = None,
        details: dict[str, Any] | None = None
    ):
        _details = details or {}
        if timeout_seconds:
            _details["timeout_seconds"] = timeout_seconds
        super().__init__(
            message=message,
            code=ErrorCode.AGENT_TIMEOUT,
            status_code=504,
            details=_details
        )


class ToolCallLimitException(DragonAIException):
    """工具调用次数超限异常"""

    def __init__(
        self,
        message: str = "Tool call limit exceeded",
        limit: int | None = None,
        current: int | None = None,
        details: dict[str, Any] | None = None
    ):
        _details = details or {}
        if limit is not None:
            _details["limit"] = limit
        if current is not None:
            _details["current"] = current
        super().__init__(
            message=message,
            code=ErrorCode.TOOL_CALL_LIMIT,
            status_code=429,
            details=_details
        )


class AgentStateException(DragonAIException):
    """Agent 状态异常"""

    def __init__(
        self,
        message: str = "Agent state error",
        details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.AGENT_ERROR,
            status_code=500,
            details=details
        )


__all__ = [
    "AgentStateException",
    "AgentTimeoutException",
    "BadRequestException",
    "ConflictException",
    "DragonAIException",
    "ExternalServiceException",
    "ForbiddenException",
    "LLMException",
    "NotFoundException",
    "RateLimitException",
    "ToolCallLimitException",
    "UnauthorizedException",
    "ValidationException",
]
