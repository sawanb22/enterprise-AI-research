import { useMemo, useState } from "react";
import { Claim } from "../api";
import { pretty, sanitizeText } from "../utils/textUtils";

interface ClaimsCardProps {
  claims: Claim[];
}

export function ClaimsCard({ claims }: ClaimsCardProps) {
  const [selectedTopic, setSelectedTopic] = useState<string>("all");
  const [selectedConfidence, setSelectedConfidence] = useState<string>("all");
  const [expandedExcerpts, setExpandedExcerpts] = useState<Record<string, boolean>>({});
  const [expandedTopics, setExpandedTopics] = useState<Record<string, boolean>>({});

  const topics = useMemo(() => {
    const map: Record<string, number> = {};
    claims.forEach((c) => {
      const t = c.topic?.trim() || "General";
      map[t] = (map[t] || 0) + 1;
    });
    return map;
  }, [claims]);

  const toggleExcerpt = (claimId: string) => {
    setExpandedExcerpts((prev) => ({ ...prev, [claimId]: !prev[claimId] }));
  };

  const toggleTopicSection = (topic: string) => {
    setExpandedTopics((prev) => ({
      ...prev,
      [topic]: prev[topic] === undefined ? false : !prev[topic],
    }));
  };

  const filteredClaims = useMemo(() => {
    let list = [...claims];
    if (selectedTopic !== "all") {
      list = list.filter((c) => (c.topic?.trim() || "General") === selectedTopic);
    }
    if (selectedConfidence !== "all") {
      list = list.filter((c) => c.confidence === selectedConfidence);
    }
    return list;
  }, [claims, selectedTopic, selectedConfidence]);

  // Group filtered claims by topic
  const groupedByTopic = useMemo(() => {
    const groups: Record<string, Claim[]> = {};
    filteredClaims.forEach((c) => {
      const t = c.topic?.trim() || "General";
      if (!groups[t]) groups[t] = [];
      groups[t].push(c);
    });
    return groups;
  }, [filteredClaims]);

  return (
    <div className="card claims-card" aria-label="Extracted Source-Grounded Claims">
      <div className="section-title">
        <div>
          <p className="eyebrow">EXTRACTED INTELLIGENCE</p>
          <h2>Source-grounded claims</h2>
        </div>
        <span className="muted">
          {filteredClaims.length} of {claims.length} claims
        </span>
      </div>

      {claims.length > 0 && (
        <div className="filter-controls-bar">
          <div className="filter-selects">
            <select
              value={selectedTopic}
              onChange={(e) => setSelectedTopic(e.target.value)}
              aria-label="Filter claims by topic"
            >
              <option value="all">All topics ({Object.keys(topics).length})</option>
              {Object.entries(topics).map(([topic, count]) => (
                <option key={topic} value={topic}>
                  {sanitizeText(topic)} ({count})
                </option>
              ))}
            </select>

            <select
              value={selectedConfidence}
              onChange={(e) => setSelectedConfidence(e.target.value)}
              aria-label="Filter claims by confidence"
            >
              <option value="all">All confidence levels</option>
              <option value="high">High confidence</option>
              <option value="medium">Medium confidence</option>
              <option value="low">Low confidence</option>
            </select>
          </div>
        </div>
      )}

      <div className="claim-topic-groups">
        {Object.entries(groupedByTopic).map(([topic, topicClaims]) => {
          const isCollapsed = expandedTopics[topic] === false;

          return (
            <div className="topic-group-card" key={topic}>
              <button
                type="button"
                className="topic-group-header"
                onClick={() => toggleTopicSection(topic)}
                aria-expanded={!isCollapsed}
                aria-label={`Topic: ${topic}, ${topicClaims.length} claims`}
              >
                <div className="topic-title-area">
                  <span className="topic-chevron" aria-hidden="true">
                    {isCollapsed ? "▸" : "▾"}
                  </span>
                  <span className="topic-tag-pill">{sanitizeText(topic)}</span>
                  <span className="topic-count-badge">
                    {topicClaims.length} {topicClaims.length === 1 ? "claim" : "claims"}
                  </span>
                </div>
              </button>

              {!isCollapsed && (
                <div className="claim-list" role="list">
                  {topicClaims.map((claim) => {
                    const isExpanded = expandedExcerpts[claim.id];
                    const sourceName =
                      claim.source?.title || claim.source?.publisher || "Referenced source";

                    return (
                      <article className="claim" key={claim.id} role="listitem">
                        <div className="claim-header-row">
                          <span
                            className={`confidence ${claim.confidence}`}
                            aria-label={`Confidence: ${claim.confidence}`}
                          >
                            <span className="conf-indicator" aria-hidden="true" />
                            {pretty(claim.confidence)}
                          </span>
                          {claim.classification && (
                            <span className="classification-pill">
                              {pretty(claim.classification)}
                            </span>
                          )}
                          <span className="claim-source-ref" title={sourceName}>
                            From: {sanitizeText(sourceName)}
                          </span>
                        </div>

                        <p className="claim-statement">{sanitizeText(claim.statement)}</p>

                        <div className="claim-excerpt-toggle">
                          <button
                            type="button"
                            className="excerpt-btn"
                            onClick={() => toggleExcerpt(claim.id)}
                            aria-expanded={isExpanded}
                          >
                            {isExpanded ? "Hide source excerpt ▴" : "Show exact source excerpt ▾"}
                          </button>

                          {isExpanded && (
                            <blockquote className="claim-blockquote" aria-label="Verbatim excerpt">
                              “{sanitizeText(claim.exact_excerpt)}”
                            </blockquote>
                          )}
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}

        {!filteredClaims.length && (
          <p className="empty">
            {claims.length === 0
              ? "Claims require exact source excerpts and will appear once extraction finishes."
              : "No claims match the selected filters."}
          </p>
        )}
      </div>
    </div>
  );
}
