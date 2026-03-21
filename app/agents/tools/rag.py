"""RAG工具 - 知识库检索"""

import json
from langchain_core.tools import tool
from app.services.knowledge_service import get_knowledge_service


@tool
async def search_knowledge_base(
    query: str,
    k: int = 4,
) -> str:
    """
    从知识库中搜索相关文档和信息。

    适用场景：
    - 用户询问专业知识、产品使用方法、故障处理等问题
    - 需要查找特定主题的详细说明或文档
    - 知识库中可能包含的相关信息

    当知识库中没有找到答案时，建议使用 web_search 工具进行联网搜索。

    Args:
        query: 搜索查询语句，描述要查找的内容
        k: 返回文档数量，默认4条，最多10条

    Returns:
        相关文档的格式化内容（JSON格式）
    """
    service = get_knowledge_service()
    documents = await service.asearch(query, k=k)

    if not documents:
        return json.dumps({
            "type": "knowledge",
            "query": query,
            "count": 0,
            "documents": []
        })

    formatted = []
    for i, doc in enumerate(documents, 1):
        source = doc.metadata.get("source", "未知")
        formatted.append({
            "index": i,
            "source": source,
            "content": doc.page_content
        })

    return json.dumps({
        "type": "knowledge",
        "query": query,
        "count": len(documents),
        "documents": formatted
    })
