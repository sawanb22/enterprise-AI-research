import { FormEvent, useState } from "react";

export type ResearchMode = "web" | "rag";

interface QuestionFormProps {
  mode: ResearchMode;
  onModeChange: (newMode: ResearchMode) => void;
  onSubmit: (finalQuestion: string) => Promise<unknown> | void;
  loading: boolean;
  hasDocuments?: boolean;
}

export function QuestionForm({
  mode,
  onModeChange,
  onSubmit,
  loading,
  hasDocuments = false,
}: QuestionFormProps) {
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
    if (trimmed.length < 8) {
      setLocalError("Enter a specific research question of at least 8 characters.");
      return;
    }
    setLocalError("");

    let finalQuestion = trimmed;

    // In Web mode, append guided context if provided
    if (mode === "web") {
      const contextParts: string[] = [];
      if (audience.trim()) contextParts.push(`Target Audience / Context: ${audience.trim()}`);
      if (region.trim()) contextParts.push(`Target Region/Market: ${region.trim()}`);
      if (timeRange && timeRange !== "any") contextParts.push(`Timeframe: ${timeRange}`);
      if (selectedSourceTypes.length > 0) contextParts.push(`Preferred Sources: ${selectedSourceTypes.join(", ")}`);
      if (usefulnessGoal.trim()) contextParts.push(`Goal/Output Need: ${usefulnessGoal.trim()}`);

      if (contextParts.length > 0) {
        finalQuestion = `${trimmed}\n\n[Research Context: ${contextParts.join(" | ")}]`;
      }
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
      // Handled by parent
    }
  };

  return (
    <form className="question-card" onSubmit={handleSubmit} aria-label="Research Question Form">
      {/* Futuristic Segmented Mode Selector */}
      <div className="mode-selector-container">
        <div className="mode-segmented-pill" role="tablist" aria-label="Select Intelligence Mode">
          <button
            type="button"
            role="tab"
            aria-selected={mode === "web"}
            className={`mode-btn ${mode === "web" ? "active" : ""}`}
            onClick={() => onModeChange("web")}
            disabled={loading}
          >
            <svg className="mode-svg-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <line x1="2" y1="12" x2="22" y2="12" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            <span className="mode-label">
              <span className="mode-label-full">Web Intelligence</span>
              <span className="mode-label-short">Web Research</span>
            </span>
            <span className="mode-badge">Live Discovery</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={mode === "rag"}
            className={`mode-btn ${mode === "rag" ? "active" : ""}`}
            onClick={() => onModeChange("rag")}
            disabled={loading}
          >
            <svg className="mode-svg-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
            <span className="mode-label">
              <span className="mode-label-full">Enterprise Document RAG</span>
              <span className="mode-label-short">Document RAG</span>
            </span>
            <span className="mode-badge highlight">PDF Vault</span>
          </button>
        </div>
      </div>

      <label htmlFor="question" className="question-label">
        {mode === "web" ? "Web Research Inquiry" : "Document RAG Research Inquiry"}
      </label>

      <div className="question-row">
        <textarea
          id="question"
          value={question}
          onChange={(e) => {
            setQuestion(e.target.value);
            if (localError) setLocalError("");
          }}
          placeholder={
            mode === "web"
              ? "How is AI transforming retail operations and customer experiences?"
              : "What are the core technical architectures, performance metrics, and limitations discussed in the uploaded PDFs?"
          }
          rows={2}
          aria-required="true"
          aria-invalid={Boolean(localError)}
          aria-describedby={localError ? "question-error" : "question-hint"}
        />
        <button
          type="submit"
          disabled={loading}
          className={`run-btn ${mode === "rag" ? "rag-btn" : ""}`}
        >
          {loading ? (
            <span className="btn-loading-content">
              <span className="spinner" aria-hidden="true" />
              {mode === "web" ? "Discovering..." : "Synthesizing..."}
            </span>
          ) : mode === "web" ? (
            "Run Web Research"
          ) : (
            "Synthesize RAG Report"
          )}
        </button>
      </div>

      {localError && (
        <div id="question-error" className="field-error" role="alert">
          {localError}
        </div>
      )}

      {/* Guided Context (Web Mode Only) */}
      {mode === "web" && (
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
      )}

      {/* Mode Guidance Subtext */}
      <p id="question-hint" className="question-hint">
        {mode === "web"
          ? "Plans multi-angle web queries, extracts verbatim source claims, and synthesizes evidence-backed conclusions."
          : "Synthesizes grounded executive research reports with page-accurate citations extracted directly from your uploaded documents."}
      </p>
    </form>
  );
}
