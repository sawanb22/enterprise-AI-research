import { useCallback, useEffect, useRef, useState } from "react";

export type ConnectionStatus = "connected" | "reconnecting" | "offline";

interface UsePollingOptions {
  enabled: boolean;
  baseIntervalMs?: number;
  maxIntervalMs?: number;
}

export function usePolling(
  pollFn: () => Promise<boolean | void>,
  { enabled, baseIntervalMs = 1800, maxIntervalMs = 30000 }: UsePollingOptions
) {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connected");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const errorCountRef = useRef(0);
  const pollFnRef = useRef(pollFn);
  pollFnRef.current = pollFn;

  const executePoll = useCallback(async () => {
    try {
      setIsRefreshing(true);
      const res = await pollFnRef.current();
      // If pollFn explicitly returns false, it means request had a network/server failure
      if (res === false) {
        throw new Error("Poll indicated failure");
      }
      errorCountRef.current = 0;
      setConnectionStatus("connected");
      setLastUpdated(new Date());
    } catch {
      errorCountRef.current += 1;
      if (errorCountRef.current >= 4) {
        setConnectionStatus("offline");
      } else {
        setConnectionStatus("reconnecting");
      }
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;

    let timeoutId: number | undefined;
    let isCancelled = false;

    const scheduleNext = () => {
      if (isCancelled) return;
      const failureCount = errorCountRef.current;
      // Exponential backoff with jitter
      const backoffFactor = Math.min(Math.pow(2, failureCount), 16);
      const delay = Math.min(baseIntervalMs * backoffFactor, maxIntervalMs);

      timeoutId = window.setTimeout(async () => {
        if (isCancelled) return;
        await executePoll();
        scheduleNext();
      }, delay);
    };

    // Trigger initial poll immediately
    executePoll().then(() => {
      scheduleNext();
    });

    return () => {
      isCancelled = true;
      if (timeoutId) window.clearTimeout(timeoutId);
    };
  }, [enabled, baseIntervalMs, maxIntervalMs, executePoll]);

  const manualRefresh = useCallback(async () => {
    errorCountRef.current = 0;
    await executePoll();
  }, [executePoll]);

  return {
    connectionStatus,
    lastUpdated,
    isRefreshing,
    manualRefresh,
    setConnectionStatus,
  };
}
