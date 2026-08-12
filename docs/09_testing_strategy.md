# 9. Testing Strategy

## Objective

Verify that the application is a dynamic, evidence-backed system—not prepared content designed for one demo question.

## Test layers

| Layer | Examples |
| --- | --- |
| Unit | URL normalization, content hashing, Pydantic validation, traceability guard, relationship enum validation. |
| Repository/database | Foreign keys, source deduplication, snapshot persistence, conclusion-to-claim links. |
| Service | Retry behavior, source failure handling, run-state transitions, bounded comparison selection. |
| API | Project creation, run status, events, source list, trace endpoint, invalid request responses. |
| End-to-end | A mocked provider/search run from question to cited conclusion. |
| Manual live demo | A new unseen research question against the configured cloud/search providers. |

## Deterministic test doubles

Automated tests must not depend on a live LLM, live search engine, or API key. Use fixture source pages and a fake `LLMProvider` returning schema-valid responses. This makes tests fast and reproducible while the actual app still supports live providers.

## Critical acceptance tests

1. A new question creates a fresh project/run and persists after restart.
2. Duplicate discovered URLs produce one source with multiple allowed snapshots, not duplicate evidence.
3. A claim without a matching source excerpt is rejected.
4. A conclusion with no linked claim cannot become `completed`.
5. A failed fetch results in a visible event and a partial run, while successful sources continue.
6. A source-injection string cannot change the expected structured extraction schema.
7. A second, different research question uses the same workflow without code/data edits.

## Demo rehearsal checklist

- Start from an empty or clearly known database state.
- Submit a prepared primary question once, then an unrelated surprise question.
- Show the event timeline, stored sources, evidence drawer, and past projects after refresh.
- Temporarily demonstrate a controlled failed-source or provider error if time permits.
- Never rely on an already-open terminal prompt or manually edited results.
