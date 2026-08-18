# 🛡️ EvidenceLab: Enterprise AI Research & Document Intelligence Platform

<p align="center">
  <img src="https://img.shields.io/badge/Status-Production%20Ready-00F0FF?style=for-the-badge&logo=shield" alt="Status: Production Ready" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React 19" />
  <img src="https://img.shields.io/badge/TypeScript-5.4-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript 5.4" />
  <img src="https://img.shields.io/badge/PostgreSQL-17.6-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL 17.6" />
  <img src="https://img.shields.io/badge/pgvector-v0.8.0-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="pgvector v0.8.0" />
  <img src="https://img.shields.io/badge/License-MIT-F59E0B?style=for-the-badge" alt="License: MIT" />
</p>

<p align="center">
  <strong>An auditable, zero-hallucination research intelligence terminal combining autonomous multi-source web discovery with high-throughput enterprise document vector RAG, 1024-dim pgvector HNSW indexing, and sub-15ms FlashRank neural reranking.</strong>
</p>

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-core-features--dual-mode-architecture">Features</a> •
  <a href="#-system-architecture">Architecture</a> •
  <a href="#-quickstart-guide">Quickstart</a> •
  <a href="#-configuration--environment-variables">Configuration</a> •
  <a href="#-rest-api-reference">API Reference</a> •
  <a href="#-database-schema--data-models">Database Schema</a> •
  <a href="#-testing--verification-gates">Testing</a> •
  <a href="#-production-deployment">Deployment</a>
</p>

---

## 📖 Overview

Modern enterprise strategy requires synthesizing insights from two complementary frontiers:
1. **The Open Web:** Real-time market developments, competitor movements, industry trends, and regulatory changes.
2. **Private Document Vaults:** Proprietary PDFs, financial statements, engineering whitepapers, and technical audits.

Standard LLM solutions frequently suffer from **hallucinations, lack of verifiable provenance, and shallow vector retrieval**. 

**EvidenceLab** eliminates these failure modes through an auditable, dual-mode intelligence terminal:

```
+---------------------------------------------------------------------------------------------------+
|                                 DUAL-MODE INTELLIGENCE TERMINAL                                   |
+---------------------------------------------------------------------------------------------------+
|  [ 🌐 Mode 1: Web Intelligence Engine ]           |  [ 📑 Mode 2: Enterprise Document RAG Vault ] |
|  • Autonomous query planning & sub-queries         |  • Drag-and-Drop PDF Knowledge Vault          |
|  • Authoritative web snapshotting (Tavily/HTTP)    |  • PyMuPDF native table-to-Markdown parser    |
|  • Atomic claim extraction with confidence scores  |  • Token-aware sliding chunker (800 / 200)    |
|  • Cross-source contradiction/support matrix       |  • Bedrock Cohere 1024-dim vector embeddings  |
|  • Verbatim character-offset excerpt validation    |  • Supabase pgvector HNSW cosine distance <=> |
|  • Executive Clean Briefing Sheet & Audit Tabs     |  • FlashRank cross-encoder neural reranker    |
|  • Slide-Over Conclusion Evidence Trace Drawer     |  • Strict Anti-Hallucination Citation Gate    |
|                                                   |  • Slide-Over Citation Deep-Dive Drawer       |
+---------------------------------------------------------------------------------------------------+
```

---

## 🌟 Core Features & Dual-Mode Architecture

### 🌐 1. Web Intelligence Engine
- **Autonomous Multi-Angle Planning:** Decomposes user inquiries into 2–4 orthogonal research sub-questions and targeted search queries.
- **Authoritative Web Discovery:** Fetches live content via Tavily API and extracts full text, applying URL canonicalization, tracking parameter removal, and SHA-256 content hashing.
- **Atomic Claim Extraction:** Extracts atomic factual assertions labeled with topical tags, confidence scores (`high`, `medium`, `low`), and exact character start/end offsets (`excerpt_start`, `excerpt_end`) validated against the retrieved text.
- **Cross-Source Evidence Assessment Matrix:** Pairwise claim comparisons classify relationships into `supports`, `qualifies`, or `contradicts` with rationale and conditional constraints.
- **Grounded Conclusion Synthesis:** Synthesizes executive conclusions hyperlinked to underlying claims with transparent reasoning and limitation disclosures.
- **Clean Briefing View & Audit Tabs:** Toggle seamlessly between an executive publication briefing sheet and a deep 4-tab technical audit view (Conclusions, Sources, Claims & Assessments, Activity Feed).

### 📑 2. Enterprise Document RAG Vault
- **PyMuPDF Structured Table Parsing:** Native `find_tables()` converts PDF table grids directly into clean Markdown tables (`| Col 1 | Col 2 |`), preventing tabular data flattening.
- **Token-Aware Sliding Window Chunking:** Dynamically splits documents into 800-token chunks with 200-token overlap, preserving semantic boundaries, page coordinates, and token counts.
- **1024-Dim Cohere Vector Embeddings:** High-dimensional vector generation via AWS Bedrock Cohere Embed-v3, indexed in Supabase PostgreSQL with HNSW cosine distance (`vector_cosine_ops`).
- **Sub-15ms FlashRank Neural Reranking:** Ultra-fast local cross-encoder reranking (`ms-marco-TinyBERT-L-2-v2` via ONNX runtime) filters top 50 pgvector candidates down to the top 15 highest-relevance passages.
- **🛡️ Anti-Hallucination Citation Gate:** All generated citations (`[DOC-X • p.Y]`) are verified against source chunks via normalized verbatim substring matching. Citations that fail verification are immediately flagged.
- **Interactive Citation Deep-Dive Drawer:** Slide-over inspection drawer with relevance percentages, document provenance, page numbers, and highlighted source quotes.

### 📱 3. Responsive Screen Metrics & a11y Hardening
- **5-Tier Adaptive Breakpoint System:** Fluid scaling across Desktop ($\ge 1024\text{px}$), Tablets ($768\text{px} - 1023\text{px}$), Large Phones ($640\text{px} - 767\text{px}$), Standard Phones ($480\text{px} - 639\text{px}$), and Compact Phones ($320\text{px} - 479\text{px}$).
- **Off-Canvas Mobile Navigation:** Replaces desktop sidebar on viewports $< 1024\text{px}$ with a sticky mobile top header (`.mobile-header`) and hardware-accelerated slide-out drawer with backdrop blur, Escape key dismissal, and touch-friendly targets.
- **Mobile Card Transformation:** Automatically converts wide data tables into readable stacked cards on screens $< 640\text{px}$ via `data-label` CSS selectors.
- **Safe-Area Inset Support:** Uses `100dvh` and `env(safe-area-inset-*)` variables for seamless rendering on notched mobile devices.

### 🔐 4. Authentication, Pilot Quota & Rate Limiting
- **Supabase Auth Integration:** Secure JWT verification supporting both authenticated users and anonymous local exploration.
- **5-Star Lifetime Pilot Quota:** Enforces a strict 5-star lifetime research run quota per user with visual star cards in `QuotaExceededModal`.
- **Sliding Window Rate Limiter:** In-memory sliding window rate limiter tracking timestamps by User ID and IP address (10 research runs/min, 60 read ops/min).

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph UI ["🖥️ Obsidian Cyber-Slate Frontend (React 19 + TypeScript + Vite)"]
        A[User Query / Research Inquiry] --> B{Mode Switch}
        B -->|🌐 Web Intelligence| C[Web Discovery Form & Guided Context]
        B -->|📑 Enterprise RAG| D[PDF Dropzone & Vault Manager]
        
        R1[Executive Clean Report Sheet] <--> R2[Interactive Citation Drawer]
        R3[4-Tab Deep Audit Panes] <--> R4[Evidence Trace Modal]
    end

    subgraph Backend ["⚡ FastAPI 0.115+ Backend Services"]
        C --> E[Autonomous Query Planner]
        E --> F[Tavily Search & Content Extraction]
        F --> G[Atomic Claim Extraction]
        G --> H[Cross-Source Evidence Assessment Matrix]
        H --> I[Conclusion Synthesis Engine]

        D --> J[PyMuPDF Text & Table Parser]
        J --> K[Token-Aware Sliding Chunker 800/200]
        K --> L[AWS Bedrock Cohere Embed-v3 1024-dim]
        L --> M[(Supabase PostgreSQL 17.6 + pgvector HNSW)]

        A --> N[RAG Retrieval Engine]
        N -->|Cosine Distance <=>| M
        M -->|Top 50 Candidates| O[FlashRank Cross-Encoder Neural Reranker]
        O -->|Top 15 Passages <15ms| P[Bedrock / MiniMax LLM Synthesis]
        P --> Q[Verbatim Quote Verification Gate]
        
        Q --> R1
        I --> R1
    end

    classDef ui fill:#0B1220,stroke:#00F0FF,stroke-width:2px,color:#fff;
    classDef srv fill:#0F172A,stroke:#3B82F6,stroke-width:2px,color:#fff;
    classDef db fill:#060911,stroke:#3ECF8E,stroke-width:2px,color:#fff;

    class A,B,C,D,R1,R2,R3,R4 ui;
    class E,F,G,H,I,J,K,L,N,O,P,Q srv;
    class M db;
```

---

## 🛠️ Tech Stack & Dependencies

| Component | Technology | Version | Purpose |
|:---|:---|:---|:---|
| **Frontend UI** | React, TypeScript, Vite | 19.0 / 5.4 / 8.2 | High-density Cyber-Slate dark terminal UI |
| **Package Manager** | `pnpm` / `npm` | 9.x+ | Deterministic frontend package management |
| **Backend Framework** | FastAPI, Starlette | 0.115+ | High-performance asynchronous REST API |
| **ORM & Migrations** | SQLAlchemy 2.0, Alembic | 2.0.48 / 1.15 | Async/Sync ORM mapping & schema migration management |
| **Primary Database** | Supabase PostgreSQL | 17.6 | Authoritative relational data store with PgBouncer pooling |
| **Vector Engine** | `pgvector` | v0.8.0 | Native HNSW vector index with cosine distance (`<=>`) |
| **Embeddings** | AWS Bedrock (Cohere) | Embed-v3 | 1024-dimensional semantic dense embeddings |
| **Cross-Encoder** | FlashRank (ONNX) | 0.2.9 | Sub-15ms local neural reranking (`ms-marco-TinyBERT`) |
| **PDF Extraction** | PyMuPDF (`fitz`) | 1.25.0 | High-fidelity text, metadata, and table-to-markdown parsing |
| **Web Discovery** | Tavily API / HTTP Client | 0.28+ | Autonomous web search, snapshotting, and sanitization |
| **Testing** | Pytest, TestClient | 8.3+ | 41 automated unit & integration test suites |

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python:** 3.12 or newer
- **Node.js:** 20.x or newer
- **Package Manager:** `pnpm` (or `npm`)
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

# Supabase Auth & JWT
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_JWT_SECRET=your_jwt_secret
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
> 📚 **Interactive Swagger Docs:** `http://localhost:8000/docs`

---

### Step 3: Frontend Setup & Launch

```powershell
# Open a new terminal and navigate to frontend
cd frontend

# Install frontend dependencies
npm.cmd install    # or: pnpm install

# Start Vite development server
npm.cmd run dev    # or: pnpm dev
```

> 🖥️ **Frontend Interface:** `http://localhost:5173`

---

## ⚙️ Configuration & Environment Variables

| Variable | Type | Default | Description |
|:---|:---|:---|:---|
| `DATABASE_URL` | String | `postgresql://...:6543/postgres` | Supabase PgBouncer transaction connection string |
| `DATABASE_URL_DIRECT` | String | `postgresql://...:5432/postgres` | Direct PostgreSQL port 5432 connection for migrations |
| `AI_PROVIDER` | String | `bedrock` | Active LLM provider: `bedrock` or `openai_compatible` |
| `AWS_REGION` | String | `us-east-1` | AWS region for Bedrock Converse and Embeddings |
| `AWS_BEARER_TOKEN_BEDROCK` | String | `None` | Bedrock / Mantle API bearer token |
| `BEDROCK_MODEL_ID` | String | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Active Bedrock LLM model ID |
| `EMBEDDING_MODEL_ID` | String | `cohere.embed-english-v3.0` | Bedrock Cohere Embed-v3 model ID |
| `EMBEDDING_DIMS` | Integer | `1024` | Cohere embedding dimensions |
| `TAVILY_API_KEY` | String | `None` | Tavily web search and extract API key |
| `AI_BASE_URL` | String | `https://api.minimax.chat/v1` | Universal OpenAI-compatible API base URL |
| `AI_API_KEY` | String | `None` | OpenAI-compatible API key (Groq, MiniMax, Kimi) |
| `AI_MODEL` | String | `minimax-text-01` | OpenAI-compatible model identifier |
| `SUPABASE_URL` | String | `https://...supabase.co` | Supabase project URL |
| `SUPABASE_ANON_KEY` | String | `None` | Supabase public anonymous API key |
| `SUPABASE_JWT_SECRET` | String | `None` | Supabase JWT signing secret |
| `MAX_FREE_MESSAGES_PER_USER` | Integer | `5` | Free lifetime pilot research runs per user |
| `RATE_LIMIT_RESEARCH_PER_MIN`| Integer | `10` | Rate limit for research run creation |
| `RATE_LIMIT_READ_PER_MIN` | Integer | `60` | Rate limit for read endpoints |
| `CHUNK_TARGET_TOKENS` | Integer | `800` | Target token size for sliding chunker |
| `CHUNK_OVERLAP_TOKENS` | Integer | `200` | Overlap token size for sliding chunker |
| `MAX_RAG_RESULTS` | Integer | `15` | Number of top passages sent to RAG synthesis |
| `MAX_RERANK_CANDIDATES` | Integer | `50` | Number of pgvector candidates sent to FlashRank |

---

## 📡 REST API Reference

### Web Intelligence & Workspace

| Method | Endpoint | Request Body | Response | Auth / Quota |
|:---|:---|:---|:---|:---|
| `GET` | `/api/v1/health` | None | `HealthStatus` | Public |
| `GET` | `/api/v1/workspace/bootstrap` | None | `WorkspaceBootstrapOut` | Optional User |
| `POST` | `/api/v1/research-projects` | `ProjectCreate` | `ProjectCreated` (202) | 1 Pilot Star |
| `GET` | `/api/v1/research-projects` | None | `List[ProjectOut]` | Optional User |
| `GET` | `/api/v1/research-runs/{id}` | None | `RunDetail` | Public |
| `POST` | `/api/v1/research-runs/{id}/retry` | None | `RunDetail` (202) | 1 Pilot Star |
| `GET` | `/api/v1/conclusions/{id}/trace` | None | `TraceOut` | Public |

### Enterprise Document RAG

| Method | Endpoint | Request Body | Response | Auth / Quota |
|:---|:---|:---|:---|:---|
| `POST` | `/api/v1/rag-vaults` | `RAGVaultCreate` | `RAGVaultOut` (201) | Optional User |
| `POST` | `/api/v1/projects/{id}/documents` | Multipart `file: UploadFile` | `DocumentOut` (201) | Optional User |
| `GET` | `/api/v1/projects/{id}/documents` | None | `DocumentListOut` | Optional User |
| `DELETE`| `/api/v1/documents/{id}` | None | `{ "deleted": true }` | Optional User |
| `POST` | `/api/v1/projects/{id}/rag-research` | `RAGResearchRequest` | `RAGReportOut` (200) | 1 Pilot Star |
| `GET` | `/api/v1/rag-reports/{id}` | None | `RAGReportOut` | Public |

### Authentication & User Quota

| Method | Endpoint | Request Body | Response | Auth / Quota |
|:---|:---|:---|:---|:---|
| `GET` | `/api/v1/auth/me` | None | `UserProfileOut` | Bearer JWT |
| `GET` | `/api/v1/auth/quota` | None | `UserQuotaOut` | Bearer JWT |

---

## 🗄️ Database Schema & Data Models

The platform defines **15 relational tables** managed via SQLAlchemy and Alembic migrations:

```
research_projects (id, user_id, project_type, title, original_question, created_at)
  ├── research_runs (id, project_id, status, provider_name, model_name, started_at, completed_at)
  │     ├── plan_items (id, run_id, item_type, text, position)
  │     ├── run_events (id, run_id, stage, status, message, metadata_json, occurred_at)
  │     ├── source_snapshots (id, source_id, run_id, content_hash, cleaned_text, fetch_status)
  │     │     └── claims (id, run_id, snapshot_id, topic, statement, exact_excerpt, excerpt_start, excerpt_end)
  │     │           ├── evidence_assessments (id, left_claim_id, right_claim_id, relationship, rationale)
  │     │           └── conclusion_claims (conclusion_id, claim_id, role)
  │     └── conclusions (id, run_id, statement, confidence, reasoning, limitations)
  │
  ├── documents (id, project_id, filename, file_hash, file_size_bytes, status, page_count)
  │     └── document_chunks (id, document_id, page_number, chunk_index, raw_text, combined_context, embedding: Vector(1024))
  │           └── rag_report_citations (id, report_id, chunk_id, verbatim_quote)
  │
  └── rag_reports (id, project_id, question, report_json, status, created_at)

sources (id, canonical_url, title, publisher, source_type, first_retrieved_at)
user_quotas (id, user_id, total_runs_used, max_free_runs, created_at, updated_at)
```

---

## 🧪 Testing & Verification Gates

### Backend Test Suite (Pytest)
The backend test suite executes 41 unit and integration tests verifying URL normalization, provider failover, JSON repair, RAG retrieval, and citation verification:

```powershell
# Run full pytest suite
python -m pytest backend/tests -v
```

### Frontend TypeScript & Build Verification
```powershell
cd frontend

# Run TypeScript typecheck
npm.cmd run lint    # tsc -b --noEmit

# Run Vite production build
npm.cmd run build   # tsc -b && vite build
```

---

## 🚢 Production Deployment

Detailed production deployment instructions are documented in [`DEPLOYMENT_GUIDE.md`](file:///d:/assignment-modus/DEPLOYMENT_GUIDE.md).

### Quick Deployment Topology:
1. **Database:** Supabase PostgreSQL 17.6 with `pgvector` enabled (`CREATE EXTENSION IF NOT EXISTS vector;`).
2. **Backend:** Railway / Docker deployment (`Procfile` / `railway.toml`) running `python run_server.py`.
3. **Frontend:** Vercel / Netlify static deployment pointing `VITE_API_URL` to the Railway backend domain.

---

## 📄 License

This project is licensed under the **MIT License** — see the [`LICENSE`](file:///d:/assignment-modus/LICENSE) file for details.
