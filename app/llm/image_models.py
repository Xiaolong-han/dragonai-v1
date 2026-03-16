"""DashScope 图像模型类 - 基于官方 SDK

使用 dashscope 官方 SDK 统一图像模型调用接口
支持图像生成、图像编辑等功能
"""

from abc import ABC, abstractmethod
from typing import List, Any

import dashscope
from dashscope import AioMultiModalConversation
from dashscope.aigc import AioImageSynthesis

from app.config import settings


# ============================================================================
# 工具函数：响应解析
# ============================================================================

def _extract_qwen_image_urls(response) -> List[str]:
    """从 Qwen 图像模型响应中提取 URL
    
    Qwen 响应格式 (生成和编辑相同)：
    output.choices[0].message.content = [
        {"image": "https://xxx.png"}
    ]
    
    Args:
        response: DashScope API 响应对象
        
    Returns:
        图片 URL 列表
    """
    urls = []
    if hasattr(response, 'output') and response.output:
        output = response.output
        if hasattr(output, 'choices') and output.choices:
            for choice in output.choices:
                if hasattr(choice, 'message') and choice.message:
                    message = choice.message
                    if hasattr(message, 'content') and message.content:
                        content_list = message.content
                        if isinstance(content_list, list):
                            for content_item in content_list:
                                if hasattr(content_item, 'image') and content_item.image:
                                    urls.append(content_item.image.strip())
                                elif isinstance(content_item, dict) and 'image' in content_item:
                                    urls.append(content_item['image'].strip())
    return urls


def _extract_wanx_image_urls(response) -> List[str]:
    """从 Wanx 图像模型响应中提取 URL
    
    Wanx 实际响应格式 (AioImageSynthesis API)：
    output = {
        "task_id": "xxx",
        "task_status": "SUCCEEDED",
        "results": [
            {"url": "https://xxx.png"}
        ]
    }
    
    Args:
        response: DashScope API 响应对象
        
    Returns:
        图片 URL 列表
    """
    urls = []
    if hasattr(response, 'output') and response.output:
        output = response.output
        # Wanx 使用 AioImageSynthesis API，响应格式为 output.results[].url
        if hasattr(output, 'results') and output.results:
            for result in output.results:
                if hasattr(result, 'url') and result.url:
                    urls.append(result.url.strip())
                elif isinstance(result, dict) and 'url' in result:
                    urls.append(result['url'].strip())
    return urls


# ============================================================================
# 图像模型类层次结构
# ============================================================================

class DashScopeImageModel(ABC):
    """图像模型基类
    
    所有图像相关模型的抽象基类
    """
    
    def __init__(self, model_name: str, api_key: str = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key or settings.qwen_api_key
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens")
        
        # 配置 SDK
        dashscope.api_key = self.api_key
        self.model_category = "image"
    
    @abstractmethod
    async def agenerate(self, prompt: str, **kwargs) -> List[str]:
        """生成图像的抽象方法"""
        pass
    
    @abstractmethod
    async def aedit(self, image_url: str, prompt: str, **kwargs) -> str:
        """编辑图像的抽象方法"""
        pass
    
    def get_model_type(self) -> str:
        return "image_generation"


class QwenImageGenerationModel(DashScopeImageModel):
    """通义千问图像生成模型
    
    支持模型：
    qwen-image, 
    qwen-image-plus, 
    qwen-image-max,
    qwen-image-2.0,
    qwen-image-2.0-pro
    """
    
    async def agenerate(
        self, 
        prompt: str, 
        size: str = "1664*928", 
        n: int = 1, 
        negative_prompt: str = None, 
        **kwargs
    ) -> List[str]:
        """生成图像"""
        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ]
        response = await AioMultiModalConversation.call(
            api_key=self.api_key,
            model=self.model_name,
            messages=messages,
            result_format='message',
            stream=False,
            watermark=False,
            prompt_extend=True,
            negative_prompt=negative_prompt,
            size=size,
            n=n,
            **kwargs,
        )

        return _extract_qwen_image_urls(response)

    async def aedit(self, image_url: str, prompt: str, **kwargs) -> str:
        """图像生成（文生图）模型不支持图像编辑"""
        raise NotImplementedError(
            "QwenImageGenerationModel only supports text-to-image generation, "
            "not image editing"
        )


class QwenImageEditModel(DashScopeImageModel):
    """通义千问图像编辑专用模型
    
    支持模型：
    qwen-image-edit, 
    qwen-image-edit-plus,
    qwen-image-edit-max,
    qwen-image-2.0,
    qwen-image-2.0-pro
    注意：统一使用配置的模型，不区分版本
    """
    
    async def agenerate(self, prompt: str, **kwargs) -> List[str]:
        """图像编辑模型不支持纯文生图"""
        raise NotImplementedError(
            "QwenImageEditModel only supports image editing, "
            "not text-to-image generation"
        )
    
    async def aedit(self, image_url: str, prompt: str, **kwargs) -> str:
        """编辑图像"""

        messages = [
            {
                "role": "user",
                "content": [{"image": image_url}, {"text": prompt}]
            }
        ]
        response = await AioMultiModalConversation.call(
            api_key=self.api_key,
            model=self.model_name,
            messages=messages,
            response_format='message',
            stream=False,
            watermark=False,
            prompt_extend=True,
            negative_prompt=" ",
            n=1,
            **kwargs,
        )
        urls = _extract_qwen_image_urls(response)
        return urls[0] if urls else ""


class WanxImageGenerationModelV2(DashScopeImageModel):
    """万相图像生成模型
    
    支持模型：wan2.5 及其以下版本
    wan2.5-t2i-preview,
    wan2.2-t2i-flash,
    wan2.2-t2i-plus,
    wanx2.1-t2i-turbo,
    wanx2.1-t2i-plus,
    """
    
    async def agenerate(
        self, 
        prompt: str, 
        size: str = "1280*1280", 
        n: int = 1, 
        negative_prompt: str = None, 
        **kwargs
    ) -> List[str]:
        """生成图像"""
        response = await AioImageSynthesis.call(
            api_key=self.api_key,
            model=self.model_name,
            prompt=prompt,
            watermark=False,
            prompt_extend=True,
            negative_prompt=negative_prompt,
            size="1280*1280",
            n=n,
            **kwargs,
        )

        return _extract_wanx_image_urls(response)

    async def aedit(self, image_url: str, prompt: str, **kwargs) -> str:
        """图像生成（文生图）模型不支持图像编辑"""
        raise NotImplementedError(
            "WanxImageGenerationModel only supports text-to-image generation, "
            "not image editing"
        )


class WanxImageEditModelV2_5(DashScopeImageModel):
    """万相图像编辑专用模型
    
    支持模型：wan2.5-i2i-preview
    """
    
    async def agenerate(self, prompt: str, **kwargs) -> List[str]:
        """图像编辑模型不支持纯文生图"""
        raise NotImplementedError(
            "WanxImageEditModel only supports image editing, "
            "not text-to-image generation"
        )
    
    async def aedit(self, image_url: str, prompt: str, **kwargs) -> str:
        """编辑图像"""
        response = await AioImageSynthesis.call(
            api_key=self.api_key,
            model=self.model_name,
            prompt=prompt,
            images=[image_url],
            watermark=False,
            prompt_extend=True,
            negative_prompt=" ",
            n=1,
            **kwargs,
        )
        urls = _extract_wanx_image_urls(response)
        return urls[0] if urls else ""
