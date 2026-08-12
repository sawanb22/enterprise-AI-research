import { useEffect, useState } from "react";
import { ConnectionIndicator } from "./components/ConnectionIndicator";
import { EvidenceDrawer } from "./components/EvidenceDrawer";
import { PipelineCard } from "./components/PipelineCard";
import { QuestionForm } from "./components/QuestionForm";
import { ResearchTabs, TabKey } from "./components/ResearchTabs";
import { Sidebar } from "./components/Sidebar";
import { useResearchData } from "./hooks/useResearchData";
import { formatDateTime, pretty, sanitizeText } from "./utils/textUtils";

export function App() {
  const {
    projects,
    run,
    events,
    sources,
    claims,
    assessments,
    trace,
    loading,
    error,
    healthInfo,
    connectionStatus,
    lastUpdated,
    isRefreshing,
    manualRefresh,
    createProject,
    openProject,
    openRunById,
    openTrace,
    closeTrace,
    retry,
    completedStages,
    isActiveRun,
  } = useResearchData();

  const [activeTab, setActiveTab] = useState<TabKey>("conclusions");

  // When a new run is loaded or active run finishes, manage tab selection
  useEffect(() => {
    if (!run) return;
    if (isActiveRun) {
      // While actively running, let users see activity or keep their tab
      // If conclusions exist, they can still view conclusions
    } else {
      // Completed, partial, or failed run -> default to conclusions tab
      setActiveTab("conclusions");
    }
  }, [run?.id, isActiveRun]);

  return (
    <main className="shell">
      <Sidebar
        projects={projects}
        activeProjectId={run?.project_id}
        selectedRunId={run?.id}
        healthInfo={healthInfo}
        onSelectProject={openProject}
        onSelectRun={openRunById}
      />

      <section className="workspace" id="main-content">
        <header className="workspace-header">
          <div className="workspace-title-area">
            <p className="eyebrow">ENTERPRISE RESEARCH AGENT</p>
            <h1>Evidence before conclusions.</h1>
            <p className="subhead">Plan, source, compare, and trace every answer with auditable evidence.</p>
          </div>

          <div className="header-meta-actions">
            <ConnectionIndicator
              status={connectionStatus}
              lastUpdated={lastUpdated}
              isRefreshing={isRefreshing}
              onRefresh={manualRefresh}
            />
            {run && (
              <span
                className={`status ${run.status}`}
                role="status"
                aria-label={`Run status: ${run.status}`}
              >
                <span className={`dot-status ${run.status}`} aria-hidden="true" />
                {pretty(run.status)}
              </span>
            )}
          </div>
        </header>

        <QuestionForm onSubmit={createProject} loading={loading} />

        {error && (
          <div className="alert" role="alert">
            <strong>Attention:</strong> {sanitizeText(error)}
          </div>
        )}

        {!run && (
          <section className="empty-state" aria-label="Getting started">
            <div className="empty-state-graphic" aria-hidden="true">🔬</div>
            <h2>Start with a business or technical question</h2>
            <p>
              EvidenceLab will execute multi-angle discovery, retrieve authoritative snapshots,
              extract verbatim claims, compare cross-source agreements, and synthesize verified conclusions.
            </p>
          </section>
        )}

        {run && (
          <>
            <section className="run-context" aria-label="Active research question context">
              <div className="run-context-info">
                <p className="eyebrow">RESEARCH INQUIRY</p>
                <h2>{sanitizeText(run.question)}</h2>
                <p className="muted">
                  Provider: <b>{pretty(run.provider_name)}</b> · Model: <b>{run.model_name}</b> · Started{" "}
                  {formatDateTime(run.started_at)}
                </p>
              </div>

              <div className="metrics" role="group" aria-label="Research volume metrics">
                <div className="metric-pill">
                  <b>{run.source_count}</b>
                  <span>{run.source_count === 1 ? "source" : "sources"}</span>
                </div>
                <div className="metric-pill">
                  <b>{run.claim_count}</b>
                  <span>{run.claim_count === 1 ? "claim" : "claims"}</span>
                </div>
                <div className="metric-pill">
                  <b>{run.conclusion_count}</b>
                  <span>{run.conclusion_count === 1 ? "conclusion" : "conclusions"}</span>
                </div>
              </div>
            </section>

            {/* Pipeline card: summary mode on completed runs, or live mode on active runs */}
            {(isActiveRun || activeTab !== "activity") && (
              <PipelineCard
                run={run}
                events={events}
                completedStages={completedStages}
                onRetry={retry}
                onViewActivity={() => setActiveTab("activity")}
              />
            )}

            {/* Tabbed results-first view */}
            <ResearchTabs
              activeTab={activeTab}
              onSelectTab={setActiveTab}
              run={run}
              events={events}
              sources={sources}
              claims={claims}
              assessments={assessments}
              completedStages={completedStages}
              onViewEvidence={openTrace}
              onRetry={retry}
            />
          </>
        )}
      </section>

      {trace && (
        <EvidenceDrawer trace={trace} onClose={closeTrace} />
      )}
    </main>
  );
}

export default App;
