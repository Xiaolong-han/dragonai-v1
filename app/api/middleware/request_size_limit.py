"""请求体大小限制中间件"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.schemas.response import ResponseBuilder

logger = logging.getLogger(__name__)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """请求体大小限制中间件

    阻止过大的请求体，防止资源耗尽
    """

    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.max_request_size:
                max_mb = settings.max_request_size // (1024 * 1024)
                logger.warning(
                    "Request payload too large",
                    extra={"extra_data": {
                        "content_length": content_length,
                        "max_size": settings.max_request_size,
                        "path": request.url.path
                    }}
                )
                return JSONResponse(
                    status_code=413,
                    content=ResponseBuilder.error(
                        code=1000,  # BAD_REQUEST 类
                        message=f"请求体过大，最大 {max_mb}MB"
                    )
                )
        return await call_next(request)
