"""Agent 配置测试"""

import pytest
from app.config import settings


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
