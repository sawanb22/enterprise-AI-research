import { useState } from "react";
import { PageCitation, RAGReport } from "../api";
import { CleanDocumentView } from "./CleanDocumentView";
import { AuditorReportView } from "./AuditorReportView";
import { formatDateTime, sanitizeText } from "../utils/textUtils";

interface RAGReportViewProps {
  report: RAGReport;
  onOpenCitation: (citation: PageCitation, index: number, total: number) => void;
}

export function RAGReportView({ report, onOpenCitation }: RAGReportViewProps) {
  const [viewMode, setViewMode] = useState<"clean" | "auditor">("clean");
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
      md += `### ${idx + 1}. ${sec.heading}\n\n${sec.content}\n\n`;
      if (sec.citations.length > 0) {
        md += `*Sources & Evidence:*\n`;
        sec.citations.forEach((cit) => {
          md += `- **[${cit.document_filename}, p.${cit.page_number}]**: "${cit.verbatim_quote}"\n`;
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

  const handleExportMarkdownFile = () => {
    let md = `# Executive Research Briefing: ${report.question}\n\n`;
    md += `*Generated:* ${formatDateTime(report.created_at)} | *Sources Cited:* ${report.total_sources_cited}\n\n`;
    md += `## Executive Summary\n${report.summary}\n\n`;

    report.sections.forEach((sec, idx) => {
      md += `### ${idx + 1}. ${sec.heading}\n\n${sec.content}\n\n`;
      if (sec.citations.length > 0) {
        md += `*Sources:*\n`;
        sec.citations.forEach((cit) => {
          md += `- [${cit.document_filename}, Page ${cit.page_number}]: "${cit.verbatim_quote}"\n`;
        });
        md += `\n`;
      }
    });

    if (report.limitations) {
      md += `## Scope & Limitations\n${report.limitations}\n`;
    }

    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `Research_Briefing_${new Date().toISOString().slice(0, 10)}.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="rag-report-container">
      {/* Top Report Action & Mode Bar */}
      <div className="report-action-toolbar">
        <div className="report-view-mode-toggle" role="group" aria-label="Report Display Mode">
          <button
            type="button"
            className={`view-mode-btn ${viewMode === "clean" ? "active" : ""}`}
            onClick={() => setViewMode("clean")}
          >
            <span className="mode-icon" aria-hidden="true">📄</span>
            <span>Clean Document</span>
          </button>
          <button
            type="button"
            className={`view-mode-btn ${viewMode === "auditor" ? "active" : ""}`}
            onClick={() => setViewMode("auditor")}
          >
            <span className="mode-icon" aria-hidden="true">🔬</span>
            <span>Auditor Telemetry</span>
          </button>
        </div>

        <div className="report-export-actions">
          <button
            type="button"
            className="report-tool-btn"
            onClick={handleCopyMarkdown}
            title="Copy structured briefing to clipboard"
          >
            {copied ? (
              <>
                <span className="check-icon" aria-hidden="true">✓</span>
                <span>Copied Formatted Text</span>
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
                <span>Copy Text</span>
              </>
            )}
          </button>

          <button
            type="button"
            className="report-tool-btn primary"
            onClick={handleExportMarkdownFile}
            title="Download report as Markdown document"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span>Export .MD</span>
          </button>
        </div>
      </div>

      {/* Main Body */}
      {viewMode === "clean" ? (
        <CleanDocumentView
          report={report}
          allCitations={allCitations}
          onOpenCitation={onOpenCitation}
        />
      ) : (
        <AuditorReportView
          report={report}
          allCitations={allCitations}
          onOpenCitation={onOpenCitation}
        />
      )}
    </div>
  );
}

export default RAGReportView;
