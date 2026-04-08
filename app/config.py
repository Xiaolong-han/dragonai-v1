from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentMiddlewareSettings(BaseSettings):
    enable_todo_list: bool = True
    enable_tool_retry: bool = True
    enable_model_fallback: bool = True
    enable_filesystem: bool = True
    enable_skills: bool = True
    enable_summarization: bool = True
    enable_tool_call_limit: bool = True
    enable_model_call_limit: bool = True
    enable_memory: bool = True  # 记忆中间件

    tool_retry_max_retries: int = 1
    tool_retry_backoff_factor: float = 2.0

    filesystem_tool_token_limit: int = 8000

    summarization_max_tokens: int = 10000
    summarization_messages_to_keep: int = 6

    model_call_limit: int = 50

    # 记忆中间件配置
    memory_max_to_load: int = 5  # 会话开始时最多加载的记忆数
    memory_enable_extraction: bool = True  # 是否启用自动提取
    memory_enable_semantic_search: bool = True  # 是否启用语义检索
    memory_extraction_interval: int = 3  # 每 N 轮对话后提取记忆

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
        env_prefix="agent_middleware_"
    )


class Settings(BaseSettings):
    app_name: str = "DragonAI"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"  # nosec B104  # 开发环境默认值，生产环境应覆盖
    app_port: int = 8000

    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    database_url: str = "postgresql://user:password@localhost:5432/dragonai"

    redis_url: str = "redis://localhost:6379/0"

    chroma_persist_dir: str = "./chroma_db"

    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    tavily_api_key: str = ""

    storage_dir: str = "./storage"
    skills_dir: str = "./storage/skills"

    log_level: str = "INFO"
    log_dir: str = "./logs"

    model_general_fast: str = "glm-4.7"
    model_general_expert: str = "glm-5"

    model_vision_ocr: str = "qwen-vl-ocr"
    model_vision: str = "qwen3-vl-plus"
    """
    文本到图像模型:qwen-image, qwen-image-plus, qwen-image-max, qwen-image-2.0,qwen-image-2.0-pro
                wan2.5-t2i-preview,wan2.2-t2i-flash,wan2.2-t2i-plus,wanx2.1-t2i-turbo,
                wanx2.1-t2i-plus,z-image-turbo
    """
    model_text_to_image: str = "wanx2.1-t2i-turbo"
    """
    图像编辑模型:qwen-image-edit, qwen-image-edit-plus,
                qwen-image-edit-max,
                qwen-image-2.0,qwen-image-2.0-pro
    """
    model_image_edit: str = "qwen-image-edit"

    model_coder: str = "qwen3-coder-flash"

    model_translation: str = "qwen-mt-flash"

    model_embedding: str = "text-embedding-v4"

    agent_tool_call_limit: int = 10
    agent_timeout: int = 120

    agent_middleware: AgentMiddlewareSettings = Field(
        default_factory=AgentMiddlewareSettings
    )

    rate_limit_storage: str = "redis"
    rate_limit_default: str = "100/minute"
    rate_limit_chat: str = "30/minute"
    rate_limit_auth: str = "10/minute"

    max_request_size: int = 10 * 1024 * 1024

    rag_enable_hybrid: bool = False
    rag_hybrid_alpha: float = 0.5

    rag_enable_rerank: bool = False

    rag_rerank_provider: str = "cross-encoder"
    rag_rerank_model: str = "BAAI/bge-reranker-base"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
