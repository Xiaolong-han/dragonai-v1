"""API 异常处理器"""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.exceptions import DragonAIException
from app.api.middleware.rate_limit import rate_limit_exceeded_handler


async def dragonai_exception_handler(request: Request, exc: DragonAIException):
    """统一异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


__all__ = [
    "dragonai_exception_handler",
    "rate_limit_exceeded_handler",
]
