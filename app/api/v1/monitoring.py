"""监控 API 路由"""

import contextlib

from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

from app.api.dependencies import get_current_active_user
from app.cache import get_cache_stats
from app.models.user import User
from app.schemas.response import ResponseBuilder

router = APIRouter(prefix="/monitoring", tags=["监控"])


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus 指标端点 (无需认证，供 Prometheus 抓取)

    返回 Prometheus 格式的指标数据，包括:
    - LLM 调用次数、延迟、Token 消耗
    - 工具调用次数、延迟
    - SSE 连接数
    - 缓存操作统计
    """
    return Response(
        generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/metrics/summary")
async def metrics_summary(current_user: User = Depends(get_current_active_user)):
    """指标摘要 (需要认证，人类可读格式)"""

    # 收集指标值
    metrics_text = generate_latest(REGISTRY).decode('utf-8')

    # 解析并汇总
    summary = {
        "llm": {
            "total_calls": 0,
            "success_calls": 0,
            "error_calls": 0,
            "by_model": {}
        },
        "tools": {
            "total_calls": 0,
            "by_tool": {}
        },
        "sse": {
            "active_connections": 0
        }
    }

    for line in metrics_text.split('\n'):
        if line.startswith('llm_calls_total{'):
            # 解析: llm_calls_total{model="glm-5",status="success"} 42
            try:
                parts = line.split(' ')
                value = int(float(parts[-1]))
                summary["llm"]["total_calls"] += value

                # 解析标签
                label_part = line.split('{')[1].split('}')[0]
                labels = {}
                for kv in label_part.split(','):
                    k, v = kv.split('=')
                    labels[k] = v.strip('"')

                model = labels.get('model', 'unknown')
                status = labels.get('status', 'unknown')

                if model not in summary["llm"]["by_model"]:
                    summary["llm"]["by_model"][model] = {"success": 0, "error": 0}
                summary["llm"]["by_model"][model][status] = value

                if status == "success":
                    summary["llm"]["success_calls"] += value
                else:
                    summary["llm"]["error_calls"] += value
            except Exception:
                pass

        elif line.startswith('tool_calls_total{'):
            try:
                parts = line.split(' ')
                value = int(float(parts[-1]))
                summary["tools"]["total_calls"] += value

                label_part = line.split('{')[1].split('}')[0]
                labels = {}
                for kv in label_part.split(','):
                    k, v = kv.split('=')
                    labels[k] = v.strip('"')

                tool = labels.get('tool', 'unknown')
                if tool not in summary["tools"]["by_tool"]:
                    summary["tools"]["by_tool"][tool] = {"success": 0, "error": 0}

                status = labels.get('status', 'unknown')
                summary["tools"]["by_tool"][tool][status] = value
            except Exception:
                pass

        elif line.startswith('sse_connections_active '):
            with contextlib.suppress(Exception):
                summary["sse"]["active_connections"] = int(float(line.split()[-1]))

    return ResponseBuilder.success(data=summary)


@router.get("/cache/stats")
async def get_cache_statistics(current_user: User = Depends(get_current_active_user)):
    """获取缓存统计信息（需要认证）"""
    stats = await get_cache_stats()
    return ResponseBuilder.success(data=stats)


@router.get("/health/detailed")
async def detailed_health_check():
    """详细健康检查"""
    from app.cache import redis_client
    from app.core.database import engine

    health = {
        "status": "healthy",
        "services": {}
    }

    try:
        await redis_client.client.ping()
        health["services"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"

    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        health["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        health["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"

    return ResponseBuilder.success(data=health)
