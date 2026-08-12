# 4. Research Workflow

## Run lifecycle

```text
queued -> planning -> discovering -> fetching -> extracting
-> comparing -> synthesising -> validating -> completed
                                         \-> partial / failed
```

Every transition writes a `run_event`. The UI shows these events with counts and errors so that the assessment panel can observe the backend pipeline.

## Steps

1. **Create run.** Store the original research question, limits, selected provider configuration name, and start time.
2. **Reuse known knowledge.** Query existing source snapshots and claims with full-text/keyword matching. This supports a reusable knowledge base, but never prevents fresh research.
3. **Plan.** Ask the LLM for a bounded set of sub-questions and search queries using a validated schema.
4. **Discover.** Search each query through the configured provider. Normalize URLs and remove duplicates.
5. **Select and fetch.** Take the best candidates within the source cap. Fetch permitted public pages, extract readable text, and store an immutable snapshot with a content hash and retrieval time.
6. **Extract.** Ask the LLM for concise, atomic claims. Each returned claim must cite an exact excerpt from its snapshot; unmatched excerpts are rejected.
7. **Classify and compare.** Group claims by topic. Compare only related pairs and classify each pair as supports, qualifies, contradicts, or unrelated. Store the rationale and conditions.
8. **Synthesise.** Generate a short report from stored claims and relationships. The model must return referenced claim IDs, not free-form citations.
9. **Validate.** Reject conclusions with no valid claim links. Mark a run `partial` if there is insufficient evidence or a recoverable provider/source failure.

## Run limits for the MVP

| Item | Limit |
| --- | --- |
| Search queries | 3 |
| Stored source snapshots | 5-8 |
| Text sent from a source at once | A bounded cleaned-text excerpt/chunk |
| Extracted claims | 8-15 |
| Claim comparisons | Only related topics; capped to prevent pair explosion |
| Conclusions | 3-5 |

## Failure behavior

No results are invented. If a source cannot be fetched, persist a visible failed source-attempt record and continue. If the provider is unavailable, persist the failure details. A retry creates a new immutable run for the same project, preserving the prior run rather than duplicating its stage outputs.
