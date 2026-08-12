import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import SessionLocal
from .models import (
    Claim,
    Conclusion,
    ConclusionClaim,
    EvidenceAssessment,
    PlanItem,
    ResearchProject,
    ResearchRun,
    RunEvent,
    Source,
    SourceSnapshot,
)
from .ai import BaseLLMProvider, BedrockProvider, OpenAICompatibleProvider, ProviderError, get_llm_provider
from .search import SearchResult, TavilyProvider


settings = get_settings()
VALID_CONFIDENCE = {"low", "medium", "high"}
VALID_CLASSIFICATIONS = {"opportunity", "impact", "risk", "limitation", "trend"}
VALID_RELATIONSHIPS = {"supports", "qualifies", "contradicts", "unrelated"}
TRACKING_QUERY_KEYS = {"fbclid", "gclid", "dclid", "mc_cid", "mc_eid", "_hsenc", "_hsmi"}


class PartialResearchError(RuntimeError):
    """The run made useful progress but cannot make an evidence-backed conclusion."""


def now() -> datetime:
    return datetime.now(timezone.utc)


def add_event(db: Session, run_id: str, stage: str, status: str, message: str, metadata: dict | None = None) -> None:
    db.add(RunEvent(run_id=run_id, stage=stage, status=status, message=message, metadata_json=json.dumps(metadata or {})))
    db.commit()


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    hostname = (parts.hostname or "").lower()
    try:
        port = parts.port
    except ValueError:
        port = None
    default_port = (parts.scheme.lower() == "https" and port == 443) or (parts.scheme.lower() == "http" and port == 80)
    netloc = hostname if not port or default_port else f"{hostname}:{port}"
    query = sorted(
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_QUERY_KEYS
    )
    return urlunsplit((parts.scheme.lower(), netloc, parts.path.rstrip("/") or "/", urlencode(query), ""))


def normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def project_title(question: str) -> str:
    return question[:77].rstrip() + ("..." if len(question) > 77 else "")


def create_project_and_run(db: Session, question: str, title: str | None) -> tuple[ResearchProject, ResearchRun]:
    project = ResearchProject(title=title or project_title(question), original_question=question)
    db.add(project)
    db.flush()
    run = ResearchRun(
        project_id=project.id,
        status="queued",
        provider_name=settings.effective_provider,
        model_name=settings.effective_model_name,
        limits_json=json.dumps(
            {
                "max_queries": settings.max_queries,
                "max_sources": settings.max_sources,
                "max_claims": settings.max_claims,
                "max_comparisons": settings.max_comparisons,
            }
        ),
    )
    db.add(run)
    db.commit()
    db.refresh(project)
    db.refresh(run)
    add_event(db, run.id, "queued", "complete", "Research run created.")
    return project, run


def _store_plan(db: Session, run_id: str, plan: dict[str, list[str]]) -> None:
    for position, text in enumerate(plan["sub_questions"]):
        db.add(PlanItem(run_id=run_id, item_type="sub_question", text=text, position=position))
    for position, text in enumerate(plan["search_queries"]):
        db.add(PlanItem(run_id=run_id, item_type="search_query", text=text, position=position))
    db.commit()


def _stored_plan(db: Session, run_id: str) -> dict[str, list[str]] | None:
    """Return a persisted plan in provider-ready form, if one already exists."""
    items = list(db.scalars(select(PlanItem).where(PlanItem.run_id == run_id).order_by(PlanItem.item_type, PlanItem.position)).all())
    if not items:
        return None
    plan = {"sub_questions": [], "search_queries": []}
    for item in items:
        if item.item_type == "sub_question":
            plan["sub_questions"].append(item.text)
        elif item.item_type == "search_query":
            plan["search_queries"].append(item.text)
    return plan if plan["search_queries"] else None


def _stage_is_complete(db: Session, run_id: str, stage: str) -> bool:
    return db.scalar(
        select(RunEvent.id)
        .where(RunEvent.run_id == run_id, RunEvent.stage == stage, RunEvent.status == "complete")
        .limit(1)
    ) is not None


def _get_or_create_source(db: Session, result: SearchResult) -> Source:
    url = canonicalize_url(result.url)
    source = db.scalar(select(Source).where(Source.canonical_url == url))
    if source:
        if not source.title and result.title:
            source.title = result.title
            db.commit()
        return source
    publisher = urlsplit(url).netloc.removeprefix("www.")
    source = Source(canonical_url=url, title=result.title, publisher=publisher)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def _store_snapshot(db: Session, run_id: str, source: Source, text: str) -> SourceSnapshot:
    cleaned = normalized_text(text)
    content_hash = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
    snapshot = db.scalar(
        select(SourceSnapshot).where(
            SourceSnapshot.run_id == run_id,
            SourceSnapshot.source_id == source.id,
            SourceSnapshot.content_hash == content_hash,
        )
    )
    if snapshot:
        return snapshot
    snapshot = SourceSnapshot(source_id=source.id, run_id=run_id, content_hash=content_hash, cleaned_text=cleaned)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def _store_failed_snapshot(db: Session, run_id: str, source: Source, error: str) -> SourceSnapshot:
    """Keep a visible source-attempt record even when its content cannot be retrieved."""
    content_hash = hashlib.sha256(f"failed:{error}".encode("utf-8")).hexdigest()
    snapshot = db.scalar(
        select(SourceSnapshot).where(
            SourceSnapshot.run_id == run_id,
            SourceSnapshot.source_id == source.id,
            SourceSnapshot.content_hash == content_hash,
        )
    )
    if snapshot:
        return snapshot
    snapshot = SourceSnapshot(
        source_id=source.id,
        run_id=run_id,
        content_hash=content_hash,
        cleaned_text="",
        fetch_status="failed",
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def _valid_excerpt(source_text: str, excerpt: str) -> tuple[str, int, int] | None:
    excerpt = excerpt.strip()
    if not 20 <= len(excerpt) <= 500:
        return None
    start = source_text.find(excerpt)
    if start >= 0:
        return excerpt, start, start + len(excerpt)

    # Fallback 1: Quote normalization (“” ‘’ -> "" '')
    def _norm_quotes(t: str) -> str:
        return t.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")

    norm_source = _norm_quotes(source_text)
    norm_excerpt = _norm_quotes(excerpt)
    start = norm_source.find(norm_excerpt)
    if start >= 0:
        return source_text[start : start + len(norm_excerpt)], start, start + len(norm_excerpt)

    # Fallback 2: Whitespace tolerance (matching across variable whitespace)
    words = [re.escape(_norm_quotes(w)) for w in norm_excerpt.split() if w]
    if len(words) >= 3:
        pattern = r"\s+".join(words)
        match = re.search(pattern, norm_source, re.IGNORECASE)
        if match:
            s, e = match.span()
            return source_text[s:e], s, e

    return None


def _store_claims(db: Session, run_id: str, snapshot: SourceSnapshot, drafts: list[dict], remaining: int) -> int:
    stored = 0
    for draft in drafts:
        if stored >= remaining:
            break
        topic = str(draft.get("topic", "")).strip()[:160]
        statement = str(draft.get("statement", "")).strip()
        classification = str(draft.get("classification", "")).strip().lower()
        confidence = str(draft.get("confidence", "")).strip().lower()
        excerpt_check = _valid_excerpt(snapshot.cleaned_text, str(draft.get("excerpt", "")))
        if not topic or not statement or classification not in VALID_CLASSIFICATIONS or confidence not in VALID_CONFIDENCE or not excerpt_check:
            continue
        excerpt, start, end = excerpt_check
        duplicate = db.scalar(
            select(Claim).where(Claim.run_id == run_id, Claim.snapshot_id == snapshot.id, Claim.statement == statement)
        )
        if duplicate:
            continue
        db.add(
            Claim(
                run_id=run_id,
                snapshot_id=snapshot.id,
                topic=topic,
                statement=statement,
                classification=classification,
                confidence=confidence,
                exact_excerpt=excerpt,
                excerpt_start=start,
                excerpt_end=end,
            )
        )
        stored += 1
    db.commit()
    return stored


def _select_comparison_pairs(claims: list[Claim], max_pairs: int) -> list[tuple[Claim, Claim]]:
    groups: dict[str, list[Claim]] = defaultdict(list)
    for claim in claims:
        groups[claim.topic.lower().strip()].append(claim)
    pairs: list[tuple[Claim, Claim]] = []
    for group in groups.values():
        for index, left in enumerate(group):
            for right in group[index + 1 :]:
                if left.snapshot_id != right.snapshot_id:
                    pairs.append((left, right))
                    if len(pairs) >= max_pairs:
                        return pairs
    if len(pairs) < max_pairs:
        for index, left in enumerate(claims):
            for right in claims[index + 1 :]:
                if left.snapshot_id != right.snapshot_id and (left, right) not in pairs and (right, left) not in pairs:
                    pairs.append((left, right))
                    if len(pairs) >= max_pairs:
                        return pairs
    return pairs


def _claim_payload(claim: Claim) -> dict[str, str]:
    return {
        "id": claim.id,
        "topic": claim.topic,
        "statement": claim.statement,
        "classification": claim.classification,
        "confidence": claim.confidence,
        "excerpt": claim.exact_excerpt,
    }


def create_retry_run(db: Session, previous_run: ResearchRun) -> ResearchRun:
    """Create an immutable retry that starts from the prior run's persisted progress."""
    retry = ResearchRun(
        project_id=previous_run.project_id,
        status="queued",
        provider_name=previous_run.provider_name,
        model_name=previous_run.model_name,
        limits_json=previous_run.limits_json,
    )
    db.add(retry)
    db.commit()
    db.refresh(retry)

    # Copy immutable work products into the new run.  The retry never changes the
    # failed run, while subsequent stages can use the same saved evidence without
    # spending more provider requests to recreate it.
    prior_plan = list(db.scalars(select(PlanItem).where(PlanItem.run_id == previous_run.id).order_by(PlanItem.position)).all())
    for item in prior_plan:
        db.add(PlanItem(run_id=retry.id, item_type=item.item_type, text=item.text, position=item.position))

    snapshot_ids: dict[str, str] = {}
    prior_snapshots = list(db.scalars(select(SourceSnapshot).where(SourceSnapshot.run_id == previous_run.id)).all())
    for snapshot in prior_snapshots:
        copied = SourceSnapshot(
            source_id=snapshot.source_id,
            run_id=retry.id,
            content_hash=snapshot.content_hash,
            cleaned_text=snapshot.cleaned_text,
            fetch_status=snapshot.fetch_status,
            http_status=snapshot.http_status,
        )
        db.add(copied)
        db.flush()
        snapshot_ids[snapshot.id] = copied.id

    claim_ids: dict[str, str] = {}
    prior_claims = list(db.scalars(select(Claim).where(Claim.run_id == previous_run.id)).all())
    for claim in prior_claims:
        copied_snapshot_id = snapshot_ids.get(claim.snapshot_id)
        if not copied_snapshot_id:
            continue
        copied = Claim(
            run_id=retry.id,
            snapshot_id=copied_snapshot_id,
            topic=claim.topic,
            statement=claim.statement,
            classification=claim.classification,
            confidence=claim.confidence,
            exact_excerpt=claim.exact_excerpt,
            excerpt_start=claim.excerpt_start,
            excerpt_end=claim.excerpt_end,
        )
        db.add(copied)
        db.flush()
        claim_ids[claim.id] = copied.id

    if claim_ids:
        prior_assessments = list(
            db.scalars(
                select(EvidenceAssessment)
                .join(Claim, EvidenceAssessment.left_claim_id == Claim.id)
                .where(Claim.run_id == previous_run.id)
            ).all()
        )
        for assessment in prior_assessments:
            left_claim_id = claim_ids.get(assessment.left_claim_id)
            right_claim_id = claim_ids.get(assessment.right_claim_id)
            if not left_claim_id or not right_claim_id:
                continue
            db.add(
                EvidenceAssessment(
                    left_claim_id=left_claim_id,
                    right_claim_id=right_claim_id,
                    relationship=assessment.relationship,
                    rationale=assessment.rationale,
                    conditions=assessment.conditions,
                    confidence=assessment.confidence,
                )
            )
    db.commit()

    completed = {event.stage for event in db.scalars(select(RunEvent).where(RunEvent.run_id == previous_run.id, RunEvent.status == "complete")).all()}
    # A copied plan is usable even if a process stopped immediately after it was
    # persisted, before it could emit its completion event.
    if prior_plan:
        completed.add("planning")
    # Source snapshots prove the upstream discovery work that produced them.
    if "fetching" in completed:
        completed.add("discovering")

    stage_order = ["planning", "discovering", "fetching", "extracting", "comparing"]
    next_stage = "planning"
    for stage in stage_order:
        if stage not in completed:
            next_stage = stage
            break
    else:
        next_stage = "synthesising"

    add_event(
        db,
        retry.id,
        "queued",
        "complete",
        f"Retry created from prior run {previous_run.id}; it will resume at {next_stage}.",
        {"previous_run_id": previous_run.id, "resume_stage": next_stage},
    )
    for stage in stage_order:
        if stage not in completed:
            continue
        add_event(
            db,
            retry.id,
            stage,
            "complete",
            f"Reused persisted {stage} output from prior run.",
            {"previous_run_id": previous_run.id},
        )
    return retry


def run_research(run_id: str) -> None:
    """Persisted, sequential MVP workflow. Exceptions are always recorded on the run."""
    db = SessionLocal()
    try:
        run = db.get(ResearchRun, run_id)
        if not run or run.status not in {"queued", "failed", "partial"}:
            return
        project = db.get(ResearchProject, run.project_id)
        if not project:
            return
        run.started_at = now()
        run.error_summary = None
        db.commit()

        llm = BedrockProvider(settings) if settings.effective_provider == "bedrock" else OpenAICompatibleProvider(settings)
        search = TavilyProvider(settings)
        fetch_errors: list[str] = []
        plan = _stored_plan(db, run_id)
        if not plan:
            run.status = "planning"
            db.commit()
            add_event(db, run_id, "planning", "started", "Generating research plan.")
            plan = llm.plan(project.original_question, settings.max_queries)
            _store_plan(db, run_id, plan)
            add_event(db, run_id, "planning", "complete", "Stored research plan.", {"queries": len(plan["search_queries"])})

        # Fetching is the first stage whose output is fully persisted.  A retry
        # with completed snapshots skips discovery/fetching entirely; a retry
        # interrupted mid-fetch reuses fetched snapshots and only fetches what is
        # still missing from a fresh discovery result.
        fetching_complete = _stage_is_complete(db, run_id, "fetching")
        if not fetching_complete:
            run.status = "discovering"
            db.commit()
            add_event(db, run_id, "discovering", "started", "Searching permitted public sources.")
            candidates: dict[str, SearchResult] = {}
            search_errors: list[str] = []
            for query in plan["search_queries"]:
                try:
                    for result in search.search(query, max_results=3):
                        candidates.setdefault(canonicalize_url(result.url), result)
                except ProviderError as exc:
                    search_errors.append(str(exc))
            selected = list(candidates.values())[: settings.max_sources]
            if not selected:
                raise ProviderError("No usable sources were discovered. " + (search_errors[0] if search_errors else ""))
            add_event(
                db,
                run_id,
                "discovering",
                "complete",
                "Selected unique sources.",
                {"selected_sources": len(selected), "source_urls": [canonicalize_url(item.url) for item in selected]},
            )

            run.status = "fetching"
            db.commit()
            add_event(db, run_id, "fetching", "started", "Fetching and snapshotting source content.")
            for candidate in selected:
                source = _get_or_create_source(db, candidate)
                existing = db.scalar(
                    select(SourceSnapshot).where(
                        SourceSnapshot.run_id == run_id,
                        SourceSnapshot.source_id == source.id,
                        SourceSnapshot.fetch_status == "fetched",
                    )
                )
                if existing:
                    continue
                try:
                    _store_snapshot(db, run_id, source, search.extract(source.canonical_url))
                except ProviderError as exc:
                    error = f"{candidate.url}: {exc}"
                    fetch_errors.append(error)
                    _store_failed_snapshot(db, run_id, source, str(exc))
                    add_event(db, run_id, "fetching", "failed", "Source fetch failed.", {"url": source.canonical_url, "error": str(exc)[:300]})
            snapshots = list(
                db.scalars(
                    select(SourceSnapshot).where(SourceSnapshot.run_id == run_id, SourceSnapshot.fetch_status == "fetched")
                ).all()
            )
            if not snapshots:
                raise ProviderError("No source content could be fetched. " + (fetch_errors[0] if fetch_errors else ""))
            add_event(db, run_id, "fetching", "complete", "Stored source snapshots.", {"snapshots": len(snapshots), "failed": len(fetch_errors)})
        else:
            snapshots = list(
                db.scalars(
                    select(SourceSnapshot).where(SourceSnapshot.run_id == run_id, SourceSnapshot.fetch_status == "fetched")
                ).all()
            )

        extracting_complete = _stage_is_complete(db, run_id, "extracting")
        if not extracting_complete:
            run.status = "extracting"
            db.commit()
            add_event(db, run_id, "extracting", "started", "Extracting source-grounded claims.")
            total_claims = db.scalar(select(func.count()).select_from(Claim).where(Claim.run_id == run_id)) or 0
            for snapshot in snapshots:
                if total_claims >= settings.max_claims:
                    break
                already_extracted = db.scalar(select(Claim.id).where(Claim.run_id == run_id, Claim.snapshot_id == snapshot.id).limit(1))
                if already_extracted:
                    continue
                source = db.get(Source, snapshot.source_id)
                try:
                    drafts = llm.extract_claims(snapshot.cleaned_text[:12000], source.canonical_url, min(3, settings.max_claims - total_claims))
                    total_claims += _store_claims(db, run_id, snapshot, drafts, settings.max_claims - total_claims)
                except ProviderError as exc:
                    fetch_errors.append(f"claim extraction {source.canonical_url}: {exc}")
        claims = list(db.scalars(select(Claim).where(Claim.run_id == run_id)).all())
        if not claims:
            raise PartialResearchError("No valid, source-grounded claims were extracted from the retrieved sources.")
        if not extracting_complete:
            add_event(db, run_id, "extracting", "complete", "Stored source-grounded claims.", {"claims": len(claims)})

        if not _stage_is_complete(db, run_id, "comparing"):
            run.status = "comparing"
            db.commit()
            add_event(db, run_id, "comparing", "started", "Comparing related claims.")
            stored_assessments = 0
            existing_pairs = {
                (item.left_claim_id, item.right_claim_id)
                for item in db.scalars(
                    select(EvidenceAssessment)
                    .join(Claim, EvidenceAssessment.left_claim_id == Claim.id)
                    .where(Claim.run_id == run_id)
                ).all()
            }
            for left, right in _select_comparison_pairs(claims, settings.max_comparisons):
                if (left.id, right.id) in existing_pairs or (right.id, left.id) in existing_pairs:
                    continue
                try:
                    assessment = llm.compare_claims(_claim_payload(left), _claim_payload(right))
                    relationship = str(assessment.get("relationship", "")).lower()
                    confidence = str(assessment.get("confidence", "")).lower()
                    if relationship not in VALID_RELATIONSHIPS or confidence not in VALID_CONFIDENCE:
                        continue
                    db.add(
                        EvidenceAssessment(
                            left_claim_id=left.id,
                            right_claim_id=right.id,
                            relationship=relationship,
                            rationale=str(assessment.get("rationale", "")).strip()[:2000],
                            conditions=str(assessment.get("conditions", "")).strip()[:1000],
                            confidence=confidence,
                        )
                    )
                    db.commit()
                    stored_assessments += 1
                except ProviderError as exc:
                    fetch_errors.append(f"claim comparison: {exc}")
            add_event(db, run_id, "comparing", "complete", "Stored evidence assessments.", {"assessments": stored_assessments})

        run.status = "synthesising"
        db.commit()
        add_event(db, run_id, "synthesising", "started", "Generating evidence-bounded conclusions.")
        assessments = list(db.scalars(select(EvidenceAssessment).join(Claim, EvidenceAssessment.left_claim_id == Claim.id).where(Claim.run_id == run_id)).all())
        assessment_payloads = [
            {
                "relationship": item.relationship,
                "rationale": item.rationale,
                "conditions": item.conditions,
                "left_claim_id": item.left_claim_id,
                "right_claim_id": item.right_claim_id,
            }
            for item in assessments
        ]
        conclusion_drafts = llm.synthesise(project.original_question, [_claim_payload(item) for item in claims], assessment_payloads)
        known_claims = {claim.id: claim for claim in claims}
        stored_conclusions = 0
        for draft in conclusion_drafts[:5]:
            statement = str(draft.get("statement", "")).strip()
            confidence = str(draft.get("confidence", "")).lower()
            claim_ids = [claim_id for claim_id in draft.get("claim_ids", []) if claim_id in known_claims]
            if not statement or confidence not in VALID_CONFIDENCE or not claim_ids:
                continue
            conclusion = Conclusion(
                run_id=run_id,
                statement=statement,
                confidence=confidence,
                reasoning=str(draft.get("reasoning", "")).strip()[:3000],
                limitations=str(draft.get("limitations", "")).strip()[:2000],
            )
            db.add(conclusion)
            db.flush()
            for claim_id in dict.fromkeys(claim_ids):
                db.add(ConclusionClaim(conclusion_id=conclusion.id, claim_id=claim_id, role="supports"))
            db.commit()
            stored_conclusions += 1
        if not stored_conclusions:
            raise PartialResearchError("Synthesis returned no conclusions with valid stored claim references.")

        orphaned_conclusions = db.scalar(
            select(func.count())
            .select_from(Conclusion)
            .outerjoin(ConclusionClaim, ConclusionClaim.conclusion_id == Conclusion.id)
            .where(Conclusion.run_id == run_id, ConclusionClaim.conclusion_id.is_(None))
        ) or 0
        if orphaned_conclusions:
            raise PartialResearchError("Traceability validation found a conclusion without linked evidence.")

        if getattr(llm, "repair_count", 0):
            add_event(db, run_id, "ai_validation", "complete", "Repaired invalid structured AI output.", {"repairs": llm.repair_count})
        run.status = "partial" if fetch_errors else "completed"
        run.completed_at = now()
        run.error_summary = "; ".join(fetch_errors[:3]) if fetch_errors else None
        db.commit()
        add_event(db, run_id, "validating", "complete", "Traceability validation passed.", {"conclusions": stored_conclusions, "status": run.status})
    except PartialResearchError as exc:
        run = db.get(ResearchRun, run_id)
        if run:
            run.status = "partial"
            run.completed_at = now()
            run.error_summary = str(exc)[:2000]
            db.commit()
            add_event(db, run_id, "validating", "partial", "Research completed without sufficient validated evidence.", {"error": str(exc)[:500]})
    except Exception as exc:  # recorded as state rather than exposing a background exception
        run = db.get(ResearchRun, run_id)
        if run:
            run.status = "failed"
            run.completed_at = now()
            run.error_summary = str(exc)[:2000]
            db.commit()
            add_event(db, run_id, "failed", "failed", "Research run failed.", {"error": str(exc)[:500]})
    finally:
        db.close()


def get_run_counts(db: Session, run_id: str) -> tuple[int, int, int]:
    source_count = db.scalar(select(func.count()).select_from(SourceSnapshot).where(SourceSnapshot.run_id == run_id)) or 0
    claim_count = db.scalar(select(func.count()).select_from(Claim).where(Claim.run_id == run_id)) or 0
    conclusion_count = db.scalar(select(func.count()).select_from(Conclusion).where(Conclusion.run_id == run_id)) or 0
    return int(source_count), int(claim_count), int(conclusion_count)
