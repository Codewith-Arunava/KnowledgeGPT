# 🧠 KnowledgeGPT — Production-Grade Multi-Agent RAG Platform

> A portfolio-quality AI SaaS platform demonstrating LLM Engineering, RAG, Agentic AI, LangGraph, LlamaIndex, FastAPI, React, PostgreSQL, and ChromaDB.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND (React/Vite/TS)                    │
│  Auth │ Dashboard │ KB Manager │ Chat │ Eval │ Analytics    │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────┐
│                  BACKEND (FastAPI / Python)                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         LangGraph 9-Agent Orchestrator               │  │
│  │  Query → Retrieval → Research → Summary → Citation   │  │
│  │  → Hallucination → Response → Memory → Feedback      │  │
│  └───────────────────────────────────────────────────────┘  │
│  LangChain Chains │ LlamaIndex Engine │ LangSmith Tracing   │
└──────┬───────────────────────┬─────────────────────┬────────┘
       │                       │                     │
┌──────▼──────┐  ┌─────────────▼──────────┐  ┌──────▼─────┐
│ PostgreSQL  │  │ ChromaDB / Pinecone    │  │ File Store │
│ (Users/KBs/ │  │ (Vectors/Embeddings)   │  │ (PDFs)     │
│ Convos/Msgs)│  └────────────────────────┘  └────────────┘
└─────────────┘
```

---

## ✨ Features

### AI Pipeline
- 🤖 **9 LangGraph Agents**: Query Understanding → Retrieval → Research → Summarization → Citation Verification → Hallucination Detection → Response Generation → Memory → Feedback
- 📚 **RAG Engine**: Vector similarity, MMR, and hybrid search
- 🔍 **LangChain + LlamaIndex**: Toggle retriever engines per knowledge base
- 🌐 **Web Search Fallback**: Tavily/Serper integration when KB lacks information
- 🎯 **Deep Research Mode**: Generates academic-quality research reports

### Document Management
- 📄 **PDF Upload**: Drag & drop, multi-file, 50MB limit
- 🧹 **Smart Chunking**: RecursiveCharacterTextSplitter (1000/200)
- 🔢 **Embedding Models**: OpenAI small/large, Gemini, BGE-Large, Sentence Transformers
- 🗄️ **Vector Stores**: ChromaDB (local) or Pinecone (cloud)

### AI Models
- GPT-4o, GPT-4.1, GPT-4o Mini (OpenAI)
- Gemini 2.5 Pro, Gemini 2.5 Flash (Google)

### Evaluation & Analytics
- 📊 Context Precision, Retrieval Accuracy Trend
- 🛡️ Hallucination Detection (Low/Medium/High risk)
- 💯 Confidence Scores (Retrieval/Citation/Answer)
- 📈 Daily Queries, Token Usage, API Cost Estimation
- 🔭 LangSmith Tracing Integration

### Frontend
- ⚡ React + TypeScript + Vite
- 🎨 TailwindCSS v4 dark theme with glassmorphism
- 💬 ChatGPT-style interface with Markdown + code highlighting
- 📑 Citation panel with source previews
- 🔬 Agent trace explainability panel
- 📉 Recharts dashboards

---

## 🚀 Quick Start

### 1. Clone & configure

```bash
git clone <your-repo>
cd "RAG PROJECT"
cp .env.example .env
# Fill in your API keys in .env
```

### 2. Docker (Recommended — zero config)

```bash
docker-compose up
```

Services start at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api/docs
- **ChromaDB**: http://localhost:8001

### 3. Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate         # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## ⚙️ Environment Variables

See [`.env.example`](.env.example) for all variables. Minimum required:

```env
# Choose at least one LLM provider
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/knowledgegpt

# JWT
JWT_SECRET_KEY=your-secure-secret-32-chars-min
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login, get JWT |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/knowledge-bases/` | Create knowledge base |
| GET | `/api/v1/knowledge-bases/` | List knowledge bases |
| POST | `/api/v1/documents/upload/{kb_id}` | Upload PDFs |
| POST | `/api/v1/chat/` | Send message (runs agent pipeline) |
| GET | `/api/v1/analytics/` | Get analytics summary |
| GET | `/api/v1/evaluation/` | Get evaluation report |
| POST | `/api/v1/feedback/` | Submit message feedback |

Full interactive docs: http://localhost:8000/api/docs

---

## 🗄️ Database Schema

```
users              → knowledge_bases → documents
  └─ conversations → messages → feedback
     └─ analytics_events
```

---

## 🤖 LangGraph Workflow

```
START
  │
  ▼
[Query Understanding] → intent, entities, refined query
  │
  ▼
[Retrieval Agent] → top-K chunks with scores
  │
  ▼
[Research Agent] → findings, gaps, web search trigger
  │
  ├──(summary/research query)──► [Summarization Agent]
  │                                        │
  ◄────────────────────────────────────────┘
  │
  ▼
[Citation Verification] → per-claim confidence scores
  │
  ▼
[Hallucination Detection] → Low/Medium/High risk
  │
  ▼
[Response Generation] → Markdown answer + citations
  │
  ▼
[Memory Agent] → conversation history update
  │
  ▼
END
```

---

## 🧪 Testing

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## 🐳 Docker Services

| Service | Image | Port |
|---------|-------|------|
| backend | Python 3.12 + FastAPI | 8000 |
| frontend | Node 20 + Vite | 5173 |
| postgres | postgres:16-alpine | 5432 |
| chromadb | chromadb/chroma | 8001 |

---

## 🚢 Deployment

### Render / Railway
1. Push to GitHub
2. Connect repo to Render/Railway
3. Set environment variables
4. Deploy

### Docker VPS
```bash
docker-compose -f docker-compose.yml up -d
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, TailwindCSS v4 |
| State | Zustand, React Query |
| UI | Recharts, Lucide Icons, React Markdown |
| Backend | FastAPI, Python 3.12, Pydantic v2 |
| Database | PostgreSQL 16, SQLAlchemy async, Alembic |
| Vector DB | ChromaDB (default), Pinecone (optional) |
| AI Orchestration | LangGraph, LangChain |
| Retrieval | LangChain retriever + LlamaIndex (toggle) |
| LLMs | OpenAI GPT-4o/4.1, Google Gemini 2.5 |
| Embeddings | OpenAI, Gemini, BGE-Large, Sentence Transformers |
| Monitoring | LangSmith |
| Web Search | Tavily, Serper |
| Auth | JWT (access + refresh), bcrypt |
| DevOps | Docker, Docker Compose, Nginx |

---

## 📄 License

MIT © KnowledgeGPT
