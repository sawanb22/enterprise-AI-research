import { useEffect, useRef } from "react";
import { PageCitation } from "../api";
import { sanitizeText } from "../utils/textUtils";

interface CitationDrawerProps {
  citation: PageCitation;
  onClose: () => void;
  onNext?: () => void;
  onPrev?: () => void;
  hasNext?: boolean;
  hasPrev?: boolean;
  citationIndex?: number;
  totalCitations?: number;
}

export function CitationDrawer({
  citation,
  onClose,
  onNext,
  onPrev,
  hasNext = false,
  hasPrev = false,
  citationIndex,
  totalCitations,
}: CitationDrawerProps) {
  const drawerRef = useRef<HTMLElement>(null);
  const closeBtnRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Focus trap and Escape key handler
  useEffect(() => {
    previousFocusRef.current = document.activeElement as HTMLElement | null;
    closeBtnRef.current?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        return;
      }
      if (e.key === "ArrowRight" && hasNext && onNext) {
        e.preventDefault();
        onNext();
        return;
      }
      if (e.key === "ArrowLeft" && hasPrev && onPrev) {
        e.preventDefault();
        onPrev();
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
  }, [onClose, onNext, onPrev, hasNext, hasPrev]);

  const scorePct = citation.score != null ? Math.round(citation.score * 100) : null;

  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} aria-hidden="true" />
      <aside
        ref={drawerRef}
        className="trace-panel citation-deepdive-drawer"
        role="dialog"
        aria-modal="true"
        aria-label="Citation Provenance Inspector"
      >
        <div className="trace-panel-top">
          <button
            ref={closeBtnRef}
            type="button"
            className="close-drawer-btn"
            onClick={onClose}
            aria-label="Close citation inspector"
          >
            ✕
          </button>
          <div className="drawer-eyebrow-row">
            <span className="eyebrow">GROUNDED PROVENANCE TRACE</span>
            {citationIndex != null && totalCitations != null && (
              <span className="citation-counter">
                Citation {citationIndex + 1} of {totalCitations}
              </span>
            )}
          </div>
          <h2>Source Evidence Inspector</h2>
        </div>

        {/* Target Document Card */}
        <div className="citation-target-card">
          <div className="citation-target-icon" aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </div>
          <div className="citation-target-info">
            <h3 className="target-filename">{citation.document_filename}</h3>
            <div className="target-tags">
              <span className="target-tag page-tag">Page {citation.page_number}</span>
              <span className="target-tag chunk-tag">Chunk #{citation.chunk_index + 1}</span>
              {scorePct != null && (
                <span className="target-tag score-tag">{scorePct}% Relevance</span>
              )}
            </div>
          </div>
        </div>

        {/* Provenance Flow Pipeline */}
        <div className="trace-path" aria-label="Evidence lineage flow">
          <span>Target PDF</span>
          <span className="arrow" aria-hidden="true">→</span>
          <span>Page {citation.page_number}</span>
          <span className="arrow" aria-hidden="true">→</span>
          <span>Verified Verbatim Quote</span>
        </div>

        {/* Verbatim Quote Highlight Box */}
        <div className="citation-quote-section">
          <div className="quote-header-row">
            <span className="quote-label">VERIFIED SOURCE PASSAGE</span>
            <span className="quote-verification-pill">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span>Grounded</span>
            </span>
          </div>

          <blockquote className="citation-verbatim-quote">
            “{sanitizeText(citation.verbatim_quote)}”
          </blockquote>
        </div>

        {/* Verification explanation */}
        <div className="citation-audit-info">
          <p>
            <strong>Auditable Grounding Guarantee:</strong> This passage was extracted directly from
            the indexed vector chunk on <em>Page {citation.page_number}</em> of <em>{citation.document_filename}</em> and passed
            cross-encoder verification against the synthesizer output.
          </p>
        </div>

        {/* Bottom Navigation */}
        <div className="citation-drawer-footer">
          <div className="citation-nav-group">
            {hasPrev && onPrev && (
              <button
                type="button"
                className="citation-nav-btn prev-btn"
                onClick={onPrev}
                title="Previous Citation (Left Arrow)"
              >
                ← Previous
              </button>
            )}
            {hasNext && onNext && (
              <button
                type="button"
                className="citation-nav-btn next-btn"
                onClick={onNext}
                title="Next Citation (Right Arrow)"
              >
                Next Citation →
              </button>
            )}
          </div>
          <button type="button" className="close-action-btn" onClick={onClose}>
            Done
          </button>
        </div>
      </aside>
    </>
  );
}
