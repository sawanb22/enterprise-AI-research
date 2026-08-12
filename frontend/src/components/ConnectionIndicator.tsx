import { useEffect, useState } from "react";
import { ConnectionStatus } from "../hooks/usePolling";
import { formatRelativeTime } from "../utils/textUtils";

interface ConnectionIndicatorProps {
  status: ConnectionStatus;
  lastUpdated: Date | null;
  isRefreshing?: boolean;
  onRefresh?: () => void;
}

export function ConnectionIndicator({
  status,
  lastUpdated,
  isRefreshing = false,
  onRefresh,
}: ConnectionIndicatorProps) {
  const [, setTick] = useState(0);

  // Update relative time display every 5 seconds
  useEffect(() => {
    const timer = window.setInterval(() => {
      setTick((t) => t + 1);
    }, 5000);
    return () => window.clearInterval(timer);
  }, []);

  const getStatusText = () => {
    switch (status) {
      case "connected":
        return "Connected";
      case "reconnecting":
        return "Reconnecting...";
      case "offline":
        return "Offline";
    }
  };

  return (
    <div
      className={`connection-indicator ${status}`}
      role="status"
      aria-live="polite"
      aria-label={`Connection status: ${getStatusText()}`}
    >
      <span className={`status-indicator-dot ${status} ${isRefreshing ? "refreshing" : ""}`} />
      <span className="connection-label">{getStatusText()}</span>
      {lastUpdated && (
        <span className="last-updated-text">
          · Updated {formatRelativeTime(lastUpdated)}
        </span>
      )}
      {onRefresh && (
        <button
          type="button"
          className="refresh-btn"
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Manual refresh"
          aria-label="Refresh data now"
        >
          {isRefreshing ? "↻" : "↺"}
        </button>
      )}
    </div>
  );
}
