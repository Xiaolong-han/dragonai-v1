"""重排序器模块"""

import logging
from abc import ABC, abstractmethod

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class BaseReranker(ABC):
    """重排序器基类"""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: list[Document],
        top_k: int = 4,
    ) -> list[Document]:
        """重排序文档

        Args:
            query: 查询文本
            documents: 待排序的文档列表
            top_k: 返回的文档数量

        Returns:
            重排序后的文档列表
        """
        pass


class CohereReranker(BaseReranker):
    """Cohere Rerank API"""

    def __init__(self, model: str = "rerank-multilingual"):
        """
        Args:
            model: Cohere 模型名称
                - rerank-multilingual: 多语言支持
                - rerank-english-v3.0: 英文
        """
        try:
            from langchain_cohere import CohereRerank
            self._reranker = CohereRerank(model=model)
            self._available = True
        except ImportError:
            logger.warning("[RAG] langchain-cohere not installed, CohereReranker unavailable")
            self._available = False
        except Exception as e:
            logger.warning(f"[RAG] Failed to initialize CohereReranker: {e}")
            self._available = False

    async def rerank(
        self,
        query: str,
        documents: list[Document],
        top_k: int = 4,
    ) -> list[Document]:
        if not documents or not self._available:
            return documents[:top_k] if documents else []

        try:
            reranked = await self._reranker.arerank(
                documents=[doc.page_content for doc in documents],
                query=query,
                top_n=min(top_k, len(documents)),
            )

            return [documents[r.index] for r in reranked]
        except Exception as e:
            logger.error(f"[RAG] Cohere rerank failed: {e}")
            return documents[:top_k]


class CrossEncoderReranker(BaseReranker):
    """本地 Cross-Encoder 模型重排序

    使用 sentence-transformers 的 Cross-Encoder 模型，
    无需网络调用，适合离线场景。
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        """
        Args:
            model_name: 模型名称，推荐:
                - BAAI/bge-reranker-base: 中文效果好，速度快
                - BAAI/bge-reranker-large: 中文效果好，速度慢
                - cross-encoder/ms-marco-MiniLM-L-6-v2: 英文
        """
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(model_name)
            self._available = True
            logger.info(f"[RAG] CrossEncoderReranker initialized with model: {model_name}")
        except ImportError:
            logger.warning("[RAG] sentence-transformers not installed, CrossEncoderReranker unavailable")
            self._available = False
        except Exception as e:
            logger.warning(f"[RAG] Failed to initialize CrossEncoderReranker: {e}")
            self._available = False

    async def rerank(
        self,
        query: str,
        documents: list[Document],
        top_k: int = 4,
    ) -> list[Document]:
        if not documents or not self._available:
            return documents[:top_k] if documents else []

        try:
            pairs = [[query, doc.page_content] for doc in documents]

            scores = self._model.predict(pairs)

            scored_docs = list(zip(documents, scores))
            scored_docs.sort(key=lambda x: x[1], reverse=True)

            return [doc for doc, _ in scored_docs[:top_k]]
        except Exception as e:
            logger.error(f"[RAG] CrossEncoder rerank failed: {e}")
            return documents[:top_k]


def get_reranker(
    provider: str = "cross-encoder",
    model_name: str | None = None,
    **kwargs,
) -> BaseReranker | None:
    """获取重排序器

    Args:
        provider: "cohere" | "cross-encoder"
        model_name: 模型名称 (仅 cross-encoder 使用)

    Returns:
        重排序器实例，如果初始化失败返回 None
    """
    if provider == "cohere":
        reranker = CohereReranker(**kwargs)
        return reranker if reranker._available else None

    reranker = CrossEncoderReranker(model_name=model_name or "BAAI/bge-reranker-base", **kwargs)
    return reranker if reranker._available else None
