import { ChangeEvent, DragEvent, useRef, useState } from "react";

interface DocumentUploadProps {
  onUpload: (file: File) => Promise<unknown>;
  onReplace?: (file: File) => Promise<unknown>;
  disabled?: boolean;
  totalPages?: number;
  maxPagesLimit?: number;
  remainingPages?: number;
  hasDocuments?: boolean;
}

export function DocumentUpload({
  onUpload,
  onReplace,
  disabled,
  totalPages = 0,
  maxPagesLimit = 10,
  remainingPages = 10,
  hasDocuments = false,
}: DocumentUploadProps) {
  const isQuotaFull = totalPages >= maxPagesLimit || remainingPages <= 0;
  const isUploadDisabled = disabled;
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndUpload = async (file: File) => {
    setUploadError(null);

    // Validate MIME / extension
    if (!file.name.toLowerCase().endsWith(".pdf") && file.type !== "application/pdf") {
      setUploadError("Only PDF documents are supported for enterprise RAG indexing.");
      return;
    }

    // Validate size (max 50 MB)
    const maxSizeBytes = 50 * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setUploadError(`File exceeds maximum size of 50 MB (${(file.size / (1024 * 1024)).toFixed(1)} MB).`);
      return;
    }

    setSelectedFileName(file.name);
    setIsUploading(true);

    try {
      if (isQuotaFull && onReplace) {
        await onReplace(file);
      } else {
        await onUpload(file);
      }
      setSelectedFileName(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to upload document.";
      setUploadError(message);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isUploadDisabled && !isUploading) {
      setIsDragOver(true);
    }
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (isUploadDisabled || isUploading) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      void validateAndUpload(file);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      void validateAndUpload(file);
    }
  };

  const quotaPercent = Math.min(100, Math.round((totalPages / maxPagesLimit) * 100));

  return (
    <div className="doc-upload-container">
      {/* Pilot Quota Gauge Header */}
      <div className="pilot-quota-card" role="region" aria-label="Pilot Ingestion Quota">
        <div className="pilot-quota-header">
          <div className="pilot-quota-title">
            <span className="pilot-badge">PILOT TIER</span>
            <span className="pilot-quota-label">Document Ingestion Quota</span>
          </div>
          <div className="pilot-quota-counter">
            <span className="pages-used">{totalPages}</span>
            <span className="pages-sep">/</span>
            <span className="pages-limit">{maxPagesLimit} pages</span>
            <span className={`pilot-status-pill ${isQuotaFull ? "limit-reached" : "available"}`}>
              {isQuotaFull ? "Quota Reached" : `${remainingPages} left`}
            </span>
          </div>
        </div>
        <div className="pilot-progress-track">
          <div
            className={`pilot-progress-bar ${isQuotaFull ? "full" : ""}`}
            style={{ width: `${quotaPercent}%` }}
            role="progressbar"
            aria-valuenow={totalPages}
            aria-valuemin={0}
            aria-valuemax={maxPagesLimit}
          />
        </div>
        {isQuotaFull && (
          <p className="pilot-quota-warning">
            ✦ Pilot project limit reached ({maxPagesLimit}/{maxPagesLimit} pages). Remove an existing document from the repository to free up ingestion capacity.
          </p>
        )}
      </div>

      <div
        className={`doc-dropzone ${isDragOver ? "drag-over" : ""} ${isUploading ? "uploading" : ""} ${isUploadDisabled ? "disabled" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploadDisabled && !isUploading && fileInputRef.current?.click()}
        role="button"
        tabIndex={isUploadDisabled ? -1 : 0}
        aria-label="Upload PDF Document Dropzone"
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && !isUploadDisabled && !isUploading) {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileChange}
          style={{ display: "none" }}
          disabled={isUploadDisabled || isUploading}
        />

        <div className="dropzone-ambient-glow" aria-hidden="true" />

        <div className="dropzone-content">
          {isUploading ? (
            <div className="upload-state active">
              <div className="cyber-spinner" aria-hidden="true" />
              <div className="upload-meta">
                <p className="upload-title">Ingesting & Vectorizing Document...</p>
                <p className="upload-subtext">{selectedFileName}</p>
              </div>
            </div>
          ) : (
            <div className="upload-state idle">
              <div className="dropzone-icon-box" aria-hidden="true">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="12" y1="18" x2="12" y2="12" />
                  <polyline points="9 15 12 12 15 15" />
                </svg>
              </div>
              <div className="upload-meta">
                <p className="upload-title">
                  {isQuotaFull ? (
                    <span className="quota-full-title"><span className="highlight-action">Click to replace PDF</span> or drop a new document to re-index</span>
                  ) : (
                    <>
                      <span className="highlight-action">Click to upload</span> or drag PDF here
                    </>
                  )}
                </p>
                <p className="upload-subtext">
                  {isQuotaFull
                    ? "Dropping a new PDF will replace existing documents and re-index vector embeddings automatically."
                    : `Max 10 pages per document • ${remainingPages} page allowance remaining in this project`}
                </p>
              </div>
              <div className="vault-tag" aria-hidden="true">
                <span>PDF Knowledge Vault</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {uploadError && (
        <div className="upload-error-alert" role="alert">
          <span className="error-icon" aria-hidden="true">⚠</span>
          <span>{uploadError}</span>
          <button
            type="button"
            className="error-dismiss-btn"
            onClick={() => setUploadError(null)}
            aria-label="Dismiss error"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
