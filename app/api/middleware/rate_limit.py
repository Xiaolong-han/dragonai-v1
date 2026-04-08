"""请求限流中间件"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.schemas.response import ResponseBuilder

logger = logging.getLogger(__name__)


def get_client_identifier(request: Request) -> str:
    """获取客户端标识符（用于限流）

    优先使用认证用户ID，其次使用 X-Forwarded-For，最后使用远程地址
    """
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    return f"ip:{get_remote_address(request)}"


def get_storage_uri() -> str:
    """获取限流存储URI

    生产环境使用 Redis 存储，支持多实例部署
    开发环境可使用内存存储
    """
    if settings.rate_limit_storage == "redis":
        return settings.redis_url
    return "memory://"


limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[settings.rate_limit_default],
    storage_uri=get_storage_uri(),
    storage_options={"socket_connect_timeout": 5} if settings.rate_limit_storage == "redis" else {},
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """自定义限流响应"""
    logger.warning(
        "Request rate limited",
        extra={"extra_data": {
            "client": get_client_identifier(request),
            "path": request.url.path,
            "method": request.method
        }}
    )
    return JSONResponse(
        status_code=429,
        content=ResponseBuilder.rate_limited()
    )


CHAT_RATE_LIMIT = settings.rate_limit_chat
AUTH_RATE_LIMIT = settings.rate_limit_auth
DEFAULT_RATE_LIMIT = settings.rate_limit_default
