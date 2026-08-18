import React, { useState } from "react";
import { Claim, RunDetail, Source } from "../api";
import { formatDateTime, pretty, sanitizeText } from "../utils/textUtils";

interface WebReportToolbarProps {
  run: RunDetail;
  sources: Source[];
  claims: Claim[];
  viewMode: "clean" | "tabs";
  onToggleMode: (mode: "clean" | "tabs") => void;
}

export function WebReportToolbar({
  run,
  sources,
  claims,
  viewMode,
  onToggleMode,
}: WebReportToolbarProps) {
  const [copied, setCopied] = useState(false);

  const generateMarkdown = () => {
    let md = `# Executive Web Intelligence Briefing: ${run.question}\n\n`;
    md += `*Generated on ${formatDateTime(run.completed_at || run.started_at)} • ${sources.length} Verified Sources • Grounded Multi-Source Synthesis*\n\n`;

    md += `## Key Findings\n\n`;
    run.conclusions.forEach((c, idx) => {
      md += `### ${idx + 1}. ${c.statement}\n\n`;
    });

    if (sources.length > 0) {
      md += `## Verified Web Sources\n\n`;
      sources.forEach((s, idx) => {
        md += `${idx + 1}. [${s.title || s.canonical_url}](${s.canonical_url}) (${pretty(s.source_type || "web")})\n`;
      });
      md += `\n`;
    }

    md += `---\n*EvidenceLab synthesized this structured briefing from ${sources.length} authoritative web sources across public research.*\n`;

    return md;
  };

  const handleCopyMarkdown = () => {
    const md = generateMarkdown();
    navigator.clipboard.writeText(md).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  };

  const handleExportMarkdown = () => {
    const md = generateMarkdown();
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `Web_Intelligence_Briefing_${new Date().toISOString().slice(0, 10)}.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="report-action-toolbar web-toolbar">
      <div className="report-view-mode-toggle" role="group" aria-label="Web Report Display Mode">
        <button
          type="button"
          className={`view-mode-btn ${viewMode === "clean" ? "active" : ""}`}
          onClick={() => onToggleMode("clean")}
        >
          <span className="mode-icon" aria-hidden="true">📄</span>
          <span>Clean Executive Report</span>
        </button>
        <button
          type="button"
          className={`view-mode-btn ${viewMode === "tabs" ? "active" : ""}`}
          onClick={() => onToggleMode("tabs")}
        >
          <span className="mode-icon" aria-hidden="true">🔬</span>
          <span>Detailed Tabs View</span>
        </button>
      </div>

      <div className="report-export-actions">
        <button
          type="button"
          className="report-tool-btn"
          onClick={handleCopyMarkdown}
          title="Copy formatted briefing to clipboard"
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
          onClick={handleExportMarkdown}
          title="Download briefing as Markdown document"
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
  );
}
