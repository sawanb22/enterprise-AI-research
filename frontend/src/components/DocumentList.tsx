import { DocumentItem } from "../api";
import { formatDateTime } from "../utils/textUtils";

interface DocumentListProps {
  documents: DocumentItem[];
  loading?: boolean;
  totalPages?: number;
  maxPagesLimit?: number;
  remainingPages?: number;
  onDelete?: (documentId: string) => Promise<unknown>;
  onRefresh?: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function DocumentList({
  documents,
  loading = false,
  totalPages = 0,
  maxPagesLimit = 10,
  remainingPages = 10,
  onDelete,
  onRefresh,
}: DocumentListProps) {
  return (
    <div className="doc-list-container">
      <div className="doc-list-header">
        <div className="doc-list-title-row">
          <div className="doc-list-title-box">
            <span className="section-eyebrow">INDEXED CORPUS</span>
            <div className="doc-list-title-with-badge">
              <h3>Document Repository ({documents.length})</h3>
              <span className={`pilot-list-quota-badge ${totalPages >= maxPagesLimit ? "full" : ""}`}>
                {totalPages}/{maxPagesLimit} pages
              </span>
            </div>
          </div>
          {onRefresh && (
            <button
              type="button"
              className="refresh-vault-btn"
              onClick={onRefresh}
              title="Refresh repository status"
              disabled={loading}
            >
              <svg
                className={`refresh-icon ${loading ? "spinning" : ""}`}
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M23 4v6h-6M1 20v-6h6" />
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
              </svg>
              <span>Sync</span>
            </button>
          )}
        </div>
      </div>

      {documents.length === 0 ? (
        <div className="doc-empty-state">
          <div className="empty-vault-icon" aria-hidden="true">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
          </div>
          <h4>No documents ingested in this project yet</h4>
          <p>
            Upload research papers, PDF reports, or documentation above. The vector engine will parse,
            chunk, extract tables, and generate 1024-dim embeddings for sub-second RAG synthesis.
          </p>
        </div>
      ) : (
        <div className="doc-card-grid">
          {documents.map((doc) => (
            <article key={doc.id} className={`doc-card status-${doc.status}`}>
              <div className="doc-card-top">
                <div className="doc-file-info">
                  <div className="pdf-icon-badge" aria-hidden="true">
                    <span>PDF</span>
                  </div>
                  <div className="doc-file-meta">
                    <h4 className="doc-filename" title={doc.filename}>
                      {doc.filename}
                    </h4>
                    <span className="doc-submeta">
                      {formatBytes(doc.file_size_bytes)}
                      {doc.page_count ? ` • ${doc.page_count} ${doc.page_count === 1 ? "page" : "pages"}` : ""}
                    </span>
                  </div>
                </div>

                <span className={`doc-status-badge ${doc.status}`}>
                  <span className="doc-status-dot" aria-hidden="true" />
                  <span>{doc.status}</span>
                </span>
              </div>

              {doc.error_message && (
                <div className="doc-error-banner">
                  <span>Error: {doc.error_message}</span>
                </div>
              )}

              <div className="doc-card-footer">
                <div className="doc-hash-pill" title={`SHA-256: ${doc.file_hash}`}>
                  <span className="hash-label">HASH:</span>
                  <span className="hash-val">{doc.file_hash.slice(0, 10)}…</span>
                </div>

                <div className="doc-actions">
                  <span className="doc-time">{formatDateTime(doc.created_at)}</span>
                  {onDelete && (
                    <button
                      type="button"
                      className="doc-delete-btn"
                      onClick={() => {
                        if (confirm(`Remove "${doc.filename}" from the project knowledge base?`)) {
                          void onDelete(doc.id);
                        }
                      }}
                      title="Remove document"
                      aria-label={`Delete ${doc.filename}`}
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
