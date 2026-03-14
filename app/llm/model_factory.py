"""模型工厂 - 支持配置化模型创建

所有模型名从配置文件读取，避免硬编码
统一使用异步调用方式
支持连接池复用和重试机制
"""

import asyncio
import hashlib
import logging
from typing import Optional, List, Dict, Any, Union

from openai import AsyncOpenAI
from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings

from app.config import settings

logger = logging.getLogger(__name__)


class ModelFactory:
    """模型工厂 - 支持配置化模型创建，连接池复用"""

    _chat_clients: Dict[str, ChatTongyi] = {}
    _async_clients: Dict[str, AsyncOpenAI] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def get_async_client(
        cls,
        api_key: str = None,
        base_url: str = None,
        timeout: float = 60.0,
        max_retries: int = 3
    ) -> AsyncOpenAI:
        """获取或创建异步客户端（连接池复用）

        Args:
            api_key: API密钥
            base_url: API基础URL
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数

        Returns:
            AsyncOpenAI 客户端实例
        """
        api_key = api_key or settings.qwen_api_key
        base_url = base_url or settings.qwen_base_url
        cache_key = hashlib.sha256(f"{api_key}_{base_url}".encode()).hexdigest()[:16]

        if cache_key not in cls._async_clients:
            async with cls._lock:
                if cache_key not in cls._async_clients:
                    cls._async_clients[cache_key] = AsyncOpenAI(
                        api_key=api_key,
                        base_url=base_url,
                        timeout=timeout,
                        max_retries=max_retries,
                    )
                    logger.debug(f"[MODEL FACTORY] AsyncOpenAI client created: {cache_key}")

        return cls._async_clients[cache_key]

    @classmethod
    def get_general_model(
        cls,
        is_expert: bool = False,
        enable_thinking: bool = False,
        use_cache: bool = True,
        streaming: bool = True,
    ) -> ChatTongyi:
        """获取通用模型（连接池复用）

        使用 LangChain 的 ChatTongyi 创建模型，支持 bind_tools (用于 Agent)

        Args:
            is_expert: 是否使用专家模型
            thinking: 是否启用深度思考
            use_cache: 是否使用缓存（默认True）
            streaming: 是否启用流式输出（默认True，用于Agent）
        """
        cache_key = f"general_{is_expert}_{enable_thinking}_{streaming}"

        if use_cache and cache_key in cls._chat_clients:
            logger.debug(f"[MODEL FACTORY] ChatTongyi cache hit: {cache_key}")
            return cls._chat_clients[cache_key]

        model_name = (
            settings.model_general_expert if is_expert
            else settings.model_general_fast
        )

        model_kwargs = {}
        if enable_thinking:
            model_kwargs["enable_thinking"] = True
            # The incremental_output parameter must be "true" when enable_thinking is true under stream mode
            if streaming:
                model_kwargs["incremental_output"] = True
        else:
            model_kwargs["enable_thinking"] = False
            # incremental_output only support stream call
            if streaming:
                model_kwargs["incremental_output"] = True

        client = ChatTongyi(
            model=model_name,
            dashscope_api_key=settings.qwen_api_key,
            streaming=streaming,
            temperature=0.3 if enable_thinking else 0.6,
            model_kwargs=model_kwargs if model_kwargs else None,
            request_timeout=60,
            max_retries=3
        )

        if use_cache:
            cls._chat_clients[cache_key] = client
            logger.debug(f"[MODEL FACTORY] ChatTongyi created and cached: {cache_key}")

        return client

    @classmethod
    def get_vision_model(cls, is_ocr: bool = False, **kwargs) -> "AsyncToolModel":
        """获取视觉模型

        Args:
            is_ocr: 是否使用OCR专用模型
        """
        model_name = (
            settings.model_vision_ocr if is_ocr
            else settings.model_vision_general
        )
        return AsyncToolModel(
            model_name=model_name,
            api_key=settings.qwen_api_key,
            **kwargs
        )

    @classmethod
    def get_image_model(cls, is_turbo: bool = True, **kwargs):
        """获取图像生成模型

        注意：图像生成模型使用阿里云百炼多模态生成API，不是OpenAI接口

        Args:
            is_turbo: 是否使用快速模型
        """
        from app.llm.qwen_models import QwenImageModel

        model_name = (
            settings.model_image_fast if is_turbo
            else settings.model_image_expert
        )
        return QwenImageModel(
            model_name=model_name,
            api_key=settings.qwen_api_key
        )

    @classmethod
    def get_image_edit_model(cls, **kwargs):
        """获取图像编辑模型

        注意：图像编辑使用专门的 qwen-image-edit 模型
        """
        from app.llm.qwen_models import QwenImageModel

        return QwenImageModel(
            model_name=settings.model_image_edit,
            api_key=settings.qwen_api_key
        )

    @classmethod
    def get_coder_model(cls, is_plus: bool = False, **kwargs) -> "AsyncToolModel":
        """获取编程模型

        Args:
            is_plus: 是否使用专家模型
        """
        model_name = (
            settings.model_coder_expert if is_plus
            else settings.model_coder_fast
        )
        return AsyncToolModel(
            model_name=model_name,
            api_key=settings.qwen_api_key,
            **kwargs
        )

    @classmethod
    def get_translation_model(cls, is_plus: bool = False, **kwargs) -> "AsyncToolModel":
        """获取翻译模型

        Args:
            is_plus: 是否使用专家模型
        """
        model_name = (
            settings.model_translation_expert if is_plus
            else settings.model_translation_fast
        )
        return AsyncToolModel(
            model_name=model_name,
            api_key=settings.qwen_api_key,
            **kwargs
        )

    @classmethod
    def get_embedding(cls, model_name: str = None, **kwargs) -> DashScopeEmbeddings:
        """获取Embedding模型

        使用 DashScopeEmbeddings 官方集成

        Args:
            model_name: 模型名称，默认使用配置中的 model_embedding
        """
        return DashScopeEmbeddings(
            model=model_name or settings.model_embedding,
            dashscope_api_key=settings.qwen_api_key,
            **kwargs
        )

    @classmethod
    async def close_all(cls):
        """关闭所有客户端连接，清理缓存"""
        cls._chat_clients.clear()

        for key, client in cls._async_clients.items():
            try:
                await client.close()
                logger.debug(f"[MODEL FACTORY] AsyncOpenAI client closed: {key}")
            except Exception as e:
                logger.warning(f"[MODEL FACTORY] Failed to close client {key}: {e}")

        cls._async_clients.clear()
        logger.info("[MODEL FACTORY] All clients closed and cache cleared")

    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """获取缓存状态"""
        return {
            "chat_clients": list(cls._chat_clients.keys()),
            "async_clients": list(cls._async_clients.keys()),
            "total_chat": len(cls._chat_clients),
            "total_async": len(cls._async_clients),
        }


class AsyncToolModel:
    """异步工具模型 - 用于直接工具触发的模型（视觉/编程/翻译等）

    使用共享的连接池，支持重试机制
    """

    def __init__(
        self,
        model_name: str,
        api_key: str = None,
        base_url: str = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        top_p: float = None,
    ):
        self.model_name = model_name
        self.api_key = api_key or settings.qwen_api_key
        self.base_url = base_url or settings.qwen_base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p

        if not self.api_key:
            raise ValueError("Qwen API key is required. Set qwen_api_key in config or environment.")

    async def _get_async_client(self) -> AsyncOpenAI:
        """获取异步客户端（使用连接池）"""
        return await ModelFactory.get_async_client(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=60.0,
            max_retries=3
        )

    async def ainvoke(self, messages: List[Dict[str, Any]], **kwargs) -> Any:
        """异步调用模型"""
        client = await self._get_async_client()

        request_kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
        }

        if self.max_tokens:
            request_kwargs["max_tokens"] = self.max_tokens
        if self.top_p:
            request_kwargs["top_p"] = self.top_p

        request_kwargs.update(kwargs)

        response = await client.chat.completions.create(**request_kwargs)
        return response.choices[0].message
