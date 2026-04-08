"""联网搜索工具"""

import json

from langchain_core.tools import tool
from tavily import AsyncTavilyClient

from app.config import settings

async_tavily_client = AsyncTavilyClient(api_key=settings.tavily_api_key)


@tool
async def web_search(query: str, max_results: int = 5) -> str:
    """
    联网搜索获取最新信息和实时数据。

    适用场景：
    - 用户询问实时信息、新闻、当前事件
    - 查询天气、股价、体育比分等动态信息
    - 知识库中未包含的内容
    - 需要最新数据的查询

    注意：此工具会产生网络请求，非必要不调用。

    Args:
        query: 搜索查询语句，尽量精确以提高搜索质量
        max_results: 返回结果数量，默认5条，最多10条

    Returns:
        搜索结果（JSON格式），包含标题、链接和摘要
    """
    results = await async_tavily_client.search(
        query,
        search_depth="advanced",
        include_raw_content=False,
        max_results=max_results,
        topic="general"
    )

    links = []
    result_list = results.get("results", [])
    for item in result_list[:5]:
        links.append({
            "title": item.get("title", ""),
            "url": item.get("url", "")
        })

    return json.dumps({
        "type": "search_results",
        "query": query,
        "count": len(result_list),
        "links": links,
        "results": result_list
    })
