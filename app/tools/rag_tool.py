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
    从扫地/扫拖机器人知识库中搜索相关文档。

    当用户询问扫地机器人、扫拖机器人的使用方法、故障处理、环境适配、选购建议、维护保养等问题时使用此工具。

    Args:
        query: 搜索查询语句
        k: 返回文档数量，默认4条

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
