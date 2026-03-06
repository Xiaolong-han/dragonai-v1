import asyncio
import json
import time
from typing import AsyncGenerator

SSE_HEARTBEAT_INTERVAL = 15


async def sse_with_heartbeat(
    stream_generator: AsyncGenerator[str, None],
    heartbeat_interval: int = SSE_HEARTBEAT_INTERVAL
) -> AsyncGenerator[str, None]:
    """带心跳的 SSE 生成器
    
    使用 asyncio.Queue 实现并发心跳发送。
    主流和心跳发送器并发运行，通过队列传递数据。
    
    Args:
        stream_generator: 原始 SSE 数据生成器
        heartbeat_interval: 心跳间隔（秒）
        
    Yields:
        SSE 格式的数据或心跳消息
    """
    queue: asyncio.Queue = asyncio.Queue()
    stream_done = False
    
    async def stream_producer():
        """流数据生产者"""
        try:
            async for chunk in stream_generator:
                await queue.put(chunk)
        finally:
            nonlocal stream_done
            stream_done = True
            await queue.put(None)
    
    async def heartbeat_producer():
        """心跳生产者"""
        while not stream_done:
            try:
                await asyncio.wait_for(
                    asyncio.sleep(heartbeat_interval),
                    timeout=heartbeat_interval + 1
                )
                if not stream_done:
                    heartbeat_msg = f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()}, ensure_ascii=False)}\n\n"
                    await queue.put(heartbeat_msg)
            except asyncio.CancelledError:
                break
    
    producer_task = asyncio.create_task(stream_producer())
    heartbeat_task = asyncio.create_task(heartbeat_producer())
    
    try:
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk
    finally:
        producer_task.cancel()
        heartbeat_task.cancel()
        try:
            await producer_task
        except asyncio.CancelledError:
            pass
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
