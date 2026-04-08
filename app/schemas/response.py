"""统一 API 响应模型

提供标准化的 API 响应格式：
- 成功响应：{code: 0, message: "success", data: {...}}
- 错误响应：{code: ERROR_CODE, message: "错误信息", data: null}

错误码规范：
- 0: 成功
- 1xxx: 客户端错误 (4xx)
- 2xxx: 服务端错误 (5xx)
- 3xxx: 业务错误
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


# ==================== 错误码定义 ====================

class ErrorCode:
    """统一错误码定义

    错误码范围：
    - 0: 成功
    - 1000-1999: 客户端错误 (对应 HTTP 4xx)
    - 2000-2999: 服务端错误 (对应 HTTP 5xx)
    - 3000-3999: 业务逻辑错误
    """

    # 成功
    SUCCESS = 0

    # 客户端错误 (1xxx)
    BAD_REQUEST = 1000
    UNAUTHORIZED = 1001
    FORBIDDEN = 1003
    NOT_FOUND = 1004
    METHOD_NOT_ALLOWED = 1005
    VALIDATION_ERROR = 1022
    RATE_LIMIT_EXCEEDED = 1029

    # 服务端错误 (2xxx)
    INTERNAL_ERROR = 2000
    SERVICE_UNAVAILABLE = 2003
    EXTERNAL_SERVICE_ERROR = 2002
    GATEWAY_TIMEOUT = 2004

    # 业务错误 (3xxx)
    USER_NOT_FOUND = 3001
    USER_ALREADY_EXISTS = 3002
    CONVERSATION_NOT_FOUND = 3010
    MESSAGE_NOT_FOUND = 3011
    KNOWLEDGE_NOT_FOUND = 3020
    FILE_NOT_FOUND = 3030
    TOOL_NOT_FOUND = 3040

    # Agent 相关错误 (31xx)
    AGENT_ERROR = 3100
    AGENT_TIMEOUT = 3101
    TOOL_CALL_LIMIT = 3102
    LLM_ERROR = 3103


# HTTP 状态码到错误码的映射
HTTP_TO_ERROR_CODE: dict[int, int] = {
    400: ErrorCode.BAD_REQUEST,
    401: ErrorCode.UNAUTHORIZED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.METHOD_NOT_ALLOWED,
    422: ErrorCode.VALIDATION_ERROR,
    429: ErrorCode.RATE_LIMIT_EXCEEDED,
    500: ErrorCode.INTERNAL_ERROR,
    502: ErrorCode.EXTERNAL_SERVICE_ERROR,
    503: ErrorCode.SERVICE_UNAVAILABLE,
    504: ErrorCode.GATEWAY_TIMEOUT,
}


# ==================== 响应模型 ====================

class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应模型

    Attributes:
        code: 状态码，0 表示成功，非 0 表示错误
        message: 响应消息
        data: 响应数据
        request_id: 请求追踪 ID（可选）
    """
    code: int = ErrorCode.SUCCESS
    message: str = "success"
    data: T | None = None
    request_id: str | None = None

    class Config:
        populate_by_name = True


class PagedData(BaseModel, Generic[T]):
    """分页数据模型

    Attributes:
        items: 数据列表
        total: 总数量
        page: 当前页码
        page_size: 每页数量
    """
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20


# ==================== 响应构建器 ====================

class ResponseBuilder:
    """响应构建器

    提供便捷的响应构建方法
    """

    @staticmethod
    def success(data: Any = None, message: str = "success") -> dict:
        """构建成功响应"""
        return {
            "code": ErrorCode.SUCCESS,
            "message": message,
            "data": data
        }

    @staticmethod
    def error(
        code: int = ErrorCode.INTERNAL_ERROR,
        message: str = "Internal server error",
        data: Any = None
    ) -> dict:
        """构建错误响应"""
        return {
            "code": code,
            "message": message,
            "data": data
        }

    @staticmethod
    def not_found(resource: str = "Resource") -> dict:
        """构建资源未找到响应"""
        return ResponseBuilder.error(
            code=ErrorCode.NOT_FOUND,
            message=f"{resource} not found"
        )

    @staticmethod
    def unauthorized(message: str = "Unauthorized") -> dict:
        """构建未授权响应"""
        return ResponseBuilder.error(
            code=ErrorCode.UNAUTHORIZED,
            message=message
        )

    @staticmethod
    def forbidden(message: str = "Forbidden") -> dict:
        """构建禁止访问响应"""
        return ResponseBuilder.error(
            code=ErrorCode.FORBIDDEN,
            message=message
        )

    @staticmethod
    def bad_request(message: str = "Bad request") -> dict:
        """构建错误请求响应"""
        return ResponseBuilder.error(
            code=ErrorCode.BAD_REQUEST,
            message=message
        )

    @staticmethod
    def validation_error(message: str = "Validation error", details: Any = None) -> dict:
        """构建验证错误响应"""
        return ResponseBuilder.error(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            data=details
        )

    @staticmethod
    def rate_limited(retry_after: int | None = None) -> dict:
        """构建限流响应"""
        data = {"retry_after": retry_after} if retry_after else None
        return ResponseBuilder.error(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message="请求过于频繁，请稍后再试",
            data=data
        )

    @staticmethod
    def paged(items: list, total: int, page: int = 1, page_size: int = 20) -> dict:
        """构建分页响应"""
        return ResponseBuilder.success(
            data=PagedData(
                items=items,
                total=total,
                page=page,
                page_size=page_size
            ).model_dump()
        )


__all__ = [
    "HTTP_TO_ERROR_CODE",
    "ApiResponse",
    "ErrorCode",
    "PagedData",
    "ResponseBuilder",
]
