import React, { useState } from "react";
import "./DonationAppealAnalyzer.css";


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const MIN_TEXT_LENGTH = 10;
const MAX_TEXT_LENGTH = 10_000;
const CHAR_WARN_THRESHOLD = 9_000;
const LOW_CONFIDENCE_THRESHOLD = 0.50;

const SEVERITY_CONFIG = {
  high: { bg: "#fef2f2", border: "#fecaca", tag: "#991b1b", text: "#7f1d1d", label: "High" },
  medium: { bg: "#fff7ed", border: "#fed7aa", tag: "#92400e", text: "#78350f", label: "Medium" },
  low: { bg: "#f0f9ff", border: "#bae6fd", tag: "#075985", text: "#0c4a6e", label: "Low" },
};


class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = "ValidationError";
  }
}


function detectScript(text) {
  const sinhalaChars = (text.match(/[\u0D80-\u0DFF]/g) || []).length;
  const tamilChars = (text.match(/[\u0B80-\u0BFF]/g) || []).length;
  const totalChars = text.replace(/\s/g, "").length;
  if (!totalChars) return null;
  if (sinhalaChars / totalChars > 0.3) return "Sinhala";
  if (tamilChars / totalChars > 0.3) return "Tamil";
  return "English";
}


async function analyseAppeal(appealText, language) {
  const trimmed = (appealText || "").trim();
  if (!trimmed) {
    throw new ValidationError("Paste an appeal before analysing.");
  }
  if (trimmed.length < MIN_TEXT_LENGTH) {
    throw new ValidationError(
      `Appeal is too short to analyse (${trimmed.length} characters). Minimum is ${MIN_TEXT_LENGTH}.`
    );
  }
  if (trimmed.length > MAX_TEXT_LENGTH) {
    throw new ValidationError(
      `Appeal exceeds the ${MAX_TEXT_LENGTH.toLocaleString()} character limit.`
    );
  }

  const response = await fetch(`${API_BASE_URL}/api/quality/analyse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ appeal_text: trimmed, language }),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    if (response.status === 422) {
      throw new ValidationError(data?.detail || "Validation failed.");
    }
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


function LowConfidenceBanner() {
  return (
    <div className="daa-low-confidence-banner" role="alert">
      <span className="daa-low-conf-icon">!</span>
      <div>
        <strong>Low confidence score</strong>
        <p>
          The model is uncertain about this quality rating.
          Consider reviewing the appeal manually before acting on this score.
        </p>
      </div>
    </div>
  );
}


function ScoreHero({ score, label, confidence, lowConfidence = false, title = "Quality Score" }) {
  const pct = Math.round((Number(score) / 5) * 100);

  return (
    <div className="daa-score-hero">
      {lowConfidence && <LowConfidenceBanner />}
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
        <span className={`daa-conf-text ${lowConfidence ? "daa-conf-low" : ""}`}>
          {Math.round(Number(confidence) * 100)}% confidence
          {lowConfidence && " - uncertain"}
        </span>
      </div>
    </div>
  );
}


function IssueCard({ issue }) {
  const c = SEVERITY_CONFIG[issue.severity] || SEVERITY_CONFIG.low;
  const DIMENSION_HINTS = {
    specificity: "Add concrete numbers, names, or locations to strengthen this appeal.",
    urgency: "Use time-sensitive language to motivate immediate action.",
    clarity: "Simplify sentences so the ask is unambiguous.",
    credibility: "Include verifiable facts or organisation details.",
    emotional: "Connect the need to real people and their stories.",
    length: "Adjust the length to match the channel and audience.",
    cta: "End with a single, direct call to action.",
    currency: "Mention a specific donation amount or goal.",
    "content depth": "Add more detail about what donors' contributions will specifically provide.",
    content_depth: "Add more detail about what donors' contributions will specifically provide.",
    content: "Add more detail about what donors' contributions will specifically provide.",
  };
  const hint = DIMENSION_HINTS[issue.dimension?.toLowerCase()] || null;

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
      {hint && (
        <p className="daa-issue-hint" style={{ color: c.text }}>
          Tip: {hint}
        </p>
      )}
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
  const [analyseError, setAnalyseError] = useState("");
  const [analyseErrorIsValidation, setAnalyseErrorIsValidation] = useState(false);
  const [improveError, setImproveError] = useState("");
  const [copied, setCopied] = useState(false);

  const charCount = appealText.length;
  const charOverLimit = charCount > MAX_TEXT_LENGTH;
  const charNearLimit = charCount >= CHAR_WARN_THRESHOLD && !charOverLimit;
  const detectedScript = detectScript(appealText);
  const languageMismatch = (
    detectedScript !== null &&
    detectedScript !== language &&
    appealText.trim().length > 20
  );
  const wordCount = appealText.split(/\s+/).filter(Boolean).length;
  const highCount = analysis?.issues?.filter((issue) => issue.severity === "high").length || 0;
  const mediumCount = analysis?.issues?.filter((issue) => issue.severity === "medium").length || 0;
  const lowCount = analysis?.issues?.filter((issue) => issue.severity === "low").length || 0;
  const analysisLowConf = analysis
    ? (analysis.low_confidence ?? analysis.confidence < LOW_CONFIDENCE_THRESHOLD)
    : false;
  const improvementLowConf = improvement
    ? (improvement.low_confidence ?? improvement.improved_confidence < LOW_CONFIDENCE_THRESHOLD)
    : false;

  const handleAnalyse = async () => {
    setAnalyseError("");
    setAnalyseErrorIsValidation(false);
    setAnalysis(null);
    setImprovement(null);
    setImproveError("");
    setAnalysing(true);

    try {
      const result = await analyseAppeal(appealText, language);
      setAnalysis(result);
    } catch (err) {
      const isValidation = err instanceof ValidationError;
      setAnalyseError(err.message || "Analysis failed.");
      setAnalyseErrorIsValidation(isValidation);
    } finally {
      setAnalysing(false);
    }
  };

  const handleImprove = async () => {
    if (!appealText.trim() || !analysis) return;

    setImproveError("");
    setImproving(true);

    try {
      setImprovement(await improveAppeal(appealText, language));
    } catch (err) {
      setImproveError(err.message || "Improvement failed.");
    } finally {
      setImproving(false);
    }
  };

  const handleReImprove = async () => {
    setImprovement(null);
    await handleImprove();
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

            {languageMismatch && (
              <div className="daa-lang-mismatch" role="alert">
                ! Text appears to be <strong>{detectedScript}</strong> but language is set to{" "}
                <strong>{language}</strong> - scores may be inaccurate. Update the language
                selector to match your text.
              </div>
            )}

            <div className={`daa-char-count ${charOverLimit ? "daa-char-over" : charNearLimit ? "daa-char-warn" : ""}`}>
              {charCount.toLocaleString()} / {MAX_TEXT_LENGTH.toLocaleString()} characters
              {charOverLimit && " - too long"}
              {charNearLimit && " - approaching limit"}
              {!charOverLimit && !charNearLimit && `, ${wordCount} words`}
            </div>
          </div>

          <textarea
            className={`daa-textarea ${charOverLimit ? "daa-textarea-over" : ""}`}
            value={appealText}
            onChange={(event) => {
              setAppealText(event.target.value);
              setAnalysis(null);
              setImprovement(null);
              setAnalyseError("");
              setImproveError("");
            }}
            placeholder="Paste any donation appeal here..."
            rows={8}
          />

          <button
            className="daa-analyse-btn"
            type="button"
            onClick={handleAnalyse}
            disabled={analysing || !appealText.trim() || charOverLimit}
          >
            {analysing ? "Analysing..." : "Analyse Appeal"}
          </button>

          {analyseError && (
            <div
              className={`daa-error-box ${analyseErrorIsValidation ? "validation" : "api"}`}
              role="alert"
            >
              <strong>{analyseErrorIsValidation ? "Validation issue" : "Analysis failed"}</strong>
              <p>{analyseError}</p>
            </div>
          )}
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

                <div className="daa-improve-row">
                  <button
                    className="daa-improve-btn"
                    type="button"
                    onClick={improvement ? handleReImprove : handleImprove}
                    disabled={improving}
                  >
                    {improving ? (
                      <span className="daa-loading-label">
                        <span className="daa-spinner" />
                        Generating improvement...
                      </span>
                    ) : improvement ? "Regenerate Improvement" : "Generate Improved Version"}
                  </button>

                  {improveError && (
                    <div className="daa-error-box api" role="alert">
                      <strong>Improvement failed</strong>
                      <p>{improveError}</p>
                    </div>
                  )}
                </div>
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
                      lowConfidence={analysisLowConf}
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
                      lowConfidence={analysisLowConf}
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
                      lowConfidence={improvementLowConf}
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

            {improvementLowConf && (
              <div className="daa-low-confidence-banner" role="alert">
                <span className="daa-low-conf-icon">!</span>
                <div>
                  <strong>Low confidence on improved version</strong>
                  <p>
                    The model is uncertain about the improved appeal's quality rating.
                    Review it manually before publishing.
                  </p>
                </div>
              </div>
            )}

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
