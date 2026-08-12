# Project Context and Continuation Handoff

Read this file before changing the project. It is the concise source of truth for a new AI IDE session or developer taking over the work.

## 1. Project identity

- **Name:** Enterprise Research Agent / EvidenceLab
- **Assessment:** MODUS Enterprise AI Build Challenge, Assignment 9 - Enterprise AI Research Agent
- **Objective:** Build a real application that accepts an unseen enterprise research question and runs a visible, persistent workflow:

  ```text
  Question -> research plan -> source discovery -> source snapshots
  -> source-grounded claims -> evidence comparison -> conclusions
  -> clickable conclusion-to-source traceability
  ```

- **Important assessment constraint:** This must not become a chatbot wrapper, a hard-coded demo, or a single giant prompt. The evaluator may submit a new question live.

## 2. Architecture decisions already made

| Area | Decision |
| --- | --- |
| Frontend | React + Vite + TypeScript |
| Backend | Python + FastAPI modular monolith |
| Database | SQLite by default through SQLAlchemy; keep models PostgreSQL-compatible |
| LLM | Groq cloud API through `GroqProvider` adapter |
| Web research | Tavily Search + Extract through `TavilyProvider` adapter |
| Retrieval | Structured relational/full-text direction only; no RAG/vector database for MVP |
| Execution | Persisted sequential background run; no queue for MVP |
| UI purpose | Make the pipeline, sources, claims, conclusions, and evidence trail visible |

Do not introduce Docker, PostgreSQL, Redis, LangChain, a vector database, microservices, or multi-agent orchestration unless there is a concrete assessment need and time permits.

## 3. Repository map

```text
README.md                 Setup and project overview
PROJECT_CONTEXT.md        This continuation handoff
.env                      Local secrets only; ignored by Git
.env.example              Required environment variable names
docs/                     Architecture and design source-of-truth documents
backend/
  app/
    main.py               FastAPI routes and response composition
    models.py             SQLAlchemy persistence model
    services.py           Research orchestration and integrity checks
    providers.py          Groq/Tavily adapters and structured-output validation
    schemas.py            API schemas
    config.py             Environment configuration
  run_server.py           Local backend launcher
  requirements.txt        Backend dependencies
  tests/                  Unit and mocked full-workflow tests
frontend/
  src/App.tsx             Single-page dashboard and polling UI
  src/api.ts              Backend API client/types
  src/styles.css          UI styling
  package.json            Frontend scripts/dependencies
```

## 4. Environment and secrets

`.env` exists locally and is intentionally ignored. Never print, commit, log, or paste its values.

Required variables:

```dotenv
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
TAVILY_API_KEY=
DATABASE_URL=sqlite:///./data/research_agent.db
ALLOWED_ORIGINS=http://localhost:5173
```

The configured keys were successfully detected and separately validated with a small Groq planning call and Tavily search call.

## 5. Implemented functionality

### Persisted entities

`ResearchProject`, `ResearchRun`, `PlanItem`, `RunEvent`, `Source`, `SourceSnapshot`, `Claim`, `EvidenceAssessment`, `Conclusion`, and `ConclusionClaim` are implemented.

Traceability is intentionally explicit:

```text
Conclusion -> ConclusionClaim -> Claim -> SourceSnapshot -> Source URL
```

### Backend workflow

`services.run_research()` currently:

1. Creates a stored plan with sub-questions/search queries.
2. Searches Tavily and deduplicates normalized URLs.
3. Extracts and persists source snapshots.
4. Persists failed source attempts as snapshots with `fetch_status="failed"`.
5. Extracts atomic claims with exact source excerpts.
6. Compares related claims as `supports`, `qualifies`, `contradicts`, or `unrelated`.
7. Synthesises conclusions using stored claim IDs.
8. Rejects conclusions without evidence links.
9. Marks insufficient evidence as `partial`, and unrecoverable upstream failures as `failed`.

### AI output safeguards

Groq responses use Pydantic schemas. If a response has an invalid JSON shape or schema, the provider retries once with a repair instruction. Invalid output after that becomes a visible failure/partial state, not invented content.

### Retry semantics

`POST /api/v1/research-runs/{run_id}/retry` creates a **new immutable run** for the same project. It copies the prior run's persisted plan, source snapshots, claims, and assessments, then resumes from the first incomplete stage instead of redoing saved provider work. For example, a Groq rate-limit failure during synthesis retries directly at synthesis. The failed run remains unchanged.

### Frontend

The dashboard can create a research run, poll status/events, show source and claim counts, display conclusions, open evidence traces, list stored source snapshots, and retry a failed/partial run.

## 6. APIs

| Endpoint | Purpose |
| --- | --- |
| `GET /api/v1/health` | Liveness and non-secret provider configuration state |
| `POST /api/v1/research-projects` | Create project and begin run |
| `GET /api/v1/research-projects` | List persisted projects |
| `GET /api/v1/research-runs/{run_id}` | Run status, plan, and conclusions |
| `GET /api/v1/research-runs/{run_id}/events` | Visible workflow timeline |
| `GET /api/v1/research-runs/{run_id}/sources` | Source snapshots including failed fetches |
| `GET /api/v1/research-runs/{run_id}/claims` | Extracted claims |
| `GET /api/v1/research-runs/{run_id}/assessments` | Evidence relationships |
| `GET /api/v1/conclusions/{id}/trace` | Conclusion-to-source evidence chain |
| `POST /api/v1/research-runs/{run_id}/retry` | Start a clean retry run |

## 7. Verification already completed

- Python source compiles.
- Frontend production build passes: `pnpm run build`.
- **Eight automated tests pass.** They cover URL normalization, persistence, resumable immutable retry creation, a mocked end-to-end workflow, source-fetch failure persistence, partial status for zero valid claims, a structured-LLM repair attempt, and retrying a synthesis-stage rate-limit failure without rerunning plan/extraction/comparison.
- Two bounded real provider runs were completed successfully, including the hardened run with 2 sources, 4 claims, and 3 traceable conclusions.
- Backend health endpoint and frontend page both returned HTTP 200 when the local services were started.

## 8. Run the application

From the repository root, start the backend:

```powershell
python .\backend\run_server.py
```

From a second terminal, start the frontend:

```powershell
Set-Location .\frontend
pnpm dev
```

Open `http://localhost:5173`.

Backend API documentation: `http://localhost:8000/docs`.

If the UI is unavailable, verify both first:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/v1/health
Invoke-WebRequest http://127.0.0.1:5173
```

## 9. Current priority and remaining work

The vertical slice is complete. Before final assessment delivery, prioritise only the following:

1. Perform several manual live runs with varied questions and wait/retry if cloud-provider rate limits occur.
2. Improve user-facing error text for rate limits and external-provider failures, including a safe retry-after message when supplied by a provider.
3. Add API-level tests for 404/409 responses and the trace endpoint's orphan-conclusion guard.
4. Add a small sample/synthetic data set only if needed for an offline demonstration; never present it as live research.
5. Rehearse a 10-15 minute demonstration: unseen question, visible pipeline, sources, conclusions, evidence drawer, refresh persistence, then a second unrelated question.
6. Add a final license/dependency inventory check and ensure `.env` remains untracked.

## 10. Rules for the next agent/developer

- Read `README.md`, this file, and the relevant `docs/` file before altering architecture.
- Preserve the provider abstraction; do not spread Groq/Tavily calls into routes or UI.
- Do not expose `.env` values in terminal output, code, commits, screenshots, or messages.
- Do not remove persistent data or use destructive Git commands without explicit user approval.
- Keep any new conclusion evidence-linked; source snippets must remain exact and inspectable.
- Prefer small, testable changes. Run backend tests and the frontend build after meaningful changes.
- Update this file whenever architecture, test status, provider decisions, or the current remaining work materially changes.
