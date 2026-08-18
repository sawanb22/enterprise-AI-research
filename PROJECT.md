# Project: Full-Stack Security Audit, Automated Penetration Testing & OWASP Top 10 Assessment

## Architecture
- **Backend**: FastAPI with Python 3.12, SQLAlchemy 2.0 ORM, PostgreSQL with pgvector, PyMuPDF, FlashRank reranker.
- **Authentication**: Supabase Auth integration, asymmetric JWKS (ES256, RS256, EdDSA) via PyJWKClient, symmetric HS256, remote `/auth/v1/user` fallback.
- **Access Control**: Multi-tenant workspace isolation across Projects, Research Runs, Documents, Claims, Conclusions, and RAG Reports.
- **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS, Supabase client (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`), Vercel edge proxy.
- **AI Integrations**: AWS Bedrock Converse, OpenAI-compatible (MiniMax), Tavily search API, BGE-small embeddings.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | JWT Verification & JWKS | Asymmetric ES256 & symmetric HS256 verification with claims and expiration | M1 | ORIGINAL_REQUEST §R1 |
| 2 | Anti-IDOR / BOLA Authorization | Multi-tenant access control enforcing 401 unauthenticated and 404 cross-tenant across all endpoints | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Test Bypass Hardening | Environment-gating `X-Test-User-Id` and `mock-user-` token handlers | M1 | Survey Findings (VULN-01/02) |
| 4 | SQL Injection Immunity | 100% Parameterized SQLAlchemy 2.0 ORM & pgvector distance expressions | M2 | ORIGINAL_REQUEST §R2 |
| 5 | PDF Upload & Ingestion Safety | `.pdf` extension, `%PDF` magic bytes, 50MB stream limit, 10-page quota, UUID storage | M2 | ORIGINAL_REQUEST §R2 |
| 6 | SSRF & Memory Exhaustion Defense | Delegated Tavily SaaS search, bounded context windows, vision API limits | M2 | ORIGINAL_REQUEST §R2 |
| 7 | Secret Isolation Verification | Zero private credentials in `frontend/dist/` or repository files | M2 | ORIGINAL_REQUEST §R3 |
| 8 | CORS & Edge Proxy Hardening | Origin restrictions, Vercel regex, anti-proxy caching headers | M2 | ORIGINAL_REQUEST §R3 |
| 9 | Automated Security Test Suite | 100% pass rate across security, auth/quota, CORS preflight, SOLID tests | M3 | ORIGINAL_REQUEST §R4 |
| 10 | Executive Audit Report Deliverable | Comprehensive OWASP Top 10 audit report at `docs/PROJECT_WIDE_SECURITY_AUDIT_REPORT.md` | M4 | ORIGINAL_REQUEST §R4 |
| 11 | Review, Challenge & Forensic Audit | Adversarial verification, reviewer signoff, and forensic integrity audit | M5 | System Governance |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Auth & Anti-IDOR Remediation | Remediate unauthenticated IDOR in `main.py`, `documents/router.py`, `rag/router.py`; gate test headers in `dependencies.py` & `jwt_verifier.py`; add unauthenticated IDOR regression tests in `test_security_audit.py`. | None | DONE |
| M2 | Ingestion & Secrets Verification | Verify PDF magic bytes, injection immunity, secret isolation in `frontend/dist/`, and CORS headers. | M1 | DONE |
| M3 | Security Test Suite Verification | Execute full automated security test suite (`pytest tests/test_security*.py tests/test_auth_and_quota.py tests/test_cors_preflight.py tests/test_solid_architecture.py`) ensuring 100% pass rate. | M1, M2 | DONE |
| M4 | Executive Audit Report Generation | Compile executive markdown audit report at `docs/PROJECT_WIDE_SECURITY_AUDIT_REPORT.md`. | M1, M2, M3 | DONE |
| M5 | Quality Gates, Review & Forensic Audit | 2 Reviewers, 2 Challengers, and 1 Forensic Auditor to verify integrity and quality. | M4 | DONE |

## Code Layout
- `backend/app/auth/`: JWT verification, dependencies, token caching, user models
- `backend/app/documents/`: Document ingestion, PDF parser, chunker, vision, storage
- `backend/app/rag/`: Retrieval, vector store, synthesis, citations, router
- `backend/app/main.py`: Core FastAPI application endpoints and route handlers
- `backend/tests/`: Pytest security, penetration, and unit test suites
- `frontend/dist/`: Static distribution assets (verified secret-free)
- `docs/PROJECT_WIDE_SECURITY_AUDIT_REPORT.md`: Comprehensive executive security audit report deliverable
