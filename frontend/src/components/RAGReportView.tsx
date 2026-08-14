import { useState } from "react";
import { PageCitation, RAGReport } from "../api";
import { formatDateTime, pretty, sanitizeText } from "../utils/textUtils";

interface RAGReportViewProps {
  report: RAGReport;
  onOpenCitation: (citation: PageCitation, index: number, total: number) => void;
}

export function RAGReportView({ report, onOpenCitation }: RAGReportViewProps) {
  const [copied, setCopied] = useState(false);

  // Flatten all citations for global indexing
  const allCitations: PageCitation[] = [];
  report.sections.forEach((sec) => {
    sec.citations.forEach((cit) => {
      allCitations.push(cit);
    });
  });

  const handleCopyMarkdown = () => {
    let md = `# Executive Research Briefing: ${report.question}\n\n`;
    md += `**Generated:** ${formatDateTime(report.created_at)} | **Sources Cited:** ${report.total_sources_cited}\n\n`;
    md += `## Executive Summary\n${report.summary}\n\n`;

    report.sections.forEach((sec, idx) => {
      md += `### ${idx + 1}. ${sec.heading} (${sec.confidence.toUpperCase()} CONFIDENCE)\n${sec.content}\n\n`;
      if (sec.citations.length > 0) {
        md += `*Citations:*\n`;
        sec.citations.forEach((cit) => {
          md += `- [${cit.document_filename}, Page ${cit.page_number}]: "${cit.verbatim_quote}"\n`;
        });
        md += `\n`;
      }
    });

    if (report.limitations) {
      md += `## Methodological Limitations & Boundaries\n${report.limitations}\n`;
    }

    navigator.clipboard.writeText(md).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  };

  return (
    <div className="rag-report-container">
      {/* Report Header Card */}
      <section className="rag-report-header-card" aria-label="Executive Briefing Header">
        <div className="report-header-main">
          <div className="report-eyebrow-row">
            <span className="eyebrow-badge">ENTERPRISE GROUNDED BRIEFING</span>
            <span className="report-date-pill">{formatDateTime(report.created_at)}</span>
          </div>
          <h2 className="report-question-title">{sanitizeText(report.question)}</h2>
        </div>

        <div className="report-header-actions">
          <div className="report-stats-grid">
            <div className="stat-pill">
              <span className="stat-num">{report.total_sources_cited}</span>
              <span className="stat-label">Citations</span>
            </div>
            <div className="stat-pill">
              <span className="stat-num">{report.sections.length}</span>
              <span className="stat-label">Sections</span>
            </div>
          </div>

          <button
            type="button"
            className="copy-report-btn"
            onClick={handleCopyMarkdown}
            title="Copy entire briefing to clipboard as Markdown"
          >
            {copied ? (
              <>
                <span className="check-icon" aria-hidden="true">✓</span>
                <span>Copied!</span>
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
                <span>Export MD</span>
              </>
            )}
          </button>
        </div>
      </section>

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
                          <span className="pill-doc-icon" aria-hidden="true">📄</span>
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
