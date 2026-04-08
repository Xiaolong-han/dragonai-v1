"""DashScope 文本模型类 - 基于官方 SDK

使用 dashscope 官方 SDK 统一文本模型调用接口
支持视觉理解、OCR、编程、翻译等功能
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import dashscope
from dashscope import AioGeneration, AioMultiModalConversation

from app.config import settings
from app.monitoring import record_llm_call

logger = logging.getLogger(__name__)


# ============================================================================
# 文本模型类层次结构
# ============================================================================

class DashScopeModel(ABC):
    """DashScope 模型基类

    所有模型类的抽象基类，定义通用接口
    """

    def __init__(self, model_name: str, api_key: str | None = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key or settings.qwen_api_key
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens")

        # 配置 SDK
        dashscope.api_key = self.api_key

    @abstractmethod
    async def ainvoke(self, **kwargs) -> Any:
        """调用模型的抽象方法，由子类实现"""
        pass

    @abstractmethod
    def get_model_type(self) -> str:
        """返回模型类型的抽象方法"""
        pass


class DashScopeTextModel(DashScopeModel):
    """文本模型抽象基类

    所有文本生成模型的基类，定义通用接口
    不直接实现具体方法，由子类实现

    注意：不区分 fast/plus/expert，统一使用一个模型
    """

    def __init__(self, model_name: str, api_key: str | None = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key or settings.qwen_api_key
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens")

        # 配置 SDK
        dashscope.api_key = self.api_key
        self.model_category = "text"

    @abstractmethod
    async def ainvoke(self, messages: list[dict[str, Any]], **kwargs) -> Any:
        """调用文本生成模型的抽象方法，由子类实现"""
        pass

    def get_model_type(self) -> str:
        return "text_generation"


class QwenVisionModel(DashScopeTextModel):
    """千问视觉模型类

    用于图像理解等视觉任务
    支持模型：qwen3-vl-plus, qwen3-vl-falsh
            qwen-vl-plus, qwen-vl-max (qwen2.5 系列)
    """

    async def ainvoke(self, messages: list[dict[str, Any]], **kwargs) -> Any:
        """调用千问视觉理解模型"""
        start = time.time()
        try:
            response = await AioMultiModalConversation.call(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=self.api_key,
                **kwargs
            )
            record_llm_call(model=self.model_name, status="success", latency_seconds=time.time() - start)
            return response.choices[0].message
        except Exception:
            record_llm_call(model=self.model_name, status="error", latency_seconds=time.time() - start)
            raise

    def get_model_type(self) -> str:
        return "vision"


class QwenOCRModel(DashScopeTextModel):
    """千问 OCR 模型类

    用于 OCR 任务
    支持模型：qwen-vl-ocr
    """

    async def ainvoke(self, messages: list[dict[str, Any]], **kwargs) -> Any:
        """调用千问 OCR 模型"""
        start = time.time()
        try:
            response = await AioMultiModalConversation.call(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=self.api_key,
                **kwargs
            )
            record_llm_call(model=self.model_name, status="success", latency_seconds=time.time() - start)
            return response.choices[0].message
        except Exception:
            record_llm_call(model=self.model_name, status="error", latency_seconds=time.time() - start)
            raise

    def get_model_type(self) -> str:
        return "ocr"


class DashScopeCoderModel(DashScopeTextModel):
    """编程助手模型类

    用于代码生成、代码解释、编程问题解答等任务
    支持模型：qwen3-coder-next, qwen3-coder-plus, qwen3-coder-flash,
            qwen-coder-plus, qwen-coder-turbo
    """

    async def ainvoke(self, messages: list[dict[str, Any]], **kwargs) -> Any:
        """调用编程模型"""
        start = time.time()
        try:
            response = await AioGeneration.call(
                api_key=self.api_key,
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )
            record_llm_call(model=self.model_name, status="success", latency_seconds=time.time() - start)
            return response.output.choices[0].message
        except Exception:
            record_llm_call(model=self.model_name, status="error", latency_seconds=time.time() - start)
            raise

    def get_model_type(self) -> str:
        return "coder"


class DashScopeTranslationModel(DashScopeTextModel):
    """翻译模型类

    用于文本翻译任务
    支持模型：qwen-mt-plus、qwen-mt-flash、qwen-mt-lite、qwen-mt-turbo，属于 Qwen3-MT
    """

    async def ainvoke(
        self,
        messages: list[dict[str, Any]],
        translation_options: dict[str, str],
        **kwargs
    ) -> Any:
        """调用翻译模型"""
        start = time.time()
        try:
            response = await AioGeneration.call(
                api_key=self.api_key,
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                result_format='message',
                translation_options=translation_options,
                **kwargs
            )
            record_llm_call(model=self.model_name, status="success", latency_seconds=time.time() - start)
            return response.output.choices[0].message
        except Exception:
            record_llm_call(model=self.model_name, status="error", latency_seconds=time.time() - start)
            raise

    def get_model_type(self) -> str:
        return "translation"
