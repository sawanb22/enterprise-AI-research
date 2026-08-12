# 10. Scalability and Operations

## MVP boundary

The first build targets a single-user demonstration with small bounded research runs. SQLite, an in-process orchestrator, polling, and provider rate-limit-aware sequential calls are intentional scope choices, not claims of production readiness.

## Scale path

| Growth trigger | Evolution |
| --- | --- |
| Multiple concurrent users/runs | Move orchestration to a durable worker/queue and add per-user/job limits. |
| Larger operational database | Change the SQLAlchemy database URL to PostgreSQL, add migrations, backups, and indexes. |
| Large document corpus | Add chunking and vector retrieval alongside the relational evidence model; do not replace evidence links with vector results. |
| High source volume | Use asynchronous fetch workers, a URL/content cache, robots/policy controls, and rate limits. |
| Multiple organisations | Add organisation/tenant IDs, authentication, RBAC, and row-level isolation. |
| Provider risk | Add a second `LLMProvider`, circuit breaking, retries with backoff, and clear degraded-mode messages. |

## 1,000-record question

At 1,000 simultaneous research items, the current in-process loop would be insufficient. The architecture scales by separating the stateless API from durable queued workers; a run becomes a collection of idempotent tasks (discover, fetch, extract, compare, synthesise). PostgreSQL stores state, workers scale horizontally, and rate limits/backpressure protect external providers. The existing run IDs, source snapshots, claims, and events remain valid.

## Operational minimum for the challenge

- Structured application logs with run and project IDs.
- Run events persisted for user-visible diagnostics.
- Timeouts and limited retries for external requests.
- API-key configuration through environment variables.
- `.env.example`, setup guide, library/provider inventory, and license notes before delivery.
- Backup/restore is a copy of the SQLite database in MVP; a production deployment uses managed PostgreSQL backups.

## Reliability posture

An external LLM or search provider can fail or change its free plan. The application records which provider/model was used, exposes the error, preserves completed research, and allows retry. It does not silently switch to uncited static content.
