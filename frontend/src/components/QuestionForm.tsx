import { FormEvent, useState } from "react";

interface QuestionFormProps {
  onSubmit: (finalQuestion: string) => Promise<unknown> | void;
  loading: boolean;
}

export function QuestionForm({ onSubmit, loading }: QuestionFormProps) {
  const [question, setQuestion] = useState("");
  const [showContext, setShowContext] = useState(false);
  const [audience, setAudience] = useState("");
  const [region, setRegion] = useState("");
  const [timeRange, setTimeRange] = useState("any");
  const [selectedSourceTypes, setSelectedSourceTypes] = useState<string[]>([]);
  const [usefulnessGoal, setUsefulnessGoal] = useState("");
  const [localError, setLocalError] = useState("");

  const toggleSourceType = (type: string) => {
    setSelectedSourceTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const trimmed = question.trim();
    if (trimmed.length < 12) {
      setLocalError("Enter a specific research question of at least 12 characters.");
      return;
    }
    setLocalError("");

    // Build enhanced question with optional research context if provided
    let finalQuestion = trimmed;
    const contextParts: string[] = [];

    if (audience.trim()) {
      contextParts.push(`Target Audience / Context: ${audience.trim()}`);
    }
    if (region.trim()) {
      contextParts.push(`Target Region/Market: ${region.trim()}`);
    }
    if (timeRange && timeRange !== "any") {
      contextParts.push(`Timeframe: ${timeRange}`);
    }
    if (selectedSourceTypes.length > 0) {
      contextParts.push(`Preferred Sources: ${selectedSourceTypes.join(", ")}`);
    }
    if (usefulnessGoal.trim()) {
      contextParts.push(`Goal/Output Need: ${usefulnessGoal.trim()}`);
    }

    if (contextParts.length > 0) {
      finalQuestion = `${trimmed}\n\n[Research Context: ${contextParts.join(" | ")}]`;
    }

    try {
      await onSubmit(finalQuestion);
      setQuestion("");
      setAudience("");
      setRegion("");
      setTimeRange("any");
      setSelectedSourceTypes([]);
      setUsefulnessGoal("");
      setShowContext(false);
    } catch {
      // Error handled by parent
    }
  };

  return (
    <form className="question-card" onSubmit={handleSubmit} aria-label="Research Question Form">
      <label htmlFor="question" className="question-label">
        New research question
      </label>

      <div className="question-row">
        <textarea
          id="question"
          value={question}
          onChange={(e) => {
            setQuestion(e.target.value);
            if (localError) setLocalError("");
          }}
          placeholder="How is AI transforming retail operations and customer experiences?"
          rows={2}
          aria-required="true"
          aria-invalid={Boolean(localError)}
          aria-describedby={localError ? "question-error" : "question-hint"}
        />
        <button type="submit" disabled={loading} className="run-btn">
          {loading ? (
            <span className="btn-loading-content">
              <span className="spinner" aria-hidden="true" /> Starting…
            </span>
          ) : (
            "Run research"
          )}
        </button>
      </div>

      {localError && (
        <div id="question-error" className="field-error" role="alert">
          {localError}
        </div>
      )}

      <div className="guided-context-wrapper">
        <button
          type="button"
          className="context-toggle-btn"
          onClick={() => setShowContext(!showContext)}
          aria-expanded={showContext}
          aria-controls="guided-context-section"
        >
          <span>{showContext ? "▾ Hide guided research context" : "▸ Add research context (optional)"}</span>
          <span className="context-badge">Guided</span>
        </button>

        {showContext && (
          <div id="guided-context-section" className="guided-context-fields">
            <div className="context-grid">
              <div className="context-field">
                <label htmlFor="context-audience">Decision context / Audience</label>
                <input
                  id="context-audience"
                  type="text"
                  placeholder="e.g. Executive leadership, Technical strategy"
                  value={audience}
                  onChange={(e) => setAudience(e.target.value)}
                />
              </div>

              <div className="context-field">
                <label htmlFor="context-region">Target Region / Market</label>
                <input
                  id="context-region"
                  type="text"
                  placeholder="e.g. Global, North America, EMEA"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                />
              </div>

              <div className="context-field">
                <label htmlFor="context-timerange">Time Range</label>
                <select
                  id="context-timerange"
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value)}
                >
                  <option value="any">Any / Most recent evidence</option>
                  <option value="Past month">Past month</option>
                  <option value="Past quarter">Past quarter</option>
                  <option value="Past year">Past year</option>
                </select>
              </div>

              <div className="context-field">
                <label htmlFor="context-goal">What makes this answer useful?</label>
                <input
                  id="context-goal"
                  type="text"
                  placeholder="e.g. Concrete ROI metrics and key roadblocks"
                  value={usefulnessGoal}
                  onChange={(e) => setUsefulnessGoal(e.target.value)}
                />
              </div>
            </div>

            <div className="source-preferences">
              <span className="pref-label">Preferred evidence types:</span>
              <div className="pref-checkboxes">
                {["Industry Reports", "Academic Research", "Market Intelligence", "News & Analysis"].map(
                  (type) => (
                    <label key={type} className="checkbox-pill">
                      <input
                        type="checkbox"
                        checked={selectedSourceTypes.includes(type)}
                        onChange={() => toggleSourceType(type)}
                      />
                      <span>{type}</span>
                    </label>
                  )
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      <p id="question-hint" className="question-hint">
        EvidenceLab plans multi-angle queries, retrieves authoritative snapshots, extracts verbatim claims, and traces conclusions back to sources.
      </p>
    </form>
  );
}
