import React, { useState } from "react";
import Navigation from "../components/Navigation";
import Footer from "../components/Footer";
import "./Donation_Appeal.css";


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const REQUIRED_FIELDS = [
  ["location", "Location"],
  ["verified_need", "Verified Need"],
  ["campaign_goal", "Campaign Goal"],
];


async function generateAppealVariants(formData) {
  const response = await fetch(`${API_BASE_URL}/api/generate-appeal-variants`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(formData),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || "Failed to generate appeal variants.");
  }

  const data = await response.json();
  return data.variants || [];
}


async function evaluateAppeal(appealText, language) {
  const response = await fetch(`${API_BASE_URL}/api/quality/evaluate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      appeal_text: appealText,
      language,
    }),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || "Failed to evaluate appeal quality.");
  }

  return response.json();
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


function Donation_Appeal() {
  const [formData, setFormData] = useState({
    language: "en",
    campaign_type: "flood_relief",
    location: "",
    verified_need: "",
    campaign_goal: "",
    tone: "hopeful",
    channel: "facebook",
    length_category: "short",
  });
  const [generatedAppeal, setGeneratedAppeal] = useState("");
  const [variants, setVariants] = useState([]);
  const [activeVariantIndex, setActiveVariantIndex] = useState(0);
  const [generatedLanguage, setGeneratedLanguage] = useState(formData.language);
  const [loading, setLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState("");

  const activeVariant = variants[activeVariantIndex] || null;
  const activeQuality = activeVariant
    ? {
        score: Number(activeVariant.quality_score),
        status: activeVariant.quality_label,
        method: activeVariant.quality_method || activeVariant.method || "ml_model",
        confidence: Number(activeVariant.confidence || 0),
        confidenceNormalised: Number(
          activeVariant.confidence_normalised ?? activeVariant.confidence ?? 0
        ),
        confidenceDisplay: activeVariant.confidence_display,
      }
    : null;

  const getMissingRequiredFields = () =>
    REQUIRED_FIELDS.filter(([field]) => !formData[field]?.trim()).map(([, label]) => label);

  const isFormComplete = getMissingRequiredFields().length === 0;

  const validateForm = () => {
    const missingFields = getMissingRequiredFields();

    if (missingFields.length > 0) {
      const message = `Please fill in: ${missingFields.join(", ")}`;
      setError(message);
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

    setLoading(true);
    setError("");
    setGeneratedAppeal("");
    setVariants([]);
    setActiveVariantIndex(0);
    setGeneratedLanguage(requestData.language);

    try {
      const generatedVariants = await generateAppealVariants(requestData);

      if (!generatedVariants.length) {
        throw new Error("No appeal variants were generated.");
      }

      setVariants(generatedVariants);
      setGeneratedAppeal(generatedVariants[0].appeal_text);
      await handleSelectVariant(generatedVariants[0], requestData.language, 0);
    } catch (err) {
      setError(err.message || "Failed to generate appeal.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectVariant = async (variant, language = generatedLanguage, variantIndex = activeVariantIndex) => {
    setGeneratedAppeal(variant.appeal_text);
    setError("");
    setEvaluating(true);

    try {
      const quality = await evaluateAppeal(variant.appeal_text, language);
      setVariants((previousVariants) =>
        previousVariants.map((item, index) =>
          index === variantIndex
            ? {
                ...item,
                quality_label: quality.status,
                quality_score: quality.score,
                confidence: quality.confidence,
                confidence_normalised: quality.confidence_normalised,
                confidence_display: quality.confidence_display,
                quality_method: quality.method,
              }
            : item
        )
      );
    } catch (err) {
      setError(err.message || "Failed to evaluate appeal.");
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

  const handleCopy = async () => {
    if (!activeVariant) return;

    try {
      await navigator.clipboard.writeText(activeVariant.appeal_text);
      logCopyEvent(activeVariant, generatedLanguage).catch(() => {});
      alert("Appeal copied to clipboard");
    } catch {
      const textArea = document.createElement("textarea");
      textArea.value = activeVariant.appeal_text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
      logCopyEvent(activeVariant, generatedLanguage).catch(() => {});
      alert("Appeal copied to clipboard");
    }
  };

  const getStatus = (score, status) => {
    if (status) return status;
    if (!score && score !== 0) return "";
    if (score < 3.0) return "Needs improvement";
    if (score < 4.0) return "Acceptable";
    return "Good";
  };

  const getConfidence = () => {
    if (activeQuality?.confidenceDisplay) {
      return activeQuality.confidenceDisplay;
    }

    if (activeQuality?.confidenceNormalised || activeQuality?.confidenceNormalised === 0) {
      return `${Math.round(activeQuality.confidenceNormalised * 100)}%`;
    }

    return "";
  };

  return (
    <div className="donation-appeal-page">
      <Navigation />

      <main className="donation-appeal-container">
        <section className="donation-appeal-header">
          <span>Appeal Quality Evaluation</span>
          <h1>Donation Appeal Generator</h1>
          <p>
            Enter campaign details, generate an appeal, and evaluate its quality score.
          </p>
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
              <label htmlFor="verified_need">Verified Need</label>
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
                <option value="very_short">Very short (1 sentence)</option>
                <option value="short">Short (1-2 sentences)</option>
                <option value="medium">Medium (3-4 sentences)</option>
                <option value="long">Long (5+ sentences)</option>
              </select>
            </div>

            <button
              className="generate-button"
              type="button"
              onClick={handleGenerate}
              disabled={loading || !isFormComplete}
            >
              {loading ? "Generating..." : "Generate Appeal"}
            </button>

            {error && <p className="appeal-error">{error}</p>}
          </section>

          <div className="appeal-output-layout">
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
                    <div className="variant-card-header">
                      <span className={`quality-badge ${activeQuality?.status || ""}`}>
                        ● {activeQuality?.status}
                      </span>
                      <div style={{ display: "flex", gap: "0.35rem", alignItems: "center" }}>
                        {activeVariantIndex === 0 && (
                          <span className="best-match-badge">★ Best Match</span>
                        )}
                        <span className="score-chip">
                          {activeQuality?.score.toFixed(2)}
                        </span>
                        <span className="score-chip">
                          {getConfidence()}
                        </span>
                      </div>
                    </div>
                    <p>{activeVariant.appeal_text}</p>
                    <div className="variant-meta">
                      <span>{activeVariant.model}</span>
                      {activeVariant.style && <span>{activeVariant.style}</span>}
                      <span>T {activeVariant.temperature}</span>
                    </div>
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
                    <button type="button" onClick={handleCopy}>
                      Copy Text
                    </button>
                  </div>
                </>
              )}
            </section>

            <section className="quality-results">
              <h2>Quality Evaluation</h2>

              {!activeQuality && !evaluating && (
                <p className="result-placeholder">
                  Generate or switch an appeal variant to view its quality details.
                </p>
              )}

              {evaluating && (
                <p className="result-placeholder">
                  Evaluating selected appeal...
                </p>
              )}

              {activeQuality && (
                <div className="quality-box">
                  <div className="score-hero">
                    <div>
                      <span className="score-hero-number">
                        {activeQuality.score.toFixed(2)}
                      </span>
                      <span className="score-hero-denom"> / 5</span>
                    </div>
                    <div className="score-hero-label">Appeal Quality Score</div>
                    <div className="score-progress">
                      <div
                        className="score-progress-fill"
                        style={{ width: `${(activeQuality.score / 5) * 100}%` }}
                      />
                    </div>
                  </div>

                  <div className="quality-row">
                    <span>Status</span>
                    <strong className={`status-pill ${activeQuality.status || ""}`}>
                      {getStatus(activeQuality.score, activeQuality.status)}
                    </strong>
                  </div>

                  <div className="quality-row">
                    <span>Method</span>
                    <strong className="status-pill method">
                      {activeQuality.method}
                    </strong>
                  </div>

                  <div className="quality-row">
                    <span>Confidence</span>
                    <div className="confidence-row">
                      <div className="confidence-bar">
                        <div
                          className="confidence-fill"
                          style={{
                            width: activeQuality.confidenceDisplay
                              ? activeQuality.confidenceDisplay
                              : `${Math.round(activeQuality.confidenceNormalised * 100)}%`,
                          }}
                        />
                      </div>
                      <strong>{getConfidence()}</strong>
                    </div>
                  </div>
                </div>
              )}
            </section>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}


export default Donation_Appeal;
