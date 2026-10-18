import React, { useState } from "react";
import "./DonationAppealAnalyzer.css";


const API_BASE_URL = "";

const MIN_TEXT_LENGTH = 10;
const MAX_TEXT_LENGTH = 10_000;
const CHAR_WARN_THRESHOLD = 9_000;


function ClassifierResult({ result }) {
  const probabilities = result?.class_probs ?? result?.probabilities ?? {};
  const topClass = Object.entries(probabilities)
    .filter(([, probability]) => Number.isFinite(probability))
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0]?.[0];
  const label = result?.predicted_class ?? result?.classifier_top_class ?? topClass
    ?? result?.final_label ?? result?.quality_label ?? result?.label ?? result?.status;
  return <p className="daa-classifier-result">Classifier result: <strong className="daa-classifier-label">
    {["low", "medium", "high"].includes(label) ? label : "Unavailable"}
  </strong></p>;
}


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
      throw new ValidationError(`HTTP ${response.status}: ${data?.detail || "Validation failed."}`);
    }
    throw new Error(`HTTP ${response.status}: ${data?.detail || "Failed to analyse appeal."}`);
  }

  return response.json();
}


async function improveAppeal(appealText, language) {
  const response = await fetch(`${API_BASE_URL}/api/quality/improve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ appeal_text: appealText, language }),
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    console.error("[Appeal Improve] HTTP failure", { http_status: response.status });
    throw new Error(`HTTP ${response.status}: ${data?.detail || "Failed to improve appeal."}`);
  }

  const beforeScore = data?.before?.quality_score ?? data?.before?.score;
  const afterScore = data?.after?.quality_score ?? data?.after?.score;
  if (!data || typeof data.kept !== "boolean" || typeof data.improved_appeal !== "string"
      || !Number.isFinite(beforeScore) || !Number.isFinite(afterScore)) {
    console.error("[Appeal Improve] Invalid response", { http_status: response.status });
    throw new Error("The backend returned an invalid improvement response. Check the browser console and backend log.");
  }
  // Log diagnostics only: never dump appeal text or an entire provider response.
  const diagnostic = {
    diagnostic_id: data.diagnostic_id ?? "unavailable",
    http_status: response.status,
    outcome: data.kept ? "accepted" : data.rejection_reason ?? "not_attempted",
    provider_status: data.provider_status ?? null,
    provider_attempts: data.provider_attempts ?? null,
    rewrite_source: data.rewrite_source ?? null,
    original_score: data.original_score,
    original_raw_score: data.original_raw_quality_score,
    candidate_score: data.candidate_assessment?.score?.quality_score ?? null,
    candidate_raw_score: data.candidate_assessment?.score?.raw_quality_score ?? null,
    original_classifier_agreement: data.before?.label_agreement ?? null,
    candidate_classifier_agreement: data.candidate_assessment?.score?.label_agreement ?? null,
    facts_passed: data.candidate_assessment?.facts_passed ?? null,
    length_passed: data.candidate_assessment?.length_passed ?? null,
    guard_reason: data.candidate_assessment?.guard_reason ?? null,
    elapsed_ms: data.repair_ms ?? null,
  };
  if (data.kept) console.info("[Appeal Improve] Result", diagnostic);
  else console.warn("[Appeal Improve] Original retained", diagnostic);
  return data;
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
  const [improveNotice, setImproveNotice] = useState("");
  const [copied, setCopied] = useState(false);
  const [copyMessage, setCopyMessage] = useState("");

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
  const handleAnalyse = async () => {
    setImproveNotice("");
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
    setImproveNotice("");
    setImproving(true);

    try {
      const result = await improveAppeal(analysis.original_appeal ?? appealText, language);
      if (!result.kept && result.rejection_reason === "provider_error") {
        setImprovement(null);
        setImproveError(result.provider_status === "429"
          ? "The appeal service is rate-limited. Please try again later."
          : "The appeal service is temporarily unavailable. Please try again.");
      } else if (!result.kept) {
        setImprovement(null);
        setImproveNotice(result.rejection_reason === "no_improvement"
          ? ""
          : result.rejection_reason === "facts_guard"
            ? "No fact-preserving rewrite found. Your original appeal is unchanged."
            : "No accepted rewrite was found. Your original appeal is unchanged.");
      } else {
        setImprovement(result);
      }
    } catch (err) {
      console.error("[Appeal Improve] Request failed", { error_type: err.name });
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
            spellCheck={false}
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
            className="daa-primary-btn"
            type="button"
            onClick={handleAnalyse}
            disabled={analysing || !appealText.trim() || charOverLimit}
          >
            {analysing ? "Analyzing..." : "Analyze Appeal"}
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
            <section className="daa-card daa-rating-card">
              <div className="daa-input-header"><span className="daa-section-num">2</span><h2 className="daa-section-title">Classification</h2></div>
              <ClassifierResult result={analysis} />
            </section>
            <section className="daa-card daa-suggestions-card">
              <div className="daa-input-header"><span className="daa-section-num">3</span><h2 className="daa-section-title">Suggestions</h2></div>
              <div className="daa-issues-list">
                {(analysis.suggestions || []).map(s => <article className="daa-suggestion" key={s.check}>
                  <strong>{s.message}</strong>
                </article>)}
                {!analysis.suggestions?.length && <p>No suggestion is needed or available for this text.</p>}
              </div>
              <div className="daa-improve-row">
                <button className="daa-primary-btn" type="button" onClick={improvement ? handleReImprove : handleImprove}
                  disabled={improving || (improvement?.remaining_improve_uses ?? analysis.remaining_improve_uses) === 0}>
                  {improving ? "Generating improvement..." : "Improve this appeal"}
                </button>
                {improveNotice && <p role="status">{improveNotice}</p>}
                {improveError && <div className="daa-error-box api" role="alert"><p>{improveError}</p></div>}
              </div>
            </section>
          </div>
        )}

        {improvement && (
          <section className="daa-card daa-improved-card">
            <div className="daa-input-header">
              <span className="daa-section-num">4</span>
              <h2 className="daa-section-title">{improvement.kept ? "Improved version" : "Improvement result — original retained"}</h2>
            </div>

            <div className="daa-rewrite-comparison">
              <article><h3>Before</h3>
                <ClassifierResult result={improvement.before || analysis} />
                <p className="daa-original-text">{improvement.original_appeal}</p>
                <button className="daa-original-copy-btn" type="button" onClick={async () => { try { await navigator.clipboard.writeText(improvement.original_appeal); setCopyMessage("Original copied"); } catch { setCopyMessage("Copy unavailable; select the original text to copy."); } }}>Copy Original Appeal</button>
              </article>
              <article><h3>After{!improvement.kept && " (original retained)"}</h3>
                <ClassifierResult result={improvement.after || analysis} />
                <p>{improvement.improved_appeal}</p>
              </article>
            </div>
            {improvement.kept && improvement.message && <p role="status">{improvement.message}</p>}
            {copyMessage && <p role="status">{copyMessage}</p>}

            <div className="daa-copy-row">
              <button className="daa-copy-btn" type="button" onClick={handleCopy}>
                {copied ? "Copied" : improvement.kept ? "Copy Improved Appeal" : "Copy Original Appeal"}
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
