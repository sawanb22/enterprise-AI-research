import { useMemo } from "react";
import { Assessment, Claim, Source } from "../api";
import { sanitizeText } from "../utils/textUtils";

interface EvidenceQualitySummaryProps {
  sources: Source[];
  claims: Claim[];
  assessments: Assessment[];
}

export function EvidenceQualitySummary({
  sources,
  claims,
  assessments,
}: EvidenceQualitySummaryProps) {
  const quality = useMemo(() => {
    // 1. Coverage
    const fetchedSources = sources.filter((s) => s.fetch_status !== "failed");
    const publishers = new Set(
      sources
        .map((s) => s.publisher?.trim())
        .filter((p): p is string => Boolean(p && p.length > 0))
    );
    const publisherCount = publishers.size;
    const coverageText = `${sources.length} sources across ${publisherCount || 1} distinct ${
      publisherCount === 1 ? "publisher" : "publishers"
    }`;

    // 2. Agreement
    const supports = assessments.filter((a) => a.relationship === "supports").length;
    const qualifies = assessments.filter((a) => a.relationship === "qualifies").length;
    const contradicts = assessments.filter((a) => a.relationship === "contradicts").length;
    const totalAssessments = assessments.length;

    let agreementText = "No direct cross-source comparisons needed";
    if (totalAssessments > 0) {
      const parts: string[] = [];
      if (supports > 0) parts.push(`${supports} supporting`);
      if (qualifies > 0) parts.push(`${qualifies} qualifying`);
      if (contradicts > 0) parts.push(`${contradicts} contradictory`);
      agreementText = parts.length > 0 ? parts.join(", ") : `${totalAssessments} comparisons`;
    }

    // 3. Freshness
    const hasTodaySources = sources.some((s) => {
      if (!s.retrieved_at) return false;
      const d = new Date(s.retrieved_at);
      return !isNaN(d.getTime()) && (Date.now() - d.getTime()) < 24 * 3600 * 1000;
    });
    const freshnessText = hasTodaySources ? "Fresh snapshots retrieved today" : "Snapshots archived recently";

    // 4. Topic distribution & Gaps
    const topicMap: Record<string, number> = {};
    claims.forEach((c) => {
      const t = c.topic?.trim() || "General";
      topicMap[t] = (topicMap[t] || 0) + 1;
    });
    const singleClaimTopics = Object.entries(topicMap)
      .filter(([, count]) => count === 1)
      .map(([topic]) => topic);

    let gapsText = "Multi-evidence triangulation across all topics";
    if (singleClaimTopics.length > 0) {
      gapsText = `Single-source evidence on: ${singleClaimTopics.slice(0, 2).map(sanitizeText).join(", ")}`;
    } else if (claims.length === 0) {
      gapsText = "Awaiting claim extraction";
    }

    // 5. Confidence Score
    let score = 0;
    if (sources.length >= 4) score += 2;
    else if (sources.length >= 2) score += 1;

    if (publisherCount >= 3) score += 2;
    else if (publisherCount >= 2) score += 1;

    if (totalAssessments > 0) {
      const supportRatio = supports / totalAssessments;
      const contradictRatio = contradicts / totalAssessments;
      if (supportRatio >= 0.6) score += 2;
      if (contradictRatio <= 0.2) score += 1;
    } else if (claims.length >= 4) {
      score += 2;
    }

    if (hasTodaySources) score += 1;
    if (singleClaimTopics.length === 0 && Object.keys(topicMap).length > 0) score += 2;

    let verdict: "High" | "Moderate" | "Preliminary" = "Moderate";
    let verdictClass = "moderate";
    if (score >= 7) {
      verdict = "High";
      verdictClass = "high";
    } else if (score < 4) {
      verdict = "Preliminary";
      verdictClass = "preliminary";
    }

    return {
      coverageText,
      agreementText,
      freshnessText,
      gapsText,
      verdict,
      verdictClass,
      score,
      totalClaims: claims.length,
      totalSources: sources.length,
      fetchedCount: fetchedSources.length,
    };
  }, [sources, claims, assessments]);

  if (sources.length === 0 && claims.length === 0) {
    return null;
  }

  return (
    <section className="card evidence-quality-card" aria-label="Evidence Quality and Trust Assessment">
      <div className="quality-header">
        <div>
          <p className="eyebrow">DECISION SUPPORT</p>
          <h2>Evidence quality & grounding</h2>
        </div>
        <div className={`quality-verdict-badge ${quality.verdictClass}`}>
          <span className="verdict-dot" aria-hidden="true" />
          <span className="verdict-label">{quality.verdict} confidence</span>
        </div>
      </div>

      <div className="quality-signals-grid">
        <div className="quality-signal-item">
          <svg className="signal-icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <line x1="2" y1="12" x2="22" y2="12" />
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
          </svg>
          <div className="signal-content">
            <span className="signal-title">Source Coverage</span>
            <strong className="signal-value">{quality.coverageText}</strong>
          </div>
        </div>

        <div className="quality-signal-item">
          <svg className="signal-icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <polyline points="9 12 11 14 15 10" />
          </svg>
          <div className="signal-content">
            <span className="signal-title">Evidence Agreement</span>
            <strong className="signal-value">{quality.agreementText}</strong>
          </div>
        </div>

        <div className="quality-signal-item">
          <svg className="signal-icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <div className="signal-content">
            <span className="signal-title">Data Freshness</span>
            <strong className="signal-value">{quality.freshnessText}</strong>
          </div>
        </div>

        <div className="quality-signal-item">
          <svg className="signal-icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <div className="signal-content">
            <span className="signal-title">Triangulation & Gaps</span>
            <strong className="signal-value">{quality.gapsText}</strong>
          </div>
        </div>
      </div>
    </section>
  );
}
