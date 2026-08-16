import { useMemo, useState } from "react";
import { Source } from "../api";
import { formatDateTime, pretty, sanitizeText, sanitizeUrl } from "../utils/textUtils";

interface SourcesCardProps {
  sources: Source[];
}

export function SourcesCard({ sources }: SourcesCardProps) {
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [publisherFilter, setPublisherFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"newest" | "publisher" | "title">("newest");
  const [searchQuery, setSearchQuery] = useState("");

  const uniquePublishers = useMemo(() => {
    const set = new Set<string>();
    sources.forEach((s) => {
      if (s.publisher?.trim()) set.add(s.publisher.trim());
    });
    return Array.from(set).sort();
  }, [sources]);

  const filteredSources = useMemo(() => {
    let result = [...sources];

    // Status filter
    if (statusFilter === "fetched") {
      result = result.filter((s) => s.fetch_status === "fetched" || !s.fetch_status);
    } else if (statusFilter === "failed") {
      result = result.filter((s) => s.fetch_status === "failed");
    }

    // Publisher filter
    if (publisherFilter !== "all") {
      result = result.filter((s) => s.publisher?.trim() === publisherFilter);
    }

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (s) =>
          (s.title && s.title.toLowerCase().includes(q)) ||
          (s.publisher && s.publisher.toLowerCase().includes(q)) ||
          (s.canonical_url && s.canonical_url.toLowerCase().includes(q))
      );
    }

    // Sort
    result.sort((a, b) => {
      if (sortBy === "publisher") {
        return (a.publisher || "").localeCompare(b.publisher || "");
      }
      if (sortBy === "title") {
        return (a.title || "").localeCompare(b.title || "");
      }
      // newest
      const aTime = a.retrieved_at ? new Date(a.retrieved_at).getTime() : 0;
      const bTime = b.retrieved_at ? new Date(b.retrieved_at).getTime() : 0;
      return bTime - aTime;
    });

    return result;
  }, [sources, statusFilter, publisherFilter, searchQuery, sortBy]);

  return (
    <div className="card sources-card" aria-label="Retrieved Source Snapshots">
      <div className="section-title">
        <div>
          <p className="eyebrow">KNOWLEDGE BASE</p>
          <h2>Source snapshots</h2>
        </div>
        <span className="muted">
          {filteredSources.length} of {sources.length} snapshots
        </span>
      </div>

      {sources.length > 0 && (
        <div className="filter-controls-bar">
          <div className="filter-group">
            <input
              type="text"
              className="filter-search-input"
              placeholder="Filter sources..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Filter sources by title or url"
            />
          </div>

          <div className="filter-selects">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              aria-label="Filter by fetch status"
            >
              <option value="all">All statuses</option>
              <option value="fetched">Fetched successfully</option>
              <option value="failed">Fetch failed</option>
            </select>

            {uniquePublishers.length > 1 && (
              <select
                value={publisherFilter}
                onChange={(e) => setPublisherFilter(e.target.value)}
                aria-label="Filter by publisher"
              >
                <option value="all">All publishers ({uniquePublishers.length})</option>
                {uniquePublishers.map((pub) => (
                  <option key={pub} value={pub}>
                    {pub}
                  </option>
                ))}
              </select>
            )}

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as "newest" | "publisher" | "title")}
              aria-label="Sort sources by"
            >
              <option value="newest">Sort: Newest first</option>
              <option value="publisher">Sort: Publisher</option>
              <option value="title">Sort: Title</option>
            </select>
          </div>
        </div>
      )}

      <div className="source-list" role="list">
        {filteredSources.map((source) => {
          const isFailed = source.fetch_status === "failed";
          const title = sanitizeText(source.title || source.publisher || "Untitled source");

          return (
            <a
              className={`source ${isFailed ? "failed-source" : ""}`}
              href={sanitizeUrl(source.canonical_url)}
              key={source.id}
              target="_blank"
              rel="noreferrer"
              role="listitem"
              aria-label={`${title}, Publisher: ${source.publisher || "Unknown"}, Status: ${
                source.fetch_status || "fetched"
              }`}
            >
              <div className="source-top-row">
                <span className="source-title-text">{title}</span>
                <span className="source-ext-icon" aria-hidden="true">↗</span>
              </div>
              <div className="source-meta-row">
                <span className="source-publisher">{sanitizeText(source.publisher) || "Web snapshot"}</span>
                <span className="bullet">·</span>
                <span className={`source-status-badge ${source.fetch_status || "fetched"}`}>
                  {pretty(source.fetch_status || "fetched")}
                </span>
                {source.retrieved_at && (
                  <>
                    <span className="bullet">·</span>
                    <time className="source-time" dateTime={source.retrieved_at}>
                      {formatDateTime(source.retrieved_at)}
                    </time>
                  </>
                )}
              </div>
            </a>
          );
        })}

        {!filteredSources.length && (
          <p className="empty">
            {sources.length === 0
              ? "Saved source snapshots will appear here as the discovery engine explores."
              : "No sources match the selected filters."}
          </p>
        )}
      </div>
    </div>
  );
}
