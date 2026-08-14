# Enterprise AI Research & Document Intelligence Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![React: 19](https://img.shields.io/badge/react-19-61dafb.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![pgvector](https://img.shields.io/badge/pgvector-v0.8.0-336791.svg)](https://github.com/pgvector/pgvector)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL%2017-3ECF8E.svg)](https://supabase.com/)

An enterprise-grade, auditable research intelligence platform featuring a **Dual-Mode Architecture**:
1. **🌐 Web Intelligence Agent**: Autonomous multi-angle planning, authoritative source snapshotting, atomic claim extraction, cross-source disagreement matrix, and grounded conclusion lineage.
2. **📑 Enterprise Document RAG**: High-throughput PDF ingestion vault with PyMuPDF structured table parsing, 1024-dim Cohere embeddings, Supabase `pgvector` HNSW cosine similarity search, FlashRank cross-encoder reranking, and grounded executive briefings with strict verbatim citation verification.

---

## 🌟 Core Features & Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                 DUAL-MODE INTELLIGENCE TERMINAL                                   |
+---------------------------------------------------------------------------------------------------+
|  [ 🌐 Web Intelligence Mode ]                     |  [ 📑 Enterprise Document RAG Mode ]          |
|  • Autonomous query planning & discovery           |  • Drag-and-Drop PDF Knowledge Vault          |
|  • Authoritative web snapshotting (Tavily/HTTP)    |  • PyMuPDF table grid to Markdown parser     |
|  • Atomic claim extraction with confidence scores  |  • Token-aware sliding chunker (800 / 200)    |
|  • Cross-source contradiction/support matrix       |  • Bedrock Cohere 1024-dim vector embeddings  |
|  • Auditable conclusion-to-source evidence drawer  |  • Supabase pgvector HNSW cosine index        |
|                                                   |  • FlashRank cross-encoder reranker           |
|                                                   |  • Verbatim citation verification gate        |
|                                                   |  • Interactive Citation Deep-Dive Drawer      |
+---------------------------------------------------------------------------------------------------+
```

### 1. Web Intelligence Pipeline
- **Planning & Discovery**: Dynamically breaks down broad business/technical queries into targeted search angles.
- **Evidence Extraction**: Pulls verbatim excerpts and classifies claims with topic tagging and confidence ratings.
- **Cross-Source Analysis**: Evaluates claim pairs for agreement (`supports`), nuances (`qualifies`), and conflicts (`contradicts`).
- **Traceable Conclusions**: Every synthesized takeaway is hyperlinked to exact source excerpts in a slide-over trace drawer.

### 2. Enterprise Document RAG Pipeline
- **PyMuPDF Structured Parsing**: Native `find_tables()` converts complex PDF table grids into clean Markdown tables for zero-loss LLM ingestion.
- **Smart Chunking**: Token-aware sliding window (~800 tokens, 200 token overlap) with paragraph boundary preservation and page coordinates.
- **Vector Search & HNSW Indexing**: Generates 1024-dimensional embeddings via Bedrock Cohere Embed-v3, queried against Supabase PostgreSQL `pgvector` with HNSW cosine distance (`vector_cosine_ops`).
- **FlashRank Cross-Encoder Reranking**: Re-scores top 50 pgvector candidates down to the top 15 highest-relevance passages in under 15ms via ONNX runtime (`ms-marco-TinyBERT-L-2-v2`).
- **Provenance Verification Gate**: Synthesizes structured briefings with an automated verification gate that checks each citation quote against source chunks to mathematically eliminate hallucinations.

---

## 🏗️ Tech Stack

| Layer | Technologies |
|:---|:---|
| **Frontend** | React 19, TypeScript, Vite, `pnpm`, Cyber-Slate Dark Glassmorphism CSS |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic |
| **Database & Vectors** | Supabase PostgreSQL 17.6, `pgvector` v0.8.0, PgBouncer transaction pooling |
| **Embeddings & AI** | AWS Bedrock (Cohere Embed-v3, MiniMax M2.5 / Claude / Groq), FlashRank ONNX |
| **Document Processing** | PyMuPDF (fitz), Python-Multipart |
| **Testing** | Pytest (42 unit & integration tests), TestClient, SQLite in-memory fallback |

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python 3.11+** (3.12 recommended)
- **Node.js 20+**
- **pnpm** (`npm install -g pnpm`)

### 1. Clone & Configure Environment
```powershell
# Copy environment template
cp .env.example .env
```
Ensure your `.env` contains the required credentials (`AWS_BEARER_TOKEN_BEDROCK` or `GROQ_API_KEY`, `TAVILY_API_KEY`, and `DATABASE_URL`).

### 2. Backend Setup
```powershell
# Create and activate virtual environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend/requirements.txt

# Start FastAPI server
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000
```
API docs will be live at: **`http://localhost:8000/docs`**

### 3. Frontend Setup (with `pnpm`)
```powershell
# In a second terminal:
cd frontend

# Install dependencies
pnpm install

# Start Vite dev server
pnpm dev
```
Web application will be live at: **`http://localhost:5173`**

---

## 🧪 Verification & Test Suite

### Run Backend Unit & Integration Tests (42 Tests)
```powershell
.venv\Scripts\python.exe -m pytest backend\tests -v -o pythonpath=backend
```

### Run Frontend Type Checks & Production Build
```powershell
cd frontend
pnpm run build
```

---

## 📂 Project Structure

```
assignment-modus/
├── backend/
│   ├── alembic/              # Database migration definitions
│   ├── app/
│   │   ├── ai/               # Bedrock, Groq & OpenAI provider adapters
│   │   ├── documents/        # PDF parser, smart chunker, vision processor, service
│   │   ├── embeddings/       # Bedrock Cohere 1024-dim embedding provider
│   │   ├── rag/              # pgvector retrieval, FlashRank reranker, synthesis gate
│   │   ├── config.py         # App settings & environment validation
│   │   ├── database.py       # Dialect-aware lazy engine (Supabase NullPool + SQLite)
│   │   ├── models.py         # SQLAlchemy 14-table schema (pgvector Vector(1024))
│   │   ├── main.py           # FastAPI application root & router mounts
│   │   └── services.py       # Web intelligence multi-agent workflow
│   └── tests/                # 42 automated unit & integration test suites
├── frontend/
│   ├── src/
│   │   ├── components/       # UI cards, DocumentUpload, DocumentList, CitationDrawer, Tabs
│   │   ├── hooks/            # useResearchData & useRAGData polling hooks
│   │   ├── api.ts            # Typed REST API client & data contracts
│   │   ├── App.tsx           # Dual-mode root workspace
│   │   └── styles.css        # Obsidian & cyber-cyan design tokens & glassmorphism
│   ├── pnpm-lock.yaml        # Pinned pnpm lockfile
│   └── package.json
└── README.md
```

---

## 🔒 Security & Data Integrity
- Secrets live exclusively in local `.env` and are strictly excluded from source control.
- Ingested PDF text and web snapshots are treated as untrusted analytical data, isolated from execution context.
- All RAG citations must pass verbatim substring validation before being linked to final reports.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
