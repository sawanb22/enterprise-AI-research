import React from "react";
import { useAuth } from "./AuthContext";

export function QuotaExceededModal() {
  const { isQuotaModalOpen, closeQuotaModal, quota } = useAuth();

  if (!isQuotaModalOpen) return null;

  const totalUsed = quota?.total_runs_used ?? 5;
  const maxRuns = quota?.max_free_runs ?? 5;

  return (
    <div className="celestial-modal-overlay" onClick={closeQuotaModal}>
      <div
        className="celestial-auth-modal quota-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <button
          type="button"
          className="celestial-modal-close"
          onClick={closeQuotaModal}
          aria-label="Close dialog"
        >
          ✕
        </button>

        <div className="celestial-modal-header">
          <div className="celestial-modal-icon warning">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
          </div>
          <h2 className="celestial-modal-title">Pilot Quota Status</h2>
          <p className="celestial-modal-subtitle">
            You have used <strong>{totalUsed} of {maxRuns}</strong> lifetime research stars.
          </p>
        </div>

        <div className="quota-stars-display">
          {Array.from({ length: maxRuns }).map((_, idx) => {
            const isUsed = idx < totalUsed;
            return (
              <div
                key={idx}
                className={`quota-star-card ${isUsed ? "used" : "available"}`}
              >
                <span className="star-symbol">{isUsed ? "✧" : "★"}</span>
                <span className="star-label">Inquiry #{idx + 1}</span>
                <span className="star-status">{isUsed ? "Consumed" : "Ready"}</span>
              </div>
            );
          })}
        </div>

        <div className="quota-explanation-card">
          <p>
            This prototype is configured as a <strong>pilot evaluation system</strong> with a limit of 5 free lifetime research inquiries across Web Intelligence and Document RAG.
          </p>
          <p className="quota-note">
            All your synthesized conclusions, claims, and documents in your existing projects remain fully accessible to review, export, and inspect anytime.
          </p>
        </div>

        <div className="celestial-modal-footer">
          <button
            type="button"
            className="celestial-auth-submit-btn secondary"
            onClick={closeQuotaModal}
          >
            Understood
          </button>
        </div>
      </div>
    </div>
  );
}
