"""RAG 模块测试 - 重排序器"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.documents import Document

from app.rag.reranker import BaseReranker, CohereReranker, CrossEncoderReranker, get_reranker


class TestBaseReranker:
    """BaseReranker 基类测试"""

    def test_is_abstract(self):
        """测试基类是抽象类"""
        with pytest.raises(TypeError):
            BaseReranker()

    def test_subclass_must_implement_rerank(self):
        """测试子类必须实现 rerank 方法"""
        class IncompleteReranker(BaseReranker):
            pass

        with pytest.raises(TypeError):
            IncompleteReranker()


class TestCohereReranker:
    """CohereReranker 测试"""

    def test_init_success(self):
        """测试成功初始化"""
        mock_rerank = MagicMock()

        with patch('langchain_cohere.CohereRerank', return_value=mock_rerank):
            reranker = CohereReranker()

            assert reranker._available is True
            assert reranker._reranker is mock_rerank

    def test_init_import_error(self):
        """测试 langchain-cohere 未安装"""
        with patch('langchain_cohere.CohereRerank', side_effect=ImportError):
            reranker = CohereReranker()

            assert reranker._available is False

    def test_init_exception(self):
        """测试初始化异常处理"""
        with patch('langchain_cohere.CohereRerank', side_effect=Exception("API error")):
            reranker = CohereReranker()

            assert reranker._available is False

    def test_init_custom_model(self):
        """测试自定义模型"""
        mock_rerank = MagicMock()

        with patch('langchain_cohere.CohereRerank', return_value=mock_rerank) as mock_class:
            reranker = CohereReranker(model="rerank-english-v3.0")

            mock_class.assert_called_once_with(model="rerank-english-v3.0")

    @pytest.mark.asyncio
    async def test_rerank_success(self):
        """测试成功重排序"""
        mock_rerank = MagicMock()
        mock_result = MagicMock()
        mock_result.index = 1
        mock_rerank.arerank = AsyncMock(return_value=[mock_result])

        with patch('langchain_cohere.CohereRerank', return_value=mock_rerank):
            reranker = CohereReranker()

            docs = [
                Document(page_content="文档一", metadata={}),
                Document(page_content="文档二", metadata={}),
            ]

            results = await reranker.rerank("查询", docs, top_k=1)

            assert len(results) == 1
            assert results[0] == docs[1]

    @pytest.mark.asyncio
    async def test_rerank_empty_documents(self):
        """测试空文档列表"""
        with patch('langchain_cohere.CohereRerank'):
            reranker = CohereReranker()

            results = await reranker.rerank("查询", [], top_k=4)

            assert results == []

    @pytest.mark.asyncio
    async def test_rerank_unavailable(self):
        """测试不可用时返回原列表"""
        with patch('langchain_cohere.CohereRerank', side_effect=ImportError):
            reranker = CohereReranker()

            docs = [
                Document(page_content="文档一", metadata={}),
                Document(page_content="文档二", metadata={}),
            ]

            results = await reranker.rerank("查询", docs, top_k=1)

            assert len(results) == 1
            assert results[0] == docs[0]

    @pytest.mark.asyncio
    async def test_rerank_exception(self):
        """测试重排序异常处理"""
        mock_rerank = MagicMock()
        mock_rerank.arerank = AsyncMock(side_effect=Exception("API error"))

        with patch('langchain_cohere.CohereRerank', return_value=mock_rerank):
            reranker = CohereReranker()

            docs = [
                Document(page_content="文档一", metadata={}),
            ]

            results = await reranker.rerank("查询", docs, top_k=1)

            # 异常时应返回原列表
            assert results == docs[:1]


class TestCrossEncoderReranker:
    """CrossEncoderReranker 测试"""

    def test_init_success(self):
        """测试成功初始化"""
        mock_model = MagicMock()

        with patch('sentence_transformers.CrossEncoder', return_value=mock_model) as mock_class:
            reranker = CrossEncoderReranker()

            assert reranker._available is True
            assert reranker._model is mock_model

    def test_init_import_error(self):
        """测试 sentence-transformers 未安装"""
        with patch('sentence_transformers.CrossEncoder', side_effect=ImportError):
            reranker = CrossEncoderReranker()

            assert reranker._available is False

    def test_init_exception(self):
        """测试初始化异常处理"""
        with patch('sentence_transformers.CrossEncoder', side_effect=Exception("Model load error")):
            reranker = CrossEncoderReranker()

            assert reranker._available is False

    def test_init_custom_model(self):
        """测试自定义模型"""
        mock_model = MagicMock()

        with patch('sentence_transformers.CrossEncoder', return_value=mock_model) as mock_class:
            reranker = CrossEncoderReranker(model_name="BAAI/bge-reranker-large")

            mock_class.assert_called_once_with("BAAI/bge-reranker-large")

    @pytest.mark.asyncio
    async def test_rerank_success(self):
        """测试成功重排序"""
        mock_model = MagicMock()
        # 模型返回分数，第二个文档分数更高
        mock_model.predict.return_value = [0.3, 0.9]

        with patch('sentence_transformers.CrossEncoder', return_value=mock_model):
            reranker = CrossEncoderReranker()

            docs = [
                Document(page_content="文档一", metadata={"id": 1}),
                Document(page_content="文档二", metadata={"id": 2}),
            ]

            results = await reranker.rerank("查询", docs, top_k=2)

            assert len(results) == 2
            # 第二个文档分数更高，应排在前面
            assert results[0] == docs[1]
            assert results[1] == docs[0]

    @pytest.mark.asyncio
    async def test_rerank_empty_documents(self):
        """测试空文档列表"""
        with patch('sentence_transformers.CrossEncoder'):
            reranker = CrossEncoderReranker()

            results = await reranker.rerank("查询", [], top_k=4)

            assert results == []

    @pytest.mark.asyncio
    async def test_rerank_unavailable(self):
        """测试不可用时返回原列表"""
        with patch('sentence_transformers.CrossEncoder', side_effect=ImportError):
            reranker = CrossEncoderReranker()

            docs = [
                Document(page_content="文档一", metadata={}),
                Document(page_content="文档二", metadata={}),
            ]

            results = await reranker.rerank("查询", docs, top_k=1)

            assert len(results) == 1
            assert results[0] == docs[0]

    @pytest.mark.asyncio
    async def test_rerank_exception(self):
        """测试重排序异常处理"""
        mock_model = MagicMock()
        mock_model.predict.side_effect = Exception("Predict error")

        with patch('sentence_transformers.CrossEncoder', return_value=mock_model):
            reranker = CrossEncoderReranker()

            docs = [Document(page_content="文档一", metadata={})]

            results = await reranker.rerank("查询", docs, top_k=1)

            assert results == docs[:1]

    @pytest.mark.asyncio
    async def test_rerank_top_k_limit(self):
        """测试 top_k 限制"""
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.9, 0.7, 0.5, 0.3]

        with patch('sentence_transformers.CrossEncoder', return_value=mock_model):
            reranker = CrossEncoderReranker()

            docs = [
                Document(page_content=f"文档{i}", metadata={})
                for i in range(4)
            ]

            results = await reranker.rerank("查询", docs, top_k=2)

            assert len(results) == 2


class TestGetReranker:
    """get_reranker 工厂函数测试"""

    def test_get_cohere_reranker(self):
        """测试获取 Cohere 重排序器"""
        with patch('langchain_cohere.CohereRerank'):
            reranker = get_reranker(provider="cohere")

            assert isinstance(reranker, CohereReranker)

    def test_get_cohere_reranker_unavailable(self):
        """测试获取不可用的 Cohere 重排序器"""
        with patch('langchain_cohere.CohereRerank', side_effect=ImportError):
            reranker = get_reranker(provider="cohere")

            assert reranker is None

    def test_get_cross_encoder_reranker(self):
        """测试获取 CrossEncoder 重排序器"""
        with patch('sentence_transformers.CrossEncoder'):
            reranker = get_reranker(provider="cross-encoder")

            assert isinstance(reranker, CrossEncoderReranker)

    def test_get_cross_encoder_reranker_unavailable(self):
        """测试获取不可用的 CrossEncoder 重排序器"""
        with patch('sentence_transformers.CrossEncoder', side_effect=ImportError):
            reranker = get_reranker(provider="cross-encoder")

            assert reranker is None

    def test_get_cross_encoder_custom_model(self):
        """测试获取自定义模型的 CrossEncoder"""
        with patch('sentence_transformers.CrossEncoder', return_value=MagicMock()) as mock:
            reranker = get_reranker(
                provider="cross-encoder",
                model_name="BAAI/bge-reranker-large"
            )

            mock.assert_called_once_with("BAAI/bge-reranker-large")

    def test_get_reranker_default_provider(self):
        """测试默认 provider 是 cross-encoder"""
        with patch('sentence_transformers.CrossEncoder'):
            reranker = get_reranker()

            assert isinstance(reranker, CrossEncoderReranker)

    def test_get_reranker_unknown_provider(self):
        """测试未知 provider 返回 cross-encoder"""
        with patch('sentence_transformers.CrossEncoder'):
            reranker = get_reranker(provider="unknown")

            # 未知 provider 会 fallback 到 cross-encoder
            assert isinstance(reranker, CrossEncoderReranker)