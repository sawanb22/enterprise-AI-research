import { Conclusion } from "../api";
import { pretty, sanitizeText } from "../utils/textUtils";

interface ConclusionsCardProps {
  conclusions: Conclusion[];
  onViewEvidence: (conclusionId: string) => void;
}

export function ConclusionsCard({ conclusions, onViewEvidence }: ConclusionsCardProps) {
  return (
    <div className="card conclusions-card" aria-label="Synthesized Research Conclusions">
      <div className="section-title">
        <div>
          <p className="eyebrow">SYNTHESIS & FINDINGS</p>
          <h2>Key conclusions</h2>
        </div>
        <span className="muted">
          {conclusions.length} {conclusions.length === 1 ? "conclusion" : "conclusions"} · Citation gate enforced
        </span>
      </div>

      {conclusions.length ? (
        <div className="conclusion-list">
          {conclusions.map((conclusion, idx) => (
            <article className="conclusion" key={conclusion.id} aria-label={`Conclusion ${idx + 1}`}>
              <div className="conclusion-main">
                <div className="conclusion-header">
                  <span
                    className={`confidence ${conclusion.confidence}`}
                    aria-label={`Confidence level: ${conclusion.confidence}`}
                  >
                    <span className="conf-indicator" aria-hidden="true" />
                    {pretty(conclusion.confidence)} confidence
                  </span>
                  {conclusion.claim_count > 0 && (
                    <span className="grounding-badge">
                      {conclusion.claim_count} {conclusion.claim_count === 1 ? "grounded claim" : "grounded claims"}
                    </span>
                  )}
                </div>

                <p className="conclusion-statement">{sanitizeText(conclusion.statement)}</p>

                {conclusion.reasoning && (
                  <div className="reasoning-box">
                    <strong className="reasoning-tag">Deduction & Reasoning:</strong>
                    <span>{sanitizeText(conclusion.reasoning)}</span>
                  </div>
                )}

                {conclusion.limitations && (
                  <div className="limitation-box">
                    <small>
                      <strong>Limitation / Scope:</strong> {sanitizeText(conclusion.limitations)}
                    </small>
                  </div>
                )}
              </div>

              <div className="conclusion-actions">
                <button
                  type="button"
                  className="trace-button"
                  onClick={() => onViewEvidence(conclusion.id)}
                  aria-label={`View evidence chain for: ${sanitizeText(conclusion.statement.slice(0, 50))}...`}
                >
                  <span>View evidence chain</span>
                  <span aria-hidden="true">→</span>
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-conclusions-box">
          <p className="empty">
            Conclusions will be synthesized and citations verified once source-grounded claims are validated.
          </p>
        </div>
      )}
    </div>
  );
}
