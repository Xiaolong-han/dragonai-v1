"""API 异常处理器

提供统一的异常处理，将所有异常转换为标准响应格式：
{code: number, message: string, data: object | null}
"""

import logging
import traceback

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from slowapi.errors import RateLimitExceeded

from app.core.exceptions import DragonAIException
from app.schemas.response import ErrorCode, ResponseBuilder

logger = logging.getLogger(__name__)


async def dragonai_exception_handler(request: Request, exc: DragonAIException) -> JSONResponse:
    """DragonAI 统一异常处理"""
    log_context = {
        "path": request.url.path,
        "method": request.method,
        "code": exc.code,
        "message": exc.message,
    }
    if exc.details:
        log_context["details"] = exc.details

    logger.warning(f"[API ERROR] {exc.message}", extra={"extra_data": log_context})

    response_data = exc.to_dict()
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """请求验证异常处理"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(
        f"[VALIDATION ERROR] {len(errors)} validation errors",
        extra={"extra_data": {"path": request.url.path, "errors": errors}}
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ResponseBuilder.validation_error("请求参数验证失败", errors)
    )


async def pydantic_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Pydantic 验证异常处理"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(
        f"[PYDANTIC ERROR] {len(errors)} validation errors",
        extra={"extra_data": {"path": request.url.path, "errors": errors}}
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ResponseBuilder.validation_error("数据验证失败", errors)
    )


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """限流异常处理"""
    logger.warning(
        "[RATE LIMIT] Request rate limited",
        extra={"extra_data": {
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else "unknown"
        }}
    )

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=ResponseBuilder.rate_limited()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理 - 捕获所有未处理的异常"""
    error_trace = traceback.format_exc()

    logger.error(
        f"[UNHANDLED ERROR] {type(exc).__name__}: {exc!s}",
        extra={"extra_data": {
            "path": request.url.path,
            "method": request.method,
            "traceback": error_trace
        }}
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ResponseBuilder.error(
            code=ErrorCode.INTERNAL_ERROR,
            message="服务器内部错误，请稍后重试"
        )
    )


__all__ = [
    "dragonai_exception_handler",
    "generic_exception_handler",
    "pydantic_validation_handler",
    "rate_limit_exceeded_handler",
    "validation_exception_handler",
]
