"""图像工具 - 图像生成和编辑"""

import json

from langchain_core.tools import tool

from app.llm.model_factory import ModelFactory


@tool
async def generate_image(prompt: str, size: str = "1664*928", n: int = 1) -> str:
    """
    根据文本描述生成图像。

    适用场景：
    - 用户明确要求生成图片、绘画、设计图
    - 需要创意图像、概念图、示意图
    - 支持多种风格：写实、动漫、油画、水彩等

    Args:
        prompt: 图像描述，越详细效果越好。建议包含：
                - 主体内容（人物、物体、场景）
                - 风格（写实、动漫、油画等）
                - 光线、颜色、构图等细节
                示例："一只橙色的猫坐在窗台上，阳光洒落，油画风格"
        size: 图像尺寸，可选：
              - "1664*928"（默认，横版）
              - "1024*1024"（正方形）
              - "1024*768"（横版）
              - "768*1024"（竖版）
        n: 生成数量，1-4 之间，默认 1

    Returns:
        生成图像的 URL 列表（JSON 格式）
    """
    model = ModelFactory.get_text_to_image_model()
    urls = await model.agenerate(prompt=prompt, size=size, n=n)

    return json.dumps({
        "type": "image_generated",
        "prompt": prompt,
        "size": size,
        "urls": urls,
        "count": len(urls)
    })


@tool
async def edit_image(image_url: str, prompt: str) -> str:
    """
    根据指令编辑或修改现有图像。

    适用场景：
    - 修改图片风格（如转卡通风格）
    - 添加或删除元素
    - 调整颜色、背景
    - 图像修复或增强

    Args:
        image_url: 待编辑图像的路径或 URL：
                   - 相对路径：images/xxx.png
                   - 本地绝对路径
                   - HTTP/HTTPS URL
        prompt: 编辑指令，详细描述修改内容：
                示例："将背景换成海滩"、"添加一顶帽子"、"转为水彩画风格"

    Returns:
        编辑后图像的 URL（JSON 格式）
    """
    model = ModelFactory.get_image_edit_model()
    url = await model.aedit(image_url=image_url, prompt=prompt)

    return json.dumps({
        "type": "image_edited",
        "prompt": prompt,
        "original_image": image_url,
        "url": url
    })
