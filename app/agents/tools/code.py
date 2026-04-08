"""编程工具 - 代码生成和协助"""

import json

from langchain_core.tools import tool

from app.llm.model_factory import ModelFactory


@tool
async def code_assist(prompt: str, language: str = "python") -> str:
    """
    编程助手工具，用于代码生成、调试和优化。

    适用场景：
    - 编写新代码或实现特定功能
    - 解决编程问题或错误
    - 代码优化和重构建议
    - 解释代码逻辑

    重要：必须原样完整输出结果，不要总结或省略。

    Args:
        prompt: 编程需求描述。详细说明：
                - 需要实现什么功能
                - 遇到了什么问题
                - 期望的输入输出
                示例："实现一个支持并发的 HTTP 客户端"、"帮我调试这段代码..."
        language: 编程语言，支持：python, javascript, java, c++, go, rust, typescript 等
                  默认值："python"

    Returns:
        完整代码及解释说明（JSON 格式）
    """
    model = ModelFactory.get_coder_model()
    messages = [
        {"role": "system", "content": f"""你是一个专业的{language}编程助手。
请提供清晰、高效、有注释的代码，并解释关键逻辑。

重要：你的回复将直接展示给用户，请确保：
1. 代码完整、可运行
2. 包含必要的注释和说明
3. 格式清晰，使用 markdown 代码块"""},
        {"role": "user", "content": prompt}
    ]
    try:
        result = await model.ainvoke(messages)

        return json.dumps({
            "type": "code",
            "language": language,
            "prompt": prompt,
            "code": result.content
        })
    except Exception as e:
        return json.dumps({
            "type": "error",
            "language": language,
            "prompt": prompt,
            "error": str(e)
        })
