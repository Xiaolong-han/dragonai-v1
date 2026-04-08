"""翻译工具 - 文本翻译"""

import json

from langchain_core.tools import tool

from app.llm.model_factory import ModelFactory


@tool
async def translate_text(text: str, target_lang: str, source_lang: str | None = None) -> str:
    """
    将文本翻译成目标语言。

    适用场景：
    - 用户明确要求翻译
    - 需要将内容转换为其他语言

    注意：一般对话中涉及外语时直接回复即可，只有明确要求翻译时才调用此工具。

    Args:
        text: 待翻译的文本内容
        target_lang: 目标语言代码：
                     - zh: 中文
                     - en: 英语
                     - ja: 日语
                     - ko: 韩语
                     - fr: 法语
                     - de: 德语
                     - es: 西班牙语
        source_lang: 源语言代码，可选。不传则自动检测

    Returns:
        翻译后的文本（JSON 格式）
    """
    model = ModelFactory.get_translation_model()

    messages = [
        {"role": "user", "content": text}
    ]

    translation_options = {
        "source_lang": source_lang or "auto",
        "target_lang": target_lang,
    }

    translated_text = await model.ainvoke(messages, translation_options=translation_options)

    return json.dumps({
        "type": "translation",
        "source_lang": source_lang or "auto",
        "target_lang": target_lang,
        "original_text": text[:200] + "..." if len(text) > 200 else text,
        "translated_text": translated_text.content
    })
