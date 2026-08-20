import React from "react";
import { PageCitation, RAGReport } from "../api";
import { pretty, sanitizeText } from "../utils/textUtils";

interface AuditorReportViewProps {
  report: RAGReport;
  allCitations: PageCitation[];
  onOpenCitation: (citation: PageCitation, index: number, total: number) => void;
}

export function AuditorReportView({
  report,
  allCitations,
  onOpenCitation,
}: AuditorReportViewProps) {
  return (
    <div className="auditor-report-container">
      {/* Executive Summary Card */}
      <section className="rag-summary-card">
        <div className="summary-card-header">
          <div className="summary-icon-box" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
          </div>
          <h3>Executive Synthesis</h3>
        </div>
        <p className="summary-text">{sanitizeText(report.summary)}</p>
      </section>

      {/* Sections List */}
      <div className="rag-sections-list">
        {report.sections.map((section, secIdx) => (
          <article key={secIdx} className="rag-section-card">
            <div className="section-card-header">
              <div className="section-num-tag">{secIdx + 1}</div>
              <h3 className="section-heading">{sanitizeText(section.heading)}</h3>
              <span className={`confidence ${section.confidence}`}>
                <span className="conf-indicator" aria-hidden="true" />
                {pretty(section.confidence)} confidence
              </span>
            </div>

            <div className="section-body">
              <p className="section-content-text">{sanitizeText(section.content)}</p>

              {section.citations.length > 0 && (
                <div className="section-citations-tray">
                  <span className="citations-tray-label">Grounded Sources:</span>
                  <div className="citation-pills-wrap">
                    {section.citations.map((cit, citIdx) => {
                      const globalIdx = allCitations.findIndex(
                        (c) =>
                          c.document_id === cit.document_id &&
                          c.page_number === cit.page_number &&
                          c.verbatim_quote === cit.verbatim_quote
                      );
                      const displayIdx = globalIdx >= 0 ? globalIdx : citIdx;

                      return (
                        <button
                          key={citIdx}
                          type="button"
                          className="citation-pill"
                          onClick={() => onOpenCitation(cit, displayIdx, allCitations.length)}
                          title={`Inspect source quote on Page ${cit.page_number} of ${cit.document_filename}`}
                        >
                          <svg className="pill-doc-svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                            <polyline points="14 2 14 8 20 8" />
                          </svg>
                          <span className="pill-filename">{cit.document_filename}</span>
                          <span className="pill-page">p.{cit.page_number}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </article>
        ))}
      </div>

      {/* Limitations Card */}
      {report.limitations && (
        <section className="rag-limitations-card">
          <div className="limitations-header">
            <span className="limitation-icon" aria-hidden="true">ⓘ</span>
            <h4>Scope & Analytical Limitations</h4>
          </div>
          <p className="limitations-body">{sanitizeText(report.limitations)}</p>
        </section>
      )}
    </div>
  );
}
