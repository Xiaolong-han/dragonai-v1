"""请求追踪中间件测试"""

import pytest
from app.api.middleware.tracing import RequestTracingMiddleware, get_request_id, request_id_var


class TestTracing:
    def test_request_id_var_default(self):
        assert request_id_var.get() == ""
    
    def test_get_request_id(self):
        request_id_var.set("test-id-123")
        assert get_request_id() == "test-id-123"
        request_id_var.set("")
    
    @pytest.mark.asyncio
    async def test_middleware_generates_request_id(self, mock_request):
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
        middleware = RequestTracingMiddleware(None)
        mock_request.headers = {"X-Request-ID": "existing-id-456"}
        
        async def call_next(request):
            return type('Response', (), {'headers': {}, 'status_code': 200})()
        
        response = await middleware.dispatch(mock_request, call_next)
        
        assert response.headers["X-Request-ID"] == "existing-id-456"
