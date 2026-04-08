"""混合检索器 - 向量 + BM25"""

import logging

from langchain_chroma import Chroma
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class HybridRetriever:
    """混合检索器: 向量 + BM25

    结合向量检索和 BM25 关键词检索，通过加权融合提升检索质量。
    """

    def __init__(
        self,
        vector_store: Chroma,
        alpha: float = 0.5,
        use_chinese_tokenizer: bool = True,
    ):
        """
        Args:
            vector_store: 向量存储
            alpha: 向量检索权重 (0-1)，BM25 权重为 (1-alpha)
                - alpha=1.0: 纯向量检索
                - alpha=0.5: 向量和 BM25 各占 50%
                - alpha=0.0: 纯 BM25 检索
            use_chinese_tokenizer: 是否使用中文分词
        """
        self.vector_store = vector_store
        self.alpha = alpha
        self.use_chinese_tokenizer = use_chinese_tokenizer

        self._bm25 = None
        self._documents = []

    def _tokenize(self, text: str) -> list[str]:
        """分词

        Args:
            text: 待分词文本

        Returns:
            分词结果列表
        """
        if self.use_chinese_tokenizer:
            try:
                import jieba
                return list(jieba.cut(text))
            except ImportError:
                logger.warning("[RAG] jieba not installed, using simple split")
                return text.split()
        return text.split()

    def _normalize_scores(self, scores: list[float]) -> list[float]:
        """分数归一化到 [0, 1]

        Args:
            scores: 原始分数列表

        Returns:
            归一化后的分数列表
        """
        if not scores:
            return []

        min_s, max_s = min(scores), max(scores)
        if max_s == min_s:
            return [0.5] * len(scores)

        return [(s - min_s) / (max_s - min_s) for s in scores]

    def index_documents(self, documents: list[Document]) -> None:
        """索引文档（用于 BM25）

        需要在检索前调用，将文档索引到 BM25。

        Args:
            documents: 文档列表
        """
        if not documents:
            return

        try:
            from rank_bm25 import BM25Okapi

            self._documents = documents

            tokenized = [self._tokenize(doc.page_content) for doc in documents]
            self._bm25 = BM25Okapi(tokenized)

            logger.info(f"[RAG] BM25 indexed {len(documents)} documents")
        except ImportError:
            logger.warning("[RAG] rank-bm25 not installed, BM25 retrieval unavailable")
            self._bm25 = None
        except Exception as e:
            logger.error(f"[RAG] Failed to index documents for BM25: {e}")
            self._bm25 = None

    async def aretrieve(
        self,
        query: str,
        k: int = 4,
    ) -> list[Document]:
        """混合检索

        Args:
            query: 查询文本
            k: 返回数量

        Returns:
            检索结果文档列表
        """
        if self._bm25 is None:
            try:
                return await self.vector_store.asimilarity_search(query, k=k)
            except Exception as e:
                logger.error(f"[RAG] Vector search failed: {e}")
                return []

        try:
            vector_results = await self.vector_store.asimilarity_search_with_score(
                query, k=k * 2
            )
        except Exception as e:
            logger.error(f"[RAG] Vector search failed: {e}")
            vector_results = []

        tokenized_query = self._tokenize(query)
        bm25_scores = self._bm25.get_scores(tokenized_query)

        vector_scores = self._normalize_scores([score for _, score in vector_results])
        bm25_scores = self._normalize_scores(list(bm25_scores))

        doc_scores = {}
        for i, (doc, _) in enumerate(vector_results):
            doc_id = doc.metadata.get("_id", str(i))
            doc_scores[doc_id] = {
                "doc": doc,
                "vector_score": vector_scores[i] if i < len(vector_scores) else 0,
                "bm25_score": 0,
            }

        for i, doc in enumerate(self._documents):
            doc_id = doc.metadata.get("_id", str(i))
            if doc_id in doc_scores:
                doc_scores[doc_id]["bm25_score"] = bm25_scores[i] if i < len(bm25_scores) else 0

        for doc_id in doc_scores:
            v = doc_scores[doc_id]["vector_score"]
            b = doc_scores[doc_id]["bm25_score"]
            doc_scores[doc_id]["final_score"] = self.alpha * v + (1 - self.alpha) * b

        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1]["final_score"],
            reverse=True
        )

        return [item[1]["doc"] for item in sorted_docs[:k]]
