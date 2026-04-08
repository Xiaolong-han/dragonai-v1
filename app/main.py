import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from slowapi.errors import RateLimitExceeded

from app.agents.agent_factory import AgentLifecycle
from app.api.exception_handlers import (
    dragonai_exception_handler,
    generic_exception_handler,
    pydantic_validation_handler,
    rate_limit_exceeded_handler,
    validation_exception_handler,
)
from app.api.middleware import (
    RequestSizeLimitMiddleware,
    RequestTracingMiddleware,
    limiter,
)
from app.api.v1 import auth, chat, conversations, files, knowledge, models, monitoring, tools
from app.cache import cache_warmup, redis_client
from app.config import settings
from app.core.database import close_db
from app.core.exceptions import DragonAIException
from app.llm.model_factory import ModelFactory
from app.schemas.response import ResponseBuilder


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(
        log_level=settings.log_level,
        log_dir=settings.log_dir,
        app_env=settings.app_env,
    )
    logger = logging.getLogger()
    logger.info("Starting DragonAI...")

    await AgentLifecycle.initialize()
    await redis_client.connect()
    logger.info("Redis connected")
    try:
        await cache_warmup.warmup_all()
    except Exception as e:
        logger.warning(f"[CACHE WARMUP] Cache warmup failed, continuing startup: {e}")
    yield
    await AgentLifecycle.shutdown()
    await ModelFactory.close_all()
    await redis_client.close()
    await close_db()
    logger.info("Shutting down DragonAI")


def create_app():
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title="DragonAI API",
        description="DragonAI - 智能AI助手",
        version="1.0.0",
        lifespan=lifespan
    )

    app.add_middleware(RequestTracingMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)

    app.state.limiter = limiter

    # 注册异常处理器
    app.add_exception_handler(DragonAIException, dragonai_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    allowed_origins = ["*"] if settings.app_env == "development" else [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(conversations.router, prefix="/api/v1")
    app.include_router(files.router, prefix="/api/v1")
    app.include_router(knowledge.router, prefix="/api/v1")
    app.include_router(tools.router, prefix="/api/v1")
    app.include_router(models.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(monitoring.router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return ResponseBuilder.success(
            data={"name": "DragonAI API", "version": "2.0.0"},
            message="Welcome to DragonAI API"
        )

    @app.get("/health")
    async def health_check():
        return ResponseBuilder.success(
            data={"status": "healthy"}
        )

    return app


def setup_logging(log_level: str, log_dir: str, app_env: str):
    """配置日志"""
    from app.core.logging_config import setup_logging as _setup_logging
    _setup_logging(log_level=log_level, log_dir=log_dir, app_env=app_env)
