"""请求追踪中间件"""

import logging
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import set_request_id, set_user_id

logger = logging.getLogger(__name__)


def get_request_id() -> str:
    """获取当前请求的追踪 ID

    此函数保留以保持向后兼容
    """
    from app.core.logging_config import get_request_id as _get_request_id
    return _get_request_id() or ""


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """请求追踪中间件

    为每个请求生成唯一的追踪 ID，并添加到响应头和日志上下文中
    同时提取用户 ID 以支持日志追踪
    """

    async def dispatch(self, request: Request, call_next):
        # 生成或获取请求 ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # 设置请求 ID 到日志上下文
        set_request_id(request_id)

        # 保存到请求状态
        request.state.request_id = request_id

        # 执行请求
        response = await call_next(request)

        # 添加请求 ID 到响应头
        response.headers["X-Request-ID"] = request_id

        # 记录请求日志
        logger.debug(
            "Request completed",
            extra={"extra_data": {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "request_id": request_id
            }}
        )

        # 清除用户 ID（请求结束）
        set_user_id(None)

        return response
