"""
集成测试配置 - 使用真实数据库和 Redis

使用方法:
    1. 确保本地 PostgreSQL 和 Redis 已启动
    2. 创建测试数据库: CREATE DATABASE dragonai_test;
    3. 运行测试: pytest tests/integration -m integration

隔离机制:
    - 数据库: 每个测试在事务中运行，结束后回滚
    - Redis: 使用 DB 15，测试后清理
    - 文件: 使用临时目录
"""

import os
import pytest
import pytest_asyncio
import uuid
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.database import Base, get_db
from app.main import create_app
from httpx import AsyncClient, ASGITransport


# =============================================================================
# 配置
# =============================================================================

# 从环境变量读取或使用默认值
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://test_user:test_pass@localhost:5432/dragonai_test"
)

TEST_REDIS_URL = os.getenv(
    "TEST_REDIS_URL",
    "redis://localhost:6379/15"
)

TEST_REDIS_KEY_PREFIX = os.getenv(
    "TEST_REDIS_KEY_PREFIX",
    "dragonai:test"
)


# =============================================================================
# Session 级别的 Fixtures
# =============================================================================

@pytest_asyncio.fixture(scope="session")
async def integration_engine():
    """
    集成测试数据库引擎 - Session 级别
    
    只创建一次数据库表，所有测试共享
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # 关闭 SQL 日志，减少噪音
        pool_pre_ping=True,  # 自动检测连接是否有效
    )
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Session 结束时清理
    async with engine.begin() as conn:
        # 清理数据但保留表结构
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    
    await engine.dispose()


@pytest.fixture(scope="session")
def integration_test_dir():
    """集成测试临时目录"""
    temp_dir = tempfile.mkdtemp(prefix="dragonai_integration_")
    yield temp_dir
    # Session 结束时清理
    shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# Function 级别的 Fixtures - 每个测试都重新创建
# =============================================================================

@pytest_asyncio.fixture
async def integration_db(integration_engine):
    """
    集成测试数据库会话 - 使用事务回滚实现隔离
    
    每个测试在独立的事务中运行，测试结束后回滚，
    确保测试间数据隔离，互不影响
    """
    async with integration_engine.connect() as connection:
        # 开始嵌套事务（保存点）
        trans = await connection.begin_nested()
        
        session_maker = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        
        async with session_maker() as session:
            yield session
        
        # 回滚事务，撤销所有数据变更
        await trans.rollback()


@pytest.fixture
def test_id():
    """生成唯一的测试 ID"""
    return f"test_{uuid.uuid4().hex[:8]}"


@pytest_asyncio.fixture
async def integration_redis(test_id):
    """
    集成测试 Redis 客户端 - 使用 Key 前缀隔离
    
    每个测试使用唯一的前缀，测试结束后清理该前缀的所有 key
    """
    from redis.asyncio import Redis
    
    redis = Redis.from_url(TEST_REDIS_URL, decode_responses=True)
    prefix = f"{TEST_REDIS_KEY_PREFIX}:{test_id}"
    
    class PrefixedRedis:
        """带前缀的 Redis 客户端"""
        
        def __init__(self, redis_client, prefix):
            self._redis = redis_client
            self._prefix = prefix
        
        def _key(self, key: str) -> str:
            return f"{self._prefix}:{key}"
        
        async def get(self, key: str):
            return await self._redis.get(self._key(key))
        
        async def set(self, key: str, value, ex=None):
            return await self._redis.set(self._key(key), value, ex=ex)
        
        async def delete(self, key: str):
            return await self._redis.delete(self._key(key))
        
        async def exists(self, key: str):
            return await self._redis.exists(self._key(key))
        
        async def cleanup(self):
            """清理该前缀的所有 key"""
            pattern = f"{self._prefix}:*"
            cursor = 0
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self._redis.delete(*keys)
                if cursor == 0:
                    break
    
    client = PrefixedRedis(redis, prefix)
    yield client
    
    # 清理测试数据
    await client.cleanup()
    await redis.close()


@pytest_asyncio.fixture
async def integration_client(integration_engine, integration_redis, integration_test_dir):
    """
    集成测试 HTTP 客户端
    
    使用真实数据库和 Redis，但使用事务回滚确保测试隔离
    """
    # 创建应用
    app = create_app()
    
    # 覆盖数据库依赖
    async def override_get_db():
        async with integration_engine.connect() as connection:
            trans = await connection.begin_nested()
            
            session_maker = async_sessionmaker(
                bind=connection,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )
            
            async with session_maker() as session:
                yield session
            
            await trans.rollback()
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Mock 外部服务（LLM API 等）
    with patch('app.llm.model_factory.ModelFactory') as mock_factory:
        mock_factory.get_general_model = AsyncMock()
        mock_factory.get_vision_model = AsyncMock()
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            yield client


@pytest_asyncio.fixture
async def integration_user_data(test_id):
    """集成测试用户数据 - 唯一用户名避免冲突"""
    return {
        "username": f"integration_user_{test_id}",
        "email": f"integration_{test_id}@example.com",
        "password": "testpassword123"
    }


@pytest_asyncio.fixture
async def integration_auth_token(integration_client, integration_user_data):
    """集成测试认证 Token"""
    # 注册用户
    register_response = await integration_client.post(
        "/api/v1/auth/register",
        json=integration_user_data
    )
    assert register_response.status_code == 201
    
    # 登录
    login_response = await integration_client.post(
        "/api/v1/auth/login",
        json={
            "username": integration_user_data["username"],
            "password": integration_user_data["password"]
        }
    )
    assert login_response.status_code == 200
    
    return login_response.json()["access_token"]


@pytest_asyncio.fixture
async def integration_auth_headers(integration_auth_token):
    """集成测试认证请求头"""
    return {"Authorization": f"Bearer {integration_auth_token}"}


@pytest_asyncio.fixture
async def integration_authenticated_client(integration_client, integration_auth_headers):
    """已认证的集成测试客户端"""
    integration_client.headers.update(integration_auth_headers)
    return integration_client


# =============================================================================
# 辅助 Fixtures
# =============================================================================

@pytest.fixture
def temp_file(integration_test_dir):
    """临时文件路径"""
    file_path = Path(integration_test_dir) / f"temp_{uuid.uuid4().hex[:8]}.txt"
    yield str(file_path)
    # 清理
    if os.path.exists(file_path):
        os.remove(file_path)


# =============================================================================
# Pytest Hooks
# =============================================================================

def pytest_collection_modifyitems(config, items):
    """自动标记集成测试"""
    for item in items:
        # 如果测试在 integration 目录下，自动添加 integration 标记
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """测试前检查"""
    # 检查是否需要真实数据库
    if "integration" in item.keywords:
        # 可以在这里检查数据库连接
        pass
