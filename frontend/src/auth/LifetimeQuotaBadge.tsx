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
      className={`celestial-quota-badge ${isExhausted ? "exhausted" : ""} ${compact ? "compact" : ""}`}
      onClick={handleClick}
      title={
        user
          ? `Pilot Mission: ${remaining}/${maxRuns} Research Stars Remaining across Web & Document RAG.`
          : "Sign in to activate your 5 Free Research Stars!"
      }
      aria-label="Pilot Research Stars Quota"
    >
      <div className="celestial-stars-row">
        {Array.from({ length: maxRuns }).map((_, idx) => {
          const isAvailable = idx < remaining;
          return (
            <span
              key={idx}
              className={`celestial-star-orb ${isAvailable ? "active" : "spent"}`}
            >
              ★
            </span>
          );
        })}
      </div>

      <div className="celestial-quota-text">
        <span className="celestial-quota-count">
          {user ? `${remaining}/${maxRuns}` : "5/5"}
        </span>
        <span className="celestial-quota-label">
          {isExhausted ? "Limit Reached" : "Research Stars"}
        </span>
      </div>
    </button>
  );
}
