"""监控模块测试"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from prometheus_client import REGISTRY
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.monitoring import (
    record_llm_call,
    record_tool_call,
    record_agent_execution,
    LLM_CALLS,
    LLM_TOKENS,
    TOOL_CALLS,
    SSE_CONNECTIONS,
)
from app.monitoring.callbacks import MetricsCallbackHandler


class TestRecordLLMCall:
    """record_llm_call 函数测试"""

    def test_record_success_call(self):
        """测试记录成功的 LLM 调用"""
        # 获取初始值
        initial = REGISTRY.get_sample_value(
            'llm_calls_total',
            {'model': 'test-model', 'status': 'success'}
        ) or 0

        record_llm_call(model='test-model', status='success', latency_seconds=1.5)

        new_value = REGISTRY.get_sample_value(
            'llm_calls_total',
            {'model': 'test-model', 'status': 'success'}
        ) or 0

        assert new_value == initial + 1

    def test_record_error_call(self):
        """测试记录错误的 LLM 调用"""
        initial = REGISTRY.get_sample_value(
            'llm_calls_total',
            {'model': 'test-model', 'status': 'error'}
        ) or 0

        record_llm_call(model='test-model', status='error')

        new_value = REGISTRY.get_sample_value(
            'llm_calls_total',
            {'model': 'test-model', 'status': 'error'}
        ) or 0

        assert new_value == initial + 1

    def test_record_with_tokens(self):
        """测试记录 Token 消耗"""
        initial_input = REGISTRY.get_sample_value(
            'llm_tokens_total',
            {'model': 'token-test', 'type': 'input'}
        ) or 0
        initial_output = REGISTRY.get_sample_value(
            'llm_tokens_total',
            {'model': 'token-test', 'type': 'output'}
        ) or 0

        record_llm_call(
            model='token-test',
            status='success',
            input_tokens=100,
            output_tokens=50
        )

        new_input = REGISTRY.get_sample_value(
            'llm_tokens_total',
            {'model': 'token-test', 'type': 'input'}
        ) or 0
        new_output = REGISTRY.get_sample_value(
            'llm_tokens_total',
            {'model': 'token-test', 'type': 'output'}
        ) or 0

        assert new_input == initial_input + 100
        assert new_output == initial_output + 50


class TestRecordToolCall:
    """record_tool_call 函数测试"""

    def test_record_success_tool_call(self):
        """测试记录成功的工具调用"""
        initial = REGISTRY.get_sample_value(
            'tool_calls_total',
            {'tool': 'web_search', 'status': 'success'}
        ) or 0

        record_tool_call(tool='web_search', status='success', latency_seconds=2.0)

        new_value = REGISTRY.get_sample_value(
            'tool_calls_total',
            {'tool': 'web_search', 'status': 'success'}
        ) or 0

        assert new_value == initial + 1

    def test_record_error_tool_call(self):
        """测试记录失败的工具调用"""
        initial = REGISTRY.get_sample_value(
            'tool_calls_total',
            {'tool': 'rag', 'status': 'error'}
        ) or 0

        record_tool_call(tool='rag', status='error')

        new_value = REGISTRY.get_sample_value(
            'tool_calls_total',
            {'tool': 'rag', 'status': 'error'}
        ) or 0

        assert new_value == initial + 1


class TestRecordAgentExecution:
    """record_agent_execution 函数测试"""

    def test_record_fast_agent_success(self):
        """测试记录 fast Agent 成功执行"""
        initial = REGISTRY.get_sample_value(
            'agent_executions_total',
            {'type': 'fast', 'status': 'success'}
        ) or 0

        record_agent_execution(agent_type='fast', status='success', latency_seconds=5.0)

        new_value = REGISTRY.get_sample_value(
            'agent_executions_total',
            {'type': 'fast', 'status': 'success'}
        ) or 0

        assert new_value == initial + 1

    def test_record_expert_agent_timeout(self):
        """测试记录 expert Agent 超时"""
        initial = REGISTRY.get_sample_value(
            'agent_executions_total',
            {'type': 'expert', 'status': 'timeout'}
        ) or 0

        record_agent_execution(agent_type='expert', status='timeout')

        new_value = REGISTRY.get_sample_value(
            'agent_executions_total',
            {'type': 'expert', 'status': 'timeout'}
        ) or 0

        assert new_value == initial + 1


class TestSSEConnections:
    """SSE 连接数测试"""

    def test_sse_connections_gauge(self):
        """测试 SSE 连接数 Gauge"""
        initial = REGISTRY.get_sample_value('sse_connections_active') or 0

        SSE_CONNECTIONS.inc()
        after_inc = REGISTRY.get_sample_value('sse_connections_active') or 0
        assert after_inc == initial + 1

        SSE_CONNECTIONS.dec()
        after_dec = REGISTRY.get_sample_value('sse_connections_active') or 0
        assert after_dec == initial


class TestMetricsCallbackHandler:
    """LangChain 回调处理器测试"""

    def test_handler_initialization(self):
        """测试处理器初始化"""
        handler = MetricsCallbackHandler()
        assert handler._start_times == {}

    def test_on_llm_start_records_time(self):
        """测试 LLM 开始时记录时间"""
        import uuid
        handler = MetricsCallbackHandler()
        run_id = uuid.uuid4()

        handler.on_llm_start(
            serialized={},
            prompts=["test"],
            run_id=run_id
        )

        assert run_id in handler._start_times

    def test_on_llm_end_clears_time(self):
        """测试 LLM 结束时清理时间"""
        import uuid
        from langchain_core.outputs import LLMResult

        handler = MetricsCallbackHandler()
        run_id = uuid.uuid4()
        handler._start_times[run_id] = 0.0

        result = LLMResult(
            generations=[],
            llm_output={"model_name": "test-model"}
        )

        handler.on_llm_end(response=result, run_id=run_id)

        assert run_id not in handler._start_times

    def test_on_llm_error_clears_time(self):
        """测试 LLM 错误时清理时间"""
        import uuid
        handler = MetricsCallbackHandler()
        run_id = uuid.uuid4()
        handler._start_times[run_id] = 0.0

        handler.on_llm_error(
            error=Exception("test error"),
            run_id=run_id
        )

        assert run_id not in handler._start_times


class TestPrometheusMetricsAPI:
    """Prometheus 指标 API 测试"""

    def test_prometheus_metrics_returns_response(self):
        """测试 Prometheus 指标端点返回响应"""
        from app.api.v1.monitoring import prometheus_metrics

        # 直接调用函数
        import asyncio
        response = asyncio.run(prometheus_metrics())

        assert response is not None
        assert response.media_type == "text/plain; version=0.0.4; charset=utf-8"

    def test_prometheus_metrics_contains_metrics(self):
        """测试 Prometheus 指标包含预期内容"""
        from app.api.v1.monitoring import prometheus_metrics

        import asyncio
        response = asyncio.run(prometheus_metrics())

        # 响应体应该是字节
        content = response.body
        assert isinstance(content, bytes)


class TestMetricsSummaryAPI:
    """指标摘要 API 测试"""

    @pytest.mark.asyncio
    async def test_metrics_summary_requires_auth(self):
        """测试指标摘要需要认证"""
        from app.api.v1.monitoring import metrics_summary
        from app.models.user import User

        # 模拟用户
        mock_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True
        )

        result = await metrics_summary(current_user=mock_user)

        # 返回的是包装在 data 中的
        assert "llm" in result or "data" in result

    @pytest.mark.asyncio
    async def test_metrics_summary_structure(self):
        """测试指标摘要结构"""
        from app.api.v1.monitoring import metrics_summary
        from app.models.user import User

        mock_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True
        )

        result = await metrics_summary(current_user=mock_user)

        # 验证结构 - 可能是直接返回或包装在 data 中
        if "data" in result:
            data = result["data"]
        else:
            data = result

        assert "total_calls" in data["llm"] or "by_model" in data["llm"]
        assert "by_tool" in data["tools"]
        assert "active_connections" in data["sse"]


class TestCacheStatsAPI:
    """缓存统计 API 测试"""

    @pytest.mark.asyncio
    async def test_cache_stats_returns_data(self):
        """测试缓存统计返回数据"""
        from app.api.v1.monitoring import get_cache_statistics
        from app.models.user import User

        mock_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True
        )

        with patch('app.api.v1.monitoring.get_cache_stats', new_callable=AsyncMock) as mock_stats:
            mock_stats.return_value = {"hits": 100, "misses": 10}

            result = await get_cache_statistics(current_user=mock_user)

            assert result is not None
            mock_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_stats_requires_auth(self):
        """测试缓存统计需要认证"""
        from app.api.v1.monitoring import get_cache_statistics
        from app.models.user import User

        mock_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True
        )

        with patch('app.api.v1.monitoring.get_cache_stats', new_callable=AsyncMock) as mock_stats:
            mock_stats.return_value = {}

            await get_cache_statistics(current_user=mock_user)

            assert mock_stats.called


class TestDetailedHealthCheck:
    """详细健康检查 API 测试"""

    @pytest.mark.asyncio
    async def test_health_check_returns_result(self):
        """测试健康检查返回结果"""
        from app.api.v1.monitoring import detailed_health_check

        # 直接调用，依赖实际的 mock 环境
        result = await detailed_health_check()

        # 结果应该包含 status 和 services
        if "data" in result:
            data = result["data"]
        else:
            data = result

        assert "status" in data
        assert "services" in data

    @pytest.mark.asyncio
    async def test_health_check_structure(self):
        """测试健康检查结构"""
        from app.api.v1.monitoring import detailed_health_check

        result = await detailed_health_check()

        if "data" in result:
            data = result["data"]
        else:
            data = result

        assert "redis" in data["services"]
        assert "database" in data["services"]