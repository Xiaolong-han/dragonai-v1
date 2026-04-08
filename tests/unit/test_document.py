"""文档工具测试 - 扩展测试用例"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path


class TestResolvePath:
    """_resolve_path 函数测试"""

    def test_resolve_path_valid(self):
        """测试解析有效路径"""
        from app.agents.tools.document import _resolve_path

        with patch('app.agents.tools.document.FileSandbox.validate_path') as mock_validate:
            mock_validate.return_value = Path("/storage/documents/test.pdf")

            result = _resolve_path("documents/test.pdf")

            assert result == Path("/storage/documents/test.pdf")
            mock_validate.assert_called_once_with("documents/test.pdf")

    def test_resolve_path_for_write(self):
        """测试解析写入路径"""
        from app.agents.tools.document import _resolve_path

        with patch('app.agents.tools.document.FileSandbox.validate_path_for_write') as mock_validate:
            mock_validate.return_value = Path("/storage/documents/new.pdf")

            result = _resolve_path("documents/new.pdf", for_write=True)

            assert result == Path("/storage/documents/new.pdf")
            mock_validate.assert_called_once_with("documents/new.pdf")

    def test_resolve_path_permission_denied(self):
        """测试路径权限被拒绝"""
        from app.agents.tools.document import _resolve_path

        with patch('app.agents.tools.document.FileSandbox.validate_path') as mock_validate:
            mock_validate.side_effect = PermissionError("Access denied")

            with pytest.raises(ValueError) as exc_info:
                _resolve_path("/etc/passwd")

            assert "Access denied" in str(exc_info.value)

    def test_resolve_path_outside_sandbox(self):
        """测试沙箱外路径"""
        from app.agents.tools.document import _resolve_path

        with patch('app.agents.tools.document.FileSandbox.validate_path') as mock_validate:
            mock_validate.side_effect = PermissionError("Path outside sandbox")

            with pytest.raises(ValueError):
                _resolve_path("../../../etc/passwd")


class TestReadPDFSync:
    """_read_pdf_sync 函数测试"""

    def test_read_pdf_basic(self):
        """测试基本 PDF 读取"""
        from app.agents.tools.document import _read_pdf_sync

        mock_reader = MagicMock()
        mock_reader.__len__ = MagicMock(return_value=3)

        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "第一页内容"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "第二页内容"
        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = "第三页内容"

        mock_reader.pages = [mock_page1, mock_page2, mock_page3]

        with patch('pypdf.PdfReader', return_value=mock_reader):
            total_pages, content_parts, total_text, needs_ocr = _read_pdf_sync(
                Path("/test/doc.pdf"), 1, None
            )

        assert total_pages == 3
        assert "第一页内容" in total_text

    def test_read_pdf_page_range(self):
        """测试读取指定页面范围"""
        from app.agents.tools.document import _read_pdf_sync

        mock_reader = MagicMock()
        mock_reader.__len__ = MagicMock(return_value=10)

        mock_pages = [MagicMock(extract_text=MagicMock(return_value=f"第{i+1}页")) for i in range(10)]
        mock_reader.pages = mock_pages

        with patch('pypdf.PdfReader', return_value=mock_reader):
            total_pages, content_parts, total_text, needs_ocr = _read_pdf_sync(
                Path("/test/doc.pdf"), 2, 5
            )

        assert total_pages == 10

    def test_read_pdf_scanned_needs_ocr(self):
        """测试扫描版 PDF 需要 OCR"""
        from app.agents.tools.document import _read_pdf_sync

        mock_reader = MagicMock()
        mock_reader.__len__ = MagicMock(return_value=1)

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "   "  # 只有空白
        mock_reader.pages = [mock_page]

        with patch('pypdf.PdfReader', return_value=mock_reader):
            total_pages, content_parts, total_text, needs_ocr = _read_pdf_sync(
                Path("/test/scan.pdf"), 1, None
            )

        assert needs_ocr is True

    def test_read_pdf_empty_pages(self):
        """测试空页面"""
        from app.agents.tools.document import _read_pdf_sync

        mock_reader = MagicMock()
        mock_reader.__len__ = MagicMock(return_value=2)

        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = ""
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = ""

        mock_reader.pages = [mock_page1, mock_page2]

        with patch('pypdf.PdfReader', return_value=mock_reader):
            total_pages, content_parts, total_text, needs_ocr = _read_pdf_sync(
                Path("/test/empty.pdf"), 1, None
            )

        assert total_text == ""


class TestReadWordSync:
    """_read_word_sync 函数测试"""

    def test_read_word_basic(self):
        """测试基本 Word 读取"""
        from app.agents.tools.document import _read_word_sync

        mock_doc = MagicMock()
        mock_para1 = MagicMock()
        mock_para1.text = "第一段内容"
        mock_para1.style = MagicMock(name="Normal")
        mock_para2 = MagicMock()
        mock_para2.text = "第二段内容"
        mock_para2.style = MagicMock(name="Normal")

        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_doc.tables = []

        with patch('docx.Document', return_value=mock_doc):
            result = _read_word_sync(Path("/test/doc.docx"))

        assert "第一段内容" in result
        assert "第二段内容" in result

    def test_read_word_with_headings(self):
        """测试带标题的 Word"""
        from app.agents.tools.document import _read_word_sync

        mock_doc = MagicMock()
        mock_heading = MagicMock()
        mock_heading.text = "这是标题"
        # 创建正确的 style mock
        mock_style = MagicMock()
        mock_style.name = "Heading 1"
        mock_heading.style = mock_style

        mock_para = MagicMock()
        mock_para.text = "正文内容"
        mock_para.style = MagicMock(name="Normal")

        mock_doc.paragraphs = [mock_heading, mock_para]
        mock_doc.tables = []

        with patch('docx.Document', return_value=mock_doc):
            result = _read_word_sync(Path("/test/doc.docx"))

        # 验证标题被识别
        assert "这是标题" in result

    def test_read_word_with_tables(self):
        """测试带表格的 Word"""
        from app.agents.tools.document import _read_word_sync

        mock_doc = MagicMock()

        mock_para = MagicMock()
        mock_para.text = "正文"
        mock_para.style = MagicMock(name="Normal")

        mock_cell1 = MagicMock()
        mock_cell1.text = "单元格1"
        mock_cell2 = MagicMock()
        mock_cell2.text = "单元格2"
        mock_row = MagicMock()
        mock_row.cells = [mock_cell1, mock_cell2]
        mock_table = MagicMock()
        mock_table.rows = [mock_row]

        mock_doc.paragraphs = [mock_para]
        mock_doc.tables = [mock_table]

        with patch('docx.Document', return_value=mock_doc):
            result = _read_word_sync(Path("/test/doc.docx"))

        assert "表格内容" in result
        assert "单元格1" in result

    def test_read_word_empty_document(self):
        """测试空文档"""
        from app.agents.tools.document import _read_word_sync

        mock_doc = MagicMock()
        mock_doc.paragraphs = []
        mock_doc.tables = []

        with patch('docx.Document', return_value=mock_doc):
            result = _read_word_sync(Path("/test/empty.docx"))

        assert "Word 文档" in result


class TestReadPDF:
    """read_pdf 工具测试"""

    @pytest.mark.asyncio
    async def test_read_pdf_file_not_exists(self):
        """测试文件不存在"""
        from app.agents.tools.document import read_pdf

        with patch('app.agents.tools.document._resolve_path') as mock_resolve:
            mock_resolve.return_value = MagicMock(
                exists=MagicMock(return_value=False),
                suffix='.pdf'
            )

            result = await read_pdf.ainvoke({"file_path": "/test/notfound.pdf"})

        assert "错误" in result or "不存在" in result

    @pytest.mark.asyncio
    async def test_read_pdf_not_pdf_format(self):
        """测试非 PDF 格式"""
        from app.agents.tools.document import read_pdf

        with patch('app.agents.tools.document._resolve_path') as mock_resolve:
            mock_resolve.return_value = MagicMock(
                exists=MagicMock(return_value=True),
                suffix='.txt'
            )

            result = await read_pdf.ainvoke({"file_path": "/test/doc.txt"})

        assert "错误" in result or "不是 PDF" in result

    @pytest.mark.asyncio
    async def test_read_pdf_invalid_page_range(self):
        """测试无效页码范围"""
        from app.agents.tools.document import read_pdf

        with patch('app.agents.tools.document._resolve_path') as mock_resolve, \
             patch('app.agents.tools.document._read_pdf_sync') as mock_read:
            mock_resolve.return_value = MagicMock(
                exists=MagicMock(return_value=True),
                suffix='.pdf',
                name='test.pdf'
            )
            mock_read.return_value = (3, [], "", False)

            result = await read_pdf.ainvoke({
                "file_path": "/test/doc.pdf",
                "start_page": 100  # 超出范围
            })

        assert "错误" in result or "超出范围" in result

    @pytest.mark.asyncio
    async def test_read_pdf_with_ocr_mode(self):
        """测试 OCR 模式"""
        from app.agents.tools.document import read_pdf

        with patch('app.agents.tools.document._resolve_path') as mock_resolve, \
             patch('app.agents.tools.document._read_pdf_sync') as mock_read, \
             patch('app.agents.tools.document._ocr_pdf', new_callable=AsyncMock) as mock_ocr:
            mock_resolve.return_value = MagicMock(
                exists=MagicMock(return_value=True),
                suffix='.pdf',
                name='scan.pdf'
            )
            mock_read.return_value = (1, [], "", True)  # 需要 OCR
            mock_ocr.return_value = "OCR 提取的内容"

            result = await read_pdf.ainvoke({
                "file_path": "/test/scan.pdf",
                "use_ocr": True
            })

        assert mock_ocr.called

    @pytest.mark.asyncio
    async def test_read_pdf_permission_error(self):
        """测试权限错误"""
        from app.agents.tools.document import read_pdf

        with patch('app.agents.tools.document._resolve_path') as mock_resolve:
            mock_resolve.side_effect = ValueError("权限被拒绝")

            result = await read_pdf.ainvoke({"file_path": "/test/protected.pdf"})

        assert "错误" in result


class TestReadWord:
    """read_word 工具测试"""

    @pytest.mark.asyncio
    async def test_read_word_file_not_exists(self):
        """测试文件不存在"""
        from app.agents.tools.document import read_word

        with patch('app.agents.tools.document._resolve_path') as mock_resolve:
            mock_resolve.return_value = MagicMock(
                exists=MagicMock(return_value=False),
                suffix='.docx'
            )

            result = await read_word.ainvoke({"file_path": "/test/notfound.docx"})

        assert "错误" in result or "不存在" in result

    @pytest.mark.asyncio
    async def test_read_word_invalid_format(self):
        """测试非 Word 格式"""
        from app.agents.tools.document import read_word

        with patch('app.agents.tools.document._resolve_path') as mock_resolve:
            mock_resolve.return_value = MagicMock(
                exists=MagicMock(return_value=True),
                suffix='.pdf'
            )

            result = await read_word.ainvoke({"file_path": "/test/doc.pdf"})

        assert "错误" in result or "不是 Word" in result

    @pytest.mark.asyncio
    async def test_read_word_old_doc_format(self):
        """测试旧版 .doc 格式"""
        from app.agents.tools.document import read_word

        with patch('app.agents.tools.document._resolve_path') as mock_resolve:
            mock_resolve.return_value = MagicMock(
                exists=MagicMock(return_value=True),
                suffix='.doc'
            )

            result = await read_word.ainvoke({"file_path": "/test/old.doc"})

        assert "错误" in result or "不支持" in result or ".docx" in result

    @pytest.mark.asyncio
    async def test_read_word_permission_error(self):
        """测试权限错误"""
        from app.agents.tools.document import read_word

        with patch('app.agents.tools.document._resolve_path') as mock_resolve:
            mock_resolve.side_effect = ValueError("权限被拒绝")

            result = await read_word.ainvoke({"file_path": "/test/protected.docx"})

        assert "错误" in result


class TestOcrPDF:
    """_ocr_pdf 函数测试"""

    @pytest.mark.asyncio
    async def test_ocr_pdf_success(self):
        """测试 OCR PDF 成功"""
        from app.agents.tools.document import _ocr_pdf

        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="OCR 文本"))

        mock_fitz = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_fitz.open.return_value = mock_doc

        with patch('app.llm.model_factory.ModelFactory.get_vision_model', return_value=mock_model), \
             patch('app.agents.tools.document._render_pdf_page_sync') as mock_render, \
             patch('app.utils.image_utils.build_openai_image_content_async') as mock_build:
            mock_render.return_value = "data:image/png;base64,xxx"
            mock_build.return_value = [{"type": "text", "text": "prompt"}]

            result = await _ocr_pdf(Path("/test/scan.pdf"), 1, 1)

        assert "OCR" in result or "PDF" in result

    @pytest.mark.asyncio
    async def test_ocr_pdf_import_error(self):
        """测试 PyMuPDF 未安装"""
        from app.agents.tools.document import _ocr_pdf

        # 模拟 fitz 导入失败
        with patch.dict('sys.modules', {'fitz': None}):
            result = await _ocr_pdf(Path("/test/scan.pdf"), 1, 1)

        assert "错误" in result or "PyMuPDF" in result


class TestRenderPDFPageSync:
    """_render_pdf_page_sync 函数测试"""

    def test_render_pdf_page(self):
        """测试渲染 PDF 页面"""
        from app.agents.tools.document import _render_pdf_page_sync

        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_pixmap = MagicMock()
        mock_pixmap.tobytes.return_value = b"fake_png_data"
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_doc.close = MagicMock()

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc
        mock_fitz.Matrix = MagicMock()

        with patch.dict('sys.modules', {'fitz': mock_fitz}):
            with patch('base64.b64encode') as mock_b64:
                mock_b64.return_value.decode.return_value = "base64string"

                try:
                    result = _render_pdf_page_sync(Path("/test/doc.pdf"), 0)
                    assert "data:image/png;base64" in result or "base64" in result
                except ImportError:
                    # 如果 fitz 未安装，跳过测试
                    pytest.skip("PyMuPDF not installed")


class TestDocumentToolDefinitions:
    """文档工具定义测试"""

    def test_read_pdf_tool_definition(self):
        """测试 read_pdf 工具定义"""
        from app.agents.tools.document import read_pdf

        assert read_pdf.name == "read_pdf"
        assert "PDF" in read_pdf.description

    def test_read_word_tool_definition(self):
        """测试 read_word 工具定义"""
        from app.agents.tools.document import read_word

        assert read_word.name == "read_word"
        assert "Word" in read_word.description or "docx" in read_word.description

    def test_tools_have_required_args(self):
        """测试工具有必需参数"""
        from app.agents.tools.document import read_pdf, read_word

        pdf_args = read_pdf.args_schema.model_json_schema()
        assert "file_path" in pdf_args.get("properties", {})

        word_args = read_word.args_schema.model_json_schema()
        assert "file_path" in word_args.get("properties", {})