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
        <span className="quota-icon" aria-hidden="true">⚡</span>
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
