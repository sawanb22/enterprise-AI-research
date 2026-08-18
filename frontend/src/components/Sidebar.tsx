import { useEffect, useState } from "react";
import { api, Project, RAGReport, Run } from "../api";
import { LifetimeQuotaBadge, UserProfileMenu } from "../auth";
import { formatDateTime, pretty, sanitizeText } from "../utils/textUtils";

interface SidebarProps {
  projects: Project[];
  ragVaults?: { project_id: string; title: string; created_at: string }[];
  activeProjectId?: string;
  selectedRunId?: string;
  selectedReportId?: string;
  pastReports?: RAGReport[];
  currentMode: "web" | "rag";
  healthInfo: {
    aiProvider?: string;
    model?: string;
    configured: Record<string, boolean> | null;
  };
  onSelectProject: (project: Project) => void;
  onSelectRun: (runId: string) => void;
  onSelectVault?: (vaultId: string) => void;
  onSelectReport?: (reportId: string, vaultId: string) => void;
}

export function Sidebar({
  projects,
  ragVaults = [],
  activeProjectId,
  selectedRunId,
  selectedReportId,
  pastReports = [],
  currentMode,
  healthInfo,
  onSelectProject,
  onSelectRun,
  onSelectVault,
  onSelectReport,
}: SidebarProps) {
  const [projectRuns, setProjectRuns] = useState<Record<string, Run[]>>({});
  const [expandedProjects, setExpandedProjects] = useState<Record<string, boolean>>({});
  const [vaultReports, setVaultReports] = useState<Record<string, RAGReport[]>>({});
  const [expandedVaults, setExpandedVaults] = useState<Record<string, boolean>>({});

  // Auto-expand active project
  useEffect(() => {
    if (activeProjectId && currentMode === "web") {
      setExpandedProjects((prev) => ({ ...prev, [activeProjectId]: true }));
      if (!projectRuns[activeProjectId]) {
        api.projectRuns(activeProjectId).then((runs) => {
          setProjectRuns((prev) => ({ ...prev, [activeProjectId]: runs }));
        }).catch(() => {});
      }
    }
  }, [activeProjectId, selectedRunId, currentMode, projectRuns]);

  // Auto-expand active vault & cache past reports
  useEffect(() => {
    if (activeProjectId && currentMode === "rag") {
      setExpandedVaults((prev) => ({ ...prev, [activeProjectId]: true }));
      if (pastReports.length > 0) {
        setVaultReports((prev) => ({ ...prev, [activeProjectId]: pastReports }));
      } else {
        api.projectRAGReports(activeProjectId).then((res) => {
          setVaultReports((prev) => ({ ...prev, [activeProjectId]: res.reports }));
        }).catch(() => {});
      }
    }
  }, [activeProjectId, currentMode, pastReports]);

  const toggleProject = async (project: Project) => {
    const isExpanded = expandedProjects[project.id];
    setExpandedProjects((prev) => ({ ...prev, [project.id]: !isExpanded }));

    if (!isExpanded && !projectRuns[project.id]) {
      try {
        const runs = await api.projectRuns(project.id);
        setProjectRuns((prev) => ({ ...prev, [project.id]: runs }));
      } catch {}
    }
    onSelectProject(project);
  };

  const toggleVault = async (vaultId: string) => {
    const isExpanded = expandedVaults[vaultId];
    setExpandedVaults((prev) => ({ ...prev, [vaultId]: !isExpanded }));

    if (!isExpanded && !vaultReports[vaultId]) {
      try {
        const res = await api.projectRAGReports(vaultId);
        setVaultReports((prev) => ({ ...prev, [vaultId]: res.reports }));
      } catch {}
    }
    if (onSelectVault) onSelectVault(vaultId);
  };

  const aiLabel =
    healthInfo.aiProvider === "bedrock"
      ? "Bedrock"
      : healthInfo.aiProvider === "openai_compatible"
      ? "OpenAI / Groq"
      : "AI Engine";

  return (
    <aside className="sidebar" aria-label="Research Projects Navigation">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">✦</span>
        <div>
          <strong>EvidenceLab</strong>
          <small>Enterprise Research Agent</small>
        </div>
      </div>

      {/* Celestial User & Quota Card */}
      <div className="sidebar-auth-section">
        <UserProfileMenu />
        <LifetimeQuotaBadge />
      </div>

      <div className="provider-state" role="status" aria-label="System operational status">
        <div className="provider-item">
          <span className="dot ready" aria-hidden="true" />
          <span>System Operational</span>
        </div>
      </div>

      {/* Section 1: Web Intelligence Inquiries */}
      <div className="sidebar-heading" id="projects-heading">
        <span className="sidebar-heading-title">🌐 Web Inquiries</span>
        {projects.length > 0 && <span className="sidebar-section-count">{projects.length}</span>}
      </div>
      <nav className="project-list" aria-labelledby="projects-heading">
        {projects.map((project) => {
          const isSelected = activeProjectId === project.id && currentMode === "web";
          const isExpanded = expandedProjects[project.id] ?? isSelected;
          const runs = projectRuns[project.id] || (project.latest_run ? [project.latest_run] : []);

          return (
            <div className="project-group" key={project.id}>
              <button
                type="button"
                className={`project ${isSelected ? "selected" : ""}`}
                onClick={() => toggleProject(project)}
                aria-expanded={isExpanded}
                aria-label={`Project: ${project.title}, status: ${project.latest_run?.status ?? "draft"}`}
              >
                <div className="project-header-row">
                  <span className="project-chevron" aria-hidden="true">
                    {isExpanded ? "▾" : "▸"}
                  </span>
                  <span className="project-title">{sanitizeText(project.title)}</span>
                </div>
                <div className="project-meta-row">
                  <span className={`status-pill ${project.latest_run?.status ?? "draft"}`}>
                    {project.latest_run?.status ?? "draft"}
                  </span>
                  {runs.length > 1 && <span className="runs-count">{runs.length} runs</span>}
                </div>
              </button>

              {isExpanded && runs.length > 0 && (
                <div className="run-history-list" role="menu" aria-label={`Runs for ${project.title}`}>
                  {runs.map((r, idx) => {
                    const isRunActive = selectedRunId === r.id && currentMode === "web";
                    const runNumber = runs.length - idx;
                    const canResume = ["failed", "partial"].includes(r.status);

                    return (
                      <button
                        type="button"
                        key={r.id}
                        className={`run-history-item ${isRunActive ? "active" : ""}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectRun(r.id);
                        }}
                        aria-current={isRunActive ? "true" : undefined}
                      >
                        <div className="run-item-top">
                          <span className="run-label">Run {runNumber}</span>
                          <span className={`status-dot ${r.status}`} title={r.status} />
                          <span className="run-status-text">{pretty(r.status)}</span>
                          {canResume && <span className="resume-badge">Resume available</span>}
                        </div>
                        <div className="run-item-bottom">
                          <span className="run-time">{formatDateTime(r.started_at)}</span>
                          {r.conclusion_count > 0 && (
                            <span className="run-conclusions-count">
                              {r.conclusion_count} {r.conclusion_count === 1 ? "conclusion" : "conclusions"}
                            </span>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
        {!projects.length && (
          <p className="empty">No web research inquiries yet.</p>
        )}
      </nav>

      {/* Section 2: PDF Knowledge Vaults */}
      <div className="sidebar-heading" style={{ marginTop: "18px" }}>
        <span className="sidebar-heading-title">📑 Document Vaults</span>
        {ragVaults.length > 0 && <span className="sidebar-section-count">{ragVaults.length}</span>}
      </div>
      <nav className="project-list">
        {ragVaults.map((vault) => {
          const isSelected = activeProjectId === vault.project_id && currentMode === "rag";
          const isExpanded = expandedVaults[vault.project_id] ?? isSelected;
          const reports = vaultReports[vault.project_id] || (isSelected ? pastReports : []);

          return (
            <div className="project-group" key={vault.project_id}>
              <button
                type="button"
                className={`project ${isSelected ? "selected" : ""}`}
                onClick={() => toggleVault(vault.project_id)}
                aria-expanded={isExpanded}
                title={`Open PDF Knowledge Vault: ${vault.title}`}
              >
                <div className="project-header-row">
                  <span className="project-chevron" aria-hidden="true">
                    {isExpanded ? "▾" : "▸"}
                  </span>
                  <span className="project-title">{sanitizeText(vault.title.replace(/^Document Vault:\s*/, ""))}</span>
                </div>
                <div className="project-meta-row">
                  <span className="status-pill completed">Vault Ready</span>
                  {reports.length > 0 && (
                    <span className="runs-count">{reports.length} {reports.length === 1 ? "report" : "reports"}</span>
                  )}
                </div>
              </button>

              {isExpanded && reports.length > 0 && (
                <div className="run-history-list" role="menu" aria-label={`Reports for ${vault.title}`}>
                  {reports.map((r, idx) => {
                    const isReportActive = selectedReportId === r.id && currentMode === "rag";
                    const reportNumber = reports.length - idx;

                    return (
                      <button
                        type="button"
                        key={r.id}
                        className={`run-history-item ${isReportActive ? "active" : ""}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (onSelectReport) onSelectReport(r.id, vault.project_id);
                        }}
                        aria-current={isReportActive ? "true" : undefined}
                      >
                        <div className="run-item-top">
                          <span className="run-label">Report #{reportNumber}</span>
                          <span className="status-dot completed" title="completed" />
                          <span className="run-status-text">Grounded</span>
                        </div>
                        <div className="run-item-bottom">
                          <span className="run-time">{formatDateTime(r.created_at)}</span>
                          <span className="run-conclusions-count" title={r.question}>
                            {sanitizeText(r.question.length > 28 ? r.question.slice(0, 28) + "..." : r.question)}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
        {!ragVaults.length && (
          <p className="empty">No PDF document vaults yet.</p>
        )}
      </nav>
    </aside>
  );
}
