# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DragonAI is an intelligent AI assistant platform built with FastAPI and LangChain/LangGraph. It features multi-agent task dispatching, RAG knowledge base, tool calling (web search, code execution, image generation), and long-term memory storage.

## Tech Stack

- **Backend**: FastAPI + Uvicorn, SQLAlchemy 2.0 (async), PostgreSQL, Redis, ChromaDB
- **AI Framework**: LangChain + LangGraph + DeepAgents for agent orchestration
- **LLM**: DashScope (Tongyi Qwen series via Alibaba Cloud)
- **Frontend**: Vue 3 + TypeScript + Vite + Pinia + Element Plus
- **Database Migration**: Alembic
- **Testing**: pytest with asyncio support
- **Deployment**: Docker Compose with Nginx reverse proxy

## Common Commands

### Development

```bash
# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with required API keys (QWEN_API_KEY, TAVILY_API_KEY)

# Database migrations
alembic upgrade head          # Run all migrations
alembic revision --autogenerate -m "description"  # Create new migration

# Initialize database tables (without migrations)
python scripts/init_db.py

# Start development server
python run.py
# Or directly with uvicorn
uvicorn app.main:create_app --reload --factory
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_chat_service.py -v

# Run integration tests only
pytest tests/integration/ -v

# Run unit tests only
pytest tests/unit/ -v
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # Development server
npm run build    # Production build
```

### Production Deployment

```bash
# Using deploy script
chmod +x deploy.sh
./deploy.sh deploy    # Full deploy (build + start)
./deploy.sh build     # Build only
./deploy.sh logs      # View logs
./deploy.sh stop      # Stop services
./deploy.sh restart   # Restart services
./deploy.sh status    # Check container status

# Manual Docker commands
docker-compose up -d
docker-compose logs -f backend
docker-compose down
```

## Architecture Overview

### Application Structure

```
app/
├── api/v1/           # API routers (auth, chat, conversations, files, knowledge, tools)
├── agents/           # AgentFactory - creates DeepAgents with task dispatching
├── cache/            # Redis client and cache warmup
├── core/             # Database, security, rate limiting, logging config
├── llm/              # DashScope client wrapper for Tongyi models
├── models/           # SQLAlchemy ORM models (User, Conversation, Message)
├── rag/              # RAG pipeline: hybrid retriever, reranker, document loader
├── schemas/          # Pydantic request/response models
├── services/         # Business logic layer
├── storage/          # File storage, vector store, sandbox
└── tools/            # Agent tools: web_search, code_tools, image_tools, rag_tool
```

### Key Architectural Patterns

**Agent System (app/agents/agent_factory.py)**
- Uses DeepAgents library with `create_deep_agent()`
- Main agent handles task dispatching to sub-agents
- Sub-agents: general-purpose, researcher, coder, image-creator
- Long-term memory via CompositeBackend routing to PostgreSQL
- Checkpointer for conversation state (AsyncPostgresSaver)

**Database (app/core/database.py)**
- Async SQLAlchemy with asyncpg driver
- Converts `postgresql://` URLs to `postgresql+asyncpg://`
- Pool size: 20, max overflow: 40
- Dependency injection via `get_db()` generator

**LLM Integration (app/llm/dashscope_client.py)**
- Unified DashScope SDK client for all Tongyi models
- Supports both Generation (text) and MultiModalConversation APIs
- Async wrapper using `asyncio.to_thread()`

**RAG Pipeline (app/rag/)**
- Hybrid retriever: vector + BM25 with configurable alpha
- Reranker: Cross-encoder or Cohere
- Document processing with unstructured library
- ChromaDB for vector storage

**Streaming (app/services/stream/)**
- SSE with heartbeat for long-running agent tasks
- StreamProcessor for chunked responses

### Configuration

Environment variables managed in `app/config.py` via Pydantic Settings:

Required:
- `QWEN_API_KEY` - DashScope API key for LLM
- `TAVILY_API_KEY` - Web search API key
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key

Model Configuration:
- General: `deepseek-v3.1` (fast), `qwen-plus-2025-12-01` (expert)
- Vision: `qwen-vl-ocr`, `qwen3-vl-plus`
- Image: `qwen-image`, `qwen-image-plus`
- Coder: `qwen3-coder-flash`, `qwen3-coder-plus`
- Embedding: `text-embedding-v4`

### Testing Structure

- `tests/conftest.py` - Shared fixtures with SQLite in-memory for unit tests
- `tests/unit/` - Isolated unit tests with mocked dependencies
- `tests/integration/` - API integration tests requiring real services

### Important Notes

- Windows requires `WindowsSelectorEventLoopPolicy` (configured in `run.py`)
- Database URLs automatically converted to asyncpg format
- Agent warmup runs on startup to cache model connections
- Rate limiting uses Redis with slowapi
- File uploads use signature verification for security
- Storage directory used for files, skills, and sandbox
