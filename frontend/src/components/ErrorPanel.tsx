import { useState } from "react";
import { sanitizeText } from "../utils/textUtils";

interface ErrorPanelProps {
  errorSummary: string;
  stage?: string;
  onRetry?: () => void;
  isRetrying?: boolean;
}

interface ParsedError {
  category: "rate_limit" | "network" | "data_quality" | "provider_error";
  title: string;
  description: string;
  actionHint: string;
}

function parseErrorSummary(errorText: string, stage?: string): ParsedError {
  const lower = errorText.toLowerCase();
  const stageName = stage ? ` during ${stage}` : "";

  if (
    lower.includes("rate limit") ||
    lower.includes("429") ||
    lower.includes("too many requests") ||
    lower.includes("tpm") ||
    lower.includes("rpm")
  ) {
    return {
      category: "rate_limit",
      title: `Research paused${stageName}`,
      description:
        "The AI provider temporarily reached its request rate limit. All your gathered sources, extracted claims, and comparisons are safely saved in the database.",
      actionHint: "You can retry from saved progress now. The workflow will resume right where it left off.",
    };
  }

  if (
    lower.includes("timeout") ||
    lower.includes("timed out") ||
    lower.includes("connection") ||
    lower.includes("unreachable") ||
    lower.includes("econnrefused")
  ) {
    return {
      category: "network",
      title: `Connection interrupted${stageName}`,
      description:
        "A network or service timeout occurred while communicating with research services. Your progress has been preserved.",
      actionHint: "Check your internet connection and click retry to resume from saved progress.",
    };
  }

  if (
    lower.includes("no usable sources") ||
    lower.includes("no valid") ||
    lower.includes("zero snapshots")
  ) {
    return {
      category: "data_quality",
      title: "Insufficient source data found",
      description:
        "The search discovery phase could not retrieve enough relevant public web sources to meet our citation threshold.",
      actionHint: "Try refining your question or retry to search again with fresh queries.",
    };
  }

  return {
    category: "provider_error",
    title: `Research paused${stageName}`,
    description:
      "An unexpected service response interrupted the current research step. All completed stages and evidence have been safely saved.",
    actionHint: "You can retry immediately from saved progress without losing any previous work.",
  };
}

export function ErrorPanel({ errorSummary, stage, onRetry, isRetrying = false }: ErrorPanelProps) {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const parsed = parseErrorSummary(errorSummary, stage);

  return (
    <div className={`error-recovery-panel ${parsed.category}`} role="alert" aria-live="assertive">
      <div className="error-panel-header">
        <div className="error-icon-wrapper" aria-hidden="true">
          {parsed.category === "rate_limit" ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
          ) : parsed.category === "network" ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="1" y1="1" x2="23" y2="23" />
              <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55" />
              <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39" />
              <path d="M10.71 5.05A16 16 0 0 1 22.58 9" />
              <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88" />
              <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
              <line x1="12" y1="20" x2="12.01" y2="20" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
          )}
        </div>
        <div className="error-header-text">
          <h3>{parsed.title}</h3>
          <p className="error-description">{parsed.description}</p>
        </div>
      </div>

      <div className="error-panel-action-box">
        <p className="action-hint">{parsed.actionHint}</p>
        {onRetry && (
          <button
            type="button"
            className="retry-primary-btn"
            onClick={onRetry}
            disabled={isRetrying}
          >
            {isRetrying ? "Resuming research..." : "Retry from saved progress"}
          </button>
        )}
      </div>

      <div className="technical-details-section">
        <button
          type="button"
          className="technical-toggle-btn"
          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
          aria-expanded={showTechnicalDetails}
        >
          <span>{showTechnicalDetails ? "▾ Hide technical details" : "▸ View technical details"}</span>
        </button>

        {showTechnicalDetails && (
          <div className="technical-raw-box">
            <pre>{sanitizeText(errorSummary)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
