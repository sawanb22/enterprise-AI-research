# 7. Evidence and Traceability

## Traceability contract

Every visible conclusion must be explainable through this navigable path:

```text
Conclusion
  -> linked claim(s)
  -> exact source excerpt
  -> immutable source snapshot
  -> source URL and retrieval metadata
```

The UI will expose this through a **View evidence** action on each conclusion. It displays linked claims, their classification/confidence, the exact quoted excerpt, source title, publisher, URL, and retrieval date.

## What counts as evidence

- A `Source` identifies where information came from.
- A `SourceSnapshot` records the material actually retrieved at a specific time.
- A `Claim` is a concise statement grounded in an exact excerpt from one snapshot.
- An `EvidenceAssessment` explains how two related claims interact.
- A `Conclusion` is a synthesis that links to claims; it is not evidence by itself.

## Relationship semantics

| Relationship | Meaning |
| --- | --- |
| Supports | The claims make compatible statements about the same topic. |
| Qualifies | One claim narrows, conditions, or limits the other. |
| Contradicts | The claims make materially incompatible statements under comparable scope/conditions. |
| Unrelated | The pair shares too little scope to compare. |

## Contradiction policy

The application does not declare a source false. It presents a model-generated evidence assessment with its stated conditions, source excerpts, and confidence. Differing time periods, metrics, populations, or data quality commonly mean **qualifies**, not **contradicts**.

## Source quality and limitations

Sources carry a simple visible quality tier: primary/official, academic/reputable research, established reporting, or other public web content. This tier helps the user assess evidence but does not decide truth automatically. Reports must include a limitations section for missing sources, failed fetches, thin evidence, and unresolved disagreement.

## Validation rules

1. Claims without source excerpts are not stored as usable evidence.
2. Conclusions without linked claims are not published.
3. Generated source citations are not trusted; IDs must resolve to persisted records.
4. A failed validation becomes a run event, not silent fallback prose.
