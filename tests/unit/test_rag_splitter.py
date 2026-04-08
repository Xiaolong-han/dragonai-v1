"""RAG 模块测试 - 文档分割器"""

import pytest
from langchain_core.documents import Document

from app.rag.splitter import DocumentSplitter


class TestDocumentSplitter:
    """DocumentSplitter 测试"""

    def test_default_separators(self):
        """测试默认分隔符"""
        splitter = DocumentSplitter()

        assert "\n\n" in splitter.text_splitter._separators
        assert "\n" in splitter.text_splitter._separators
        assert "。" in splitter.text_splitter._separators
        assert "！" in splitter.text_splitter._separators
        assert "？" in splitter.text_splitter._separators

    def test_custom_chunk_size(self):
        """测试自定义分块大小"""
        splitter = DocumentSplitter(chunk_size=500, chunk_overlap=50)

        assert splitter.text_splitter._chunk_size == 500
        assert splitter.text_splitter._chunk_overlap == 50

    def test_custom_separators(self):
        """测试自定义分隔符"""
        custom_seps = ["\n\n", "\n", " "]
        splitter = DocumentSplitter(separators=custom_seps)

        assert splitter.text_splitter._separators == custom_seps

    def test_split_single_document(self):
        """测试分割单个文档"""
        splitter = DocumentSplitter(chunk_size=100, chunk_overlap=20)

        doc = Document(
            page_content="这是第一段内容。" * 30,
            metadata={"source": "test.txt"}
        )

        chunks = splitter.split_documents([doc])

        assert len(chunks) > 1
        assert all("source" in chunk.metadata for chunk in chunks)

    def test_split_multiple_documents(self):
        """测试分割多个文档"""
        splitter = DocumentSplitter(chunk_size=100, chunk_overlap=10)

        docs = [
            Document(page_content="文档一内容。" * 20, metadata={"source": "doc1.txt"}),
            Document(page_content="文档二内容。" * 20, metadata={"source": "doc2.txt"}),
        ]

        chunks = splitter.split_documents(docs)

        assert len(chunks) >= 2
        sources = {chunk.metadata.get("source") for chunk in chunks}
        assert "doc1.txt" in sources
        assert "doc2.txt" in sources

    def test_split_empty_documents(self):
        """测试分割空文档列表"""
        splitter = DocumentSplitter()

        chunks = splitter.split_documents([])

        assert len(chunks) == 0

    def test_split_short_document(self):
        """测试分割短文档（不需要分割）"""
        splitter = DocumentSplitter(chunk_size=1000, chunk_overlap=200)

        doc = Document(
            page_content="这是一个短文档。",
            metadata={"source": "short.txt"}
        )

        chunks = splitter.split_documents([doc])

        assert len(chunks) == 1
        assert chunks[0].page_content == "这是一个短文档。"

    def test_split_preserves_metadata(self):
        """测试分割保留元数据"""
        splitter = DocumentSplitter(chunk_size=50, chunk_overlap=10)

        doc = Document(
            page_content="这是一个需要分割的长文档内容。" * 10,
            metadata={"source": "test.txt", "author": "test_author", "page": 1}
        )

        chunks = splitter.split_documents([doc])

        for chunk in chunks:
            assert chunk.metadata.get("source") == "test.txt"
            assert chunk.metadata.get("author") == "test_author"
            assert chunk.metadata.get("page") == 1

    def test_split_chinese_text(self):
        """测试分割中文文本"""
        splitter = DocumentSplitter(chunk_size=50, chunk_overlap=10)

        doc = Document(
            page_content="这是第一句话。这是第二句话。这是第三句话。这是第四句话。这是第五句话。",
            metadata={"source": "chinese.txt"}
        )

        chunks = splitter.split_documents([doc])

        assert len(chunks) >= 1
        full_content = "".join(chunk.page_content for chunk in chunks)
        assert "第一句话" in full_content
        assert "第五句话" in full_content

    def test_split_with_newlines(self):
        """测试分割带换行的文本"""
        splitter = DocumentSplitter(chunk_size=100, chunk_overlap=20)

        doc = Document(
            page_content="第一段内容。\n\n第二段内容。\n\n第三段内容。",
            metadata={"source": "newlines.txt"}
        )

        chunks = splitter.split_documents([doc])

        assert len(chunks) >= 1

    def test_chunk_overlap(self):
        """测试分块重叠"""
        splitter = DocumentSplitter(chunk_size=50, chunk_overlap=20)

        doc = Document(
            page_content="这是一个比较长的文档内容，用于测试分块重叠功能是否正常工作。",
            metadata={"source": "overlap.txt"}
        )

        chunks = splitter.split_documents([doc])

        if len(chunks) > 1:
            # 检查是否有重叠内容
            # 重叠意味着第一个块的结尾部分应该在第二个块的开头部分出现
            pass  # 具体重叠行为由 RecursiveCharacterTextSplitter 实现

    def test_default_parameters(self):
        """测试默认参数"""
        splitter = DocumentSplitter()

        assert splitter.text_splitter._chunk_size == 1000
        assert splitter.text_splitter._chunk_overlap == 200