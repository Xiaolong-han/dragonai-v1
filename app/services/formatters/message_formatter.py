import logging
from typing import Dict, Any, Optional, List
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.messages.tool import ToolMessage
from langchain_core.messages.human import HumanMessage

logger = logging.getLogger(__name__)


def _is_summarization_message(message) -> bool:
    """检查消息是否来自 SummarizationMiddleware
    
    检查方式：
    1. 消息是 HumanMessage
    2. 消息的 additional_kwargs 中有 lc_source=summarization
    """
    if not isinstance(message, HumanMessage):
        return False
    
    additional_kwargs = getattr(message, 'additional_kwargs', {}) or {}
    lc_source = additional_kwargs.get('lc_source')
    
    return lc_source == 'summarization'


class MessageFormatter:
    """消息格式化器，负责从 LangChain 消息对象中提取和格式化内容"""
    
    @staticmethod
    def extract_thinking_content(message) -> Optional[str]:
        """从消息中提取思考内容"""
        if hasattr(message, 'additional_kwargs'):
            return message.additional_kwargs.get('reasoning_content')
        return None
    
    @staticmethod
    def extract_text_content(content) -> str:
        """从 content 中提取文本内容
        
        处理 content 为字符串或列表的情况
        """
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    text_parts.append(item.get('text', ''))
                elif isinstance(item, str):
                    text_parts.append(item)
            return ''.join(text_parts)
        return ""
    
    @staticmethod
    def format_stream_message(message, metadata, include_thinking: bool) -> Optional[Dict[str, Any]]:
        """格式化流式消息（stream_mode="messages"）
        
        Args:
            message: AIMessageChunk 或 ToolMessage
            metadata: 包含 langgraph_node 等信息
            include_thinking: 是否包含思考内容
            
        Returns:
            格式化后的消息字典，如果不需要输出则返回 None
        """
        # 检查是否是摘要消息，如果是则不输出到前端
        if _is_summarization_message(message):
            return None 
        if isinstance(message, AIMessageChunk):
            tool_call_chunks = getattr(message, 'tool_call_chunks', None)
            if tool_call_chunks:
                return None
            
            content = getattr(message, 'content', "")
            
            if include_thinking:
                thinking_content = MessageFormatter.extract_thinking_content(message)
                if thinking_content:
                    return {
                        "type": "thinking",
                        "data": {"content": thinking_content}
                    }
            
            if content and not isinstance(content, list):
                return {
                    "type": "token",
                    "data": {"content": content}
                }
        
        elif isinstance(message, ToolMessage):
            return None
        
        return None
    
    @staticmethod
    def format_update(event: Dict, include_thinking: bool) -> List[Dict[str, Any]]:
        """格式化更新事件（stream_mode="updates"）
        
        Args:
            event: 事件字典，格式为 {"model": {"messages": [...]}} 或 {"tools": {"messages": [...]}}
            include_thinking: 是否包含思考内容
            
        Returns:
            格式化后的事件列表，可能包含 thinking 和 content 两个事件
        """
        for node_name, node_output in event.items():
            if node_name in ("model", "agent"):
                return MessageFormatter._format_model_update(node_output, include_thinking)
            elif node_name == "tools":
                return MessageFormatter._format_tools_update(node_output)
        
        return [{"type": "unknown", "data": event}]
    
    @staticmethod
    def _format_model_update(node_output, include_thinking: bool) -> List[Dict[str, Any]]:
        """格式化 model/agent 节点的更新"""
        from app.services.formatters.tool_result_formatter import ToolResultFormatter
        
        messages = node_output.get("messages", []) if isinstance(node_output, dict) else []
        
        if not messages:
            return []
        
        last_message = messages[-1]
        if not hasattr(last_message, 'type') or last_message.type != "ai":
            return []
        
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            calls = []
            for tc in last_message.tool_calls:
                args = tc.get('args', {})
                args_preview = ToolResultFormatter.get_args_preview(args)
                calls.append({
                    "id": tc.get('id', ''),
                    "name": tc.get('name', ''),
                    "args_preview": args_preview
                })
            if calls:
                return [{"type": "tool_call", "data": {"calls": calls}}]
        
        results = []
        
        if include_thinking:
            thinking_content = MessageFormatter.extract_thinking_content(last_message)
            if thinking_content:
                results.append({"type": "thinking", "data": {"content": thinking_content}})
        
        return results
    
    @staticmethod
    def _format_tools_update(node_output) -> List[Dict[str, Any]]:
        """格式化 tools 节点的更新"""
        from app.services.formatters.tool_result_formatter import ToolResultFormatter
        
        messages = node_output.get("messages", []) if isinstance(node_output, dict) else []
        
        if not messages:
            return []
        
        last_message = messages[-1]
        if hasattr(last_message, 'type') and last_message.type == "tool":
            name = getattr(last_message, 'name', None)
            content = getattr(last_message, 'content', None)
            
            formatted = ToolResultFormatter.format_result(name, content)
            
            return [{
                "type": "tool_result",
                "data": {
                    "tool_call_id": getattr(last_message, 'tool_call_id', None),
                    "name": name,
                    **formatted
                }
            }]
        
        return []
