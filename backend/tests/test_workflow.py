from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app import services
from app.database import Base
from app.models import Claim, Conclusion, ConclusionClaim, EvidenceAssessment, ResearchRun, SourceSnapshot
from app.search import SearchResult


class FakeLLM:
    def __init__(self, _settings):
        pass

    def plan(self, _question, _max_queries):
        return {
            "sub_questions": ["What operational benefits are reported?"],
            "search_queries": ["AI retail demand forecast research", "AI retail forecast limitations research"],
        }

    def extract_claims(self, source_text, _url, _max_claims):
        if "historical sales data is reliable" in source_text:
            excerpt = "AI improves demand forecasts when historical sales data is reliable."
            statement = "AI can improve demand forecasting when reliable historical data is available."
        else:
            excerpt = "Poor data quality can limit the benefit of forecasting systems."
            statement = "Poor data quality can limit the benefit of AI forecasting systems."
        return [{"topic": "demand forecasting", "statement": statement, "classification": "impact", "confidence": "medium", "excerpt": excerpt}]

    def compare_claims(self, _left, _right):
        return {"relationship": "qualifies", "rationale": "The second claim identifies a condition that limits the first claim.", "conditions": "Historical data quality", "confidence": "high"}

    def synthesise(self, _question, claims, _assessments):
        return [{"statement": "AI forecasting can help retail operations when the underlying historical data is reliable.", "confidence": "medium", "claim_ids": [claim["id"] for claim in claims], "limitations": "The evidence is limited to the selected public sources."}]


class FakeSearch:
    def __init__(self, _settings):
        pass

    def search(self, query, max_results=3):
        if "limitations" in query:
            return [SearchResult(url="https://example.com/limitations", title="Forecasting limitations", snippet="")]
        return [SearchResult(url="https://example.com/benefits", title="Forecasting benefits", snippet="")]

    def extract(self, url):
        if "limitations" in url:
            return "Poor data quality can limit the benefit of forecasting systems. " * 8
        return "AI improves demand forecasts when historical sales data is reliable. " * 8


class PartiallyFailingSearch(FakeSearch):
    def extract(self, url):
        if "limitations" in url:
            raise services.ProviderError("Simulated source fetch failure")
        return super().extract(url)


class EmptyClaimLLM(FakeLLM):
    def extract_claims(self, _source_text, _url, _max_claims):
        return []


class RateLimitedSynthesisLLM(FakeLLM):
    allow_synthesis = False
    plan_calls = 0
    extract_calls = 0
    compare_calls = 0
    synthesise_calls = 0

    def plan(self, *args):
        type(self).plan_calls += 1
        return super().plan(*args)

    def extract_claims(self, *args):
        type(self).extract_calls += 1
        return super().extract_claims(*args)

    def compare_claims(self, *args):
        type(self).compare_calls += 1
        return super().compare_claims(*args)

    def synthesise(self, *args):
        type(self).synthesise_calls += 1
        if not type(self).allow_synthesis:
            raise services.ProviderError("Bedrock request failed (429): rate limit exceeded")
        return super().synthesise(*args)


def test_full_workflow_persists_traceable_conclusion(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'workflow.db'}")
    Base.metadata.create_all(engine)
    local_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(services, "SessionLocal", local_session)
    monkeypatch.setattr(services, "BedrockProvider", FakeLLM)
    monkeypatch.setattr(services, "OpenAICompatibleProvider", FakeLLM)
    monkeypatch.setattr(services, "TavilyProvider", FakeSearch)

    db = local_session()
    _, run = services.create_project_and_run(db, "How is AI transforming retail operations?", "Retail AI")
    run_id = run.id
    db.close()
    services.run_research(run_id)

    db = local_session()
    stored_run = db.get(ResearchRun, run_id)
    claims = list(db.scalars(select(Claim).where(Claim.run_id == run_id)).all())
    conclusion = db.scalar(select(Conclusion).where(Conclusion.run_id == run_id))
    link = db.scalar(select(ConclusionClaim).where(ConclusionClaim.conclusion_id == conclusion.id))
    snapshots = list(db.scalars(select(SourceSnapshot).where(SourceSnapshot.run_id == run_id)).all())
    assert stored_run.status == "completed"
    assert len(snapshots) == 2
    assert len(claims) == 2
    assert conclusion is not None
    assert link is not None and link.claim_id in {claim.id for claim in claims}
    db.close()


def _run_with_fakes(tmp_path, monkeypatch, llm_type=FakeLLM, search_type=FakeSearch):
    engine = create_engine(f"sqlite:///{tmp_path / 'edge.db'}")
    Base.metadata.create_all(engine)
    local_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(services, "SessionLocal", local_session)
    monkeypatch.setattr(services, "BedrockProvider", llm_type)
    monkeypatch.setattr(services, "OpenAICompatibleProvider", llm_type)
    monkeypatch.setattr(services, "TavilyProvider", search_type)
    db = local_session()
    _, run = services.create_project_and_run(db, "How is AI transforming retail operations?", "Retail AI")
    run_id = run.id
    db.close()
    services.run_research(run_id)
    return local_session, run_id


def test_failed_source_is_persisted_and_run_is_partial(tmp_path, monkeypatch):
    local_session, run_id = _run_with_fakes(tmp_path, monkeypatch, search_type=PartiallyFailingSearch)
    db = local_session()
    run = db.get(ResearchRun, run_id)
    snapshots = list(db.scalars(select(SourceSnapshot).where(SourceSnapshot.run_id == run_id)).all())
    assert run.status == "partial"
    assert any(snapshot.fetch_status == "failed" for snapshot in snapshots)
    db.close()


def test_zero_valid_claims_is_partial_not_failed(tmp_path, monkeypatch):
    local_session, run_id = _run_with_fakes(tmp_path, monkeypatch, llm_type=EmptyClaimLLM)
    db = local_session()
    run = db.get(ResearchRun, run_id)
    assert run.status == "partial"
    assert "No valid" in run.error_summary
    db.close()


def test_retry_resumes_at_synthesis_and_reuses_persisted_evidence(tmp_path, monkeypatch):
    RateLimitedSynthesisLLM.allow_synthesis = False
    RateLimitedSynthesisLLM.plan_calls = 0
    RateLimitedSynthesisLLM.extract_calls = 0
    RateLimitedSynthesisLLM.compare_calls = 0
    RateLimitedSynthesisLLM.synthesise_calls = 0
    local_session, run_id = _run_with_fakes(tmp_path, monkeypatch, llm_type=RateLimitedSynthesisLLM)

    db = local_session()
    original = db.get(ResearchRun, run_id)
    original_source_count = len(list(db.scalars(select(SourceSnapshot).where(SourceSnapshot.run_id == run_id)).all()))
    original_claim_count = len(list(db.scalars(select(Claim).where(Claim.run_id == run_id)).all()))
    original_assessment_count = len(list(db.scalars(select(EvidenceAssessment).join(Claim, EvidenceAssessment.left_claim_id == Claim.id).where(Claim.run_id == run_id)).all()))
    assert original.status == "failed"
    assert original_source_count == 2
    assert original_claim_count == 2
    assert original_assessment_count == 1

    retry = services.create_retry_run(db, original)
    retry_id = retry.id
    db.close()

    db = local_session()
    assert len(list(db.scalars(select(SourceSnapshot).where(SourceSnapshot.run_id == retry_id)).all())) == original_source_count
    assert len(list(db.scalars(select(Claim).where(Claim.run_id == retry_id)).all())) == original_claim_count
    assert len(list(db.scalars(select(EvidenceAssessment).join(Claim, EvidenceAssessment.left_claim_id == Claim.id).where(Claim.run_id == retry_id)).all())) == original_assessment_count
    db.close()

    before_retry_calls = (RateLimitedSynthesisLLM.plan_calls, RateLimitedSynthesisLLM.extract_calls, RateLimitedSynthesisLLM.compare_calls)
    RateLimitedSynthesisLLM.allow_synthesis = True
    services.run_research(retry_id)

    db = local_session()
    resumed = db.get(ResearchRun, retry_id)
    assert resumed.status == "completed"
    assert (RateLimitedSynthesisLLM.plan_calls, RateLimitedSynthesisLLM.extract_calls, RateLimitedSynthesisLLM.compare_calls) == before_retry_calls
    assert RateLimitedSynthesisLLM.synthesise_calls == 2
    assert db.scalar(select(Conclusion).where(Conclusion.run_id == retry_id)) is not None
    db.close()
