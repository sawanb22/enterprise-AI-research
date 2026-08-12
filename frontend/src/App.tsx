import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { api, Assessment, Claim, Project, RunDetail, RunEvent, Source, Trace } from "./api";

const stages = ["planning", "discovering", "fetching", "extracting", "comparing", "synthesising", "validating"];
const activeStatuses = new Set(["queued", "planning", "discovering", "fetching", "extracting", "comparing", "synthesising"]);

function pretty(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function time(value: string | null) {
  return value ? new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—";
}

function App() {
  const [question, setQuestion] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [run, setRun] = useState<RunDetail | null>(null);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [trace, setTrace] = useState<Trace | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [configured, setConfigured] = useState<Record<string, boolean> | null>(null);

  const refreshProjects = useCallback(async () => {
    try {
      setProjects(await api.projects());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load projects.");
    }
  }, []);

  const refreshRun = useCallback(async (runId: string) => {
    try {
      const [nextRun, nextEvents, nextSources, nextClaims, nextAssessments] = await Promise.all([
        api.run(runId), api.events(runId), api.sources(runId), api.claims(runId), api.assessments(runId),
      ]);
      setRun(nextRun);
      setEvents(nextEvents);
      setSources(nextSources);
      setClaims(nextClaims);
      setAssessments(nextAssessments);
      if (!activeStatuses.has(nextRun.status)) refreshProjects();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load research run.");
    }
  }, [refreshProjects]);

  useEffect(() => {
    refreshProjects();
    api.health().then((result) => setConfigured(result.providers_configured)).catch(() => setError("Backend is not reachable. Start FastAPI first."));
  }, [refreshProjects]);

  useEffect(() => {
    if (!run) return;
    refreshRun(run.id);
    if (!activeStatuses.has(run.status)) return;
    const timer = window.setInterval(() => refreshRun(run.id), 1800);
    return () => window.clearInterval(timer);
  }, [run?.id, run?.status, refreshRun]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const trimmed = question.trim();
    if (trimmed.length < 12) {
      setError("Enter a specific research question of at least 12 characters.");
      return;
    }
    setError("");
    setTrace(null);
    setLoading(true);
    try {
      const created = await api.createProject(trimmed);
      setQuestion("");
      await refreshRun(created.run_id);
      refreshProjects();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start research.");
    } finally {
      setLoading(false);
    }
  }

  async function openProject(project: Project) {
    if (!project.latest_run) return;
    setError("");
    setTrace(null);
    await refreshRun(project.latest_run.id);
  }

  async function openTrace(conclusionId: string) {
    try {
      setTrace(await api.trace(conclusionId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load evidence trace.");
    }
  }

  async function retry() {
    if (!run) return;
    try {
      const retryRun = await api.retry(run.id);
      setTrace(null);
      await refreshRun(retryRun.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not retry the research run.");
    }
  }

  const completedStages = useMemo(() => new Set(events.filter((event) => event.status === "complete").map((event) => event.stage)), [events]);

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">E</span><div><strong>EvidenceLab</strong><small>Enterprise Research Agent</small></div></div>
        <div className="provider-state">
          <span className={configured?.groq ? "dot ready" : "dot"} /> Groq {configured?.groq ? "ready" : "needs key"}
          <span className={configured?.tavily ? "dot ready" : "dot"} /> Tavily {configured?.tavily ? "ready" : "needs key"}
        </div>
        <div className="sidebar-heading">Research projects</div>
        <div className="project-list">
          {projects.map((project) => (
            <button className={`project ${run?.project_id === project.id ? "selected" : ""}`} key={project.id} onClick={() => openProject(project)}>
              <span>{project.title}</span><small>{project.latest_run?.status ?? "draft"}</small>
            </button>
          ))}
          {!projects.length && <p className="empty">Your completed research will persist here.</p>}
        </div>
      </aside>

      <section className="workspace">
        <header><div><p className="eyebrow">STRUCTURED RESEARCH</p><h1>Evidence before conclusions.</h1><p className="subhead">Plan, source, compare, and trace every answer.</p></div>{run && <span className={`status ${run.status}`}>{pretty(run.status)}</span>}</header>
        <form className="question-card" onSubmit={submit}>
          <label htmlFor="question">New research question</label>
          <div className="question-row"><textarea id="question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="How is AI transforming retail operations?" rows={2} /><button disabled={loading}>{loading ? "Starting…" : "Run research"}</button></div>
          <p>The workflow will use up to 3 queries and 6 public-source snapshots. Results remain evidence-linked.</p>
        </form>

        {error && <div className="alert"><strong>Attention:</strong> {error}</div>}

        {!run && <section className="empty-state"><h2>Start with a real question</h2><p>The dashboard will make each backend stage, source, claim, and conclusion inspectable.</p></section>}

        {run && <>
          <section className="run-context"><div><p className="eyebrow">ACTIVE QUESTION</p><h2>{run.question}</h2><p className="muted">Model: {run.model_name} · Started {time(run.started_at)}</p></div><div className="metrics"><span><b>{run.source_count}</b> sources</span><span><b>{run.claim_count}</b> claims</span><span><b>{run.conclusion_count}</b> conclusions</span></div></section>
          <section className="pipeline card"><div className="section-title"><div><p className="eyebrow">LIVE PIPELINE</p><h2>Research run</h2></div><span className="muted">{events.length} recorded events</span></div><div className="stage-row">{stages.map((stage) => <div className={`stage ${completedStages.has(stage) ? "done" : run.status === stage ? "current" : ""}`} key={stage}><i />{pretty(stage)}</div>)}</div><div className="events">{events.slice(-5).map((event, index) => <div className="event" key={`${event.occurred_at}-${index}`}><span className={`event-icon ${event.status}`} /> <span>{event.message}</span><time>{time(event.occurred_at)}</time></div>)}</div>{run.error_summary && <div className="run-error">{run.error_summary}</div>}{["failed", "partial"].includes(run.status) && <button className="secondary" onClick={retry}>Retry from saved progress</button>}</section>
          <section className="grid">
            <div className="card conclusions"><div className="section-title"><div><p className="eyebrow">SYNTHESIS</p><h2>Conclusions</h2></div><span className="muted">Citation gate enforced</span></div>{run.conclusions.length ? run.conclusions.map((conclusion) => <article className="conclusion" key={conclusion.id}><div><span className={`confidence ${conclusion.confidence}`}>{conclusion.confidence}</span><p>{conclusion.statement}</p>{conclusion.limitations && <small>Limitation: {conclusion.limitations}</small>}</div><button className="trace-button" onClick={() => openTrace(conclusion.id)}>View evidence <span>→</span></button></article>) : <p className="empty">Conclusions appear after validated source-grounded claims are stored.</p>}</div>
            <div className="card"><div className="section-title"><div><p className="eyebrow">KNOWLEDGE BASE</p><h2>Sources</h2></div><span className="muted">{sources.length} snapshots</span></div><div className="source-list">{sources.map((source) => <a className="source" href={source.canonical_url} key={source.id} target="_blank" rel="noreferrer"><span>{source.title || source.publisher || "Untitled source"}</span><small>{source.publisher} · {source.fetch_status}</small></a>)}{!sources.length && <p className="empty">Saved source snapshots will appear here.</p>}</div></div>
          </section>
          <section className="grid lower-grid"><div className="card"><div className="section-title"><div><p className="eyebrow">EXTRACTED INTELLIGENCE</p><h2>Claims</h2></div><span className="muted">{claims.length} source-grounded</span></div><div className="claim-list">{claims.map((claim) => <article className="claim" key={claim.id}><div><span className="tag">{claim.topic}</span><span className={`confidence ${claim.confidence}`}>{claim.confidence}</span></div><p>{claim.statement}</p><blockquote>“{claim.exact_excerpt}”</blockquote></article>)}{!claims.length && <p className="empty">Claims require exact source excerpts.</p>}</div></div><div className="card"><div className="section-title"><div><p className="eyebrow">EVIDENCE COMPARISON</p><h2>Relationships</h2></div><span className="muted">{assessments.length} assessments</span></div><div className="assessment-list">{assessments.map((assessment) => <article className="assessment" key={assessment.id}><span className={`relationship ${assessment.relationship}`}>{assessment.relationship}</span><p>{assessment.rationale}</p>{assessment.conditions && <small>Conditions: {assessment.conditions}</small>}</article>)}{!assessments.length && <p className="empty">Related claims will be compared when sources cover the same topic.</p>}</div></div></section>
        </>}
      </section>

      {trace && <aside className="trace-panel"><button className="close" onClick={() => setTrace(null)}>×</button><p className="eyebrow">TRACEABILITY</p><h2>Evidence chain</h2><p className="trace-conclusion">{trace.conclusion.statement}</p><div className="trace-path">Conclusion <span>↓</span> Claims <span>↓</span> Source snapshots</div>{trace.claims.map((claim) => <article className="trace-claim" key={claim.id}><span className="tag">{claim.topic}</span><p>{claim.statement}</p><blockquote>“{claim.exact_excerpt}”</blockquote><a href={claim.source.canonical_url} target="_blank" rel="noreferrer">{claim.source.title || claim.source.publisher || "Open original source"} ↗</a></article>)}{trace.assessments.length > 0 && <><h3>Related evidence</h3>{trace.assessments.map((assessment) => <p className="trace-assessment" key={assessment.id}><b>{pretty(assessment.relationship)}:</b> {assessment.rationale}</p>)}</>}</aside>}
    </main>
  );
}

export default App;
