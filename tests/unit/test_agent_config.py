"""Agent 配置测试"""

import pytest
from app.config import settings, AgentMiddlewareSettings


class TestAgentConfig:
    """Agent 配置测试"""

    def test_agent_tool_call_limit_exists(self):
        """测试工具调用限制配置存在"""
        assert hasattr(settings, "agent_tool_call_limit")
        assert settings.agent_tool_call_limit > 0
        assert settings.agent_tool_call_limit == 10

    def test_agent_timeout_exists(self):
        """测试 Agent 超时配置存在"""
        assert hasattr(settings, "agent_timeout")
        assert settings.agent_timeout > 0
        assert settings.agent_timeout == 120

    def test_agent_config_types(self):
        """测试配置类型正确"""
        assert isinstance(settings.agent_tool_call_limit, int)
        assert isinstance(settings.agent_timeout, int)

    def test_agent_config_reasonable_values(self):
        """测试配置值合理"""
        assert 1 <= settings.agent_tool_call_limit <= 50
        assert 10 <= settings.agent_timeout <= 600


class TestAgentMiddlewareSettings:
    """Agent 中间件配置测试"""

    def test_middleware_settings_exists(self):
        """测试中间件配置存在"""
        assert hasattr(settings, "agent_middleware")
        assert settings.agent_middleware is not None
        assert isinstance(settings.agent_middleware, AgentMiddlewareSettings)

    def test_middleware_enable_flags(self):
        """测试中间件启用/禁用开关"""
        mw = settings.agent_middleware
        assert isinstance(mw.enable_todo_list, bool)
        assert isinstance(mw.enable_tool_retry, bool)
        assert isinstance(mw.enable_model_fallback, bool)
        assert isinstance(mw.enable_filesystem, bool)
        assert isinstance(mw.enable_skills, bool)
        assert isinstance(mw.enable_summarization, bool)
        assert isinstance(mw.enable_tool_call_limit, bool)
        assert isinstance(mw.enable_model_call_limit, bool)

    def test_middleware_retry_params(self):
        """测试 ToolRetryMiddleware 参数"""
        mw = settings.agent_middleware
        assert mw.tool_retry_max_retries >= 0
        assert mw.tool_retry_backoff_factor > 0

    def test_filesystem_params(self):
        """测试 FilesystemMiddleware 参数"""
        mw = settings.agent_middleware
        assert mw.filesystem_tool_token_limit > 0

    def test_summarization_params(self):
        """测试 SummarizationMiddleware 参数"""
        mw = settings.agent_middleware
        assert mw.summarization_max_tokens > 0
        assert mw.summarization_messages_to_keep >= 2

    def test_model_call_limit_params(self):
        """测试 ModelCallLimitMiddleware 参数"""
        mw = settings.agent_middleware
        assert mw.model_call_limit > 0

    def test_default_middleware_all_enabled(self):
        """测试默认配置所有中间件启用"""
        mw = settings.agent_middleware
        assert mw.enable_todo_list is True
        assert mw.enable_tool_retry is True
        assert mw.enable_model_fallback is True
        assert mw.enable_filesystem is True
        assert mw.enable_skills is True
        assert mw.enable_summarization is True
        assert mw.enable_tool_call_limit is True
        assert mw.enable_model_call_limit is True

    def test_retry_params_reasonable_values(self):
        """测试重试参数值合理"""
        mw = settings.agent_middleware
        assert mw.tool_retry_max_retries <= 5
        assert 0.1 <= mw.tool_retry_backoff_factor <= 10.0

    def test_summarization_reasonable_values(self):
        """测试摘要参数值合理"""
        mw = settings.agent_middleware
        assert 1000 <= mw.summarization_max_tokens <= 100000
        assert 2 <= mw.summarization_messages_to_keep <= 20
