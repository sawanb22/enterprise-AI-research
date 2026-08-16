import { DocumentItem, PageCitation, RAGReport } from "../api";
import { DocumentList } from "./DocumentList";
import { DocumentUpload } from "./DocumentUpload";
import { RAGReportView } from "./RAGReportView";
import { formatDateTime } from "../utils/textUtils";

export type RAGTabKey = "report" | "vault" | "telemetry" | "history";

interface RAGWorkspaceTabsProps {
  activeTab: RAGTabKey;
  onSelectTab: (tab: RAGTabKey) => void;
  report: RAGReport | null;
  pastReports: RAGReport[];
  documents: DocumentItem[];
  totalPages?: number;
  maxPagesLimit?: number;
  remainingPages?: number;
  docsLoading: boolean;
  onUploadDoc: (file: File) => Promise<void>;
  onDeleteDoc: (docId: string) => Promise<void>;
  onRefreshDocs: () => void;
  onSelectPastReport: (report: RAGReport) => void;
  onOpenCitation: (citation: PageCitation, index: number, total: number) => void;
}

export function RAGWorkspaceTabs({
  activeTab,
  onSelectTab,
  report,
  pastReports,
  documents,
  totalPages = 0,
  maxPagesLimit = 10,
  remainingPages = 10,
  docsLoading,
  onUploadDoc,
  onDeleteDoc,
  onRefreshDocs,
  onSelectPastReport,
  onOpenCitation,
}: RAGWorkspaceTabsProps) {
  const readyDocsCount = documents.filter((d) => d.status === "ready").length;

  return (
    <div className="rag-workspace-tabs-container">
      {/* Modern Segmented Navigation Bar */}
      <nav className="tabs-nav-bar rag-nav-bar" role="tablist" aria-label="Document RAG Views">
        <button
          type="button"
          role="tab"
          id="tab-rag-report"
          aria-selected={activeTab === "report"}
          aria-controls="panel-rag-report"
          className={`tab-btn ${activeTab === "report" ? "active" : ""}`}
          onClick={() => onSelectTab("report")}
        >
          <span className="tab-icon" aria-hidden="true">📊</span>
          <span>Grounded Report</span>
          {report && <span className="tab-count-badge">{report.sections.length} sections</span>}
        </button>

        <button
          type="button"
          role="tab"
          id="tab-rag-vault"
          aria-selected={activeTab === "vault"}
          aria-controls="panel-rag-vault"
          className={`tab-btn ${activeTab === "vault" ? "active" : ""}`}
          onClick={() => onSelectTab("vault")}
        >
          <span className="tab-icon" aria-hidden="true">📚</span>
          <span>Knowledge Vault</span>
          <span className="tab-count-badge">{documents.length}</span>
        </button>

        <button
          type="button"
          role="tab"
          id="tab-rag-telemetry"
          aria-selected={activeTab === "telemetry"}
          aria-controls="panel-rag-telemetry"
          className={`tab-btn ${activeTab === "telemetry" ? "active" : ""}`}
          onClick={() => onSelectTab("telemetry")}
        >
          <span className="tab-icon" aria-hidden="true">🎯</span>
          <span>Vector Telemetry</span>
          {readyDocsCount > 0 && <span className="tab-count-badge green-badge">Active</span>}
        </button>

        <button
          type="button"
          role="tab"
          id="tab-rag-history"
          aria-selected={activeTab === "history"}
          aria-controls="panel-rag-history"
          className={`tab-btn ${activeTab === "history" ? "active" : ""}`}
          onClick={() => onSelectTab("history")}
        >
          <span className="tab-icon" aria-hidden="true">⏱</span>
          <span>Report Archive</span>
          {pastReports.length > 0 && <span className="tab-count-badge">{pastReports.length}</span>}
        </button>
      </nav>

      {/* Tab Panels */}
      <div className="tab-panels-wrapper">
        {/* Tab 1: Grounded Report */}
        {activeTab === "report" && (
          <div
            id="panel-rag-report"
            role="tabpanel"
            aria-labelledby="tab-rag-report"
            className="tab-panel"
          >
            {report ? (
              <RAGReportView report={report} onOpenCitation={onOpenCitation} />
            ) : (
              <div className="rag-empty-report-state">
                <div className="empty-graphic" aria-hidden="true">📑</div>
                <h3>No RAG Report Generated Yet</h3>
                <p>
                  {readyDocsCount > 0
                    ? `You have ${readyDocsCount} indexed PDF document(s) ready. Enter a question above and click "Synthesize RAG Report" to generate an auditable multi-section briefing.`
                    : 'Upload at least one PDF in the "Knowledge Vault" tab to enable vector-grounded RAG research.'}
                </p>
                {readyDocsCount === 0 && (
                  <button
                    type="button"
                    className="go-to-vault-btn"
                    onClick={() => onSelectTab("vault")}
                  >
                    Open Knowledge Vault →
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Knowledge Vault */}
        {activeTab === "vault" && (
          <div
            id="panel-rag-vault"
            role="tabpanel"
            aria-labelledby="tab-rag-vault"
            className="tab-panel vault-panel"
          >
            <DocumentUpload
              onUpload={onUploadDoc}
              totalPages={totalPages}
              maxPagesLimit={maxPagesLimit}
              remainingPages={remainingPages}
            />
            <DocumentList
              documents={documents}
              totalPages={totalPages}
              maxPagesLimit={maxPagesLimit}
              remainingPages={remainingPages}
              loading={docsLoading}
              onDelete={onDeleteDoc}
              onRefresh={onRefreshDocs}
            />
          </div>
        )}

        {/* Tab 3: Vector Telemetry */}
        {activeTab === "telemetry" && (
          <div
            id="panel-rag-telemetry"
            role="tabpanel"
            aria-labelledby="tab-rag-telemetry"
            className="tab-panel telemetry-panel"
          >
            <div className="telemetry-grid">
              <div className="telemetry-card">
                <div className="telemetry-header">
                  <span className="telemetry-label">EMBEDDING PIPELINE</span>
                  <span className="telemetry-status live">Active</span>
                </div>
                <h4>Bedrock Cohere Embed-v3</h4>
                <p className="telemetry-detail">
                  Dimensions: <b>1024-dim</b> · Batch Limit: <b>96 chunks</b> · Truncate: <b>END</b>
                </p>
                <div className="telemetry-bar">
                  <div className="telemetry-bar-fill" style={{ width: "100%" }} />
                </div>
              </div>

              <div className="telemetry-card">
                <div className="telemetry-header">
                  <span className="telemetry-label">VECTOR INDEX</span>
                  <span className="telemetry-status live">pgvector HNSW</span>
                </div>
                <h4>Supabase PostgreSQL 17</h4>
                <p className="telemetry-detail">
                  Indexed Chunks: <b>{documents.reduce((acc, d) => acc + (d.page_count ? d.page_count * 2 : 0), 0)} est.</b> · Distance: <b>Cosine ($\Leftrightarrow$)</b>
                </p>
                <div className="telemetry-bar">
                  <div className="telemetry-bar-fill green" style={{ width: "100%" }} />
                </div>
              </div>

              <div className="telemetry-card">
                <div className="telemetry-header">
                  <span className="telemetry-label">CROSS-ENCODER RERANKER</span>
                  <span className="telemetry-status live">ONNX Runtime</span>
                </div>
                <h4>FlashRank ms-marco-TinyBERT</h4>
                <p className="telemetry-detail">
                  Candidate Top-K: <b>50</b> · Synthesizer Top-K: <b>15</b> · Sub-15ms Scoring
                </p>
                <div className="telemetry-bar">
                  <div className="telemetry-bar-fill blue" style={{ width: "100%" }} />
                </div>
              </div>

              <div className="telemetry-card">
                <div className="telemetry-header">
                  <span className="telemetry-label">PROVENANCE GATE</span>
                  <span className="telemetry-status live">Strict Filter</span>
                </div>
                <h4>Verbatim Quote Matcher</h4>
                <p className="telemetry-detail">
                  Zero Hallucination Tolerance · Normalized Substring Match · Page-Linked
                </p>
                <div className="telemetry-bar">
                  <div className="telemetry-bar-fill purple" style={{ width: "100%" }} />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Past Reports Archive */}
        {activeTab === "history" && (
          <div
            id="panel-rag-history"
            role="tabpanel"
            aria-labelledby="tab-rag-history"
            className="tab-panel history-panel"
          >
            {pastReports.length === 0 ? (
              <div className="rag-empty-report-state">
                <h4>No Archived Reports</h4>
                <p>Synthesize your first research briefing to populate the archive.</p>
              </div>
            ) : (
              <div className="rag-history-list">
                {pastReports.map((pRep) => (
                  <article key={pRep.id} className="rag-history-item">
                    <div className="history-item-top">
                      <h4 className="history-question">{pRep.question}</h4>
                      <span className="history-date">{formatDateTime(pRep.created_at)}</span>
                    </div>
                    <p className="history-summary">{pRep.summary.slice(0, 160)}…</p>
                    <div className="history-item-footer">
                      <span className="history-sources-tag">
                        {pRep.total_sources_cited} citations · {pRep.sections.length} sections
                      </span>
                      <button
                        type="button"
                        className="load-report-btn"
                        onClick={() => {
                          onSelectPastReport(pRep);
                          onSelectTab("report");
                        }}
                      >
                        Open Briefing →
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
