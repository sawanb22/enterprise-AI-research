import { useCallback, useEffect, useMemo, useState } from "react";
import { api, Assessment, Claim, Project, RunDetail, RunEvent, Source, Trace } from "../api";
import { usePolling } from "./usePolling";

export const activeStatuses = new Set([
  "queued",
  "planning",
  "discovering",
  "fetching",
  "extracting",
  "comparing",
  "synthesising",
]);

export function useResearchData() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [run, setRun] = useState<RunDetail | null>(null);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [trace, setTrace] = useState<Trace | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [healthInfo, setHealthInfo] = useState<{
    aiProvider?: string;
    model?: string;
    configured: Record<string, boolean> | null;
  }>({ configured: null });

  const refreshProjects = useCallback(async () => {
    try {
      const data = await api.projects();
      setProjects(data);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load projects.");
      return false;
    }
  }, []);

  const hydrateWebProject = useCallback((data: {
    project: Project;
    run: RunDetail | null;
    sources: Source[];
    claims: Claim[];
    events: RunEvent[];
    assessments: Assessment[];
  }) => {
    if (data.run) {
      setRun(data.run);
      setEvents(data.events || []);
      setSources(data.sources || []);
      setClaims(data.claims || []);
      setAssessments(data.assessments || []);
    }
  }, []);

  const refreshRun = useCallback(async (runId: string) => {
    try {
      const [nextRun, nextEvents, nextSources, nextClaims, nextAssessments] = await Promise.all([
        api.run(runId),
        api.events(runId),
        api.sources(runId),
        api.claims(runId),
        api.assessments(runId),
      ]);
      setRun(nextRun);
      setEvents(nextEvents);
      setSources(nextSources);
      setClaims(nextClaims);
      setAssessments(nextAssessments);
      if (!activeStatuses.has(nextRun.status)) {
        refreshProjects();
      }
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load research run.");
      return false;
    }
  }, [refreshProjects]);

  const isPollingEnabled = Boolean(run && activeStatuses.has(run.status));

  const pollFn = useCallback(async () => {
    if (!run?.id) return true;
    return await refreshRun(run.id);
  }, [run?.id, refreshRun]);

  const { connectionStatus, lastUpdated, isRefreshing, manualRefresh } = usePolling(pollFn, {
    enabled: isPollingEnabled,
    baseIntervalMs: 1800,
  });

  useEffect(() => {
    api
      .health()
      .then((result) =>
        setHealthInfo({
          aiProvider: result.ai_provider,
          model: result.model,
          configured: result.providers_configured,
        })
      )
      .catch(() => setError("Backend is not reachable. Start FastAPI first."));
  }, []);

  const createProject = useCallback(async (question: string) => {
    setError("");
    setTrace(null);
    setLoading(true);
    try {
      const created = await api.createProject(question);
      await refreshRun(created.run_id);
      await refreshProjects();
      return created;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start research.");
      throw err;
    } finally {
      setLoading(false);
    }
  }, [refreshRun, refreshProjects]);

  const openProject = useCallback(async (project: Project) => {
    if (!project.latest_run) return;
    setError("");
    setTrace(null);
    await refreshRun(project.latest_run.id);
  }, [refreshRun]);

  const openRunById = useCallback(async (runId: string) => {
    setError("");
    setTrace(null);
    await refreshRun(runId);
  }, [refreshRun]);

  const openTrace = useCallback(async (conclusionId: string) => {
    try {
      const traceData = await api.trace(conclusionId);
      setTrace(traceData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load evidence trace.");
    }
  }, []);

  const closeTrace = useCallback(() => {
    setTrace(null);
  }, []);

  const retry = useCallback(async () => {
    if (!run) return;
    try {
      const retryRun = await api.retry(run.id);
      setTrace(null);
      await refreshRun(retryRun.id);
      await refreshProjects();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not retry the research run.");
    }
  }, [run, refreshRun, refreshProjects]);

  const completedStages = useMemo(
    () => new Set(events.filter((event) => event.status === "complete").map((event) => event.stage)),
    [events]
  );

  return {
    projects,
    setProjects,
    run,
    events,
    sources,
    claims,
    assessments,
    trace,
    loading,
    error,
    setError,
    healthInfo,
    connectionStatus,
    lastUpdated,
    isRefreshing,
    manualRefresh,
    refreshProjects,
    hydrateWebProject,
    refreshRun,
    createProject,
    openProject,
    openRunById,
    openTrace,
    closeTrace,
    retry,
    completedStages,
    isActiveRun: Boolean(run && activeStatuses.has(run.status)),
  };
}
