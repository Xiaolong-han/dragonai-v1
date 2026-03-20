"""多模态工具 - 图片理解和 OCR"""

from langchain_core.tools import tool
from app.llm.model_factory import ModelFactory
from app.utils.image_utils import build_openai_image_content_async


@tool
async def understand_image(image_url: str) -> str:
    """
    理解并描述图片内容。

    适用场景：
    - 用户上传图片询问内容
    - 分析图片场景、物体、人物
    - 图片内容问答

    Args:
        image_url: 图片路径或 URL：
                   - 相对路径：images/xxx.png
                   - 本地绝对路径
                   - HTTP/HTTPS URL

    Returns:
        图片内容的详细描述
    """
    model = ModelFactory.get_vision_model(is_ocr=False)
    
    prompt = "请详细描述这张图片的内容，包括场景、物体、人物、颜色等细节。"
    content = await build_openai_image_content_async(image_url, prompt)
    messages = [{"role": "user", "content": content}]
    
    result = await model.ainvoke(messages)
    return result.content


@tool
async def ocr_document(image_url: str) -> str:
    """
    识别图片中的文字（OCR）。

    适用场景：
    - 提取图片中的文字内容
    - 文档图片转文字
    - 截图文字识别

    重要：必须原样完整输出识别结果，不要总结、不要省略。

    Args:
        image_url: 图片路径或 URL：
                   - 相对路径：images/xxx.png
                   - 本地绝对路径
                   - HTTP/HTTPS URL

    Returns:
        图片中识别出的文字内容
    """
    model = ModelFactory.get_vision_model(is_ocr=True)
    
    prompt = "请提取这张图片中的所有文字内容，保持原有格式。"
    content = await build_openai_image_content_async(image_url, prompt)
    messages = [{"role": "user", "content": content}]
    
    result = await model.ainvoke(messages)
    return result.content
