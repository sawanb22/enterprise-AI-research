import { useEffect, useState } from "react";
import { api, Project, Run } from "../api";
import { formatDateTime, pretty, sanitizeText } from "../utils/textUtils";

interface SidebarProps {
  projects: Project[];
  activeProjectId?: string;
  selectedRunId?: string;
  healthInfo: {
    aiProvider?: string;
    model?: string;
    configured: Record<string, boolean> | null;
  };
  onSelectProject: (project: Project) => void;
  onSelectRun: (runId: string) => void;
}

export function Sidebar({
  projects,
  activeProjectId,
  selectedRunId,
  healthInfo,
  onSelectProject,
  onSelectRun,
}: SidebarProps) {
  const [projectRuns, setProjectRuns] = useState<Record<string, Run[]>>({});
  const [expandedProjects, setExpandedProjects] = useState<Record<string, boolean>>({});

  // Auto-expand active project
  useEffect(() => {
    if (activeProjectId) {
      setExpandedProjects((prev) => ({ ...prev, [activeProjectId]: true }));
      // Fetch runs for this project
      api.projectRuns(activeProjectId).then((runs) => {
        setProjectRuns((prev) => ({ ...prev, [activeProjectId]: runs }));
      }).catch(() => {});
    }
  }, [activeProjectId, selectedRunId]);

  const toggleProject = async (project: Project) => {
    const isExpanded = expandedProjects[project.id];
    setExpandedProjects((prev) => ({ ...prev, [project.id]: !isExpanded }));

    if (!isExpanded && !projectRuns[project.id]) {
      try {
        const runs = await api.projectRuns(project.id);
        setProjectRuns((prev) => ({ ...prev, [project.id]: runs }));
      } catch {
        // Fallback to project latest run
      }
    }
    onSelectProject(project);
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
        <span className="brand-mark" aria-hidden="true">E</span>
        <div>
          <strong>EvidenceLab</strong>
          <small>Enterprise Research Agent</small>
        </div>
      </div>

      <div className="provider-state" role="status" aria-label="Provider configuration status">
        <div className="provider-item">
          <span
            className={healthInfo.configured?.ai ? "dot ready" : "dot"}
            aria-hidden="true"
          />
          <span>{aiLabel} {healthInfo.configured?.ai ? "ready" : "needs key"}</span>
        </div>
        <div className="provider-item">
          <span
            className={healthInfo.configured?.tavily ? "dot ready" : "dot"}
            aria-hidden="true"
          />
          <span>Tavily {healthInfo.configured?.tavily ? "ready" : "needs key"}</span>
        </div>
      </div>

      <div className="sidebar-heading" id="projects-heading">Research projects</div>
      <nav className="project-list" aria-labelledby="projects-heading">
        {projects.map((project) => {
          const isSelected = activeProjectId === project.id;
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
                    const isRunActive = selectedRunId === r.id;
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
          <p className="empty">Your completed research will persist here.</p>
        )}
      </nav>
    </aside>
  );
}
