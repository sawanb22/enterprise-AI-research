import { useMemo, useState } from "react";
import { Assessment } from "../api";
import { pretty, sanitizeText } from "../utils/textUtils";

interface AssessmentsCardProps {
  assessments: Assessment[];
}

export function AssessmentsCard({ assessments }: AssessmentsCardProps) {
  const [relationshipFilter, setRelationshipFilter] = useState<string>("all");

  const counts = useMemo(() => {
    return {
      supports: assessments.filter((a) => a.relationship === "supports").length,
      qualifies: assessments.filter((a) => a.relationship === "qualifies").length,
      contradicts: assessments.filter((a) => a.relationship === "contradicts").length,
      unrelated: assessments.filter((a) => a.relationship === "unrelated").length,
    };
  }, [assessments]);

  const filteredAssessments = useMemo(() => {
    if (relationshipFilter === "all") return assessments;
    return assessments.filter((a) => a.relationship === relationshipFilter);
  }, [assessments, relationshipFilter]);

  const getRelationshipIcon = (rel: string) => {
    switch (rel) {
      case "supports":
        return "✓";
      case "qualifies":
        return "≈";
      case "contradicts":
        return "✕";
      default:
        return "·";
    }
  };

  return (
    <div className="card assessments-card" aria-label="Cross-Source Evidence Comparisons">
      <div className="section-title">
        <div>
          <p className="eyebrow">EVIDENCE COMPARISON & SYNTHESIS</p>
          <h2>Cross-source comparisons</h2>
        </div>
        <span className="muted">
          {filteredAssessments.length} of {assessments.length} assessments
        </span>
      </div>

      {assessments.length > 0 && (
        <div className="assessment-summary-header">
          <div className="assessment-pills-row">
            <button
              type="button"
              className={`assessment-filter-pill ${relationshipFilter === "all" ? "active" : ""}`}
              onClick={() => setRelationshipFilter("all")}
            >
              All ({assessments.length})
            </button>
            {counts.supports > 0 && (
              <button
                type="button"
                className={`assessment-filter-pill supports ${
                  relationshipFilter === "supports" ? "active" : ""
                }`}
                onClick={() => setRelationshipFilter("supports")}
              >
                ✓ {counts.supports} Supporting
              </button>
            )}
            {counts.qualifies > 0 && (
              <button
                type="button"
                className={`assessment-filter-pill qualifies ${
                  relationshipFilter === "qualifies" ? "active" : ""
                }`}
                onClick={() => setRelationshipFilter("qualifies")}
              >
                ≈ {counts.qualifies} Qualifying
              </button>
            )}
            {counts.contradicts > 0 && (
              <button
                type="button"
                className={`assessment-filter-pill contradicts ${
                  relationshipFilter === "contradicts" ? "active" : ""
                }`}
                onClick={() => setRelationshipFilter("contradicts")}
              >
                ✕ {counts.contradicts} Contradicting
              </button>
            )}
          </div>
        </div>
      )}

      <div className="assessment-list" role="list">
        {filteredAssessments.map((assessment) => (
          <article className="assessment" key={assessment.id} role="listitem">
            <div className="assessment-top">
              <span
                className={`relationship ${assessment.relationship}`}
                aria-label={`Relationship: ${assessment.relationship}`}
              >
                <span className="rel-icon" aria-hidden="true">
                  {getRelationshipIcon(assessment.relationship)}
                </span>
                {pretty(assessment.relationship)}
              </span>
              {assessment.confidence && (
                <span className="assessment-conf">
                  {pretty(assessment.confidence)} confidence
                </span>
              )}
            </div>

            <p className="assessment-rationale">{sanitizeText(assessment.rationale)}</p>

            {assessment.conditions && (
              <div className="conditions-box">
                <small>
                  <strong>Contextual Conditions:</strong> {sanitizeText(assessment.conditions)}
                </small>
              </div>
            )}
          </article>
        ))}

        {!filteredAssessments.length && (
          <p className="empty">
            {assessments.length === 0
              ? "Related claims will be compared across sources when multiple citations cover intersecting topics."
              : "No assessments match the selected relationship filter."}
          </p>
        )}
      </div>
    </div>
  );
}
