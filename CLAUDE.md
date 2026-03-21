# CLAUDE.md - DragonAI v2 Local 开发指南

## 📋 项目概述

DragonAI 是一个基于 LangChain 1.0+ 和 LangGraph 构建的智能 AI 助手系统，采用 FastAPI + Vue 3 全栈架构。

### 核心特性
- 🤖 **多模型支持**: 通义千问系列模型 (对话/代码/翻译/图像/视觉)
- ⚡ **流式响应**: SSE 实时流式输出 + 心跳保活
- 🔧 **工具调用**: 代码执行/文件操作/网络搜索/图像处理/RAG/文档读取
- 📚 **知识库**: 混合检索 (向量+BM25) + 重排序
- 💾 **持久化**: PostgreSQL (对话/消息/Agent 状态) + Redis (缓存/限流)
- 🔐 **安全**: JWT 认证 + 令牌黑名单 + API 限流
- 💡 **深度思考**: 支持启用/禁用深度思考模式
- 🧠 **长期记忆**: 基于用户偏好的跨会话记忆系统
- 🔧 **技能系统**: 支持自定义技能文件 (SKILL.md)

## 🏗️ 技术架构

### 后端技术栈
- **框架**: FastAPI 0.115+ (异步 Web 服务)
- **AI 框架**: LangChain 1.0+ + LangGraph + deepagents
- **数据库**: PostgreSQL 15+ + SQLAlchemy 2.0 (异步 ORM)
- **缓存**: Redis 7+ (限流/缓存)
- **向量库**: ChromaDB 0.5+ (RAG 检索)
- **LLM**: 通义千问 (DashScope API)
- **SDK**: dashscope + openai + langchain-community
- **迁移**: Alembic (数据库版本控制)

### 前端技术栈
- **框架**: Vue 3.5+ + TypeScript 5.9+
- **构建**: Vite 7.3+
- **状态**: Pinia 3.0+
- **路由**: Vue Router 5.0+
- **UI**: Element Plus 2.13+
- **HTTP**: Axios 1.13+
- **Markdown**: marked 17.0+
- **代码高亮**: highlight.js 11.11+

## 📁 目录结构

```
dragonai-v2-local/
├── app/                          # 后端主目录
│   ├── agents/                   # Agent 工厂和配置
│   │   ├── agent_factory.py      # LangChain Agent 创建 (核心)
│   │   ├── prompts.py            # 系统提示词
│   │   ├── error_classifier.py   # 错误分类器
│   │   └── middleware/           # 自定义中间件
│   │       ├── memory.py         # 记忆管理中间件
│   │       └── skills.py         # 技能中间件扩展
│   ├── api/                      # API 层
│   │   ├── middleware/           # 中间件 (限流/追踪/大小限制)
│   │   ├── v1/                   # API 路由
│   │   │   ├── auth.py           # 认证/注册
│   │   │   ├── chat.py           # 聊天接口 (SSE 流)
│   │   │   ├── conversations.py  # 会话管理
│   │   │   ├── files.py          # 文件上传
│   │   │   ├── knowledge.py      # 知识库管理
│   │   │   ├── tools.py          # 工具列表
│   │   │   ├── models.py         # 模型列表
│   │   │   └── monitoring.py     # 监控接口
│   │   └── dependencies.py       # 依赖注入
│   ├── cache/                    # Redis 缓存
│   │   ├── redis.py              # Redis 客户端
│   │   └── warmup.py             # 缓存预热
│   ├── core/                     # 核心模块
│   │   ├── database.py           # 数据库连接
│   │   ├── security.py           # JWT 认证
│   │   ├── rate_limit.py         # 限流配置
│   │   ├── tracing.py            # 链路追踪
│   │   ├── sandbox.py            # 沙盒配置
│   │   └── exceptions.py         # 异常定义
│   ├── llm/                      # LLM 模型工厂
│   │   ├── model_factory.py      # 模型创建/管理
│   │   ├── text_models.py        # 文本模型类
│   │   └── image_models.py       # 图像模型类
│   ├── models/                   # SQLAlchemy 模型
│   │   ├── user.py               # 用户模型
│   │   ├── conversation.py       # 会话模型
│   │   └── message.py            # 消息模型
│   ├── rag/                      # RAG 模块
│   │   ├── loader.py             # 文档加载
│   │   ├── splitter.py           # 文本分割
│   │   ├── vector_store.py       # 向量存储
│   │   ├── hybrid_retriever.py   # 混合检索
│   │   └── reranker.py           # 重排序
│   ├── schemas/                  # Pydantic 模型
│   ├── security/                 # 安全模块
│   ├── services/                 # 业务服务层
│   │   ├── chat_service.py       # 聊天服务 (编排层)
│   │   ├── conversation_service.py
│   │   ├── user_service.py
│   │   ├── knowledge_service.py
│   │   ├── repositories/         # 数据访问层
│   │   │   └── message_repository.py
│   │   ├── formatters/           # 格式化器
│   │   │   └── message_formatter.py
│   │   └── stream/               # 流处理
│   │       ├── sse_emitter.py    # SSE 发射器
│   │       ├── sse_heartbeat.py  # SSE 心跳
│   │       └── stream_processor.py
│   ├── storage/                  # 存储模块
│   │   ├── file_storage.py       # 文件存储
│   │   └── sandbox.py            # 沙盒存储
│   ├── tools/                    # Agent 工具
│   │   ├── rag_tool.py           # 知识库检索
│   │   ├── web_search_tool.py    # 网络搜索
│   │   ├── code_tools.py         # 代码助手
│   │   ├── image_tools.py        # 图像生成/编辑
│   │   ├── translation_tools.py  # 翻译
│   │   ├── multimodal_tool.py    # 多模态 (OCR/理解)
│   │   └── filesystem_tools.py   # 文档读取 (PDF/Word)
│   ├── utils/                    # 工具函数
│   └── config.py                 # 配置管理
│
├── frontend/                     # 前端主目录
│   ├── src/
│   │   ├── components/           # Vue 组件
│   │   │   ├── ChatInput.vue     # 聊天输入框
│   │   │   ├── ChatMessageBubble.vue
│   │   │   ├── ChatMessageList.vue
│   │   │   ├── ConversationList.vue
│   │   │   ├── ModelSelector.vue # 模型选择器
│   │   │   ├── ToolCallCard.vue  # 工具调用卡片
│   │   │   ├── ThinkingProcess.vue # 思考过程
│   │   │   └── ThemeSwitcher.vue # 主题切换
│   │   ├── views/                # 页面视图
│   │   │   ├── Chat.vue          # 聊天页面
│   │   │   ├── Coding.vue        # 代码页面
│   │   │   ├── ImageGeneration.vue # 图像生成
│   │   │   ├── ImageEditing.vue  # 图像编辑
│   │   │   ├── Translation.vue   # 翻译页面
│   │   │   ├── Login.vue         # 登录
│   │   │   └── Register.vue      # 注册
│   │   ├── stores/               # Pinia 状态
│   │   │   ├── auth.ts           # 认证状态
│   │   │   ├── chat.ts           # 聊天状态
│   │   │   ├── conversation.ts   # 会话状态
│   │   │   └── theme.ts          # 主题状态
│   │   ├── router/               # 路由配置
│   │   └── utils/                # 工具函数
│   └── public/                   # 静态资源
│
├── alembic/                      # 数据库迁移
├── tests/                        # 测试用例
│   ├── unit/                     # 单元测试
│   └── integration/              # 集成测试
├── scripts/                      # 脚本文件
└── storage/                      # 运行时存储
    ├── skills/                   # 技能文件 (SKILL.md)
    └── chroma_db/                # ChromaDB 持久化
```

## 🔧 开发环境配置

### 后端配置 (.env)

```bash
# 基础配置
APP_NAME=DragonAI
APP_ENV=development
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

# 安全配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/dragonai

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# ChromaDB 配置
CHROMA_PERSIST_DIR=./chroma_db

# LLM 配置
QWEN_API_KEY=sk-your-api-key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
TAVILY_API_KEY=tvly-your-api-key

# 模型配置
MODEL_GENERAL_FAST=deepseek-r1-0528
MODEL_GENERAL_EXPERT=deepseek-r1
MODEL_VISION_OCR=qwen-vl-ocr
MODEL_VISION=qwen3-vl-plus
MODEL_TEXT_TO_IMAGE=wanx2.1-t2i-turbo
MODEL_IMAGE_EDIT=qwen-image-edit
MODEL_CODER=qwen3-coder-flash
MODEL_TRANSLATION=qwen-mt-flash
MODEL_EMBEDDING=text-embedding-v4

# Agent 配置
AGENT_TOOL_CALL_LIMIT=10
AGENT_TIMEOUT=120

# RAG 配置
RAG_ENABLE_HYBRID=false
RAG_ENABLE_RERANK=false

# LangSmith 配置
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2-your-api-key
LANGSMITH_PROJECT=dragonai-v2
```

### 前端配置

创建 `frontend/.env.local`:
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 🚀 启动命令

### 后端启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据库
alembic upgrade head
python scripts/init_db.py

# 3. 启动服务
python run.py
# 或开发模式
uvicorn app.main:app --reload
```

### 前端启动

```bash
# 1. 安装依赖
cd frontend
npm install

# 2. 启动开发服务器
npm run dev

# 3. 构建生产版本
npm run build
```

### Docker 部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 🧪 测试命令

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_agent_factory.py
pytest tests/unit/test_chat_service.py

# 带覆盖率报告
pytest --cov=app tests/
```

## 📝 代码规范

### Python 代码风格
- 使用 type hints (类型注解)
- 遵循 PEP 8 规范
- 异步代码使用 `async/await`
- 使用 Pydantic 进行数据验证

### TypeScript 代码风格
- 使用 TypeScript 严格模式
- 接口使用 PascalCase
- 变量和函数使用 camelCase
- 组件文件使用 PascalCase 命名

### 重要约定

1. **Agent 实现**: 参考 LangChain 1.0+ 的 `create_agent` API
2. **中间件模式**: 使用 LangChain middleware 扩展 Agent 功能
3. **异步优先**: 所有 I/O 操作使用异步版本
4. **依赖注入**: 使用 FastAPI 的依赖注入系统
5. **错误处理**: 统一使用 DragonAIException 处理错误

## 🔑 核心模块说明

### Agent 系统 (app/agents/agent_factory.py)

```python
from app.agents.agent_factory import AgentFactory, AgentLifecycle

# 初始化 (应用启动时)
await AgentLifecycle.initialize()

# 创建聊天 Agent
agent = AgentFactory.create_chat_agent(
    is_expert=False,      # 是否使用专家模型
    enable_thinking=False # 是否启用深度思考
)

# 调用 Agent
config, context = AgentFactory.get_agent_config(
    conversation_id=123,
    user_id=1
)

response = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "你好"}]},
    config=config,
    context=context
)

# 关闭 (应用关闭时)
await AgentLifecycle.shutdown()
```

### Agent 中间件栈

Agent 中间件按顺序执行（可通过 `AgentMiddlewareSettings` 配置启用/禁用）:
1. `MemoryMiddleware` - 记忆加载与自动提取 (默认启用)
2. `TodoListMiddleware` - 任务规划和跟踪 (默认启用)
3. `PatchToolCallsMiddleware` - 修补工具调用 (始终启用)
4. `ToolRetryMiddleware` - 工具调用重试 (默认启用)
5. `ModelFallbackMiddleware` - 模型降级 (默认启用)
6. `FilesystemMiddleware` - 文件系统工具 (ls/read/write/edit/glob/grep) (默认启用)
7. `SkillsMiddleware` - 技能系统 (默认启用)
8. `SummarizationMiddleware` - 长文本摘要 (默认启用)
9. `ToolCallLimitMiddleware` - 工具调用次数限制 (默认启用)
10. `ModelCallLimitMiddleware` - 模型调用次数限制 (默认启用)

**中间件配置** (`AgentMiddlewareSettings`):
- `enable_*` 开关控制启用/禁用
- `tool_retry_max_retries` / `tool_retry_backoff_factor` - 重试参数
- `filesystem_tool_token_limit` - 文件系统 token 限制
- `summarization_max_tokens` / `summarization_messages_to_keep` - 摘要参数
- `model_call_limit` - 模型调用限制
- `memory_max_to_load` - 会话开始时最多加载的记忆数
- `memory_enable_extraction` - 是否启用自动提取
- `memory_enable_semantic_search` - 是否启用语义检索

环境变量前缀: `AGENT_MIDDLEWARE_` (如 `AGENT_MIDDLEWARE_ENABLE_SUMMARIZATION=false`)

### 工具系统

**内置工具** (ALL_TOOLS):
- `search_knowledge_base` - RAG 知识库检索
- `web_search` - Tavily 网络搜索
- `ocr_document` - OCR 文档识别
- `understand_image` - 图像理解
- `generate_image` - 图像生成
- `edit_image` - 图像编辑
- `code_assist` - 代码助手
- `translate_text` - 文本翻译
- `read_pdf` - 读取 PDF 文件
- `read_word` - 读取 Word 文件

**文件系统工具** (由 FilesystemMiddleware 提供):
- `ls` - 列出目录
- `read_file` - 读取文件
- `write_file` - 写入文件
- `edit_file` - 编辑文件
- `glob` - 文件匹配
- `grep` - 文本搜索

**模型类层次结构**:
```
DashScopeModel (抽象基类)
├── DashScopeTextModel (文本模型基类)
│   ├── DashScopeVisionModel (视觉理解模型)
│   ├── DashScopeCoderModel (编程助手模型)
│   └── DashScopeTranslationModel (翻译模型)
└── DashScopeImageModel (图像模型基类)
    ├── QwenImageGenerationModel (通义千问图像生成)
    ├── QwenImageEditModel (通义千问图像编辑)
    ├── WanxImageGenerationModelV2 (万相图像生成)
    └── WanxImageEditModelV2_5 (万相图像编辑)
```

### 模型工厂 (app/llm/model_factory.py)

```python
from app.llm.model_factory import ModelFactory

# 获取通用模型
model = ModelFactory.get_general_model(
    is_expert=False,
    enable_thinking=True,
    streaming=True
)

# 获取视觉模型
vision_model = ModelFactory.get_vision_model(is_ocr=False)

# 获取图像生成模型
image_model = ModelFactory.get_text_to_image_model()

# 获取图像编辑模型
edit_model = ModelFactory.get_image_edit_model()

# 获取编程模型
coder_model = ModelFactory.get_coder_model()

# 获取翻译模型
translation_model = ModelFactory.get_translation_model()

# 获取 Embedding 模型
embedding = ModelFactory.get_embedding()
```

### SSE 流式响应

```python
# 聊天服务生成 SSE 流
from app.services.chat_service import chat_service

async for chunk in chat_service.generate_sse_stream(
    db=db,
    conversation_id=123,
    user_id=1,
    content="你好",
    is_expert=True,
    enable_thinking=False
):
    yield chunk
```

**SSE 事件格式**:
- `thinking` - 思考过程内容
- `thinking_end` - 思考结束
- `content` - 文本消息
- `tool_call` - 工具调用
- `tool_result` - 工具结果
- `error` - 错误消息

### 数据库模型

```python
# User 模型
class User(Base):
    id: int (PK)
    username: str (unique, index)
    email: str (unique, index)
    hashed_password: str
    created_at: datetime

# Conversation 模型
class Conversation(Base):
    id: int (PK)
    user_id: int (FK, index)
    title: str
    created_at: datetime
    updated_at: datetime

# Message 模型
class Message(Base):
    id: int (PK)
    conversation_id: int (FK, index)
    role: str (user/assistant)
    content: str
    extra_data: dict (JSONB)
    created_at: datetime
```

### 长期记忆系统

Agent 通过 `MemoryMiddleware` 和 `StoreBackend` 实现长期记忆，支持跨会话持久化和语义检索。

**架构特性**:
- 基于 LangGraph Store，支持向量检索（pgvector）
- 自动记忆加载：会话开始时根据当前查询语义检索相关记忆
- 自动记忆提取：会话结束后自动提取用户偏好和重要事实
- 多用户隔离：通过 namespace `(user_id, "memories")` 实现用户隔离

**记忆路径** (Agent 通过 read_file 读取时使用的虚拟路径):
- `/memories/preferences.txt` - 用户偏好记忆
- `/memories/facts/general.txt` - 用户相关事实和重要信息
- `/memories/notes.txt` - 备注

> 注意：内部存储时，CompositeBackend 会将 `/memories/` 前缀剥离，实际存储的 key 为 `/preferences.txt`、`/facts/general.txt` 等。

**提取策略（混合策略）**:
- **轮数间隔**：每 N 轮对话后提取（默认 3 轮）
- **关键词触发**：对话中包含「我喜欢」「我的职业」「请记住」等关键词时立即提取
- 两个条件满足其一即可触发提取

**配置项** (`AgentMiddlewareSettings`):
- `enable_memory` - 是否启用记忆中间件
- `memory_max_to_load` - 会话开始时最多加载的记忆数
- `memory_enable_extraction` - 是否启用自动提取
- `memory_enable_semantic_search` - 是否启用语义检索
- `memory_extraction_interval` - 轮数间隔（默认 3）

**使用方式**:
```python
# 通过 Store API 手动操作记忆
from app.agents.agent_factory import AgentFactory

store = AgentFactory.get_store()
namespace = (str(user_id), "memories")

# 保存记忆（自动向量化）
# 注意：key 必须以 "/" 开头，与 CompositeBackend 路由后的格式一致
store.put(
    namespace,
    "/preferences.txt",  # key 必须有 "/" 前缀
    {"content": ["# 用户偏好", "", "- **语言**: 中文"], "created_at": "...", "modified_at": "..."}
)

# 语义检索记忆
memories = store.search(
    namespace,
    query="用户喜欢什么编程语言？",
    limit=5
)
```

### 技能系统

技能文件存储在 `storage/skills/` 目录下，每个技能包含一个 SKILL.md 文件。

**示例结构**:
```
storage/skills/
└── xhs-copywriting/
    └── SKILL.md
```

**Agent 使用技能**:
当用户请求匹配技能描述时，Agent 会自动调用 `read_file` 读取技能文件，并严格按照技能中的流程执行。

### RAG 混合检索 (app/rag/hybrid_retriever.py)

```python
from app.rag.hybrid_retriever import HybridRetriever

# 创建混合检索器
retriever = HybridRetriever(
    vector_store=vector_store,
    alpha=0.5,  # 向量检索权重
    use_chinese_tokenizer=True
)

# 索引文档
retriever.index_documents(documents)

# 检索
results = await retriever.aretrieve(query="查询文本", k=4)
```

### API 路由

**认证相关**:
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户登出

**聊天相关**:
- `GET /api/v1/chat/conversations/{id}/history` - 获取聊天历史
- `POST /api/v1/chat/send` - 发送消息 (SSE 流)

**会话管理**:
- `GET /api/v1/conversations` - 获取会话列表
- `POST /api/v1/conversations` - 创建会话
- `PUT /api/v1/conversations/{id}` - 更新会话
- `DELETE /api/v1/conversations/{id}` - 删除会话

**知识库**:
- `POST /api/v1/knowledge/upload` - 上传知识文档
- `GET /api/v1/knowledge/search` - 搜索知识
- `DELETE /api/v1/knowledge/{id}` - 删除知识

**文件**:
- `POST /api/v1/files/upload` - 上传文件

**监控**:
- `GET /api/v1/monitoring/health` - 健康检查
- `GET /api/v1/monitoring/cache` - 缓存状态

## 🐛 常见问题

### Agent 初始化失败
检查 PostgreSQL 和 Redis 连接配置，确保数据库已创建并运行。

### 缓存预热失败
检查 LangSmith 和 DashScope API Key 配置。

### 前端跨域问题
开发环境允许所有来源，生产环境需配置 CORS。

### 向量检索慢
- 启用混合检索：`RAG_ENABLE_HYBRID=true`
- 调整向量维度或批次大小

### 数据库连接问题
确保 PostgreSQL 服务运行，检查 DATABASE_URL 配置。

### SSE 流式输出中断
检查网络代理配置，确保支持 SSE 长连接。

## 🔒 安全注意事项

1. **生产环境**: 必须更改 SECRET_KEY
2. **API 限流**: 配置合理的限流策略
3. **JWT 过期**: 设置合适的 token 过期时间
4. **输入验证**: 所有用户输入使用 Pydantic 验证
5. **文件上传**: 限制文件大小和类型
6. **CORS**: 生产环境限制允许的来源
7. **密码安全**: 使用 bcrypt 加密存储

## 📚 参考文档

- [LangChain 官方文档](https://python.langchain.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [DeepAgents 文档](https://github.com/langchain-ai/deepagents)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Vue 3 文档](https://vuejs.org/)
- [通义千问 API](https://help.aliyun.com/zh/dashscope/)
- [LangSmith 文档](https://docs.smith.langchain.com/)
