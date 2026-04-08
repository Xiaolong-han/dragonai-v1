"""RAG 模块测试 - 向量存储管理器"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import tempfile
import os

from app.rag.vector_store import VectorStoreManager


class TestVectorStoreManager:
    """VectorStoreManager 测试"""

    def test_init_with_persist_dir(self):
        """测试初始化持久化目录"""
        with patch('app.rag.vector_store.settings') as mock_settings:
            mock_settings.chroma_persist_dir = "/test/chroma"

            manager = VectorStoreManager()

            assert manager.persist_dir == "/test/chroma"
            assert manager._client is None
            assert manager._chroma_clients == {}

    def test_client_lazy_initialization(self):
        """测试客户端延迟初始化"""
        with patch('app.rag.vector_store.settings') as mock_settings, \
             patch('app.rag.vector_store.chromadb.PersistentClient') as mock_client:

            mock_settings.chroma_persist_dir = "/test/chroma"
            mock_client.return_value = MagicMock()

            manager = VectorStoreManager()

            # 首次访问应初始化
            client = manager.client
            mock_client.assert_called_once()
            assert client is not None

    def test_client_cached(self):
        """测试客户端缓存"""
        with patch('app.rag.vector_store.settings') as mock_settings, \
             patch('app.rag.vector_store.chromadb.PersistentClient') as mock_client:

            mock_settings.chroma_persist_dir = "/test/chroma"
            mock_client.return_value = MagicMock()

            manager = VectorStoreManager()

            # 多次访问应返回同一实例
            client1 = manager.client
            client2 = manager.client

            mock_client.assert_called_once()
            assert client1 is client2

    def test_get_chroma_vector_store(self):
        """测试获取 Chroma 向量存储"""
        with patch('app.rag.vector_store.settings') as mock_settings, \
             patch('app.rag.vector_store.chromadb.PersistentClient') as mock_chroma_client, \
             patch('app.rag.vector_store.Chroma') as mock_chroma:

            mock_settings.chroma_persist_dir = "/test/chroma"
            mock_chroma_client.return_value = MagicMock()
            mock_store = MagicMock()
            mock_chroma.return_value = mock_store

            manager = VectorStoreManager()
            embedding_fn = MagicMock()

            store = manager.get_chroma_vector_store("test_collection", embedding_fn)

            mock_chroma.assert_called_once()
            assert store is mock_store

    def test_get_chroma_vector_store_cached(self):
        """测试向量存储缓存"""
        with patch('app.rag.vector_store.settings') as mock_settings, \
             patch('app.rag.vector_store.chromadb.PersistentClient') as mock_chroma_client, \
             patch('app.rag.vector_store.Chroma') as mock_chroma:

            mock_settings.chroma_persist_dir = "/test/chroma"
            mock_chroma_client.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()

            manager = VectorStoreManager()
            embedding_fn = MagicMock()

            # 多次获取同一 collection 应缓存
            store1 = manager.get_chroma_vector_store("test_collection", embedding_fn)
            store2 = manager.get_chroma_vector_store("test_collection", embedding_fn)

            mock_chroma.assert_called_once()
            assert store1 is store2

    def test_get_different_collections(self):
        """测试获取不同 collection"""
        with patch('app.rag.vector_store.settings') as mock_settings, \
             patch('app.rag.vector_store.chromadb.PersistentClient') as mock_chroma_client, \
             patch('app.rag.vector_store.Chroma') as mock_chroma:

            mock_settings.chroma_persist_dir = "/test/chroma"
            mock_chroma_client.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()

            manager = VectorStoreManager()
            embedding_fn = MagicMock()

            store1 = manager.get_chroma_vector_store("collection1", embedding_fn)
            store2 = manager.get_chroma_vector_store("collection2", embedding_fn)

            assert mock_chroma.call_count == 2

    def test_delete_collection(self):
        """测试删除 collection"""
        with patch('app.rag.vector_store.settings') as mock_settings, \
             patch('app.rag.vector_store.chromadb.PersistentClient') as mock_chroma_client, \
             patch('app.rag.vector_store.Chroma') as mock_chroma:

            mock_settings.chroma_persist_dir = "/test/chroma"
            mock_inner_client = MagicMock()
            mock_chroma_client.return_value = mock_inner_client
            mock_chroma.return_value = MagicMock()

            manager = VectorStoreManager()
            embedding_fn = MagicMock()

            # 先获取再删除
            manager.get_chroma_vector_store("test_collection", embedding_fn)
            assert "test_collection" in manager._chroma_clients

            manager.delete_collection("test_collection")

            mock_inner_client.delete_collection.assert_called_once_with("test_collection")
            assert "test_collection" not in manager._chroma_clients

    def test_delete_nonexistent_collection(self):
        """测试删除不存在的 collection"""
        with patch('app.rag.vector_store.settings') as mock_settings, \
             patch('app.rag.vector_store.chromadb.PersistentClient') as mock_chroma_client:

            mock_settings.chroma_persist_dir = "/test/chroma"
            mock_inner_client = MagicMock()
            mock_chroma_client.return_value = mock_inner_client

            manager = VectorStoreManager()

            # 删除不存在的 collection 不应抛出异常
            manager.delete_collection("nonexistent")

    def test_delete_collection_with_exception(self):
        """测试删除 collection 时异常处理"""
        with patch('app.rag.vector_store.settings') as mock_settings, \
             patch('app.rag.vector_store.chromadb.PersistentClient') as mock_chroma_client:

            mock_settings.chroma_persist_dir = "/test/chroma"
            mock_inner_client = MagicMock()
            mock_inner_client.delete_collection.side_effect = Exception("Delete error")
            mock_chroma_client.return_value = mock_inner_client

            manager = VectorStoreManager()

            # 异常应被静默处理
            manager.delete_collection("test_collection")

    def test_singleton_instance(self):
        """测试单例实例存在"""
        from app.rag.vector_store import vector_store_manager

        assert vector_store_manager is not None
        assert isinstance(vector_store_manager, VectorStoreManager)