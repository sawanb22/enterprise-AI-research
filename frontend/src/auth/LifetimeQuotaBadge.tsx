import React from "react";
import { useAuth } from "./AuthContext";

export function LifetimeQuotaBadge({ compact = false }: { compact?: boolean }) {
  const { user, quota, openAuthModal, openQuotaModal } = useAuth();

  const maxRuns = quota?.max_free_runs ?? 5;
  const remaining = user ? (quota?.remaining_runs ?? 5) : 5;
  const used = user ? (quota?.total_runs_used ?? 0) : 0;
  const isExhausted = user ? (quota?.is_quota_exhausted ?? false) : false;

  const handleClick = () => {
    if (!user) {
      openAuthModal("signin");
    } else {
      openQuotaModal();
    }
  };

  return (
    <button
      type="button"
      className={`enterprise-quota-badge ${isExhausted ? "exhausted" : ""} ${compact ? "compact" : ""}`}
      onClick={handleClick}
      title={
        user
          ? `Research Allowance: ${remaining} of ${maxRuns} inquiries remaining.`
          : "Sign in to activate your 5 free research inquiries."
      }
      aria-label="Research Allowance Quota"
    >
      <div className="quota-header-row">
        <svg className="quota-svg-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden="true" style={{ display: "inline-block", verticalAlign: "middle" }}>
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
        </svg>
        <span className="quota-count">
          {user ? `${remaining}/${maxRuns}` : "5/5"}
        </span>
        <span className="quota-label">
          {isExhausted ? "Limit Reached" : "Inquiries Left"}
        </span>
      </div>

      <div className="quota-segments-row" aria-hidden="true">
        {Array.from({ length: maxRuns }).map((_, idx) => {
          const isAvailable = idx < remaining;
          return (
            <span
              key={idx}
              className={`quota-segment ${isAvailable ? "available" : "used"}`}
            />
          );
        })}
      </div>
    </button>
  );
}
