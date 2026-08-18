import React from "react";
import { Claim, Conclusion, RunDetail, Source } from "../api";
import { formatDateTime, pretty, sanitizeText } from "../utils/textUtils";

interface CleanWebReportViewProps {
  run: RunDetail;
  sources: Source[];
  claims: Claim[];
  onViewEvidence?: (conclusionId: string) => void;
}

export function CleanWebReportView({
  run,
  sources,
}: CleanWebReportViewProps) {
  return (
    <div className="clean-document-sheet web-clean-sheet">
      {/* 1. Header & Research Overview */}
      <header className="clean-doc-header">
        <h1 className="clean-doc-title">{sanitizeText(run.question)}</h1>
        <div className="clean-doc-meta">
          <span>Generated on {formatDateTime(run.completed_at || run.started_at)}</span>
          <span className="meta-sep">•</span>
          <span>{sources.length} Verified Web Sources</span>
          <span className="meta-sep">•</span>
          <span>{run.conclusions.length} Synthesized Key Findings</span>
          <span className="meta-sep">•</span>
          <span>Grounded Multi-Source Synthesis</span>
        </div>
      </header>

      <hr className="clean-doc-divider" />

      {/* 2. Pure Structured Answer & Findings */}
      {run.conclusions.length > 0 && (
        <section className="clean-doc-section">
          <h2 className="clean-section-title">Executive Briefing & Findings</h2>
          <div className="clean-findings-container">
            {run.conclusions.map((conclusion, idx) => (
              <div key={conclusion.id} className="clean-finding-block web-pure-finding">
                <div className="web-pure-finding-row">
                  <span className="web-finding-number">#{idx + 1}</span>
                  <div className="web-finding-content">
                    <p className="web-finding-statement">
                      {sanitizeText(conclusion.statement)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 3. Verified Web Sources & Citations Table */}
      {sources.length > 0 && (
        <section className="clean-doc-section">
          <h2 className="clean-section-title">Verified Web Sources & Citations</h2>
          <p className="clean-section-subtitle">
            Public sources retrieved, analyzed, and cross-compared to ground this briefing.
          </p>

          <div className="clean-bibliography-table-wrapper">
            <table className="clean-bibliography-table">
              <thead>
                <tr>
                  <th className="th-ref">Ref</th>
                  <th className="th-doc">Source Title & Publisher</th>
                  <th className="th-page">Type</th>
                  <th className="th-quote">Canonical Source URL</th>
                  <th className="th-action">Link</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((source, idx) => {
                  const hostname = source.canonical_url
                    ? new URL(source.canonical_url).hostname.replace(/^www\./, "")
                    : "web";

                  return (
                    <tr key={source.id} className="clean-biblio-row">
                      <td className="biblio-ref-cell" data-label="Ref">
                        <span className="biblio-ref-tag">[{idx + 1}]</span>
                      </td>
                      <td className="biblio-doc-cell" data-label="Source">
                        <div className="biblio-doc-name">
                          <svg className="doc-svg-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                            <circle cx="12" cy="12" r="10" />
                            <line x1="2" y1="12" x2="22" y2="12" />
                            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                          </svg>
                          <div>
                            <strong className="web-source-title">
                              {sanitizeText(source.title || hostname)}
                            </strong>
                            {source.publisher && (
                              <span className="web-source-pub"> • {source.publisher}</span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="biblio-page-cell" data-label="Type">{pretty(source.source_type || "web")}</td>
                      <td className="biblio-quote-cell" data-label="URL">
                        <span className="web-canonical-link-text">{source.canonical_url}</span>
                      </td>
                      <td className="biblio-action-cell" data-label="Link">
                        <a
                          href={source.canonical_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="biblio-inspect-btn"
                          title="Open original source in new tab"
                        >
                          Visit ↗
                        </a>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* 4. Methodology Note */}
      <footer className="clean-doc-section clean-doc-limitations">
        <p className="clean-limitations-text">
          EvidenceLab synthesized this structured briefing from {sources.length} authoritative web sources across public digital research. For detailed claim comparison matrices and confidence scores, switch to the <strong>Detailed Tabs View</strong>.
        </p>
      </footer>
    </div>
  );
}
