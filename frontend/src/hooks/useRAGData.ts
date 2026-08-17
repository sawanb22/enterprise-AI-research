import { useCallback, useEffect, useState } from "react";
import { ActiveRAGVaultData, api, DocumentItem, PageCitation, RAGReport } from "../api";
import { RAGTabKey } from "../components/RAGWorkspaceTabs";

export function useRAGData(
  activeVaultId?: string,
  onEnsureVault?: (title: string) => Promise<string>
) {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [totalPages, setTotalPages] = useState<number>(0);
  const [maxPagesLimit, setMaxPagesLimit] = useState<number>(10);
  const [remainingPages, setRemainingPages] = useState<number>(10);
  const [docsLoading, setDocsLoading] = useState(false);
  const [report, setReport] = useState<RAGReport | null>(null);
  const [pastReports, setPastReports] = useState<RAGReport[]>([]);
  const [ragVaults, setRagVaults] = useState<{ project_id: string; title: string; created_at: string }[]>([]);
  const [ragLoading, setRagLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<RAGTabKey>("vault");

  // Citation Deep-Dive Drawer state
  const [activeCitation, setActiveCitation] = useState<PageCitation | null>(null);
  const [activeCitationIndex, setActiveCitationIndex] = useState<number>(0);
  const [totalCitations, setTotalCitations] = useState<number>(0);
  const [allReportCitations, setAllReportCitations] = useState<PageCitation[]>([]);

  const refreshVaults = useCallback(async () => {
    try {
      const v = await api.ragVaults();
      setRagVaults(v);
      return v;
    } catch {
      return [];
    }
  }, []);

  const hydrateVaultData = useCallback((data: ActiveRAGVaultData) => {
    setDocuments(data.documents || []);
    setPastReports(data.reports || []);
    setTotalPages(data.total_pages || 0);
    setMaxPagesLimit(data.max_pages_limit || 10);
    setRemainingPages(data.remaining_pages || 10);
    if (data.reports && data.reports.length > 0) {
      setReport(data.reports[0]);
      setActiveTab("report");
    } else if (data.documents && data.documents.length > 0) {
      setActiveTab("vault");
    }
  }, []);

  // Refresh documents for vault
  const refreshDocuments = useCallback(async (vaultId?: string) => {
    const pid = vaultId ?? activeVaultId;
    if (!pid) return;
    try {
      setDocsLoading(true);
      const res = await api.projectDocuments(pid);
      setDocuments(res.documents);
      const pagesCount = res.total_pages ?? res.documents.reduce((acc, d) => acc + (d.page_count || 0), 0);
      const limit = res.max_pages_limit ?? 10;
      setTotalPages(pagesCount);
      setMaxPagesLimit(limit);
      setRemainingPages(res.remaining_pages ?? Math.max(0, limit - pagesCount));
    } catch {
      // Silently catch in polling
    } finally {
      setDocsLoading(false);
    }
  }, [activeVaultId]);

  // Refresh past reports for vault
  const refreshReports = useCallback(async (vaultId?: string) => {
    const pid = vaultId ?? activeVaultId;
    if (!pid) return;
    try {
      const res = await api.projectRAGReports(pid);
      setPastReports(res.reports);
      if (res.reports.length > 0 && !report) {
        setReport(res.reports[0]);
        setActiveTab("report");
      }
    } catch {
      // Silently catch
    }
  }, [activeVaultId, report]);

  const openReportById = useCallback((reportId: string) => {
    const found = pastReports.find((r) => r.id === reportId);
    if (found) {
      setReport(found);
      setActiveTab("report");
    } else {
      api.ragReport(reportId).then((r) => {
        setReport(r);
        setActiveTab("report");
      }).catch(() => {});
    }
  }, [pastReports]);

  // Initial load when activeVaultId changes
  useEffect(() => {
    if (activeVaultId) {
      void refreshDocuments(activeVaultId);
      void refreshReports(activeVaultId);
    }
  }, [activeVaultId, refreshDocuments, refreshReports]);

  // Auto-poll while any document is in pending or processing status
  useEffect(() => {
    const hasActiveProcessing = documents.some(
      (d) => d.status === "pending" || d.status === "processing"
    );

    if (!hasActiveProcessing || !activeVaultId) return;

    const interval = setInterval(() => {
      void refreshDocuments(activeVaultId);
    }, 2000);

    return () => clearInterval(interval);
  }, [documents, activeVaultId, refreshDocuments]);

  // Upload document with automatic workspace creation
  const uploadDocument = useCallback(
    async (file: File) => {
      let targetProjectId = activeVaultId;
      if (!targetProjectId && onEnsureVault) {
        targetProjectId = await onEnsureVault("Document Vault: " + file.name);
      }
      if (!targetProjectId) {
        const created = await api.createRAGVault("Document Vault: " + file.name);
        targetProjectId = created.project_id;
      }
      await api.uploadDocument(targetProjectId, file);
      await refreshVaults();
      await refreshDocuments(targetProjectId);
      return targetProjectId;
    },
    [activeVaultId, onEnsureVault, refreshVaults, refreshDocuments]
  );

  // Replace existing document(s) and re-ingest new document
  const replaceDocument = useCallback(
    async (file: File) => {
      let targetProjectId = activeVaultId;
      if (!targetProjectId && onEnsureVault) {
        targetProjectId = await onEnsureVault("Document Vault: " + file.name);
      }
      if (!targetProjectId) {
        const created = await api.createRAGVault("Document Vault: " + file.name);
        targetProjectId = created.project_id;
      }

      // Clean up previous documents
      if (documents.length > 0) {
        for (const doc of documents) {
          try {
            await api.deleteDocument(doc.id);
          } catch (e) {
            console.warn("Could not delete previous document during replacement:", e);
          }
        }
      }

      await api.uploadDocument(targetProjectId, file);
      await refreshVaults();
      await refreshDocuments(targetProjectId);
      return targetProjectId;
    },
    [activeVaultId, onEnsureVault, documents, refreshVaults, refreshDocuments]
  );

  // Delete document
  const deleteDocument = useCallback(
    async (docId: string) => {
      await api.deleteDocument(docId);
      if (activeVaultId) {
        await refreshDocuments(activeVaultId);
      }
    },
    [activeVaultId, refreshDocuments]
  );

  // Execute RAG Research
  const executeRAG = useCallback(
    async (question: string) => {
      let targetProjectId = activeVaultId;
      if (!targetProjectId && onEnsureVault) {
        targetProjectId = await onEnsureVault("Document Analysis: " + question);
      }
      if (!targetProjectId) {
        throw new Error("Please upload a PDF document before running RAG research.");
      }
      setRagLoading(true);
      try {
        const generated = await api.ragResearch(targetProjectId, question);
        setReport(generated);
        setActiveTab("report");
        await refreshReports(targetProjectId);
        return generated;
      } finally {
        setRagLoading(false);
      }
    },
    [activeVaultId, onEnsureVault, refreshReports]
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
    totalPages,
    maxPagesLimit,
    remainingPages,
    docsLoading,
    report,
    setReport,
    pastReports,
    setPastReports,
    openReportById,
    ragVaults,
    setRagVaults,
    refreshVaults,
    hydrateVaultData,
    ragLoading,
    activeTab,
    setActiveTab,
    activeCitation,
    activeCitationIndex,
    totalCitations,
    uploadDocument,
    replaceDocument,
    deleteDocument,
    refreshDocuments: () => refreshDocuments(activeVaultId),
    executeRAG,
    openCitation,
    closeCitation,
    nextCitation,
    prevCitation,
    hasNextCitation: activeCitationIndex < allReportCitations.length - 1,
    hasPrevCitation: activeCitationIndex > 0,
  };
}
