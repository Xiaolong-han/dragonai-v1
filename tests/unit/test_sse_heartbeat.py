"""SSE 心跳机制测试"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock

from app.utils.sse import sse_with_heartbeat, SSE_HEARTBEAT_INTERVAL


class TestSSEHeartbeat:
    """SSE 心跳机制测试"""

    @pytest.mark.asyncio
    async def test_heartbeat_format(self):
        """测试心跳消息格式"""
        async def mock_stream():
            yield "data: test\n\n"
            await asyncio.sleep(0.1)
            yield "data: test2\n\n"
        
        chunks = []
        async for chunk in sse_with_heartbeat(mock_stream(), heartbeat_interval=0.05):
            chunks.append(chunk)
            if len(chunks) >= 3:
                break
        
        heartbeat_found = False
        for chunk in chunks:
            if "heartbeat" in chunk:
                data = chunk.replace("data: ", "").strip()
                parsed = json.loads(data)
                assert parsed["type"] == "heartbeat"
                assert "timestamp" in parsed
                heartbeat_found = True
                break
        
        assert heartbeat_found, "应该有心跳消息"

    @pytest.mark.asyncio
    async def test_stream_data_passed_through(self):
        """测试流数据正常传递"""
        async def mock_stream():
            yield "data: message1\n\n"
            yield "data: message2\n\n"
        
        chunks = []
        async for chunk in sse_with_heartbeat(mock_stream(), heartbeat_interval=1):
            chunks.append(chunk)
        
        assert "data: message1\n\n" in chunks
        assert "data: message2\n\n" in chunks

    @pytest.mark.asyncio
    async def test_heartbeat_interval(self):
        """测试心跳间隔"""
        async def mock_stream():
            yield "data: start\n\n"
            await asyncio.sleep(0.3)
            yield "data: end\n\n"
        
        chunks = []
        start_time = asyncio.get_event_loop().time()
        
        async for chunk in sse_with_heartbeat(mock_stream(), heartbeat_interval=0.1):
            chunks.append(chunk)
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        heartbeat_count = sum(1 for c in chunks if "heartbeat" in c)
        
        assert heartbeat_count >= 2, f"应该有多个心跳，实际: {heartbeat_count}"

    @pytest.mark.asyncio
    async def test_empty_stream(self):
        """测试空流"""
        async def mock_stream():
            return
            yield
        
        chunks = []
        async for chunk in sse_with_heartbeat(mock_stream(), heartbeat_interval=0.1):
            chunks.append(chunk)
        
        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_heartbeat_stops_on_stream_end(self):
        """测试流结束后心跳停止"""
        async def mock_stream():
            yield "data: done\n\n"
        
        chunks = []
        async for chunk in sse_with_heartbeat(mock_stream(), heartbeat_interval=0.05):
            chunks.append(chunk)
        
        await asyncio.sleep(0.2)
        
        assert len(chunks) == 1
        assert "done" in chunks[0]

    @pytest.mark.asyncio
    async def test_heartbeat_with_exception(self):
        """测试流异常时心跳停止"""
        async def mock_stream():
            yield "data: start\n\n"
            raise Exception("Test error")
            yield "data: never\n\n"
        
        chunks = []
        with pytest.raises(Exception):
            async for chunk in sse_with_heartbeat(mock_stream(), heartbeat_interval=0.1):
                chunks.append(chunk)
        
        assert len(chunks) >= 1
