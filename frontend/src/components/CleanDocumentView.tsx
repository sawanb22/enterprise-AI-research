import React from "react";
import { PageCitation, RAGReport } from "../api";
import { formatDateTime, sanitizeText } from "../utils/textUtils";

interface CleanDocumentViewProps {
  report: RAGReport;
  allCitations: PageCitation[];
  onOpenCitation: (citation: PageCitation, index: number, total: number) => void;
}

export function CleanDocumentView({
  report,
  allCitations,
  onOpenCitation,
}: CleanDocumentViewProps) {
  // Deduplicate citations for the clean reference table
  const uniqueCitations: { cit: PageCitation; globalIdx: number; refNum: number }[] = [];
  const seenKeys = new Set<string>();

  allCitations.forEach((cit, idx) => {
    const key = `${cit.document_id}-${cit.page_number}-${cit.verbatim_quote}`;
    if (!seenKeys.has(key)) {
      seenKeys.add(key);
      uniqueCitations.push({
        cit,
        globalIdx: idx,
        refNum: uniqueCitations.length + 1,
      });
    }
  });

  const getCitationRef = (cit: PageCitation): number => {
    const found = uniqueCitations.find(
      (u) =>
        u.cit.document_id === cit.document_id &&
        u.cit.page_number === cit.page_number &&
        u.cit.verbatim_quote === cit.verbatim_quote
    );
    return found ? found.refNum : 1;
  };

  // Helper to render text with clean paragraph structure
  const renderFormattedParagraphs = (text: string, citations: PageCitation[]) => {
    // If text contains numbered items (e.g. "1) ... 2) ..."), split them nicely
    const lines = text.split(/\n+/).filter(Boolean);

    return lines.map((line, lIdx) => {
      // Check if line is a numbered item or bullet
      const isListItem = /^\s*(\d+[\.\)]|\-|\*)\s+/.test(line);

      return (
        <p key={lIdx} className={`clean-doc-paragraph ${isListItem ? "clean-doc-list-item" : ""}`}>
          {sanitizeText(line)}
          {lIdx === lines.length - 1 && citations.length > 0 && (
            <span className="clean-inline-citations">
              {citations.map((c, cIdx) => {
                const refNum = getCitationRef(c);
                const globalIdx = allCitations.findIndex(
                  (ac) =>
                    ac.document_id === c.document_id &&
                    ac.page_number === c.page_number &&
                    ac.verbatim_quote === c.verbatim_quote
                );
                return (
                  <button
                    key={cIdx}
                    type="button"
                    className="clean-superscript-cite"
                    onClick={() => onOpenCitation(c, globalIdx >= 0 ? globalIdx : 0, allCitations.length)}
                    title={`Source: ${c.document_filename} (Page ${c.page_number}) - Click to inspect`}
                  >
                    [{refNum} • p.{c.page_number}]
                  </button>
                );
              })}
            </span>
          )}
        </p>
      );
    });
  };

  return (
    <div className="clean-document-sheet">
      {/* 1. Header & Research Overview */}
      <header className="clean-doc-header">
        <h1 className="clean-doc-title">{sanitizeText(report.question)}</h1>
        <div className="clean-doc-meta">
          <span>Generated on {formatDateTime(report.created_at)}</span>
          <span className="meta-sep">•</span>
          <span>{uniqueCitations.length} Verified Evidence Citations</span>
          <span className="meta-sep">•</span>
          <span>{report.sections.length} Analytical Sections</span>
        </div>
      </header>

      <hr className="clean-doc-divider" />

      {/* 2. Executive Summary */}
      {report.summary && (
        <section className="clean-doc-section">
          <h2 className="clean-section-title">Executive Summary</h2>
          <div className="clean-summary-body">
            <p>{sanitizeText(report.summary)}</p>
          </div>
        </section>
      )}

      {/* 3. Core Structured Findings */}
      <section className="clean-doc-section">
        <h2 className="clean-section-title">Detailed Research Findings</h2>
        <div className="clean-findings-container">
          {report.sections.map((section, secIdx) => (
            <div key={secIdx} className="clean-finding-block">
              <h3 className="clean-finding-heading">
                {secIdx + 1}. {sanitizeText(section.heading)}
              </h3>
              <div className="clean-finding-prose">
                {renderFormattedParagraphs(section.content, section.citations)}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 4. Consolidated Sources & Evidence Table */}
      {uniqueCitations.length > 0 && (
        <section className="clean-doc-section">
          <h2 className="clean-section-title">Sources & Evidence Citations</h2>
          <p className="clean-section-subtitle">
            Every factual assertion is grounded in the source PDF text with verifiable page provenance.
          </p>

          <div className="clean-bibliography-table-wrapper">
            <table className="clean-bibliography-table">
              <thead>
                <tr>
                  <th style={{ width: "45px" }}>Ref</th>
                  <th style={{ width: "220px" }}>Source Document</th>
                  <th style={{ width: "70px" }}>Page</th>
                  <th>Verbatim Quote from Document</th>
                  <th style={{ width: "80px", textAlign: "right" }}>Inspect</th>
                </tr>
              </thead>
              <tbody>
                {uniqueCitations.map(({ cit, globalIdx, refNum }) => (
                  <tr key={refNum} className="clean-biblio-row">
                    <td className="biblio-ref-cell">
                      <span className="biblio-ref-tag">[{refNum}]</span>
                    </td>
                    <td className="biblio-doc-cell" title={cit.document_filename}>
                      <div className="biblio-doc-name">
                        <span className="doc-icon" aria-hidden="true">📄</span>
                        <span className="doc-text">{cit.document_filename}</span>
                      </div>
                    </td>
                    <td className="biblio-page-cell">p. {cit.page_number}</td>
                    <td className="biblio-quote-cell">
                      <blockquote className="biblio-quote">
                        "{sanitizeText(cit.verbatim_quote)}"
                      </blockquote>
                    </td>
                    <td className="biblio-action-cell">
                      <button
                        type="button"
                        className="biblio-inspect-btn"
                        onClick={() => onOpenCitation(cit, globalIdx, allCitations.length)}
                      >
                        Inspect →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* 5. Scope & Analytical Context */}
      {report.limitations && (
        <section className="clean-doc-section clean-doc-limitations">
          <h2 className="clean-section-title">Scope & Analytical Boundaries</h2>
          <p className="clean-limitations-text">{sanitizeText(report.limitations)}</p>
        </section>
      )}
    </div>
  );
}
