# 2. Requirements

## Functional requirements

| ID | Requirement | Acceptance signal |
| --- | --- | --- |
| FR-01 | Create a project from a research question. | A persisted project and run are created. |
| FR-02 | Generate sub-questions and search queries. | The plan is visible and stored. |
| FR-03 | Discover, deduplicate, fetch, and store multiple sources. | Source cards show URL, metadata, timestamp, and snapshot status. |
| FR-04 | Extract atomic, classified claims from sources. | Each claim includes an exact supporting excerpt. |
| FR-05 | Compare related claims. | Relationships are `supports`, `qualifies`, `contradicts`, or `unrelated`. |
| FR-06 | Generate evidence-bounded conclusions. | Each conclusion links to source-backed claims. |
| FR-07 | Provide traceability. | A user can navigate conclusion -> claim -> snapshot -> source. |
| FR-08 | Support a new live question without code changes. | The same workflow processes it. |
| FR-09 | Preserve completed work. | Reloading shows prior projects/runs. |
| FR-10 | Record failed/partial work visibly. | A run shows the failed stage and can be retried. |

## Non-functional requirements

- **Reproducible:** free/open-source framework and database; cloud credentials are optional configuration, not hard-coded.
- **Explainable:** source excerpts and relationship explanations are stored, rather than only generated prose.
- **Bounded:** cap an MVP run at 3 queries, 5-8 source snapshots, and 8-15 claims.
- **Resilient:** continue with successful sources when one source fails; distinguish `partial` from `complete`.
- **Safe:** validate all LLM structured output; never execute source text; keep secrets out of the repository.
- **Honest:** label AI-generated classification/confidence as such and never claim contradiction detection is proof of fact.

## Out of scope for the first build

Authentication, multi-tenancy, streaming tokens, automated publishing, large-scale crawling, collaborative editing, embeddings, and a distributed job queue.
