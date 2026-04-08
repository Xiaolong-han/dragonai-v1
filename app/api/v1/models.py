from fastapi import APIRouter

from app.config import settings
from app.schemas.models import ChatModelResponse, ToolModelResponse
from app.schemas.response import ResponseBuilder

router = APIRouter(prefix="/models", tags=["模型"])


@router.get("/chat")
async def get_chat_models():
    """获取通用聊天模型列表"""
    models = [
        ChatModelResponse(
            name=settings.model_general_fast,
            is_expert=False
        ).model_dump(),
        ChatModelResponse(
            name=settings.model_general_expert,
            is_expert=True
        ).model_dump()
    ]
    return ResponseBuilder.success(data=models)


@router.get("/tools")
async def get_tool_models():
    """获取专项工具模型列表"""
    tool_models = [
        ToolModelResponse(
            tool_type="coder",
            display_name="编程工具",
            model=settings.model_coder
        ).model_dump(),
        ToolModelResponse(
            tool_type="translation",
            display_name="翻译工具",
            model=settings.model_translation
        ).model_dump(),
        ToolModelResponse(
            tool_type="image",
            display_name="图像生成",
            model=settings.model_text_to_image
        ).model_dump(),
        ToolModelResponse(
            tool_type="vision",
            display_name="视觉模型",
            model=settings.model_vision
        ).model_dump(),
        ToolModelResponse(
            tool_type="image_edit",
            display_name="图像编辑",
            model=settings.model_image_edit
        ).model_dump(),
        ToolModelResponse(
            tool_type="embedding",
            display_name="嵌入模型",
            model=settings.model_embedding
        ).model_dump(),
        ToolModelResponse(
            tool_type="ocr",
            display_name="OCR识别",
            model=settings.model_vision_ocr
        ).model_dump(),
    ]
    return ResponseBuilder.success(data=tool_models)
