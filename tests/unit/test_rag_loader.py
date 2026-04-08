"""RAG 模块测试 - 文档加载器"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

from app.rag.loader import DocumentLoader
from langchain_core.documents import Document


class TestDocumentLoader:
    """DocumentLoader 测试"""

    def test_supported_extensions(self):
        """测试支持的文件扩展名"""
        assert ".pdf" in DocumentLoader.SUPPORTED_EXTENSIONS
        assert ".docx" in DocumentLoader.SUPPORTED_EXTENSIONS
        assert ".md" in DocumentLoader.SUPPORTED_EXTENSIONS
        assert ".txt" in DocumentLoader.SUPPORTED_EXTENSIONS
        assert ".markdown" in DocumentLoader.SUPPORTED_EXTENSIONS

    def test_file_not_found(self):
        """测试文件不存在时抛出异常"""
        with pytest.raises(FileNotFoundError) as exc_info:
            DocumentLoader.load_file("/nonexistent/path/file.pdf")

        assert "File not found" in str(exc_info.value)

    def test_unsupported_format(self):
        """测试不支持的文件格式"""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                DocumentLoader.load_file(temp_path)

            assert "Unsupported file format" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_load_txt_file(self):
        """测试加载文本文件"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode='w', encoding='utf-8') as f:
            f.write("这是一个测试文档。\n包含多行内容。")
            temp_path = f.name

        try:
            documents = DocumentLoader.load_file(temp_path)

            assert len(documents) >= 1
            assert "测试文档" in documents[0].page_content
            assert documents[0].metadata.get("source") == temp_path
            assert documents[0].metadata.get("file_name") is not None
        finally:
            os.unlink(temp_path)

    def test_load_markdown_file(self):
        """测试加载 Markdown 文件"""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode='w', encoding='utf-8') as f:
            f.write("# 标题\n\n这是正文内容。")
            temp_path = f.name

        try:
            # Mock UnstructuredMarkdownLoader
            mock_loader = MagicMock()
            mock_loader.load.return_value = [
                Document(page_content="# 标题\n\n这是正文内容。", metadata={})
            ]

            with patch('app.rag.loader.UnstructuredMarkdownLoader', return_value=mock_loader):
                documents = DocumentLoader.load_file(temp_path)

            assert len(documents) >= 1
            assert documents[0].metadata.get("source") is not None
        finally:
            os.unlink(temp_path)

    def test_load_pdf_file(self):
        """测试加载 PDF 文件"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4\n%test pdf content")
            temp_path = f.name

        try:
            mock_loader = MagicMock()
            mock_loader.load.return_value = [
                Document(page_content="PDF content page 1", metadata={"page": 1}),
                Document(page_content="PDF content page 2", metadata={"page": 2}),
            ]

            with patch('app.rag.loader.PyPDFLoader', return_value=mock_loader):
                documents = DocumentLoader.load_file(temp_path)

            assert len(documents) == 2
            assert all("source" in doc.metadata for doc in documents)
        finally:
            os.unlink(temp_path)

    def test_load_docx_file(self):
        """测试加载 Word 文件"""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            f.write(b"PK\x03\x04")  # DOCX 文件头
            temp_path = f.name

        try:
            mock_loader = MagicMock()
            mock_loader.load.return_value = [
                Document(page_content="Word document content", metadata={})
            ]

            with patch('app.rag.loader.Docx2txtLoader', return_value=mock_loader):
                documents = DocumentLoader.load_file(temp_path)

            assert len(documents) >= 1
            assert documents[0].metadata.get("file_name") is not None
        finally:
            os.unlink(temp_path)

    def test_metadata_preserved(self):
        """测试原有 metadata 被保留"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode='w', encoding='utf-8') as f:
            f.write("test content")
            temp_path = f.name

        try:
            mock_loader = MagicMock()
            mock_loader.load.return_value = [
                Document(
                    page_content="content",
                    metadata={"existing_key": "existing_value"}
                )
            ]

            with patch('app.rag.loader.TextLoader', return_value=mock_loader):
                documents = DocumentLoader.load_file(temp_path)

            assert documents[0].metadata.get("existing_key") == "existing_value"
            assert documents[0].metadata.get("source") is not None
        finally:
            os.unlink(temp_path)

    def test_get_loader_txt(self):
        """测试获取 txt 加载器"""
        path = Path("/test/file.txt")
        loader = DocumentLoader._get_loader(path, ".txt")
        assert loader is not None

    def test_get_loader_pdf(self):
        """测试获取 PDF 加载器"""
        with patch('app.rag.loader.PyPDFLoader') as mock:
            mock.return_value = MagicMock()
            path = Path("/test/file.pdf")
            loader = DocumentLoader._get_loader(path, ".pdf")
            mock.assert_called_once()

    def test_get_loader_docx(self):
        """测试获取 DOCX 加载器"""
        with patch('app.rag.loader.Docx2txtLoader') as mock:
            mock.return_value = MagicMock()
            path = Path("/test/file.docx")
            loader = DocumentLoader._get_loader(path, ".docx")
            mock.assert_called_once()

    def test_get_loader_markdown(self):
        """测试获取 Markdown 加载器"""
        with patch('app.rag.loader.UnstructuredMarkdownLoader') as mock:
            mock.return_value = MagicMock()
            path = Path("/test/file.md")
            loader = DocumentLoader._get_loader(path, ".md")
            mock.assert_called_once()

    def test_get_loader_unsupported(self):
        """测试获取不支持的加载器抛出异常"""
        with pytest.raises(ValueError) as exc_info:
            DocumentLoader._get_loader(Path("/test/file.xyz"), ".xyz")

        assert "Unsupported file format" in str(exc_info.value)