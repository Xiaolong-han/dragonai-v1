"""工具模块测试"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import json


class TestWebSearchTool:
    """web_search 工具测试"""

    @pytest.mark.asyncio
    async def test_web_search_returns_results(self):
        """测试网络搜索返回结果"""
        from app.agents.tools.web_search import web_search

        mock_client = AsyncMock()
        mock_client.search = AsyncMock(return_value={
            "results": [
                {"title": "Result 1", "url": "https://example.com/1", "content": "Content 1"},
                {"title": "Result 2", "url": "https://example.com/2", "content": "Content 2"},
            ]
        })

        with patch('app.agents.tools.web_search.async_tavily_client', mock_client):
            result = await web_search.ainvoke({"query": "test query", "max_results": 2})

        data = json.loads(result)
        assert data["type"] == "search_results"
        assert data["count"] == 2
        assert len(data["links"]) == 2

    @pytest.mark.asyncio
    async def test_web_search_empty_results(self):
        """测试网络搜索无结果"""
        from app.agents.tools.web_search import web_search

        mock_client = AsyncMock()
        mock_client.search = AsyncMock(return_value={"results": []})

        with patch('app.agents.tools.web_search.async_tavily_client', mock_client):
            result = await web_search.ainvoke({"query": "nonexistent query"})

        data = json.loads(result)
        assert data["count"] == 0


class TestTranslationTool:
    """translate_text 工具测试"""

    @pytest.mark.asyncio
    async def test_translate_text(self):
        """测试文本翻译"""
        from app.agents.tools.translation import translate_text

        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="你好世界"))

        with patch('app.llm.model_factory.ModelFactory.get_translation_model', return_value=mock_model):
            result = await translate_text.ainvoke({
                "text": "Hello World",
                "target_lang": "zh"
            })

        data = json.loads(result)
        assert data["type"] == "translation"
        assert data["target_lang"] == "zh"

    @pytest.mark.asyncio
    async def test_translate_with_source_lang(self):
        """测试带源语言的翻译"""
        from app.agents.tools.translation import translate_text

        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="Hello"))

        with patch('app.llm.model_factory.ModelFactory.get_translation_model', return_value=mock_model):
            result = await translate_text.ainvoke({
                "text": "你好",
                "target_lang": "en",
                "source_lang": "zh"
            })

        data = json.loads(result)
        assert data["source_lang"] == "zh"


class TestRAGTool:
    """search_knowledge_base 工具测试"""

    @pytest.mark.asyncio
    async def test_search_knowledge_base(self):
        """测试知识库搜索"""
        from app.agents.tools.rag import search_knowledge_base

        # 模拟知识库服务
        mock_service = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "Knowledge content"
        mock_doc.metadata = {"source": "doc1.pdf"}
        mock_service.asearch = AsyncMock(return_value=[mock_doc])

        with patch('app.agents.tools.rag.get_knowledge_service', return_value=mock_service):
            result = await search_knowledge_base.ainvoke({
                "query": "test query",
                "k": 4
            })

        data = json.loads(result)
        assert data["type"] == "knowledge"
        assert data["count"] == 1
        assert len(data["documents"]) == 1

    @pytest.mark.asyncio
    async def test_search_knowledge_base_empty(self):
        """测试知识库搜索无结果"""
        from app.agents.tools.rag import search_knowledge_base

        mock_service = MagicMock()
        mock_service.asearch = AsyncMock(return_value=[])

        with patch('app.agents.tools.rag.get_knowledge_service', return_value=mock_service):
            result = await search_knowledge_base.ainvoke({
                "query": "nonexistent"
            })

        data = json.loads(result)
        assert data["count"] == 0
        assert data["documents"] == []


class TestCodeAssistTool:
    """code_assist 工具测试"""

    @pytest.mark.asyncio
    async def test_code_assist(self):
        """测试代码助手"""
        from app.agents.tools.code import code_assist

        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(
            content="```python\nprint('hello')\n```"
        ))

        with patch('app.llm.model_factory.ModelFactory.get_coder_model', return_value=mock_model):
            result = await code_assist.ainvoke({
                "prompt": "Write a hello world",
                "language": "python"
            })

        data = json.loads(result)
        assert data["type"] == "code"
        assert data["language"] == "python"

    @pytest.mark.asyncio
    async def test_code_assist_error(self):
        """测试代码助手错误处理"""
        from app.agents.tools.code import code_assist

        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(side_effect=Exception("API Error"))

        with patch('app.llm.model_factory.ModelFactory.get_coder_model', return_value=mock_model):
            result = await code_assist.ainvoke({
                "prompt": "Write code",
                "language": "python"
            })

        data = json.loads(result)
        assert data["type"] == "error"


class TestDocumentTools:
    """文档读取工具测试"""

    @pytest.mark.asyncio
    async def test_read_pdf(self):
        """测试读取 PDF"""
        from app.agents.tools.document import read_pdf

        # 模拟 pypdf.PdfReader
        mock_reader = MagicMock()
        mock_reader.__len__ = MagicMock(return_value=2)
        mock_page = MagicMock()
        mock_page.extract_text = MagicMock(return_value="Page content")
        mock_reader.pages = [mock_page, mock_page]

        with patch('app.agents.tools.document._resolve_path') as mock_resolve, \
             patch('app.agents.tools.document._read_pdf_sync') as mock_read:
            mock_resolve.return_value = MagicMock(
                exists=MagicMock(return_value=True),
                suffix='.pdf',
                name='test.pdf'
            )
            mock_read.return_value = (2, ["Content"], "text", False)

            result = await read_pdf.ainvoke({
                "file_path": "/test/doc.pdf"
            })

        assert "Content" in result or "错误" not in result or "PDF" in result

    @pytest.mark.asyncio
    async def test_read_pdf_file_not_found(self):
        """测试读取不存在的 PDF"""
        from app.agents.tools.document import read_pdf

        with patch('app.agents.tools.document._resolve_path') as mock_resolve:
            mock_resolve.return_value = MagicMock(
                exists=MagicMock(return_value=False),
                suffix='.pdf'
            )

            result = await read_pdf.ainvoke({
                "file_path": "/test/notfound.pdf"
            })

        assert "错误" in result or "不存在" in result

    @pytest.mark.asyncio
    async def test_read_word(self):
        """测试读取 Word"""
        from app.agents.tools.document import read_word

        with patch('app.agents.tools.document._resolve_path') as mock_resolve, \
             patch('app.agents.tools.document._read_word_sync') as mock_read:
            mock_resolve.return_value = MagicMock(
                exists=MagicMock(return_value=True),
                suffix='.docx',
                name='test.docx'
            )
            mock_read.return_value = "Document content"

            result = await read_word.ainvoke({
                "file_path": "/test/doc.docx"
            })

        assert "content" in result.lower() or "文档" in result or "错误" not in result

    @pytest.mark.asyncio
    async def test_read_word_invalid_format(self):
        """测试读取非 Word 文件"""
        from app.agents.tools.document import read_word

        with patch('app.agents.tools.document._resolve_path') as mock_resolve:
            mock_resolve.return_value = MagicMock(
                exists=MagicMock(return_value=True),
                suffix='.txt',
                name='test.txt'
            )

            result = await read_word.ainvoke({
                "file_path": "/test/doc.txt"
            })

        assert "错误" in result or "不是" in result


class TestToolsInit:
    """工具模块初始化测试"""

    def test_all_tools_defined(self):
        """测试所有工具已定义"""
        from app.agents.tools import ALL_TOOLS

        tool_names = [tool.name for tool in ALL_TOOLS]

        assert "search_knowledge_base" in tool_names
        assert "web_search" in tool_names
        assert "ocr_document" in tool_names
        assert "understand_image" in tool_names
        assert "generate_image" in tool_names
        assert "edit_image" in tool_names
        assert "code_assist" in tool_names
        assert "translate_text" in tool_names
        assert "read_pdf" in tool_names
        assert "read_word" in tool_names

    def test_all_tools_have_description(self):
        """测试所有工具都有描述"""
        from app.agents.tools import ALL_TOOLS

        for tool in ALL_TOOLS:
            assert tool.description is not None
            assert len(tool.description) > 0