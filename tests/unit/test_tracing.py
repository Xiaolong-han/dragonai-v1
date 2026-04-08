"""请求追踪中间件测试"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.api.middleware.tracing import RequestTracingMiddleware, get_request_id


class TestTracing:
    def test_get_request_id_returns_string(self):
        """测试 get_request_id 返回字符串"""
        result = get_request_id()
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_middleware_generates_request_id(self, mock_request):
        """测试中间件生成请求 ID"""
        middleware = RequestTracingMiddleware(None)

        call_count = 0

        async def call_next(request):
            nonlocal call_count
            call_count += 1
            return type('Response', (), {'headers': {}, 'status_code': 200})()

        response = await middleware.dispatch(mock_request, call_next)

        assert call_count == 1
        assert "X-Request-ID" in response.headers

    @pytest.mark.asyncio
    async def test_middleware_uses_existing_request_id(self, mock_request):
        """测试中间件使用现有请求 ID"""
        middleware = RequestTracingMiddleware(None)
        mock_request.headers = {"X-Request-ID": "existing-id-456"}

        async def call_next(request):
            return type('Response', (), {'headers': {}, 'status_code': 200})()

        response = await middleware.dispatch(mock_request, call_next)

        assert response.headers["X-Request-ID"] == "existing-id-456"

    @pytest.mark.asyncio
    async def test_middleware_sets_request_state(self, mock_request):
        """测试中间件设置请求状态"""
        middleware = RequestTracingMiddleware(None)

        async def call_next(request):
            return type('Response', (), {'headers': {}, 'status_code': 200})()

        await middleware.dispatch(mock_request, call_next)

        assert hasattr(mock_request.state, 'request_id')

    @pytest.mark.asyncio
    async def test_middleware_logs_request(self, mock_request):
        """测试中间件记录请求日志"""
        middleware = RequestTracingMiddleware(None)

        async def call_next(request):
            return type('Response', (), {'headers': {}, 'status_code': 200})()

        with patch('app.api.middleware.tracing.logger') as mock_logger:
            mock_logger.debug = MagicMock()
            await middleware.dispatch(mock_request, call_next)

            # 验证日志被调用
            assert mock_logger.debug.called