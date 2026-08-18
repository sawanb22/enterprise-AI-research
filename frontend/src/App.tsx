import { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import { AuthModal, AuthProvider, QuotaExceededModal, useAuth } from "./auth";
import { CitationDrawer } from "./components/CitationDrawer";
import { CleanWebReportView } from "./components/CleanWebReportView";
import { ConnectionIndicator } from "./components/ConnectionIndicator";
import { EvidenceDrawer } from "./components/EvidenceDrawer";
import { PipelineCard } from "./components/PipelineCard";
import { QuestionForm, ResearchMode } from "./components/QuestionForm";
import { RAGWorkspaceTabs } from "./components/RAGWorkspaceTabs";
import { ResearchTabs, TabKey } from "./components/ResearchTabs";
import { Sidebar } from "./components/Sidebar";
import { StarfieldBackground } from "./components/StarfieldBackground";
import { WebReportToolbar } from "./components/WebReportToolbar";
import { useRAGData } from "./hooks/useRAGData";
import { useResearchData } from "./hooks/useResearchData";
import { durationText, formatDateTime, pretty, sanitizeText } from "./utils/textUtils";
import { SecureWorkspaceCache } from "./utils/secureStorage";

function MainWorkspace() {
  const {
    projects,
    setProjects,
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
    refreshProjects,
    hydrateWebProject,
    refreshRun,
    createProject,
    openProject,
    openRunById,
    openTrace,
    closeTrace,
    retry,
    completedStages,
    isActiveRun,
  } = useResearchData();

  const { user, quota, openAuthModal, openQuotaModal, refreshQuota } = useAuth();

  const [mode, setMode] = useState<ResearchMode>(() => {
    return (sessionStorage.getItem("el_active_mode") as ResearchMode) || "web";
  });
  const [activeTab, setActiveTab] = useState<TabKey>("conclusions");
  const [webReportMode, setWebReportMode] = useState<"clean" | "tabs">("clean");
  const [selectedRAGVaultId, setSelectedRAGVaultId] = useState<string | undefined>(() => {
    return sessionStorage.getItem("el_active_rag_vault_id") || undefined;
  });
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  useEffect(() => {
    sessionStorage.setItem("el_active_mode", mode);
  }, [mode]);

  useEffect(() => {
    if (selectedRAGVaultId) {
      sessionStorage.setItem("el_active_rag_vault_id", selectedRAGVaultId);
    }
  }, [selectedRAGVaultId]);

  const activeWebProjectId = run?.project_id || (projects.length > 0 ? projects[0].id : undefined);

  const {
    documents,
    totalPages,
    maxPagesLimit,
    remainingPages,
    docsLoading,
    report,
    setReport,
    pastReports,
    openReportById,
    ragVaults,
    setRagVaults,
    refreshVaults,
    hydrateVaultData,
    ragLoading,
    activeTab: ragActiveTab,
    setActiveTab: setRAGActiveTab,
    activeCitation,
    activeCitationIndex,
    totalCitations,
    uploadDocument,
    replaceDocument,
    deleteDocument,
    refreshDocuments,
    executeRAG,
    openCitation,
    closeCitation,
    nextCitation,
    prevCitation,
    hasNextCitation,
    hasPrevCitation,
  } = useRAGData(
    selectedRAGVaultId,
    async (title: string): Promise<string> => {
      const created = await api.createRAGVault(title);
      setSelectedRAGVaultId(created.project_id);
      await refreshVaults();
      return created.project_id;
    }
  );

  const activeRAGVaultId = selectedRAGVaultId || (ragVaults.length > 0 ? ragVaults[0].project_id : undefined);

  // Unified fast workspace bootstrap with Instant SWR Cache Hydration (0ms reload)
  useEffect(() => {
    let mounted = true;

    // 1. Instant 0ms SWR Cache Hydration from sessionStorage
    if (user?.id) {
      const cached = SecureWorkspaceCache.loadSnapshot(user.id);
      if (cached) {
        if (cached.web_projects && cached.web_projects.length > 0) {
          setProjects(cached.web_projects);
        }
        if (cached.active_web) {
          hydrateWebProject(cached.active_web);
        }
        if (cached.rag_vaults && cached.rag_vaults.length > 0) {
          setRagVaults(cached.rag_vaults);
          if (!selectedRAGVaultId) {
            setSelectedRAGVaultId(cached.rag_vaults[0].project_id);
          }
        }
        if (cached.active_rag) {
          hydrateVaultData(cached.active_rag);
        }
      }
    }

    // 2. Background Revalidation
    async function bootstrapWorkspace() {
      try {
        const data = await api.bootstrap();
        if (!mounted) return;
        if (data.web_projects) {
          setProjects(data.web_projects);
        }
        if (data.active_web) {
          hydrateWebProject(data.active_web);
        }
        if (data.rag_vaults) {
          setRagVaults(data.rag_vaults);
          if (!selectedRAGVaultId && data.rag_vaults.length > 0) {
            setSelectedRAGVaultId(data.rag_vaults[0].project_id);
          }
        }
        if (data.active_rag) {
          hydrateVaultData(data.active_rag);
        }

        // Save fresh snapshot to tenant-isolated cache
        if (user?.id) {
          SecureWorkspaceCache.saveSnapshot(user.id, data);
        }
      } catch (err) {
        console.warn("Bootstrap fallback error:", err);
      }
    }
    void bootstrapWorkspace();
    return () => {
      mounted = false;
    };
  }, [user?.id, setProjects, hydrateWebProject, setRagVaults, hydrateVaultData, selectedRAGVaultId]);

  // When a run is loaded or active run finishes in Web mode, manage tab selection
  useEffect(() => {
    if (!run) return;
    if (!isActiveRun) {
      setActiveTab("conclusions");
    }
  }, [run?.id, isActiveRun]);

  const isCompleted = run?.status === "completed";
  const isPlanDone = completedStages.has("planning") || isCompleted;
  const isPlanActive = run?.status === "planning";
  const isDiscoverDone = completedStages.has("discovering") || completedStages.has("fetching") || isCompleted;
  const isDiscoverActive = run?.status === "discovering" || run?.status === "fetching";
  const isExtractDone = completedStages.has("extracting") || isCompleted;
  const isExtractActive = run?.status === "extracting";
  const isSynthesizeDone = completedStages.has("comparing") || completedStages.has("synthesising") || completedStages.has("validating") || isCompleted;
  const isSynthesizeActive = run?.status === "comparing" || run?.status === "synthesising";

  const runDuration = useMemo(() => {
    if (!run?.started_at) return "";
    return durationText(run.started_at, run.completed_at);
  }, [run?.started_at, run?.completed_at]);

  const handleInquirySubmit = async (finalQuestion: string) => {
    if (!user) {
      openAuthModal("signin");
      return;
    }
    if (quota?.is_quota_exhausted) {
      openQuotaModal();
      return;
    }

    try {
      if (mode === "web") {
        await createProject(finalQuestion);
      } else {
        // Document RAG mode: execute directly (auto-creates workspace if needed)
        await executeRAG(finalQuestion);
      }
      await refreshQuota();
    } catch (err: unknown) {
      const statusErr = err as Error & { status?: number };
      if (statusErr.status === 401) {
        openAuthModal("signin");
      } else if (statusErr.status === 402) {
        openQuotaModal();
      }
    }
  };

  return (
    <main className="shell">
      {/* Sticky Top Bar for Mobile & Tablet screens (< 1024px) */}
      <header className="mobile-header" aria-label="Mobile Navigation Bar">
        <button
          type="button"
          className={`mobile-menu-btn ${isMobileNavOpen ? "open" : ""}`}
          onClick={() => setIsMobileNavOpen(!isMobileNavOpen)}
          aria-expanded={isMobileNavOpen}
          aria-controls="app-sidebar"
          aria-label={isMobileNavOpen ? "Close navigation menu" : "Open navigation menu"}
        >
          <span className="hamburger-line" />
          <span className="hamburger-line" />
          <span className="hamburger-line" />
        </button>

        <div className="mobile-brand">
          <span className="brand-mark mobile-mark" aria-hidden="true">✦</span>
          <span className="mobile-brand-title">EvidenceLab</span>
        </div>

        <div className="mobile-header-right">
          <span className="mobile-mode-pill">
            {mode === "web" ? "Web Intelligence" : "Document RAG"}
          </span>
          <span className={`mobile-status-dot ${connectionStatus}`} title={`System: ${connectionStatus}`} />
        </div>
      </header>

      <Sidebar
        projects={projects}
        ragVaults={ragVaults}
        activeProjectId={mode === "web" ? activeWebProjectId : activeRAGVaultId}
        selectedRunId={run?.id}
        selectedReportId={report?.id}
        pastReports={pastReports}
        currentMode={mode}
        healthInfo={healthInfo}
        isOpen={isMobileNavOpen}
        onClose={() => setIsMobileNavOpen(false)}
        onSelectProject={(proj) => {
          setMode("web");
          openProject(proj);
        }}
        onSelectRun={(runId) => {
          setMode("web");
          openRunById(runId);
        }}
        onSelectVault={(vaultId) => {
          setSelectedRAGVaultId(vaultId);
          setMode("rag");
          setRAGActiveTab("vault");
        }}
        onSelectReport={(reportId, vaultId) => {
          setSelectedRAGVaultId(vaultId);
          setMode("rag");
          openReportById(reportId);
        }}
      />

      <section className="workspace" id="main-content">
        <header className="workspace-header">
          <div className="workspace-title-area">
            <p className="eyebrow">ENTERPRISE RESEARCH INTELLIGENCE</p>
            <h1>Evidence before conclusions.</h1>
            <p className="subhead">
              Synthesize multi-angle market intelligence and document research with verified source citations.
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
                Knowledge Vault ({documents.filter((d) => d.status === "ready").length} {documents.filter((d) => d.status === "ready").length === 1 ? "Document" : "Documents"})
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
                <div className="empty-state-graphic" aria-hidden="true">✦</div>
                <h2>Start a Research Inquiry</h2>
                <p>
                  Execute multi-angle discovery across the live web or synthesize deep insights from your uploaded PDF documents with verifiable source citations.
                </p>
              </section>
            )}

            {run && (
              <>
                <section className="run-context" aria-label="Active research question context">
                  <div className="run-context-info">
                    <p className="eyebrow">RESEARCH INQUIRY</p>
                    <h2>{sanitizeText(run.question)}</h2>
                    <div className="run-context-subline">
                      {/* Progressive Left-to-Right Micro Pipeline Track */}
                      <div className="micro-pipeline-track" role="list" aria-label="Research execution flow">
                        <button
                          type="button"
                          className={`micro-step-node ${isPlanDone ? "completed" : isPlanActive ? "active" : ""}`}
                          onClick={() => {
                            if (!isActiveRun) setWebReportMode("tabs");
                            setActiveTab("activity");
                          }}
                          title="Stage 1: Multi-Angle Query Planning"
                        >
                          <span className="micro-step-dot">
                            {isPlanDone ? (
                              <svg className="micro-step-svg" width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                                <polyline points="20 6 9 17 4 12" />
                              </svg>
                            ) : (
                              <span className="micro-step-num">1</span>
                            )}
                          </span>
                          <span className="micro-step-label">Plan</span>
                        </button>

                        <div className={`micro-step-line ${isDiscoverDone || isDiscoverActive ? "filled" : ""}`} />

                        <button
                          type="button"
                          className={`micro-step-node ${isDiscoverDone ? "completed" : isDiscoverActive ? "active" : ""}`}
                          onClick={() => {
                            if (!isActiveRun) setWebReportMode("tabs");
                            setActiveTab("sources");
                          }}
                          title="Stage 2: Web Discovery & Ingestion"
                        >
                          <span className="micro-step-dot">
                            {isDiscoverDone ? (
                              <svg className="micro-step-svg" width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                                <polyline points="20 6 9 17 4 12" />
                              </svg>
                            ) : (
                              <span className="micro-step-num">2</span>
                            )}
                          </span>
                          <span className="micro-step-label">Discover</span>
                        </button>

                        <div className={`micro-step-line ${isExtractDone || isExtractActive ? "filled" : ""}`} />

                        <button
                          type="button"
                          className={`micro-step-node ${isExtractDone ? "completed" : isExtractActive ? "active" : ""}`}
                          onClick={() => {
                            if (!isActiveRun) setWebReportMode("tabs");
                            setActiveTab("claims");
                          }}
                          title="Stage 3: Atomic Claim Extraction & Offsets"
                        >
                          <span className="micro-step-dot">
                            {isExtractDone ? (
                              <svg className="micro-step-svg" width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                                <polyline points="20 6 9 17 4 12" />
                              </svg>
                            ) : (
                              <span className="micro-step-num">3</span>
                            )}
                          </span>
                          <span className="micro-step-label">Extract</span>
                        </button>

                        <div className={`micro-step-line ${isSynthesizeDone || isSynthesizeActive ? "filled" : ""}`} />

                        <button
                          type="button"
                          className={`micro-step-node ${isSynthesizeDone ? "completed" : isSynthesizeActive ? "active" : ""}`}
                          onClick={() => {
                            if (!isActiveRun) setWebReportMode("tabs");
                            setActiveTab("conclusions");
                          }}
                          title="Stage 4: Synthesis & Verification Gate"
                        >
                          <span className="micro-step-dot">
                            {isSynthesizeDone ? (
                              <svg className="micro-step-svg" width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                                <polyline points="20 6 9 17 4 12" />
                              </svg>
                            ) : (
                              <span className="micro-step-num">4</span>
                            )}
                          </span>
                          <span className="micro-step-label">Synthesize</span>
                        </button>

                        <div className={`micro-step-line ${isCompleted ? "filled" : ""}`} />

                        {/* Verified Grounding Badge Finale */}
                        <div className={`micro-trust-badge ${isCompleted ? "verified" : isActiveRun ? "in-progress" : ""}`}>
                          <svg className="micro-trust-icon" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                            <polyline points="9 12 11 14 15 10" />
                          </svg>
                          <span>{isCompleted ? "Verified Grounding" : isActiveRun ? "Synthesizing" : "Grounded"}</span>
                        </div>
                      </div>

                      {/* Timestamp & Duration */}
                      <div className="micro-meta-details">
                        <span className="micro-time">Started {formatDateTime(run.started_at)}</span>
                        {runDuration && (
                          <>
                            <span className="micro-sep">·</span>
                            <span className="micro-duration">{runDuration}</span>
                          </>
                        )}
                      </div>
                    </div>
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

                {/* Live Pipeline during Active Discovery */}
                {isActiveRun && (
                  <PipelineCard
                    run={run}
                    events={events}
                    completedStages={completedStages}
                    onRetry={retry}
                    onViewActivity={() => setActiveTab("activity")}
                  />
                )}

                {/* Completed Run Views: Clean Executive Document vs Detailed Tabs */}
                {!isActiveRun && (
                  <>
                    <WebReportToolbar
                      run={run}
                      sources={sources}
                      claims={claims}
                      viewMode={webReportMode}
                      onToggleMode={setWebReportMode}
                    />

                    {webReportMode === "clean" ? (
                      <CleanWebReportView
                        run={run}
                        sources={sources}
                        claims={claims}
                        onViewEvidence={openTrace}
                      />
                    ) : (
                      <>
                        <PipelineCard
                          run={run}
                          events={events}
                          completedStages={completedStages}
                          onRetry={retry}
                          onViewActivity={() => setActiveTab("activity")}
                        />
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

                {/* If run is active, also show tabs below pipeline */}
                {isActiveRun && (
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
                )}
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
            onReplaceDoc={replaceDocument}
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

export function App() {
  return (
    <AuthProvider>
      <StarfieldBackground />
      <MainWorkspace />
      <AuthModal />
      <QuotaExceededModal />
    </AuthProvider>
  );
}

export default App;
