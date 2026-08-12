import { useMemo, useState } from "react";
import { RunDetail, RunEvent } from "../api";
import { durationText, pretty, time } from "../utils/textUtils";
import { ErrorPanel } from "./ErrorPanel";

export const STAGES = [
  "planning",
  "discovering",
  "fetching",
  "extracting",
  "comparing",
  "synthesising",
  "validating",
];

interface PipelineCardProps {
  run: RunDetail;
  events: RunEvent[];
  completedStages: Set<string>;
  onRetry?: () => void;
  onViewActivity?: () => void;
  forceFullView?: boolean;
}

export function PipelineCard({
  run,
  events,
  completedStages,
  onRetry,
  onViewActivity,
  forceFullView = false,
}: PipelineCardProps) {
  const [isManuallyExpanded, setIsManuallyExpanded] = useState(false);
  const isActive = [
    "queued",
    "planning",
    "discovering",
    "fetching",
    "extracting",
    "comparing",
    "synthesising",
  ].includes(run.status);

  const duration = useMemo(
    () => durationText(run.started_at, run.completed_at),
    [run.started_at, run.completed_at]
  );

  // If run is completed and not manually expanded or forced full view, render the calm summary bar
  if (!isActive && !isManuallyExpanded && !forceFullView) {
    return (
      <section className="pipeline-summary-bar card" aria-label="Research status summary">
        <div className="summary-left">
          <span className={`status-badge-inline ${run.status}`}>
            <span className={`dot-status ${run.status}`} aria-hidden="true" />
            <span>{pretty(run.status)}</span>
          </span>
          <span className="summary-text">
            {run.status === "completed" && `Completed ${duration ? `in ${duration}` : ""} · `}
            {run.source_count} {run.source_count === 1 ? "source" : "sources"} ·{" "}
            {run.claim_count} {run.claim_count === 1 ? "claim" : "claims"} ·{" "}
            {run.conclusion_count} {run.conclusion_count === 1 ? "conclusion" : "conclusions"}
          </span>
        </div>

        <div className="summary-actions">
          {run.error_summary && (
            <span className="summary-error-badge">Has notice</span>
          )}
          {onViewActivity && (
            <button
              type="button"
              className="view-activity-btn"
              onClick={onViewActivity}
            >
              View pipeline activity <span>→</span>
            </button>
          )}
          <button
            type="button"
            className="expand-pipeline-btn"
            onClick={() => setIsManuallyExpanded(true)}
            aria-label="Expand pipeline details"
          >
            Show full pipeline ▾
          </button>
        </div>

        {run.error_summary && (
          <div className="summary-error-wrapper">
            <ErrorPanel
              errorSummary={run.error_summary}
              stage={run.status}
              onRetry={onRetry}
            />
          </div>
        )}
      </section>
    );
  }

  return (
    <section className="pipeline card" aria-label="Research pipeline progression">
      <div className="section-title">
        <div>
          <p className="eyebrow">{isActive ? "LIVE PIPELINE" : "PIPELINE ACTIVITY"}</p>
          <h2>Research pipeline</h2>
        </div>
        <div className="pipeline-header-meta">
          <span className="muted">{events.length} recorded events</span>
          {!isActive && (
            <button
              type="button"
              className="collapse-pipeline-btn"
              onClick={() => setIsManuallyExpanded(false)}
            >
              Collapse pipeline ▴
            </button>
          )}
        </div>
      </div>

      <div className="stage-row" role="list" aria-label="Pipeline stages">
        {STAGES.map((stage) => {
          const isDone = completedStages.has(stage);
          const isCurrent = run.status === stage;

          return (
            <div
              className={`stage ${isDone ? "done" : isCurrent ? "current" : ""}`}
              key={stage}
              role="listitem"
              aria-label={`Stage ${stage}: ${isDone ? "completed" : isCurrent ? "active" : "pending"}`}
            >
              <i aria-hidden="true" />
              <span>{pretty(stage)}</span>
            </div>
          );
        })}
      </div>

      <div className="events" role="log" aria-label="Pipeline event log" aria-live="polite">
        {events.slice(-6).map((event, index) => (
          <div className="event" key={`${event.occurred_at}-${index}`}>
            <span
              className={`event-icon ${event.status}`}
              aria-label={`Status: ${event.status}`}
            />
            <span className="event-message">{event.message}</span>
            <time dateTime={event.occurred_at}>{time(event.occurred_at)}</time>
          </div>
        ))}
      </div>

      {run.error_summary && (
        <ErrorPanel
          errorSummary={run.error_summary}
          stage={run.status}
          onRetry={onRetry}
        />
      )}

      {["failed", "partial"].includes(run.status) && !run.error_summary && onRetry && (
        <button type="button" className="secondary retry-button-standalone" onClick={onRetry}>
          Retry from saved progress ↺
        </button>
      )}
    </section>
  );
}
