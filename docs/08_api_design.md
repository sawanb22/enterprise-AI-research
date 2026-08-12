# 8. API Design

The API is REST-like, versioned under `/api/v1`, and uses Pydantic request/response schemas. The frontend never calls an AI or search provider directly.

## MVP endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/research-projects` | Create a project and start its first research run. |
| `GET` | `/research-projects` | List persisted projects. |
| `GET` | `/research-projects/{project_id}` | Project summary and latest run. |
| `POST` | `/research-runs/{run_id}/retry` | Create a new run for the same project after a failed/partial run, retaining prior evidence unchanged. |
| `GET` | `/research-runs/{run_id}` | Run status, counts, and report summary. |
| `GET` | `/research-runs/{run_id}/events` | Observable pipeline timeline. |
| `GET` | `/research-runs/{run_id}/sources` | Source cards and fetch status. |
| `GET` | `/research-runs/{run_id}/claims` | Filtered claims and comparisons. |
| `GET` | `/conclusions/{conclusion_id}/trace` | Full conclusion-to-source evidence chain. |
| `GET` | `/health` | Liveness/configuration-safe health check. |

## Create example

```json
POST /api/v1/research-projects
{
  "question": "How is AI transforming retail operations?",
  "title": "Retail AI research"
}
```

Response: `202 Accepted` with `project_id`, `run_id`, initial `queued` status, and a status URL. The background orchestration begins after persistence succeeds.

## Response conventions

- IDs are UUIDs.
- Times are ISO 8601 UTC.
- Long-running work returns `202`, never holds the HTTP request open.
- Errors use a consistent `{code, message, details}` envelope.
- A completed-but-incomplete run returns its real `partial` status and limitations, not `200 complete` with fabricated results.

## UI polling

The UI polls the run endpoint/events every 1-2 seconds while a run is active. Server-sent events and websockets are intentionally deferred to keep the initial implementation reliable.
