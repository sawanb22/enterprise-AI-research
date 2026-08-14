# 🛡️ Enterprise AI Research & Document Intelligence Platform

<p align="center">
  <img src="https://img.shields.io/badge/Status-Production%20Ready-00F0FF?style=for-the-badge&logo=shield" alt="Status: Production Ready" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React 19" />
  <img src="https://img.shields.io/badge/PostgreSQL-17.6-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL 17.6" />
  <img src="https://img.shields.io/badge/pgvector-v0.8.0-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="pgvector v0.8.0" />
  <img src="https://img.shields.io/badge/License-MIT-F59E0B?style=for-the-badge" alt="License: MIT" />
</p>

<p align="center">
  <strong>An auditable, zero-hallucination research terminal combining autonomous multi-source web intelligence with high-throughput enterprise document RAG.</strong>
</p>

<p align="center">
  <a href="#-core-features--dual-mode-architecture">Features</a> •
  <a href="#-system-architecture">Architecture</a> •
  <a href="#-quickstart-guide">Quickstart</a> •
  <a href="#-configuration--environment-variables">Configuration</a> •
  <a href="#-rest-api-reference">API Reference</a> •
  <a href="#-testing--quality-gates">Testing</a> •
  <a href="#-security--data-governance">Security</a>
</p>

---

## 📖 Overview

Modern enterprise decision-making requires synthesizing insights from two critical frontiers:
1. **The Open Web:** Fast-moving competitor developments, market research, industry benchmarks, and news.
2. **Private Internal Vaults:** Proprietary PDFs, quarterly financial statements, engineering whitepapers, and audits.

Standard LLM solutions frequently suffer from **hallucinations, lack of verifiable provenance, and shallow retrieval**. 

This platform solves these challenges by combining a **Dual-Mode Intelligence Terminal** with **strict verbatim citation validation, 1024-dimension pgvector HNSW similarity indexing, and FlashRank cross-encoder neural reranking**.

```
+---------------------------------------------------------------------------------------------------+
|                                 DUAL-MODE INTELLIGENCE TERMINAL                                   |
+---------------------------------------------------------------------------------------------------+
|  [ 🌐 Mode 1: Web Intelligence Engine ]           |  [ 📑 Mode 2: Enterprise Document RAG Vault ] |
|  • Autonomous query planning & discovery           |  • Drag-and-Drop PDF Knowledge Vault          |
|  • Authoritative web snapshotting (Tavily/HTTP)    |  • PyMuPDF native table-to-Markdown parser    |
|  • Atomic claim extraction with confidence scores  |  • Token-aware sliding chunker (800 / 200)    |
|  • Cross-source contradiction/support matrix       |  • Bedrock Cohere 1024-dim vector embeddings  |
|  • Auditable conclusion-to-source evidence drawer  |  • Supabase pgvector HNSW cosine distance     |
|                                                   |  • FlashRank cross-encoder neural reranker    |
|                                                   |  • Verbatim citation verification gate        |
|                                                   |  • Interactive Citation Deep-Dive Drawer      |
+---------------------------------------------------------------------------------------------------+
```

---

## 🌟 Core Features & Dual-Mode Architecture

### 🌐 1. Web Intelligence Mode
- **Autonomous Multi-Angle Planning:** Automatically expands user prompts into orthogonal search angles and executes targeted discovery via Tavily / HTTP extractors.
- **Atomic Claim Extraction:** Parses source texts into atomic claims labeled with topical tags, confidence scores (`high`/`medium`/`low`), and character-offset source excerpts.
- **Cross-Source Contradiction Matrix:** Pairwise claim comparisons classify relationships into `supports`, `qualifies`, or `contradicts` with rationale.
- **Traceable Conclusion Lineage:** Synthesizes executive conclusions hyperlinked to underlying claims and snapshots.

### 📑 2. Enterprise Document RAG Mode
- **PyMuPDF Structured Table Parsing:** Native `find_tables()` converts PDF table grids directly into clean Markdown tables, preventing tabular data loss.
- **Smart Sliding Window Chunking:** Dynamically splits documents into 800-token chunks with 200-token overlap, preserving semantic boundaries, page coordinates, and token counts.
- **1024-Dim Cohere Vector Embeddings:** High-dimensional vector generation via AWS Bedrock Cohere Embed-v3, indexed in Supabase PostgreSQL with HNSW cosine distance (`vector_cosine_ops`).
- **Sub-15ms FlashRank Reranking:** Ultra-fast local cross-encoder reranking (`ms-marco-TinyBERT-L-2-v2` via ONNX runtime) filters top 50 pgvector candidates down to the top 15 highest-relevance passages.
- **🛡️ Anti-Hallucination Citation Gate:** All generated citations (`[DOC-X • p.Y]`) are verified against source chunks via normalized verbatim substring matching. Citations that fail verification are immediately flagged.
- **Interactive Citation Deep-Dive Drawer:** Slide-over inspection drawer with relevance percentages, document provenance, page numbers, and highlighted source quotes.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph UI ["🖥️ Obsidian Cyber-Slate Frontend (React 19 + TypeScript + Vite)"]
        A[User Query / Prompt] --> B{Mode Switch}
        B -->|🌐 Web Intelligence| C[Web Discovery Form]
        B -->|📑 Enterprise RAG| D[PDF Dropzone & Vault]
        R1[Executive Report View] <--> R2[Interactive Citation Drawer]
    end

    subgraph Backend ["⚡ FastAPI 0.115+ Backend Services"]
        C --> E[Autonomous Query Planner]
        E --> F[Tavily Search & Content Extraction]
        F --> G[Atomic Claim Extraction]
        G --> H[Cross-Source Evidence Assessment Matrix]
        H --> I[Conclusion Synthesis Engine]

        D --> J[PyMuPDF Text & Table Parser]
        J --> K[Token-Aware Sliding Chunker]
        K --> L[AWS Bedrock Cohere Embed-v3 1024-dim]
        L --> M[(Supabase PostgreSQL 17.6 + pgvector HNSW)]

        A --> N[RAG Retrieval Engine]
        N -->|Cosine Distance| M
        M -->|Top 50 Candidates| O[FlashRank Cross-Encoder Reranker]
        O -->|Top 15 Passages| P[Bedrock / MiniMax LLM Synthesis]
        P --> Q[Verbatim Quote Verification Gate]
        Q --> R1
        I --> R1
    end

    classDef ui fill:#0B1220,stroke:#00F0FF,stroke-width:2px,color:#fff;
    classDef srv fill:#0F172A,stroke:#3B82F6,stroke-width:2px,color:#fff;
    classDef db fill:#060911,stroke:#3ECF8E,stroke-width:2px,color:#fff;

    class A,B,C,D,R1,R2 ui;
    class E,F,G,H,I,J,K,L,N,O,P,Q srv;
    class M db;
```

---

## 🛠️ Tech Stack & Tooling

| Component | Technology | Version | Purpose |
|:---|:---|:---|:---|
| **Frontend UI** | React, TypeScript, Vite | 19.0 / 5.4 | High-density Cyber-Slate dark terminal UI |
| **Package Manager** | `pnpm` | 9.x+ | Fast, deterministic frontend package management |
| **Backend Framework** | FastAPI, Starlette | 0.115+ | High-performance asynchronous REST API |
| **ORM & Migrations** | SQLAlchemy 2.0, Alembic | 2.0.48 / 1.15 | Async ORM mapping & schema migration management |
| **Primary Database** | Supabase PostgreSQL | 17.6 | Authoritative relational data store with PgBouncer pooling |
| **Vector Engine** | `pgvector` | v0.8.0 | Native HNSW vector index with cosine distance (`<=>`) |
| **Embeddings** | AWS Bedrock (Cohere) | Embed-v3 | 1024-dimensional semantic embeddings |
| **Cross-Encoder** | FlashRank (ONNX) | 0.2.9 | Sub-15ms local neural reranking (`ms-marco-TinyBERT`) |
| **PDF Extraction** | PyMuPDF (`fitz`) | 1.25.0 | High-fidelity text, metadata, and table-to-markdown parsing |
| **Web Discovery** | Tavily API / HTTP Client | 0.28+ | Autonomous web search, snapshotting, and sanitization |
| **Testing** | Pytest, TestClient | 8.3+ | 41 automated unit & integration test suites |

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python:** 3.12 or newer
- **Node.js:** 20.x or newer
- **Package Manager:** `pnpm` (install via `npm install -g pnpm`)
- **Database:** Supabase PostgreSQL instance (or local PostgreSQL 16+ with `pgvector`)
- **AI Keys:** AWS Bedrock Bearer Token / IAM credentials **OR** OpenAI-compatible API key (MiniMax, Groq, OpenRouter)

---

### Step 1: Clone Repository & Setup Environment

```powershell
# Clone the repository
git clone https://github.com/sawanb22/enterprise-AI-research.git
cd enterprise-AI-research

# Copy environment configuration template
cp .env.example .env
```

Edit your `.env` file and supply your API credentials and database connection strings:

```env
# AI Model Provider: "bedrock" or "openai_compatible"
AI_PROVIDER=bedrock

# Bedrock / Cohere Credentials
AWS_BEARER_TOKEN_BEDROCK=your_bedrock_token
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
EMBEDDING_MODEL_ID=cohere.embed-english-v3.0

# Web Search Provider
TAVILY_API_KEY=your_tavily_key

# Supabase PostgreSQL Database (Transaction Pooler Port 6543)
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres?sslmode=require
DATABASE_URL_DIRECT=postgresql://postgres.[ref]:[password]@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres?sslmode=require
```

---

### Step 2: Backend Setup & Launch

```powershell
# 1. Create and activate Python 3.12 virtual environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1    # On Windows PowerShell
# source .venv/bin/activate     # On Linux / macOS

# 2. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r backend/requirements.txt

# 3. Start FastAPI server
python -m uvicorn backend.app.main:app --reload --port 8000
```

> 🌐 **Backend API:** `http://localhost:8000`  
> 📚 **Interactive Swagger API Docs:** `http://localhost:8000/docs`

---

### Step 3: Frontend Setup & Launch

```powershell
# Open a new terminal window
cd frontend

# 1. Install dependencies with pnpm
pnpm install

# 2. Start the Vite development server
pnpm dev
```

> 💻 **Web Application Terminal:** `http://localhost:5173`

---

## 🗄️ Database Schema & `pgvector` Setup

The application uses **14 synchronized tables** in Supabase PostgreSQL:

```mermaid
erDiagram
    research_projects ||--o{ research_runs : has
    research_projects ||--o{ documents : stores
    research_projects ||--o{ rag_reports : generates

    research_runs ||--o{ source_snapshots : captures
    research_runs ||--o{ claims : produces
    research_runs ||--o{ conclusions : synthesizes

    sources ||--o{ source_snapshots : provides
    source_snapshots ||--o{ claims : grounds
    claims ||--o{ evidence_assessments : compares
    claims ||--o{ conclusion_claims : references
    conclusions ||--o{ conclusion_claims : contains

    documents ||--o{ document_chunks : splits_into
    document_chunks ||--o{ rag_report_citations : cited_in
    rag_reports ||--o{ rag_report_citations : contains
```

### Initializing the Database in Supabase:
1. Open your **Supabase Dashboard → SQL Editor**.
2. Run `CREATE EXTENSION IF NOT EXISTS vector;` to enable `pgvector`.
3. The application will automatically synchronize tables via SQLAlchemy upon startup, or you can run migrations via Alembic:
   ```powershell
   alembic -c backend/alembic.ini upgrade head
   ```

---

## ⚙️ Configuration & Environment Variables

| Variable | Type | Default | Description |
|:---|:---:|:---|:---|
| `AI_PROVIDER` | string | `bedrock` | AI provider adapter (`bedrock` or `openai_compatible`) |
| `AWS_BEARER_TOKEN_BEDROCK` | string | `None` | Amazon Bedrock Bearer Token / API Key |
| `AWS_REGION` | string | `us-east-1` | AWS Region for Bedrock operations |
| `BEDROCK_MODEL_ID` | string | `anthropic.claude-3-5-sonnet...` | Primary LLM model identifier |
| `EMBEDDING_MODEL_ID` | string | `cohere.embed-english-v3.0` | 1024-dim embedding model for document vectors |
| `AI_BASE_URL` | string | `https://api.minimax.chat/v1` | Base URL if using OpenAI-compatible provider |
| `AI_API_KEY` | string | `None` | API Key for OpenAI-compatible provider |
| `AI_MODEL` | string | `minimax-text-01` | Model name for OpenAI-compatible provider |
| `TAVILY_API_KEY` | string | `None` | Tavily API Key for autonomous web discovery |
| `DATABASE_URL` | string | `postgresql://...` | Transaction pooler URL (Port 6543) for app queries |
| `DATABASE_URL_DIRECT` | string | `postgresql://...` | Direct connection URL (Port 5432) for migrations |
| `CHUNK_TARGET_TOKENS` | int | `800` | Target token size per document chunk |
| `CHUNK_OVERLAP_TOKENS` | int | `200` | Sliding window token overlap between chunks |
| `MAX_RERANK_CANDIDATES`| int | `50` | Number of pgvector candidates sent to FlashRank |
| `MAX_RAG_RESULTS` | int | `15` | Number of top reranked chunks supplied to LLM synthesis |
| `ALLOWED_ORIGINS` | string | `http://localhost:5173` | Allowed CORS origins for FastAPI middleware |

---

## 📡 REST API Reference

### 1. Document Ingestion Vault
| Endpoint | Method | Description |
|:---|:---:|:---|
| `/api/v1/documents/upload` | `POST` | Upload and ingest a PDF document (multipart/form-data) |
| `/api/v1/documents` | `GET` | List all uploaded documents with status, page count, and file size |
| `/api/v1/documents/{document_id}` | `GET` | Retrieve specific document metadata and chunk count |
| `/api/v1/documents/{document_id}` | `DELETE` | Delete document and cascade delete associated vector chunks |

### 2. Enterprise RAG Synthesis
| Endpoint | Method | Description |
|:---|:---:|:---|
| `/api/v1/rag/synthesize` | `POST` | Execute vector search, FlashRank rerank, and grounded LLM synthesis |
| `/api/v1/rag/reports` | `GET` | List all historical synthesized RAG reports for a project |
| `/api/v1/rag/reports/{report_id}` | `GET` | Retrieve detailed RAG report with verified citation metadata |

### 3. Web Intelligence Engine
| Endpoint | Method | Description |
|:---|:---:|:---|
| `/api/v1/projects` | `POST` | Create a new research project and start web discovery run |
| `/api/v1/projects` | `GET` | List all active research projects |
| `/api/v1/projects/{project_id}/runs` | `GET` | List all execution runs for a project |
| `/api/v1/runs/{run_id}` | `GET` | Get run telemetry, claims, matrix assessments, and conclusions |
| `/api/v1/runs/{run_id}/events` | `GET` | Get real-time stage execution timeline events |
| `/api/v1/runs/{run_id}/retry` | `POST` | Immutable run retry resuming from latest stable stage |

### 4. System Health
| Endpoint | Method | Description |
|:---|:---:|:---|
| `/api/v1/health` | `GET` | System health check (database connection, AI provider readiness) |

---

## 🧪 Testing & Quality Gates

The codebase includes a comprehensive test suite covering chunking, embeddings, PDF parsing, cross-encoders, pgvector queries, RAG synthesis, and web research workflows.

```powershell
# Run the complete test suite (41 tests) against PostgreSQL
.venv\Scripts\python.exe -m pytest backend/tests -v -o pythonpath=backend

# Run frontend TypeScript type checking
cd frontend
npx tsc --noEmit

# Test production Vite build
pnpm run build
```

---

## 🔒 Security & Data Governance

1. **Zero Secret Leakage:** Credentials live strictly in local `.env` and are blocked from git tracking.
2. **Deterministic Citation Verification:** Prevents LLM hallucinations by verifying every generated citation quote against indexed text in the database.
3. **Isolated Test Environments:** Unit and integration test fixtures run within isolated database transactions that roll back automatically upon completion.
4. **Data Minimization:** Web snapshots and uploaded PDFs are stored with SHA-256 cryptographic hashes for deduplication and audit traceability.

---

## 🤝 Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Ensure all tests pass (`pytest backend/tests -o pythonpath=backend` & `pnpm run build`).
4. Commit your changes (`git commit -m 'feat: add amazing feature'`).
5. Push to the branch (`git push origin feature/amazing-feature`).
6. Open a Pull Request.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

