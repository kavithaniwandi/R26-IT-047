import React, { useState } from "react";
import "./DonationAppealAnalyzer.css";


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const SEVERITY_CONFIG = {
  high: { bg: "#fef2f2", border: "#fecaca", tag: "#991b1b", text: "#7f1d1d", label: "High" },
  medium: { bg: "#fff7ed", border: "#fed7aa", tag: "#92400e", text: "#78350f", label: "Medium" },
  low: { bg: "#f0f9ff", border: "#bae6fd", tag: "#075985", text: "#0c4a6e", label: "Low" },
};


async function analyseAppeal(appealText, language) {
  const response = await fetch(`${API_BASE_URL}/api/quality/analyse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ appeal_text: appealText, language }),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || "Failed to analyse appeal.");
  }

  return response.json();
}


async function improveAppeal(appealText, language) {
  const response = await fetch(`${API_BASE_URL}/api/quality/improve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ appeal_text: appealText, language }),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || "Failed to improve appeal.");
  }

  return response.json();
}


function ScoreHero({ score, label, confidence, title = "Quality Score" }) {
  const pct = Math.round((Number(score) / 5) * 100);

  return (
    <div className="daa-score-hero">
      <div>
        <span className="daa-score-num">{Number(score).toFixed(2)}</span>
        <span className="daa-score-denom"> / 5</span>
      </div>
      <div className="daa-score-label">{title}</div>
      <div className="daa-score-bar">
        <div className="daa-score-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <div className="daa-score-meta">
        <span className={`daa-label-pill daa-label-${label}`}>{label}</span>
        <span className="daa-conf-text">{Math.round(Number(confidence) * 100)}% confidence</span>
      </div>
    </div>
  );
}


function IssueCard({ issue }) {
  const c = SEVERITY_CONFIG[issue.severity] || SEVERITY_CONFIG.low;

  return (
    <div
      className="daa-issue-card"
      style={{
        background: c.bg,
        border: `1.5px solid ${c.border}`,
        borderLeft: `4px solid ${c.tag}`,
        borderRadius: "8px",
        padding: "0.85rem 1rem",
      }}
    >
      <div className="daa-issue-header">
        <span className="daa-issue-dimension" style={{ color: c.text }}>
          {issue.dimension}
        </span>
        <span className="daa-issue-severity-tag" style={{ background: c.tag }}>
          {c.label} priority
        </span>
      </div>
      <p className="daa-issue-text" style={{ color: c.text }}>{issue.issue}</p>
      <div className="daa-issue-metrics">
        <span style={{ color: c.text }}><strong>Found:</strong> {issue.value}</span>
        <span style={{ color: c.text }}><strong>Target:</strong> {issue.target}</span>
      </div>
    </div>
  );
}


function ScoreDelta({ original, improved, origConf, impConf }) {
  const scoreDelta = Number(improved) - Number(original);
  const confDelta = Math.round((Number(impConf) - Number(origConf)) * 100);
  const neutral = scoreDelta === 0;

  return (
    <div className="daa-delta-wrap">
      <span className={`daa-delta ${scoreDelta > 0 ? "daa-delta-up" : neutral ? "daa-delta-neutral" : "daa-delta-down"}`}>
        {scoreDelta > 0 ? "Up" : neutral ? "Same" : "Down"} {scoreDelta > 0 ? "+" : ""}{scoreDelta.toFixed(2)} score
      </span>

      {confDelta !== 0 && (
        <div className={`daa-confidence-delta ${confDelta > 0 ? "up" : "down"}`}>
          {confDelta > 0 ? "Up" : "Down"} {Math.abs(confDelta)}% confidence
          {confDelta < 0 && neutral && (
            <p>
              Same score, lower confidence. The model sees the improved text closer to a class boundary.
            </p>
          )}
        </div>
      )}
    </div>
  );
}


export default function DonationAppealAnalyzer() {
  const [appealText, setAppealText] = useState("");
  const [language, setLanguage] = useState("English");
  const [analysis, setAnalysis] = useState(null);
  const [improvement, setImprovement] = useState(null);
  const [analysing, setAnalysing] = useState(false);
  const [improving, setImproving] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const wordCount = appealText.split(/\s+/).filter(Boolean).length;
  const highCount = analysis?.issues?.filter((issue) => issue.severity === "high").length || 0;
  const mediumCount = analysis?.issues?.filter((issue) => issue.severity === "medium").length || 0;
  const lowCount = analysis?.issues?.filter((issue) => issue.severity === "low").length || 0;

  const handleAnalyse = async () => {
    if (!appealText.trim()) {
      setError("Please paste an appeal to analyse.");
      return;
    }

    setAnalysing(true);
    setError("");
    setAnalysis(null);
    setImprovement(null);

    try {
      setAnalysis(await analyseAppeal(appealText, language));
    } catch (err) {
      setError(err.message || "Analysis failed.");
    } finally {
      setAnalysing(false);
    }
  };

  const handleImprove = async () => {
    if (!appealText.trim() || !analysis) return;

    setImproving(true);
    setError("");

    try {
      setImprovement(await improveAppeal(appealText, language));
    } catch (err) {
      setError(err.message || "Improvement failed.");
    } finally {
      setImproving(false);
    }
  };

  const handleCopy = async () => {
    if (!improvement?.improved_appeal) return;

    try {
      await navigator.clipboard.writeText(improvement.improved_appeal);
    } catch {
      const textArea = document.createElement("textarea");
      textArea.value = improvement.improved_appeal;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
    }

    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="daa-page">
      <main className="daa-container">
        <section className="daa-header">
          <div>
            <span className="daa-header-eyebrow">ML Quality Analysis</span>
            <h1 className="daa-header-title">Donation Appeal Analyzer</h1>
            <p className="daa-header-sub">
              Paste any donation appeal, review ML scoring signals, then generate a targeted improvement.
            </p>
          </div>
          <div className="daa-header-badge">ML first, Gemini second</div>
        </section>

        <section className="daa-input-card">
          <div className="daa-input-header">
            <span className="daa-section-num">1</span>
            <h2 className="daa-section-title">Paste Appeal</h2>
          </div>

          <div className="daa-input-row">
            <div className="daa-form-group">
              <label htmlFor="daa-language">Language</label>
              <select
                id="daa-language"
                value={language}
                onChange={(event) => setLanguage(event.target.value)}
              >
                <option value="English">English</option>
                <option value="Sinhala">Sinhala</option>
                <option value="Tamil">Tamil</option>
              </select>
            </div>

            <div className="daa-char-count">
              {appealText.length} characters, {wordCount} words
            </div>
          </div>

          <textarea
            className="daa-textarea"
            value={appealText}
            onChange={(event) => {
              setAppealText(event.target.value);
              setAnalysis(null);
              setImprovement(null);
              setError("");
            }}
            placeholder="Paste any donation appeal here..."
            rows={8}
          />

          <button
            className="daa-analyse-btn"
            type="button"
            onClick={handleAnalyse}
            disabled={analysing || !appealText.trim()}
          >
            {analysing ? "Analysing..." : "Analyse Appeal"}
          </button>

          {error && <p className="daa-error">{error}</p>}
        </section>

        {analysis && (
          <div className="daa-results-grid">
            <div className="daa-issues-col">
              <div className="daa-card">
                <div className="daa-input-header">
                  <span className="daa-section-num">2</span>
                  <h2 className="daa-section-title">Quality Issues</h2>
                </div>

                <div className="daa-issue-summary">
                  {highCount > 0 && <span className="daa-summary-chip daa-chip-high">{highCount} high</span>}
                  {mediumCount > 0 && <span className="daa-summary-chip daa-chip-medium">{mediumCount} medium</span>}
                  {lowCount > 0 && <span className="daa-summary-chip daa-chip-low">{lowCount} low</span>}
                  {highCount === 0 && mediumCount === 0 && (
                    <span className="daa-summary-chip daa-chip-good">No major issues</span>
                  )}
                </div>

                <div className="daa-issues-list">
                  {analysis.issues.map((issue, index) => (
                    <IssueCard key={`${issue.dimension}-${index}`} issue={issue} />
                  ))}
                </div>

                {!improvement && (
                  <button
                    className="daa-improve-btn"
                    type="button"
                    onClick={handleImprove}
                    disabled={improving}
                  >
                    {improving ? (
                      <span className="daa-loading-label">
                        <span className="daa-spinner" />
                        Generating improvement...
                      </span>
                    ) : "Generate Improved Version"}
                  </button>
                )}
              </div>
            </div>

            <div className="daa-score-col">
              <div className="daa-card">
                <div className="daa-input-header">
                  <span className="daa-section-num">3</span>
                  <h2 className="daa-section-title">
                    {improvement ? "Score Comparison" : "Quality Score"}
                  </h2>
                </div>

                {!improvement ? (
                  <>
                    <ScoreHero
                      score={analysis.score}
                      label={analysis.label}
                      confidence={analysis.confidence}
                    />
                    <div className="daa-score-rows">
                      <div className="daa-score-row">
                        <span>Method</span>
                        <span className="daa-method-pill">{analysis.method}</span>
                      </div>
                      <div className="daa-score-row">
                        <span>Issues found</span>
                        <span>{analysis.issues.length}</span>
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <p className="daa-compare-label">Before</p>
                    <ScoreHero
                      score={analysis.score}
                      label={analysis.label}
                      confidence={analysis.confidence}
                      title="Original Score"
                    />

                    <div className="daa-compare-divider">
                      <ScoreDelta
                        original={analysis.score}
                        improved={improvement.improved_score}
                        origConf={analysis.confidence}
                        impConf={improvement.improved_confidence}
                      />
                    </div>

                    <p className="daa-compare-label">After</p>
                    <ScoreHero
                      score={improvement.improved_score}
                      label={improvement.improved_label}
                      confidence={improvement.improved_confidence}
                      title="Improved Score"
                    />
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {improvement && (
          <section className="daa-card daa-improved-card">
            <div className="daa-input-header">
              <span className="daa-section-num">4</span>
              <h2 className="daa-section-title">Improved Appeal</h2>
            </div>

            <div className="daa-improved-badges">
              <span className={`daa-label-pill daa-label-${improvement.improved_label}`}>
                {improvement.improved_label}
              </span>
              <span className="daa-score-chip">
                {Number(improvement.improved_score).toFixed(2)} / 5
              </span>
              <span className="daa-score-chip">
                {Math.round(Number(improvement.improved_confidence) * 100)}% confidence
              </span>
            </div>

            <div className="daa-improved-text">
              <p>{improvement.improved_appeal}</p>
            </div>

            <div className="daa-copy-row">
              <button className="daa-copy-btn" type="button" onClick={handleCopy}>
                {copied ? "Copied" : "Copy Improved Appeal"}
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
