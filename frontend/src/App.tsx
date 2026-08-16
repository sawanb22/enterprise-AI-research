import { useEffect, useState } from "react";
import { CitationDrawer } from "./components/CitationDrawer";
import { ConnectionIndicator } from "./components/ConnectionIndicator";
import { EvidenceDrawer } from "./components/EvidenceDrawer";
import { PipelineCard } from "./components/PipelineCard";
import { QuestionForm, ResearchMode } from "./components/QuestionForm";
import { RAGWorkspaceTabs } from "./components/RAGWorkspaceTabs";
import { ResearchTabs, TabKey } from "./components/ResearchTabs";
import { Sidebar } from "./components/Sidebar";
import { useRAGData } from "./hooks/useRAGData";
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
    setError,
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
    refreshProjects,
  } = useResearchData();

  const [mode, setMode] = useState<ResearchMode>("web");
  const [activeTab, setActiveTab] = useState<TabKey>("conclusions");

  const activeProjectId = run?.project_id || (projects.length > 0 ? projects[0].id : undefined);

  const {
    documents,
    totalPages,
    maxPagesLimit,
    remainingPages,
    docsLoading,
    report,
    setReport,
    pastReports,
    ragLoading,
    activeTab: ragActiveTab,
    setActiveTab: setRAGActiveTab,
    activeCitation,
    activeCitationIndex,
    totalCitations,
    uploadDocument,
    deleteDocument,
    refreshDocuments,
    executeRAG,
    openCitation,
    closeCitation,
    nextCitation,
    prevCitation,
    hasNextCitation,
    hasPrevCitation,
  } = useRAGData(activeProjectId);

  // When a run is loaded or active run finishes in Web mode, manage tab selection
  useEffect(() => {
    if (!run) return;
    if (!isActiveRun) {
      setActiveTab("conclusions");
    }
  }, [run?.id, isActiveRun]);

  const handleInquirySubmit = async (finalQuestion: string) => {
    if (mode === "web") {
      await createProject(finalQuestion);
    } else {
      // Document RAG mode
      if (!activeProjectId) {
        // Automatically initialize project first
        const created = await createProject(finalQuestion);
        await executeRAG(finalQuestion);
        await refreshProjects();
      } else {
        await executeRAG(finalQuestion);
      }
    }
  };

  return (
    <main className="shell">
      <Sidebar
        projects={projects}
        activeProjectId={activeProjectId}
        selectedRunId={run?.id}
        healthInfo={healthInfo}
        onSelectProject={(proj) => {
          openProject(proj);
          if (mode === "rag") {
            setRAGActiveTab("vault");
          }
        }}
        onSelectRun={openRunById}
      />

      <section className="workspace" id="main-content">
        <header className="workspace-header">
          <div className="workspace-title-area">
            <p className="eyebrow">ENTERPRISE RESEARCH LAB</p>
            <h1>Evidence before conclusions.</h1>
            <p className="subhead">
              Plan, source, compare, and trace every answer with auditable provenance.
            </p>
          </div>

          <div className="header-meta-actions">
            <ConnectionIndicator
              status={connectionStatus}
              lastUpdated={lastUpdated}
              isRefreshing={isRefreshing}
              onRefresh={manualRefresh}
            />
            {mode === "web" && run && (
              <span
                className={`status ${run.status}`}
                role="status"
                aria-label={`Run status: ${run.status}`}
              >
                <span className={`dot-status ${run.status}`} aria-hidden="true" />
                {pretty(run.status)}
              </span>
            )}
            {mode === "rag" && (
              <span className="status rag-ready" role="status" aria-label="RAG Engine Active">
                <span className="dot-status ready" aria-hidden="true" />
                Document RAG ({documents.filter((d) => d.status === "ready").length} indexed)
              </span>
            )}
          </div>
        </header>

        <QuestionForm
          mode={mode}
          onModeChange={(newMode) => {
            setMode(newMode);
            setError("");
          }}
          onSubmit={handleInquirySubmit}
          loading={mode === "web" ? loading : ragLoading}
          hasDocuments={documents.length > 0}
        />

        {error && (
          <div className="alert" role="alert">
            <strong>Attention:</strong> {sanitizeText(error)}
          </div>
        )}

        {/* --- MODE 1: WEB INTELLIGENCE VIEW --- */}
        {mode === "web" && (
          <>
            {!run && (
              <section className="empty-state" aria-label="Getting started">
                <div className="empty-state-graphic" aria-hidden="true">🔬</div>
                <h2>Start with a business or technical inquiry</h2>
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

                {/* Pipeline Card */}
                {(isActiveRun || activeTab !== "activity") && (
                  <PipelineCard
                    run={run}
                    events={events}
                    completedStages={completedStages}
                    onRetry={retry}
                    onViewActivity={() => setActiveTab("activity")}
                  />
                )}

                {/* Tabbed Results-First View */}
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
          </>
        )}

        {/* --- MODE 2: ENTERPRISE DOCUMENT RAG VIEW --- */}
        {mode === "rag" && (
          <RAGWorkspaceTabs
            activeTab={ragActiveTab}
            onSelectTab={setRAGActiveTab}
            report={report}
            pastReports={pastReports}
            documents={documents}
            totalPages={totalPages}
            maxPagesLimit={maxPagesLimit}
            remainingPages={remainingPages}
            docsLoading={docsLoading}
            onUploadDoc={uploadDocument}
            onDeleteDoc={deleteDocument}
            onRefreshDocs={refreshDocuments}
            onSelectPastReport={setReport}
            onOpenCitation={openCitation}
          />
        )}
      </section>

      {/* Slide-over Drawers */}
      {trace && (
        <EvidenceDrawer trace={trace} onClose={closeTrace} />
      )}

      {activeCitation && (
        <CitationDrawer
          citation={activeCitation}
          onClose={closeCitation}
          onNext={nextCitation}
          onPrev={prevCitation}
          hasNext={hasNextCitation}
          hasPrev={hasPrevCitation}
          citationIndex={activeCitationIndex}
          totalCitations={totalCitations}
        />
      )}
    </main>
  );
}

export default App;
