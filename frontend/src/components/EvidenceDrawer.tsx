import { useEffect, useRef } from "react";
import { Trace } from "../api";
import { pretty, sanitizeText } from "../utils/textUtils";

interface EvidenceDrawerProps {
  trace: Trace;
  onClose: () => void;
}

export function EvidenceDrawer({ trace, onClose }: EvidenceDrawerProps) {
  const drawerRef = useRef<HTMLElement>(null);
  const closeBtnRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Focus trap and Escape key listener
  useEffect(() => {
    previousFocusRef.current = document.activeElement as HTMLElement | null;
    closeBtnRef.current?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        return;
      }

      if (e.key === "Tab" && drawerRef.current) {
        const focusableElements = drawerRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement?.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement?.focus();
          }
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      previousFocusRef.current?.focus();
    };
  }, [onClose]);

  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} aria-hidden="true" />
      <aside
        ref={drawerRef}
        className="trace-panel"
        role="dialog"
        aria-modal="true"
        aria-label="Evidence chain trace"
      >
        <div className="trace-panel-top">
          <button
            ref={closeBtnRef}
            type="button"
            className="close-drawer-btn"
            onClick={onClose}
            aria-label="Close evidence panel"
          >
            ✕
          </button>
          <p className="eyebrow">AUDITABLE TRACEABILITY</p>
          <h2>Evidence chain</h2>
        </div>

        <div className="trace-conclusion-box">
          <span
            className={`confidence ${trace.conclusion.confidence}`}
            aria-label={`Confidence: ${trace.conclusion.confidence}`}
          >
            {pretty(trace.conclusion.confidence)} confidence
          </span>
          <p className="trace-conclusion">{sanitizeText(trace.conclusion.statement)}</p>
        </div>

        {trace.conclusion.reasoning && (
          <div className="trace-reasoning">
            <strong>Synthesis Rationale:</strong>
            <p>{sanitizeText(trace.conclusion.reasoning)}</p>
          </div>
        )}

        <div className="trace-path" aria-label="Evidence lineage flow">
          <span>Conclusion</span>
          <span className="arrow" aria-hidden="true">↓</span>
          <span>{trace.claims.length} Grounded Claims</span>
          <span className="arrow" aria-hidden="true">↓</span>
          <span>Original Sources</span>
        </div>

        <div className="trace-claims-list">
          <h3>Cited source excerpts</h3>
          {trace.claims.map((claim) => (
            <article className="trace-claim" key={claim.id}>
              <div className="trace-claim-meta">
                <span className="tag">{sanitizeText(claim.topic)}</span>
                <span className={`confidence ${claim.confidence}`}>{pretty(claim.confidence)}</span>
              </div>
              <p className="trace-claim-statement">{sanitizeText(claim.statement)}</p>
              <blockquote className="trace-claim-excerpt">
                “{sanitizeText(claim.exact_excerpt)}”
              </blockquote>
              <a
                href={claim.source.canonical_url}
                target="_blank"
                rel="noreferrer"
                className="trace-source-link"
              >
                <span>{sanitizeText(claim.source.title || claim.source.publisher || "View original source")}</span>
                <span aria-hidden="true">↗</span>
              </a>
            </article>
          ))}
        </div>

        {trace.assessments.length > 0 && (
          <div className="trace-assessments-section">
            <h3>Cross-source agreement on this point</h3>
            {trace.assessments.map((assessment) => (
              <div className="trace-assessment" key={assessment.id}>
                <span className={`relationship ${assessment.relationship}`}>
                  {pretty(assessment.relationship)}
                </span>
                <p>{sanitizeText(assessment.rationale)}</p>
              </div>
            ))}
          </div>
        )}
      </aside>
    </>
  );
}
