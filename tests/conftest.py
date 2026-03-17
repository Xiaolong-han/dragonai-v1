
import pytest
import pytest_asyncio
import uuid
import tempfile
import os
import shutil
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

# 首先导入 settings 并修改限流配置
# 这必须在导入其他模块之前完成
from app.config import settings

# 禁用限流 - 设置为非常大的值
settings.rate_limit_default = "1000000/minute"
settings.rate_limit_auth = "1000000/minute"
settings.rate_limit_chat = "1000000/minute"
settings.rate_limit_storage = "memory"

# 现在导入其他模块
from app.core.database import Base, get_db


# =============================================================================
# 基础 Fixtures
# =============================================================================

@pytest.fixture
def test_settings():
    """测试配置 - 禁用限流和使用内存存储"""
    settings.database_url = "sqlite+aiosqlite:///:memory:"
    settings.secret_key = "test-secret-key-for-testing-only"
    settings.access_token_expire_minutes = 30
    settings.rate_limit_storage = "memory"
    settings.rate_limit_default = "1000000/minute"
    settings.rate_limit_auth = "1000000/minute"
    settings.rate_limit_chat = "1000000/minute"
    return settings


@pytest.fixture
def async_engine():
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture
def AsyncTestingSessionLocal(async_engine):
    return async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture(autouse=True)
async def create_tables(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(AsyncTestingSessionLocal):
    async with AsyncTestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def mock_redis_client(mocker):
    mock_redis = mocker.AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = None
    mock_redis.delete.return_value = False
    mock_redis.exists.return_value = False
    mock_redis.scan.return_value = (0, [])
    mock_redis.client = mock_redis
    mock_redis.ping.return_value = True
    return mock_redis


@pytest.fixture
def mock_request():
    class MockRequest:
        def __init__(self):
            self.state = type('State', (), {})()
            self.headers = {}
            self.url = type('URL', (), {'path': '/test'})()
            self.method = 'GET'
            self.client = type('Client', (), {'host': '127.0.0.1'})()
    
    return MockRequest()


# =============================================================================
# 测试隔离 Fixtures
# =============================================================================

@pytest.fixture
def test_id():
    """生成唯一的测试 ID 用于隔离"""
    return f"test_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_redis_prefix(test_id):
    """生成唯一的 Redis key 前缀"""
    return f"{test_id}"


@pytest_asyncio.fixture
async def mock_redis():
    """Mock Redis 客户端用于 API 测试"""
    # 创建模拟的 Redis 实例
    mock_redis_instance = AsyncMock()
    mock_redis_instance.get = AsyncMock(return_value=None)
    mock_redis_instance.set = AsyncMock(return_value=None)
    mock_redis_instance.delete = AsyncMock(return_value=None)
    mock_redis_instance.exists = AsyncMock(return_value=False)
    mock_redis_instance.scan = AsyncMock(return_value=(0, []))
    mock_redis_instance.ttl = AsyncMock(return_value=-1)
    mock_redis_instance.close = AsyncMock()
    
    # 创建模拟的 RedisClient 类
    class MockRedisClient:
        def __init__(self):
            self._client = mock_redis_instance
            self._connected = True
            self.client = mock_redis_instance
            self._locks = set()
        
        async def connect(self):
            self._connected = True
        
        async def disconnect(self):
            self._connected = False
        
        async def close(self):
            self._connected = False
        
        async def get(self, key):
            return None
        
        async def set(self, key, value, ttl=None):
            return None
        
        async def delete(self, key):
            return None
        
        async def exists(self, key):
            return False
        
        async def acquire_lock(self, lock_key: str, expire_seconds: int = 10) -> bool:
            if lock_key not in self._locks:
                self._locks.add(lock_key)
                return True
            return False
        
        async def release_lock(self, lock_key: str):
            self._locks.discard(lock_key)
    
    mock_client = MockRedisClient()
    
    with patch('app.cache.redis.redis_client', mock_client), \
         patch('app.services.conversation_service.redis_client', mock_client), \
         patch('app.services.repositories.message_repository.redis_client', mock_client), \
         patch('app.core.token_blacklist.redis_client', mock_client), \
         patch('app.security.token_blacklist.redis_client', mock_client):
        yield mock_client


# =============================================================================
# API 测试 Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def client(mock_redis, test_settings):
    """
    提供 HTTP 测试客户端
    
    每个测试使用独立的临时文件数据库，确保测试间完全隔离
    限流已在模块级别禁用
    """
    from app.main import create_app
    
    # 创建临时目录和数据库文件
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    
    # 创建引擎
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    TestingSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    
    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    # 清理
    await engine.dispose()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest_asyncio.fixture
async def test_user_data():
    """测试用户数据 - 使用唯一用户名避免冲突"""
    unique_id = uuid.uuid4().hex[:8]
    return {
        "username": f"testuser_{unique_id}",
        "email": f"test_{unique_id}@example.com",
        "password": "testpassword123"
    }


@pytest_asyncio.fixture
async def auth_token(client, test_user_data, mock_redis):
    """提供认证 Token"""
    # 注册用户
    register_response = await client.post("/api/v1/auth/register", json=test_user_data)
    assert register_response.status_code == 201, f"注册失败: {register_response.text}"
    
    # 登录获取 Token
    login_response = await client.post("/api/v1/auth/login", json={
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    })
    assert login_response.status_code == 200, f"登录失败: {login_response.text}"
    
    data = login_response.json()
    assert "access_token" in data, f"响应中没有 access_token: {data}"
    return data["access_token"]


@pytest_asyncio.fixture
async def auth_headers(auth_token):
    """提供认证请求头"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest_asyncio.fixture
async def authenticated_client(client, auth_headers):
    """提供已认证的 HTTP 客户端"""
    client.headers.update(auth_headers)
    return client


@pytest_asyncio.fixture
async def test_conversation(authenticated_client):
    """创建测试会话"""
    response = await authenticated_client.post(
        "/api/v1/conversations",
        json={"title": "Test Conversation", "model_name": "qwen-flash"}
    )
    return response.json()


@pytest_asyncio.fixture
async def test_conversation_with_messages(authenticated_client, test_conversation):
    """创建带消息的测试会话"""
    # 发送消息
    await authenticated_client.post(
        "/api/v1/chat/send",
        json={
            "conversation_id": test_conversation["id"],
            "content": "Hello, this is a test message"
        }
    )
    return test_conversation
