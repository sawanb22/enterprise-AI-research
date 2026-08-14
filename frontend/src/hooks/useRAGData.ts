import { useCallback, useEffect, useState } from "react";
import { api, DocumentItem, PageCitation, RAGReport } from "../api";
import { RAGTabKey } from "../components/RAGWorkspaceTabs";

export function useRAGData(activeProjectId?: string) {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [report, setReport] = useState<RAGReport | null>(null);
  const [pastReports, setPastReports] = useState<RAGReport[]>([]);
  const [ragLoading, setRagLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<RAGTabKey>("vault");

  // Citation Deep-Dive Drawer state
  const [activeCitation, setActiveCitation] = useState<PageCitation | null>(null);
  const [activeCitationIndex, setActiveCitationIndex] = useState<number>(0);
  const [totalCitations, setTotalCitations] = useState<number>(0);
  const [allReportCitations, setAllReportCitations] = useState<PageCitation[]>([]);

  // Refresh documents for project
  const refreshDocuments = useCallback(async (projectId?: string) => {
    const pid = projectId ?? activeProjectId;
    if (!pid) return;
    try {
      setDocsLoading(true);
      const res = await api.projectDocuments(pid);
      setDocuments(res.documents);
    } catch {
      // Silently catch in polling
    } finally {
      setDocsLoading(false);
    }
  }, [activeProjectId]);

  // Refresh past reports for project
  const refreshReports = useCallback(async (projectId?: string) => {
    const pid = projectId ?? activeProjectId;
    if (!pid) return;
    try {
      const res = await api.projectRAGReports(pid);
      setPastReports(res.reports);
      if (res.reports.length > 0 && !report) {
        setReport(res.reports[0]);
      }
    } catch {
      // Silently catch
    }
  }, [activeProjectId, report]);

  // Initial load when activeProjectId changes
  useEffect(() => {
    if (activeProjectId) {
      void refreshDocuments(activeProjectId);
      void refreshReports(activeProjectId);
    } else {
      setDocuments([]);
      setPastReports([]);
      setReport(null);
    }
  }, [activeProjectId, refreshDocuments, refreshReports]);

  // Auto-poll while any document is in pending or processing status
  useEffect(() => {
    const hasActiveProcessing = documents.some(
      (d) => d.status === "pending" || d.status === "processing"
    );

    if (!hasActiveProcessing || !activeProjectId) return;

    const interval = setInterval(() => {
      void refreshDocuments(activeProjectId);
    }, 2000);

    return () => clearInterval(interval);
  }, [documents, activeProjectId, refreshDocuments]);

  // Upload document
  const uploadDocument = useCallback(
    async (file: File) => {
      if (!activeProjectId) {
        throw new Error("Select or create a project before uploading documents.");
      }
      await api.uploadDocument(activeProjectId, file);
      await refreshDocuments(activeProjectId);
    },
    [activeProjectId, refreshDocuments]
  );

  // Delete document
  const deleteDocument = useCallback(
    async (docId: string) => {
      await api.deleteDocument(docId);
      if (activeProjectId) {
        await refreshDocuments(activeProjectId);
      }
    },
    [activeProjectId, refreshDocuments]
  );

  // Execute RAG Research
  const executeRAG = useCallback(
    async (question: string) => {
      if (!activeProjectId) {
        throw new Error("Select or create a project first.");
      }
      setRagLoading(true);
      try {
        const generated = await api.ragResearch(activeProjectId, question);
        setReport(generated);
        setActiveTab("report");
        await refreshReports(activeProjectId);
        return generated;
      } finally {
        setRagLoading(false);
      }
    },
    [activeProjectId, refreshReports]
  );

  // Update citation list when report changes
  useEffect(() => {
    if (report) {
      const cits: PageCitation[] = [];
      report.sections.forEach((sec) => {
        sec.citations.forEach((c) => cits.push(c));
      });
      setAllReportCitations(cits);
    } else {
      setAllReportCitations([]);
    }
  }, [report]);

  // Citation Drawer controls
  const openCitation = useCallback((citation: PageCitation, index: number, total: number) => {
    setActiveCitation(citation);
    setActiveCitationIndex(index);
    setTotalCitations(total);
  }, []);

  const closeCitation = useCallback(() => {
    setActiveCitation(null);
  }, []);

  const nextCitation = useCallback(() => {
    if (activeCitationIndex < allReportCitations.length - 1) {
      const nextIdx = activeCitationIndex + 1;
      setActiveCitation(allReportCitations[nextIdx]);
      setActiveCitationIndex(nextIdx);
    }
  }, [activeCitationIndex, allReportCitations]);

  const prevCitation = useCallback(() => {
    if (activeCitationIndex > 0) {
      const prevIdx = activeCitationIndex - 1;
      setActiveCitation(allReportCitations[prevIdx]);
      setActiveCitationIndex(prevIdx);
    }
  }, [activeCitationIndex, allReportCitations]);

  return {
    documents,
    docsLoading,
    report,
    setReport,
    pastReports,
    ragLoading,
    activeTab,
    setActiveTab,
    activeCitation,
    activeCitationIndex,
    totalCitations,
    uploadDocument,
    deleteDocument,
    refreshDocuments: () => refreshDocuments(activeProjectId),
    executeRAG,
    openCitation,
    closeCitation,
    nextCitation,
    prevCitation,
    hasNextCitation: activeCitationIndex < allReportCitations.length - 1,
    hasPrevCitation: activeCitationIndex > 0,
  };
}
