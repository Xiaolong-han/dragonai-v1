"""本地指标查看器 - 无需 Docker 的轻量监控

使用方式:
    python scripts/metrics_viewer.py

功能:
    - 实时显示 LLM 调用统计
    - 实时显示工具调用统计
    - 实时显示 SSE 连接数

依赖:
    pip install rich requests
"""

import time
import argparse
from typing import Dict, Any

try:
    import requests
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
except ImportError:
    print("请安装依赖: pip install rich requests")
    exit(1)


console = Console()


def parse_prometheus_metrics(text: str) -> Dict[str, Any]:
    """解析 Prometheus 格式的指标"""
    metrics = {
        "llm": {
            "total": 0,
            "success": 0,
            "error": 0,
            "by_model": {},
            "latency": {}
        },
        "tools": {
            "total": 0,
            "by_tool": {}
        },
        "tokens": {
            "input": 0,
            "output": 0,
            "by_model": {}
        },
        "sse": {
            "active": 0
        },
        "cache": {
            "hit": 0,
            "miss": 0
        }
    }

    for line in text.split('\n'):
        if line.startswith('#') or not line.strip():
            continue

        try:
            # 解析指标名和值
            if '{' in line:
                name_part, value = line.rsplit('}', 1)
                metric_name = name_part.split('{')[0]
                labels_str = name_part.split('{')[1]

                # 解析标签
                labels = {}
                for kv in labels_str.split(','):
                    if '=' in kv:
                        k, v = kv.split('=', 1)
                        labels[k.strip()] = v.strip('"')

                value = float(value.strip())
            else:
                parts = line.split()
                if len(parts) >= 2:
                    metric_name = parts[0]
                    value = float(parts[1])
                    labels = {}
                else:
                    continue

            # 分类处理
            if metric_name == 'llm_calls_total':
                metrics["llm"]["total"] += value
                model = labels.get('model', 'unknown')
                status = labels.get('status', 'unknown')

                if model not in metrics["llm"]["by_model"]:
                    metrics["llm"]["by_model"][model] = {"success": 0, "error": 0, "total": 0}
                metrics["llm"]["by_model"][model][status] = value
                metrics["llm"]["by_model"][model]["total"] += value

                if status == "success":
                    metrics["llm"]["success"] += value
                else:
                    metrics["llm"]["error"] += value

            elif metric_name == 'llm_tokens_total':
                token_type = labels.get('type', 'unknown')
                model = labels.get('model', 'unknown')

                if token_type == 'input':
                    metrics["tokens"]["input"] += value
                elif token_type == 'output':
                    metrics["tokens"]["output"] += value

                if model not in metrics["tokens"]["by_model"]:
                    metrics["tokens"]["by_model"][model] = {"input": 0, "output": 0}
                if token_type in metrics["tokens"]["by_model"][model]:
                    metrics["tokens"]["by_model"][model][token_type] = value

            elif metric_name == 'llm_latency_seconds_bucket':
                # 直方图数据，只记录总数
                pass

            elif metric_name == 'tool_calls_total':
                metrics["tools"]["total"] += value
                tool = labels.get('tool', 'unknown')
                status = labels.get('status', 'unknown')

                if tool not in metrics["tools"]["by_tool"]:
                    metrics["tools"]["by_tool"][tool] = {"success": 0, "error": 0, "total": 0}
                metrics["tools"]["by_tool"][tool][status] = value
                metrics["tools"]["by_tool"][tool]["total"] += value

            elif metric_name == 'sse_connections_active':
                metrics["sse"]["active"] = int(value)

            elif metric_name == 'cache_operations_total':
                operation = labels.get('operation', 'unknown')
                result = labels.get('result', 'unknown')
                if result == 'hit':
                    metrics["cache"]["hit"] += value
                elif result == 'miss':
                    metrics["cache"]["miss"] += value

        except Exception:
            continue

    return metrics


def fetch_metrics(base_url: str) -> Dict[str, Any]:
    """从服务端获取指标"""
    try:
        resp = requests.get(f"{base_url}/api/v1/monitoring/metrics", timeout=5)
        resp.raise_for_status()
        return parse_prometheus_metrics(resp.text)
    except requests.exceptions.ConnectionError:
        return {"error": "无法连接到服务，请确保服务已启动"}
    except Exception as e:
        return {"error": str(e)}


def render_dashboard(metrics: Dict[str, Any]) -> Layout:
    """渲染仪表盘"""
    layout = Layout()

    if "error" in metrics:
        return Panel(f"[red]错误: {metrics['error']}[/red]", title="DragonAI 监控")

    # LLM 调用表
    llm_table = Table(title="LLM 调用统计", show_header=True, header_style="bold cyan")
    llm_table.add_column("模型", style="cyan")
    llm_table.add_column("成功", style="green")
    llm_table.add_column("失败", style="red")
    llm_table.add_column("总计", style="yellow")

    for model, stats in metrics["llm"]["by_model"].items():
        llm_table.add_row(
            model,
            str(int(stats.get("success", 0))),
            str(int(stats.get("error", 0))),
            str(int(stats.get("total", 0)))
        )

    # Token 消耗表
    token_table = Table(title="Token 消耗", show_header=True, header_style="bold magenta")
    token_table.add_column("模型", style="cyan")
    token_table.add_column("输入", style="blue")
    token_table.add_column("输出", style="purple")
    token_table.add_column("总计", style="yellow")

    total_input = 0
    total_output = 0
    for model, stats in metrics["tokens"]["by_model"].items():
        inp = int(stats.get("input", 0))
        out = int(stats.get("output", 0))
        total_input += inp
        total_output += out
        token_table.add_row(model, f"{inp:,}", f"{out:,}", f"{inp + out:,}")

    token_table.add_row("[bold]总计[/bold]", f"[bold]{total_input:,}[/bold]",
                       f"[bold]{total_output:,}[/bold]", f"[bold]{total_input + total_output:,}[/bold]")

    # 工具调用表
    tool_table = Table(title="工具调用统计", show_header=True, header_style="bold green")
    tool_table.add_column("工具", style="cyan")
    tool_table.add_column("成功", style="green")
    tool_table.add_column("失败", style="red")
    tool_table.add_column("总计", style="yellow")

    for tool, stats in metrics["tools"]["by_tool"].items():
        tool_table.add_row(
            tool,
            str(int(stats.get("success", 0))),
            str(int(stats.get("error", 0))),
            str(int(stats.get("total", 0)))
        )

    # 概览面板
    overview = Table.grid(padding=1)
    overview.add_column(justify="center")
    overview.add_row(f"[bold cyan]LLM 总调用:[/bold cyan] {int(metrics['llm']['total'])}")
    overview.add_row(f"[bold green]成功率:[/bold green] "
                    f"{metrics['llm']['success'] / max(metrics['llm']['total'], 1) * 100:.1f}%")
    overview.add_row(f"[bold magenta]Token 总消耗:[/bold magenta] "
                    f"{int(metrics['tokens']['input'] + metrics['tokens']['output']):,}")
    overview.add_row(f"[bold yellow]工具总调用:[/bold yellow] {int(metrics['tools']['total'])}")
    overview.add_row(f"[bold blue]活跃 SSE:[/bold blue] {metrics['sse']['active']}")

    # 组合布局
    from rich.columns import Columns
    from rich.console import Group

    return Panel(
        Group(
            Panel(overview, title="概览"),
            Columns([llm_table, token_table]),
            tool_table
        ),
        title="[bold blue]DragonAI 监控仪表盘[/bold blue]",
        border_style="blue"
    )


def main():
    parser = argparse.ArgumentParser(description="DragonAI 本地指标查看器")
    parser.add_argument("--url", default="http://localhost:8000", help="服务地址")
    parser.add_argument("--interval", type=int, default=2, help="刷新间隔(秒)")
    args = parser.parse_args()

    console.clear()
    console.print(f"[bold green]连接到 {args.url}...[/bold green]")
    console.print(f"[dim]刷新间隔: {args.interval}秒, 按 Ctrl+C 退出[/dim]")
    console.print()

    try:
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                metrics = fetch_metrics(args.url)
                live.update(render_dashboard(metrics))
                time.sleep(args.interval)
    except KeyboardInterrupt:
        console.print("\n[yellow]已退出[/yellow]")


if __name__ == "__main__":
    main()