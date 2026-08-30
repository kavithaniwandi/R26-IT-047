import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import "./PriorityApplication.css";

const SESSION_KEY = "severityQueueSession";
const STORAGE_KEY = "priorityApplications";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const RED_FLAGS = [
  "breathing_difficulty",
  "chest_pain",
  "focal_neurologic_deficit",
  "active_bleeding",
  "syncope",
  "seizure",
];

const SEV_COLOR = {
  CRITICAL: "#b91c1c",
  HIGH: "#c2410c",
  MEDIUM: "#b45309",
  LOW: "#15803d",
};

const SEV_BG = {
  CRITICAL: "#fef1ee",
  HIGH: "#fef1ee",
  MEDIUM: "#fef6e8",
  LOW: "#ebf7f0",
};

const OVERRIDE_REASONS = [
  "Clinical exam suggests lower acuity",
  "Stable vitals observed",
  "Symptoms improved after initial care",
  "Documentation clarified by MO",
  "Other clinical judgement",
];

function routeMO(mos, severity, conditionGroup) {
  const eligible = mos.filter((mo) => {
    const isJuniorWithoutSupervisor =
      ["Intern", "Resident"].includes(mo.role) && mo.supervisor !== "yes";
    return !(severity === "HIGH" && isJuniorWithoutSupervisor);
  });

  if (!eligible.length) return null;

  const roleWeight = {
    "Senior MO": 1.0,
    "Medical Officer": 0.85,
    Resident: 0.65,
    Intern: 0.45,
  };

  const scored = eligible.map((mo) => {
    const condition = conditionGroup.toLowerCase();
    const specMatch =
      mo.specialty.toLowerCase().includes(condition) ||
      mo.skills.some((skill) => skill.name.toLowerCase().includes(condition));
    const roleScore = roleWeight[mo.role] || 0.5;
    const loadScore = 1 / (1 + (mo.queueDepth || 0));

    return {
      mo,
      score: roleScore * (0.5 + 0.5 * Number(specMatch)) * loadScore,
    };
  });

  scored.sort((first, second) => second.score - first.score);
  return scored[0].mo;
}

export default function PriorityApplication() {
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [form, setForm] = useState({ age: "", symptoms: "", clinicalNote: "" });
  const [checkedFlags, setCheckedFlags] = useState([]);
  const [severityResult, setSeverityResult] = useState(null);
  const [assignedMO, setAssignedMO] = useState(null);
  const [extractResult, setExtractResult] = useState(null);
  const [overrideSeverity, setOverrideSeverity] = useState("");
  const [overrideReason, setOverrideReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) {
      navigate("/camp-setup");
      return;
    }
    setSession(JSON.parse(raw));
  }, [navigate]);

  useEffect(() => {
    if (!severityResult || !extractResult || !overrideSeverity) return;

    const currentSession = JSON.parse(localStorage.getItem(SESSION_KEY));
    setAssignedMO(routeMO(currentSession.mos, overrideSeverity, extractResult.specialty));
  }, [extractResult, overrideSeverity, severityResult]);

  const handleFlagToggle = (flag) => {
    setCheckedFlags((previous) =>
      previous.includes(flag)
        ? previous.filter((item) => item !== flag)
        : [...previous, flag]
    );
  };

  const updateFormField = (field, value) => {
    setForm((previous) => ({ ...previous, [field]: value }));
  };

  const validatePatientForm = () => {
    const age = form.age === "" ? null : Number(form.age);
    const symptoms = form.symptoms.trim();
    const clinicalNote = form.clinicalNote.trim();

    if (form.age !== "" && (!Number.isFinite(age) || age < 0 || age > 120)) {
      return "Age must be between 0 and 120.";
    }

    if (!symptoms) {
      return "Presenting symptoms are required.";
    }
    if (symptoms.length < 8) {
      return "Add a little more symptom detail.";
    }

    if (!clinicalNote) {
      return "Clinical note is required.";
    }
    if (clinicalNote.length < 12) {
      return "Clinical note must include enough detail to classify.";
    }

    return "";
  };

  const handleClassify = async () => {
    const validationError = validatePatientForm();
    if (validationError) {
      setError(validationError);
      window.alert(validationError);
      return;
    }

    setLoading(true);
    setError("");
    setSeverityResult(null);
    setAssignedMO(null);
    setExtractResult(null);
    setOverrideSeverity("");
    setOverrideReason("");

    try {
      const extractRes = await fetch(`${API_BASE_URL}/api/severity/extract`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clinical_note: form.clinicalNote,
          symptoms: form.symptoms,
        }),
      });

      let extractData;
      try {
        extractData = await extractRes.json();
      } catch {
        throw new Error("NLP extraction returned unreadable response.");
      }

      if (!extractRes.ok) {
        console.error("NLP extraction error:", extractData);
        throw new Error(
          typeof extractData?.detail === "string"
            ? extractData.detail
            : "NLP extraction failed."
        );
      }

      if (!extractData.valid || extractData.extracted_symptoms.length === 0) {
        throw new Error(
          "No recognisable medical content found in the clinical note. " +
          "Please enter a valid clinical description before classifying."
        );
      }

      const conditionGroup = extractData.condition_group;
      const specialty = extractData.specialty;
      const hasRedFlag = checkedFlags.length > 0 ? 1 : 0;
      const rfFlagsObj = Object.fromEntries(checkedFlags.map((flag) => [flag, 1]));

      const classifyRes = await fetch(`${API_BASE_URL}/api/severity/classify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clinical_note: form.clinicalNote,
          age: form.age === "" ? null : Number(form.age),
          mode: "ml",
          source: session?.camp?.type?.toUpperCase() || "TRIAGE",
          condition_group: conditionGroup,
          has_red_flag: hasRedFlag,
          red_flag_count: checkedFlags.length,
          rf_flags: rfFlagsObj,
          symptoms: form.symptoms,
        }),
      });

      let classifyData;
      try {
        classifyData = await classifyRes.json();
      } catch {
        throw new Error("Classification returned unreadable response.");
      }

      if (!classifyRes.ok) {
        console.error("Backend error:", classifyData);
        throw new Error(
          typeof classifyData?.detail === "string"
            ? classifyData.detail
            : "Classification failed."
        );
      }

      const currentSession = JSON.parse(localStorage.getItem(SESSION_KEY));
      const mo = routeMO(currentSession.mos, classifyData.severity, specialty);

      setSeverityResult(classifyData);
      setAssignedMO(mo);
      setOverrideSeverity(classifyData.severity);
      setOverrideReason("");
      setExtractResult({
        conditionGroup,
        specialty,
        extractedSymptoms: extractData.extracted_symptoms,
      });
    } catch (err) {
      setError(typeof err?.message === "string" ? err.message : "Classification failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!severityResult) {
      setError("Classify severity before submitting.");
      return;
    }
    const finalSeverity = overrideSeverity || severityResult.severity;
    const hasOverride = finalSeverity !== severityResult.severity;

    if (hasOverride && !overrideReason) {
      const message = "Select a clinical override reason before submitting.";
      setError(message);
      window.alert(message);
      return;
    }

    if (!severityResult.should_queue && !hasOverride) {
      setError(severityResult.queue_description);
      return;
    }

    const currentSession = JSON.parse(localStorage.getItem(SESSION_KEY));
    const conditionGroup = extractResult?.conditionGroup || "General Practice";
    const specialty = extractResult?.specialty || "General Practice";

    const routedMO = routeMO(currentSession.mos, finalSeverity, specialty);

    if (routedMO) {
      currentSession.mos = currentSession.mos.map((mo) =>
        mo.id === routedMO.id
          ? { ...mo, queueDepth: (mo.queueDepth || 0) + 1 }
          : mo
      );
      localStorage.setItem(SESSION_KEY, JSON.stringify(currentSession));
    }

    const currentApplications = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    const patientId = `PT-${String(currentApplications.length + 1).padStart(4, "0")}`;
    const entry = {
      id: patientId,
      submittedAt: new Date().toISOString(),
      title: severityResult.queue_title,
      description: severityResult.queue_description,
      recommended_action: severityResult.recommended_action,
      queue_reason: severityResult.queue_reason,
      queue_reason_text: severityResult.queue_reason_text,
      display_note: hasOverride
        ? `Clinician override applied: ${severityResult.severity} changed to ${finalSeverity}.`
        : severityResult.display_note,
      source: session?.camp?.type?.toUpperCase() || "TRIAGE",
      severity: finalSeverity,
      ai_severity: severityResult.severity,
      scores: severityResult.scores,
      risk_score: severityResult.risk_score,
      priority_score: severityResult.priority_score,
      method: severityResult.method,
      symptoms: form.symptoms,
      age: form.age,
      red_flags: checkedFlags,
      condition_group: conditionGroup,
      specialty,
      extracted_symptoms: extractResult?.extractedSymptoms || [],
      camp: session?.camp || null,
      assigned_mo_id: routedMO?.id || null,
      assigned_mo_name: routedMO?.name || null,
      clinician_override: hasOverride
        ? {
            from: severityResult.severity,
            to: finalSeverity,
            reason: overrideReason,
            created_at: new Date().toISOString(),
          }
        : null,
      critical_trigger: severityResult.critical_trigger,
      matched_rules: severityResult.matched_rules,
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify([entry, ...currentApplications]));
    api.saveTriagePatient({
      ...entry,
      session_id: currentSession.session_id,
    }).catch((error) => {
      console.warn("[triage] patient save:", error);
    });
    navigate("/priority-queue");
  };

  if (!session) return null;

  return (
    <div className="priority-application-page">
      <main className="priority-application-container">
        <section className="priority-application-header">
          <span>{session.camp.code} - {session.camp.name}</span>
          <h1>Patient Intake</h1>
          <p>
            Enter presenting symptoms and clinical note. The ML model will classify severity
            and assign the case to the best available MO.
          </p>
        </section>

        <section className="priority-application-panel">
          <form className="priority-application-form" onSubmit={handleSubmit}>
            <div className="priority-application-group">
              <label htmlFor="age">Patient Age</label>
              <input
                id="age"
                name="age"
                type="number"
                min="0"
                max="120"
                value={form.age}
                onChange={(event) => updateFormField("age", event.target.value)}
                placeholder="e.g. 45"
              />
            </div>

            <div className="priority-application-group">
              <label htmlFor="symptoms">Presenting Symptoms / Complaint <span>*</span></label>
              <textarea
                id="symptoms"
                rows={3}
                value={form.symptoms}
                onChange={(event) => updateFormField("symptoms", event.target.value)}
                placeholder="e.g. Shortness of breath, chest tightness, dizziness"
                required
              />
            </div>

            <div className="priority-application-group">
              <label>Red Flags Observed</label>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginTop: "6px" }}>
                {RED_FLAGS.map((flag) => {
                  const active = checkedFlags.includes(flag);
                  return (
                    <label
                      key={flag}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "6px",
                        fontSize: "12px",
                        fontWeight: active ? 600 : 400,
                        cursor: "pointer",
                        background: active ? "#fef1ee" : "#f1f5f9",
                        border: `1px solid ${active ? "#f4b5a8" : "#e2e8f0"}`,
                        color: active ? "#c23b22" : "#475569",
                        padding: "5px 12px",
                        borderRadius: "6px",
                        userSelect: "none",
                        transition: "all 0.15s",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={active}
                        onChange={() => handleFlagToggle(flag)}
                        style={{
                          width: "14px",
                          height: "14px",
                          margin: 0,
                          flexShrink: 0,
                          cursor: "pointer",
                          accentColor: "#c23b22",
                        }}
                      />
                      {flag.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase())}
                    </label>
                  );
                })}
              </div>
            </div>

            <div className="priority-application-group">
              <label htmlFor="clinicalNote">Clinical Note <span>*</span></label>
              <textarea
                id="clinicalNote"
                rows={5}
                value={form.clinicalNote}
                onChange={(event) => updateFormField("clinicalNote", event.target.value)}
                placeholder="Enter detailed clinical note for ML severity classification"
                required
              />
            </div>

            <button
              className="priority-application-submit"
              type="button"
              onClick={handleClassify}
              disabled={loading}
            >
              {loading ? "Classifying..." : "Classify and Assign"}
            </button>

            {error && <div className="priority-application-error">{error}</div>}

            {severityResult && (
              <div
                className="priority-result-card"
                style={{
                  background: SEV_BG[severityResult.severity] || "#f1f5f9",
                  borderColor: `${SEV_COLOR[severityResult.severity]}55`,
                }}
              >
                <div className="priority-result-header">
                  <span>Classification Result</span>
                  <strong style={{ background: SEV_COLOR[severityResult.severity] }}>
                    {severityResult.severity}
                  </strong>
                </div>

                <div className="priority-result-grid">
                  {[
                    ["Priority Score", severityResult.priority_score],
                    ["Risk Score", `${severityResult.risk_score} / 100`],
                    ["Method", severityResult.method],
                    ["Queue Decision", severityResult.should_queue ? "Add to queue" : "Do not queue"],
                  ].map(([label, value]) => (
                    <div key={label} className="priority-result-metric">
                      <span>{label}</span>
                      <strong>{value}</strong>
                    </div>
                  ))}
                </div>

                <p className="priority-result-note">{severityResult.display_note}</p>

                <div className="priority-ai-review-note">
                  This classification is AI-assisted. The assigned MO should review and override
                  if clinically inappropriate before confirming.
                </div>

                {!severityResult.critical_trigger && (
                  <div className="priority-override-panel">
                    <div className="priority-override-head">
                      <span>Clinical Override</span>
                      <strong>
                        {overrideSeverity === severityResult.severity
                          ? "AI result kept"
                          : `${severityResult.severity} -> ${overrideSeverity}`}
                      </strong>
                    </div>
                    <div className="priority-override-buttons">
                      {["HIGH", "MEDIUM", "LOW"].map((severity) => (
                        <button
                          key={severity}
                          type="button"
                          className={`priority-override-btn ${overrideSeverity === severity ? "selected" : ""}`}
                          onClick={() => {
                            setOverrideSeverity(severity);
                            if (severity === severityResult.severity) {
                              setOverrideReason("");
                            }
                          }}
                          style={{
                            borderColor: overrideSeverity === severity ? SEV_COLOR[severity] : undefined,
                            color: overrideSeverity === severity ? SEV_COLOR[severity] : undefined,
                            background: overrideSeverity === severity ? SEV_BG[severity] : undefined,
                          }}
                        >
                          {severity}
                        </button>
                      ))}
                    </div>
                    {overrideSeverity !== severityResult.severity && (
                      <select
                        className="priority-override-select"
                        value={overrideReason}
                        onChange={(event) => setOverrideReason(event.target.value)}
                      >
                        <option value="">Select override reason...</option>
                        {OVERRIDE_REASONS.map((reason) => (
                          <option key={reason} value={reason}>
                            {reason}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                )}

                {severityResult.critical_trigger && (
                  <p className="priority-result-critical">
                    Critical trigger: {severityResult.critical_trigger}
                  </p>
                )}

                {severityResult.matched_rules?.length > 0 && (
                  <p className="priority-result-rules">
                    Matched rules: {severityResult.matched_rules.join(", ")}
                  </p>
                )}

                {assignedMO ? (
                  <div className="priority-assigned-mo">
                    <span>Assigned MO</span>
                    <strong>{assignedMO.name}</strong>
                    <p>{assignedMO.role} - {assignedMO.specialty}</p>
                  </div>
                ) : (
                  <div className="priority-unassigned-alert">
                    No eligible MO available - manual assignment required.
                  </div>
                )}
              </div>
            )}

            {severityResult && (
              <button className="priority-application-submit" type="submit">
                Submit to Queue
              </button>
            )}
          </form>
        </section>
      </main>

    </div>
  );
}
