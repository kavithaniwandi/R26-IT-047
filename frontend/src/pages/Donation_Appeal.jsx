import React, { useState } from "react";
import { Link } from "react-router-dom";
import CreditStatusBar from "../components/CreditStatusBar";
import "./Donation_Appeal.css";
import AppealScorecard from "../components/AppealScorecard";
import LENGTH_CONFIG from "../config/appealLengths.json";


const API_BASE_URL = "";

const MIN_APPEAL_LENGTH = 10;
const MAX_APPEAL_LENGTH = 10_000;

const REQUIRED_FIELDS = [
  ["location", "Location"],
  ["verified_need", "Specific need"],
  ["campaign_goal", "Campaign Goal"],
];


async function appealRequest(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail
      : data?.detail ? JSON.stringify(data.detail) : "Appeal request failed.";
    const message = `HTTP ${response.status}: ${detail}`;
    if (response.status === 422) throw new ValidationError(message);
    throw new Error(message);
  }
  if (!data || typeof data !== "object") throw new Error(`HTTP ${response.status}: Invalid response body.`);
  return data;
}

function responseVariants(data) {
  return Array.isArray(data?.variants) ? data.variants.filter(item => typeof item?.appeal_text === "string" && item.appeal_text.trim()) : [];
}

const LABEL_RANK = { low: 0, medium: 1, high: 2 };

function orderVariants(items, category) {
  const band = LENGTH_CONFIG[category] || LENGTH_CONFIG.short;
  const inside = item => { const words = item.appeal_text.trim().split(/\s+/).filter(Boolean).length; return words >= band.minimum && words <= band.maximum; };
  return [...items].sort((a, b) => Number(inside(b)) - Number(inside(a))
    || Number(b.label_agreement === true) - Number(a.label_agreement === true)
    || (LABEL_RANK[b.final_label] ?? -1) - (LABEL_RANK[a.final_label] ?? -1)
    || Number(b.classifier_confidence ?? b.confidence ?? 0) - Number(a.classifier_confidence ?? a.confidence ?? 0)
    || Number(b.quality_score) - Number(a.quality_score));
}

function AppealLengthWarning({ result }) {
  if (!result?.length_warning) return null;
  return <div className="appeal-length-warning" role="note">
    <p>{String(result.length_warning)}</p>
  </div>;
}

function partialGenerationMessage(data) {
  let message = "Some variants are unavailable. The available appeal is kept below.";
  if (data.generation_error) message += ` ${data.generation_error}`;
  if (data.retry_after_seconds > 0) message += ` Try Generate Appeal again in about ${data.retry_after_seconds} seconds.`;
  return message;
}


async function evaluateAppeal(appealText, language, campaign = {}) {
  const trimmed = (appealText || "").trim();
  if (!trimmed) {
    throw new ValidationError("Appeal text is empty and cannot be evaluated.");
  }
  if (trimmed.length < MIN_APPEAL_LENGTH) {
    throw new ValidationError(
      `Appeal is too short to evaluate (${trimmed.length} characters). Minimum is ${MIN_APPEAL_LENGTH}.`
    );
  }
  if (trimmed.length > MAX_APPEAL_LENGTH) {
    throw new ValidationError(
      `Appeal exceeds the maximum length of ${MAX_APPEAL_LENGTH.toLocaleString()} characters.`
    );
  }

  return appealRequest("/api/quality/evaluate", { ...campaign, appeal_text: trimmed, language });
}


async function logCopyEvent(variant, language) {
  if (!variant) return;

  await fetch(`${API_BASE_URL}/api/log-copy`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      appeal_text: variant.appeal_text,
      language,
      quality_score: variant.quality_score,
      quality_label: variant.quality_label,
      confidence: variant.confidence,
      confidence_normalised: variant.confidence_normalised,
      confidence_display: variant.confidence_display,
      style: variant.style,
    }),
  });
}


class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = "ValidationError";
  }
}


function Donation_Appeal() {
  const [formData, setFormData] = useState({
    language: "en",
    campaign_type: "flood_relief",
    location: "",
    verified_need: "",
    campaign_goal: "Support affected families and help the community in need",
    tone: "hopeful",
    channel: "facebook",
    length_category: "short",
  });
  const [generatedAppeal, setGeneratedAppeal] = useState("");
  const [variants, setVariants] = useState([]);
  const [activeVariantIndex, setActiveVariantIndex] = useState(0);
  const [generatedLanguage, setGeneratedLanguage] = useState(formData.language);
  const [loading, setLoading] = useState(false);
  const [loadingRemaining, setLoadingRemaining] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [generateError, setGenerateError] = useState("");
  const [evaluateError, setEvaluateError] = useState("");
  const [evaluateErrorIsValidation, setEvaluateErrorIsValidation] = useState(false);

  const [finalizing, setFinalizing] = useState(false);
  const [partialMessage, setPartialMessage] = useState("");
  const [copyMessage, setCopyMessage] = useState("");
  const [generatedRequest, setGeneratedRequest] = useState({});
  const activeVariant = variants[activeVariantIndex] || null;
  const getMissingRequiredFields = () =>
    REQUIRED_FIELDS.filter(([field]) => !formData[field]?.trim()).map(([, label]) => label);

  const isFormComplete = getMissingRequiredFields().length === 0;

  const validateForm = () => {
    const missingFields = getMissingRequiredFields();

    if (missingFields.length > 0) {
      const message = `Please fill in: ${missingFields.join(", ")}`;
      setGenerateError(message);
      alert(message);
      return false;
    }

    return true;
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((previousData) => ({
      ...previousData,
      [name]: value,
    }));
  };

  const handleGenerate = async () => {
    if (!validateForm()) return;

    const requestData = { ...formData };
    setGeneratedRequest(requestData);
    setFinalizing(true);
    setPartialMessage("");
    setCopyMessage("");

    setLoading(true);
    setGenerateError("");
    setEvaluateError("");
    setEvaluateErrorIsValidation(false);
    setLoadingRemaining(false);
    setGeneratedAppeal("");
    setVariants([]);
    setActiveVariantIndex(0);
    setGeneratedLanguage(requestData.language);

    try {
      const first = await appealRequest("/api/generate-appeal-variants", requestData);
      const firstVariants = responseVariants(first);

      if (!firstVariants.length) {
        throw new Error("No appeal variants were generated.");
      }

      setVariants(firstVariants);
      if (first.partial) setPartialMessage(partialGenerationMessage(first));
      setGeneratedAppeal(firstVariants[0].appeal_text);
      setLoading(false);

      await handleSelectVariant(firstVariants[0], requestData.language, 0, requestData);

      setLoadingRemaining(true);
      appealRequest("/api/generate-appeal-variants/remaining", requestData)
        .then((data) => {
          const remainingVariants = responseVariants(data);
          if (data.partial || !remainingVariants.length) setPartialMessage(partialGenerationMessage(data));
          else setPartialMessage("");
          if (remainingVariants.length > 0) {
            const unique = new Map(firstVariants.map(variant => [`${variant.style || ""}:${variant.appeal_text.trim()}`, variant]));
            for (const variant of remainingVariants) unique.set(`${variant.style || ""}:${variant.appeal_text.trim()}`, variant);
            const ordered = orderVariants([...unique.values()], requestData.length_category);
            setVariants(ordered);
            setActiveVariantIndex(0);
            setGeneratedAppeal(ordered[0].appeal_text);
          }
        })
        .catch((err) => {
          setPartialMessage(`More variants unavailable. ${err.message}`);
        })
        .finally(() => {
          setLoadingRemaining(false);
          setFinalizing(false);
        });
    } catch (err) {
      setGenerateError(err.message || "Failed to generate appeal.");
      setLoading(false);
      setFinalizing(false);
    }
  };

  const handleSelectVariant = async (variant, language = generatedLanguage, variantIndex = activeVariantIndex, campaign = generatedRequest) => {
    setGeneratedAppeal(variant.appeal_text);
    setEvaluateError("");
    setEvaluateErrorIsValidation(false);
    setEvaluating(true);

    try {
      const quality = await evaluateAppeal(variant.appeal_text, language, campaign);
      setVariants((previousVariants) =>
        previousVariants.map((item, index) =>
          index === variantIndex
            ? {
                ...item,
                ...quality,
                quality_label: quality.status,
                final_label: quality.final_label ?? quality.status,
                quality_score: quality.score,
                confidence: quality.confidence,
                confidence_normalised: quality.confidence_normalised,
                confidence_display: quality.confidence_display,
                low_confidence: quality.low_confidence ?? false,
                quality_method: quality.method,
                predicted_class: quality.predicted_class ?? null,
                class_probs: quality.class_probs ?? {},
              }
            : item
        )
      );
    } catch (err) {
      const isValidation = err instanceof ValidationError;
      setEvaluateError(err.message || "Failed to evaluate appeal.");
      setEvaluateErrorIsValidation(isValidation);
    } finally {
      setEvaluating(false);
    }
  };

  const showVariant = async (nextIndex) => {
    if (!variants.length || evaluating) return;

    const wrappedIndex = (nextIndex + variants.length) % variants.length;
    setActiveVariantIndex(wrappedIndex);
    await handleSelectVariant(variants[wrappedIndex], generatedLanguage, wrappedIndex);
  };

  const handleCopy = async (variant = activeVariant) => {
    if (!variant) return;
    try {
      await navigator.clipboard.writeText(variant.appeal_text);
      logCopyEvent(variant, generatedLanguage).catch(() => {});
      setCopyMessage("Appeal copied to clipboard");
    } catch {
      // Preserve the existing copy fallback when Clipboard API access is unavailable.
      const textArea = document.createElement("textarea");
      textArea.value = variant.appeal_text;
      document.body.appendChild(textArea);
      textArea.select();
      try {
        if (!document.execCommand("copy")) throw new Error("Copy unavailable");
        logCopyEvent(variant, generatedLanguage).catch(() => {});
        setCopyMessage("Appeal copied to clipboard");
      } catch {
        setCopyMessage("Copy unavailable; select the appeal text to copy it manually.");
      } finally {
        textArea.remove();
      }
    }
  };

  return (
    <div className="donation-appeal-page">
      <main className="donation-appeal-container">
        <section className="donation-appeal-header">
          <div>
            <span>Appeal Quality Evaluation</span>
            <h1>Donation Appeal Generator</h1>
            <p>
              Enter campaign details, generate an appeal, and evaluate its quality score.
            </p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <CreditStatusBar />
            <Link
              className="appeal-analyzer-button"
              to="/donation-appeal-analyzer"
            >
              Donation Appeal Analyzer
            </Link>
          </div>
        </section>

        <div className="donation-appeal-layout">
          <section className="campaign-form">
            <h2>Campaign Details</h2>

            <div className="form-group">
              <label htmlFor="language">Language</label>
              <select
                id="language"
                name="language"
                value={formData.language}
                onChange={handleChange}
              >
                <option value="en">English</option>
                <option value="si">Sinhala</option>
                <option value="ta">Tamil</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="campaign_type">Campaign Type</label>
              <select
                id="campaign_type"
                name="campaign_type"
                value={formData.campaign_type}
                onChange={handleChange}
              >
                <option value="flood_relief">Flood Relief</option>
                <option value="financial_emergency">Financial Emergency</option>
                <option value="landslide">Landslide</option>
                <option value="cyclone">Cyclone</option>
                <option value="drought">Drought</option>
                <option value="education">Education</option>
                <option value="children">Children</option>
                <option value="charity_general">Charity General</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="location">Location</label>
              <input
                id="location"
                type="text"
                name="location"
                value={formData.location}
                onChange={handleChange}
                placeholder="e.g. Gampaha"
              />
            </div>

            <div className="form-group">
              <label htmlFor="verified_need">Specific need</label>
              <input
                id="verified_need"
                type="text"
                name="verified_need"
                value={formData.verified_need}
                onChange={handleChange}
                placeholder="e.g. Household supplies"
              />
            </div>

            <div className="form-group">
              <label htmlFor="campaign_goal">Campaign Goal</label>
              <input
                id="campaign_goal"
                type="text"
                name="campaign_goal"
                value={formData.campaign_goal}
                onChange={handleChange}
                placeholder="e.g. Support affected families"
              />
            </div>

            <div className="form-group">
              <label htmlFor="tone">Tone</label>
              <select
                id="tone"
                name="tone"
                value={formData.tone}
                onChange={handleChange}
              >
                <option value="hopeful">Hopeful</option>
                <option value="urgent">Urgent</option>
                <option value="compassionate">Compassionate</option>
                <option value="trust">Trustworthy</option>
                <option value="community">Community-focused</option>
                <option value="direct">Direct</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="channel">Channel</label>
              <select
                id="channel"
                name="channel"
                value={formData.channel}
                onChange={handleChange}
              >
                <option value="facebook">Facebook</option>
                <option value="website">Website</option>
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="whatsapp">WhatsApp</option>
                <option value="direct">Direct</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="length_category">Length</label>
              <select
                id="length_category"
                name="length_category"
                value={formData.length_category}
                onChange={handleChange}
              >
                {Object.entries(LENGTH_CONFIG).filter(([, band]) => band.visible !== false).map(([key, band]) => <option key={key} value={key}>{band.name} (about {band.minimum}-{band.maximum} words)</option>)}
              </select>
            </div>

            <button
              className="generate-button"
              type="button"
              onClick={handleGenerate}
              disabled={loading || loadingRemaining || finalizing || evaluating || !isFormComplete}
            >
              {loading ? "Generating..." : "Generate Appeal"}
            </button>

            {generateError && (
              <p className="appeal-error" role="alert">
                {generateError}
              </p>
            )}
          </section>

          <div className="appeal-output-layout">
            {finalizing && <p className="appeal-final-progress" role="status">Choosing your final appeal after all available variants are checked...</p>}
            {partialMessage && <p className="appeal-partial-note" role="status">{partialMessage}</p>}
            {copyMessage && <p role="status">{copyMessage}</p>}
            <section className="appeal-results">
              <h2>Generated Appeal</h2>

              {!generatedAppeal && variants.length === 0 && !loading && (
                <p className="result-placeholder">
                  Enter campaign details and click Generate Appeal to see the result here.
                </p>
              )}

              {loading && (
                <p className="result-placeholder">
                  Generating appeal variants...
                </p>
              )}

              {variants.length > 0 && (
                <div className="variant-viewer">
                  <div className="variant-controls">
                    <button
                      aria-label="Previous appeal variant"
                      className="variant-arrow"
                      type="button"
                      onClick={() => showVariant(activeVariantIndex - 1)}
                      disabled={evaluating}
                    >
                      &lt;
                    </button>
                    <span className="variant-count">
                      {activeVariantIndex + 1}/{variants.length}
                      {loadingRemaining && (
                        <span className="remaining-loading" title="Loading more variants...">
                          {" "}...
                        </span>
                      )}
                    </span>
                    <button
                      aria-label="Next appeal variant"
                      className="variant-arrow"
                      type="button"
                      onClick={() => showVariant(activeVariantIndex + 1)}
                      disabled={evaluating}
                    >
                      &gt;
                    </button>
                  </div>

                  <div className="variant-card">
                    {activeVariant?.generator_status === "fallback" && (
                      <div className="fallback-banner" role="alert">
                        <span className="fallback-banner-icon">⚠</span>
                        <div>
                          <strong>Generation unavailable — template used</strong>
                          <p>This is a local template, not a live Gemini response. Check it before publishing.</p>
                          <p>
                            {activeVariant.generator_error
                              ? activeVariant.generator_error
                              : "All generation providers failed. Edit this placeholder before publishing."}
                          </p>
                        </div>
                      </div>
                    )}
                    <p>{activeVariant.appeal_text}</p>
                    {activeVariant.generator_status !== "fallback" && <AppealScorecard result={activeVariant} />}
                    {evaluating && <p role="status">Evaluating selected appeal...</p>}
                    {evaluateError && <div className={`appeal-error-box ${evaluateErrorIsValidation ? "validation" : "api"}`} role="alert">{evaluateError}</div>}
                    <AppealLengthWarning result={activeVariant} />
                    {activeVariant.style && <div className="variant-meta"><span>{activeVariant.style}</span></div>}
                  </div>
                </div>
              )}

              {generatedAppeal && (
                <>
                  {variants.length === 0 && (
                    <div className="appeal-box">
                      <p>{generatedAppeal}</p>
                    </div>
                  )}

                  <div className="result-actions">
                    <button type="button" onClick={() => handleCopy()}>
                      Copy Text
                    </button>
                  </div>
                </>
              )}
            </section>


          </div>
        </div>
      </main>
    </div>
  );
}


export default Donation_Appeal;
