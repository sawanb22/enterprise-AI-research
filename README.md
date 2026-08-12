# Enterprise AI Research Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React: 19](https://img.shields.io/badge/react-19-61dafb.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)

A working enterprise AI research application for MODUS Assignment 9. It accepts a new research question, runs a structured research workflow, persists its results, compares sourced claims, highlights disagreement, and produces conclusions that a reviewer can trace back to source excerpts.


## Project goal

This is not a chatbot with web search. The application owns the workflow, research records, source snapshots, claim relationships, run history, and traceability. An LLM is used only for bounded semantic tasks: planning, claim extraction, evidence comparison, and synthesis.

## MVP architecture decisions

| Area | MVP decision |
| --- | --- |
| Assignment | 9 - Enterprise AI Research Agent |
| Frontend | React + Vite + TypeScript |
| Backend | Python + FastAPI |
| Persistence | SQLAlchemy with SQLite by default; PostgreSQL-compatible schema for later deployment |
| AI | Cloud-provider adapter; Groq is the first provider to test, not a hard dependency |
| Search | Provider adapter; the final permitted/free source-discovery provider is selected during implementation |
| Retrieval | Structured and full-text retrieval; no vector database/RAG in the MVP |
| Execution | Persisted in-process research run with retry/restart support; no queue for the MVP |

## The live demonstration path

```text
New question -> plan -> discover sources -> fetch/store snapshots
-> extract atomic claims -> compare evidence -> synthesise conclusions
-> open a conclusion and trace it to exact source excerpts
```

The evaluator must be able to enter a question not prepared in advance and see this pipeline operate.

## Documentation

- [Project context and continuation handoff](PROJECT_CONTEXT.md)
- [Problem definition](docs/01_problem_definition.md)
- [Requirements](docs/02_requirements.md)
- [System architecture](docs/03_system_architecture.md)
- [Research workflow](docs/04_research_workflow.md)
- [Data model](docs/05_data_model.md)
- [AI pipeline](docs/06_ai_pipeline.md)
- [Evidence and traceability](docs/07_evidence_and_traceability.md)
- [API design](docs/08_api_design.md)
- [Testing strategy](docs/09_testing_strategy.md)
- [Scalability and operations](docs/10_scalability.md)

## Implementation status

The MVP application is implemented: FastAPI API, persistent SQLite data model, Groq/Tavily provider adapters, React UI, evidence trace drawer, and automated core tests. API credentials are intentionally not included.

## Run locally

Prerequisites: Python 3.11+, Node.js 20+, and pnpm (or npm). Docker and PostgreSQL are not required.

1. Copy `.env.example` to `.env` and set `GROQ_API_KEY` and `TAVILY_API_KEY`. Do not commit `.env` or paste its values into chat.
2. Create a Python virtual environment, activate it, and install backend dependencies:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r .\backend\requirements.txt
   ```

3. Start the API from the repository root:

   ```powershell
   python .\backend\run_server.py
   ```

   The API documentation is available at `http://localhost:8000/docs`.

4. In a second terminal, start the React application:

   ```powershell
   Set-Location .\frontend
   pnpm install
   pnpm dev
   ```

   Open `http://localhost:5173`.

5. Submit a new question. The app stores the local SQLite database at `data/research_agent.db` and shows a visible event timeline as it plans, searches, fetches, extracts, compares, synthesises, and validates evidence.

## Verify

```powershell
$env:PYTHONPATH = "$PWD\backend"
python -m pytest .\backend\tests -q
Set-Location .\frontend
pnpm run build
```

## Technology and licence inventory

| Component | Purpose | Licence / service terms |
| --- | --- | --- |
| FastAPI, SQLAlchemy, Pydantic, HTTPX | Backend/API/data validation | Open-source; retain the pinned dependency list |
| React, Vite, TypeScript | Web interface/build | Open-source; retain `frontend/pnpm-lock.yaml` |
| SQLite | Persistent local knowledge base | Public domain |
| Groq API | Configured cloud LLM provider | External free-tier service; provider terms and rate limits apply |
| Tavily API | Configured source discovery/extraction | External free-tier service; provider terms and rate limits apply |

The provider adapters are isolated so either cloud service can be replaced if its free plan changes.

## Security and configuration rules

- API keys must live only in local `.env` files and never in source control.
- The repository will include `.env.example`, with variable names but no secrets.
- External source text is untrusted data, never an instruction to the model or application.
- The app will retain retrieval timestamps, source URLs, source snapshots, and model/provider metadata for every run.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

