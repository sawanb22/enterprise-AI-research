import { Assessment, Claim, Conclusion, RunDetail, RunEvent, Source } from "../api";
import { AssessmentsCard } from "./AssessmentsCard";
import { ClaimsCard } from "./ClaimsCard";
import { ConclusionsCard } from "./ConclusionsCard";
import { EvidenceQualitySummary } from "./EvidenceQualitySummary";
import { PipelineCard } from "./PipelineCard";
import { SourcesCard } from "./SourcesCard";

export type TabKey = "conclusions" | "sources" | "claims" | "activity";

interface ResearchTabsProps {
  activeTab: TabKey;
  onSelectTab: (tab: TabKey) => void;
  run: RunDetail;
  events: RunEvent[];
  sources: Source[];
  claims: Claim[];
  assessments: Assessment[];
  completedStages: Set<string>;
  onViewEvidence: (conclusionId: string) => void;
  onRetry: () => void;
}

export function ResearchTabs({
  activeTab,
  onSelectTab,
  run,
  events,
  sources,
  claims,
  assessments,
  completedStages,
  onViewEvidence,
  onRetry,
}: ResearchTabsProps) {
  return (
    <div className="research-tabs-container">
      <nav className="tabs-nav-bar" role="tablist" aria-label="Research Data Views">
        <button
          type="button"
          role="tab"
          id="tab-conclusions"
          aria-selected={activeTab === "conclusions"}
          aria-controls="panel-conclusions"
          className={`tab-btn ${activeTab === "conclusions" ? "active" : ""}`}
          onClick={() => onSelectTab("conclusions")}
        >
          <span className="tab-icon" aria-hidden="true">💡</span>
          <span>Conclusions</span>
          {run.conclusions.length > 0 && (
            <span className="tab-count-badge">{run.conclusions.length}</span>
          )}
        </button>

        <button
          type="button"
          role="tab"
          id="tab-sources"
          aria-selected={activeTab === "sources"}
          aria-controls="panel-sources"
          className={`tab-btn ${activeTab === "sources" ? "active" : ""}`}
          onClick={() => onSelectTab("sources")}
        >
          <span className="tab-icon" aria-hidden="true">🌐</span>
          <span>Sources</span>
          {sources.length > 0 && (
            <span className="tab-count-badge">{sources.length}</span>
          )}
        </button>

        <button
          type="button"
          role="tab"
          id="tab-claims"
          aria-selected={activeTab === "claims"}
          aria-controls="panel-claims"
          className={`tab-btn ${activeTab === "claims" ? "active" : ""}`}
          onClick={() => onSelectTab("claims")}
        >
          <span className="tab-icon" aria-hidden="true">📑</span>
          <span>Claims & Comparisons</span>
          {claims.length > 0 && (
            <span className="tab-count-badge">{claims.length}</span>
          )}
        </button>

        <button
          type="button"
          role="tab"
          id="tab-activity"
          aria-selected={activeTab === "activity"}
          aria-controls="panel-activity"
          className={`tab-btn ${activeTab === "activity" ? "active" : ""}`}
          onClick={() => onSelectTab("activity")}
        >
          <span className="tab-icon" aria-hidden="true">⚡</span>
          <span>Pipeline Activity</span>
          {events.length > 0 && (
            <span className="tab-count-badge">{events.length}</span>
          )}
        </button>
      </nav>

      <div className="tab-panels-wrapper">
        {activeTab === "conclusions" && (
          <div
            id="panel-conclusions"
            role="tabpanel"
            aria-labelledby="tab-conclusions"
            className="tab-panel conclusions-panel"
          >
            <ConclusionsCard
              conclusions={run.conclusions}
              onViewEvidence={onViewEvidence}
            />
            <EvidenceQualitySummary
              sources={sources}
              claims={claims}
              assessments={assessments}
            />
          </div>
        )}

        {activeTab === "sources" && (
          <div
            id="panel-sources"
            role="tabpanel"
            aria-labelledby="tab-sources"
            className="tab-panel sources-panel"
          >
            <SourcesCard sources={sources} />
          </div>
        )}

        {activeTab === "claims" && (
          <div
            id="panel-claims"
            role="tabpanel"
            aria-labelledby="tab-claims"
            className="tab-panel claims-panel"
          >
            <div className="grid lower-grid">
              <ClaimsCard claims={claims} />
              <AssessmentsCard assessments={assessments} />
            </div>
          </div>
        )}

        {activeTab === "activity" && (
          <div
            id="panel-activity"
            role="tabpanel"
            aria-labelledby="tab-activity"
            className="tab-panel activity-panel"
          >
            <PipelineCard
              run={run}
              events={events}
              completedStages={completedStages}
              onRetry={onRetry}
              forceFullView={true}
            />
          </div>
        )}
      </div>
    </div>
  );
}
