import { useState, useCallback } from "react";
import { saveRequest } from "../services/db";
import { useNetworkStatus } from "../hooks/useNetworkStatus";

// ── Medicine row default ───────────────────────────────────
const emptyMedicine = () => ({ id: Date.now() + Math.random(), name: "", grams: "" });

const URGENCY_LEVELS = [
  {
    value: "critical",
    label: "Critical",
    description: "Life-threatening, immediate attention required",
    color: "#c0392b",
    bg: "#fdf0ef",
    border: "#e74c3c",
    pulse: true,
  },
  {
    value: "high",
    label: "High",
    description: "Serious condition, urgent care needed",
    color: "#d35400",
    bg: "#fef5ec",
    border: "#e67e22",
    pulse: false,
  },
  {
    value: "normal",
    label: "Normal",
    description: "Stable, requires medical attention",
    color: "#1a6b3c",
    bg: "#edfaf3",
    border: "#27ae60",
    pulse: false,
  },
];

const MEDICAL_NEEDS = [
  "Injury / Trauma",
  "Respiratory Distress",
  "Cardiac Emergency",
  "Infection / Fever",
  "Diabetic Emergency",
  "Maternity / Obstetric",
  "Mental Health Crisis",
  "Chronic Disease Flare",
  "Pediatric Emergency",
  "Other",
];

export default function RequestForm() {
  const { isOnline, refreshPendingCount } = useNetworkStatus();

  const [form, setForm] = useState({
    patientName: "",
    age: "",
    urgency: "",
    medicalNeed: "",
    medicines: [emptyMedicine()],
    notes: "",
    location: null,
  });

  const [gpsStatus, setGpsStatus] = useState("idle"); // idle | loading | success | error
  const [submitStatus, setSubmitStatus] = useState(null); // null | saving | queued | synced | error
  const [errors, setErrors] = useState({});

  // ── GPS capture ─────────────────────────────────────────
  const captureGPS = useCallback(() => {
    if (!navigator.geolocation) {
      setGpsStatus("error");
      return;
    }
    setGpsStatus("loading");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setForm((f) => ({
          ...f,
          location: {
            lat: pos.coords.latitude.toFixed(6),
            lng: pos.coords.longitude.toFixed(6),
            accuracy: Math.round(pos.coords.accuracy),
          },
        }));
        setGpsStatus("success");
      },
      () => setGpsStatus("error"),
      { timeout: 10000, enableHighAccuracy: true }
    );
  }, []);

  // ── Medicine list helpers ────────────────────────────────
  const addMedicine = () =>
    setForm((f) => ({ ...f, medicines: [...f.medicines, emptyMedicine()] }));

  const removeMedicine = (id) =>
    setForm((f) => ({
      ...f,
      medicines: f.medicines.filter((m) => m.id !== id),
    }));

  const updateMedicine = (id, field, value) =>
    setForm((f) => ({
      ...f,
      medicines: f.medicines.map((m) => (m.id === id ? { ...m, [field]: value } : m)),
    }));

  // ── Validation ───────────────────────────────────────────
  const validate = () => {
    const e = {};
    if (!form.patientName.trim()) e.patientName = "Patient name is required";
    if (!form.age || form.age < 0 || form.age > 120) e.age = "Enter a valid age";
    if (!form.urgency) e.urgency = "Select urgency level";
    if (!form.medicalNeed) e.medicalNeed = "Select medical need type";
    form.medicines.forEach((m, i) => {
      if (m.name.trim() && !m.grams) e[`med_grams_${i}`] = "Enter amount";
      if (!m.name.trim() && m.grams) e[`med_name_${i}`] = "Enter medicine name";
    });
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  // ── Submit ───────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitStatus("saving");
    try {
      const payload = {
        ...form,
        medicines: form.medicines.filter((m) => m.name.trim()),
        submittedAt: new Date().toISOString(),
      };
      await saveRequest(payload);
      await refreshPendingCount();
      setSubmitStatus(isOnline ? "synced" : "queued");
      // Reset form
      setForm({
        patientName: "",
        age: "",
        urgency: "",
        medicalNeed: "",
        medicines: [emptyMedicine()],
        notes: "",
        location: null,
      });
      setGpsStatus("idle");
      setErrors({});
    } catch {
      setSubmitStatus("error");
    }
  };

  const selectedUrgency = URGENCY_LEVELS.find((u) => u.value === form.urgency);

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

        .rf-wrap {
          font-family: 'DM Sans', sans-serif;
          max-width: 680px;
          margin: 0 auto;
          padding: 0 16px 48px;
        }

        .rf-header {
          background: linear-gradient(135deg, #0a3d62 0%, #1565c0 100%);
          border-radius: 16px 16px 0 0;
          padding: 32px 36px 28px;
          color: white;
          position: relative;
          overflow: hidden;
        }

        .rf-header::before {
          content: '';
          position: absolute;
          top: -40px; right: -40px;
          width: 180px; height: 180px;
          border-radius: 50%;
          background: rgba(255,255,255,0.05);
        }

        .rf-header-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: rgba(255,255,255,0.15);
          border: 1px solid rgba(255,255,255,0.25);
          border-radius: 20px;
          padding: 4px 12px;
          font-size: 12px;
          font-weight: 500;
          letter-spacing: 0.5px;
          margin-bottom: 12px;
        }

        .rf-header h1 {
          font-family: 'DM Serif Display', serif;
          font-size: 28px;
          font-weight: 400;
          margin: 0 0 6px;
          letter-spacing: -0.3px;
        }

        .rf-header p {
          margin: 0;
          font-size: 14px;
          opacity: 0.75;
          font-weight: 300;
        }

        .rf-body {
          background: #fff;
          border: 1px solid #e3eaf3;
          border-top: none;
          border-radius: 0 0 16px 16px;
          padding: 32px 36px;
          box-shadow: 0 8px 32px rgba(13,61,98,0.08);
        }

        .rf-section {
          margin-bottom: 28px;
        }

        .rf-section-title {
          font-size: 11px;
          font-weight: 600;
          letter-spacing: 1.2px;
          text-transform: uppercase;
          color: #1565c0;
          margin-bottom: 14px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .rf-section-title::after {
          content: '';
          flex: 1;
          height: 1px;
          background: #e3eaf3;
        }

        .rf-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 14px;
        }

        .rf-field {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .rf-field.full { grid-column: 1 / -1; }

        .rf-label {
          font-size: 13px;
          font-weight: 500;
          color: #2c3e50;
        }

        .rf-input, .rf-select, .rf-textarea {
          padding: 10px 14px;
          border: 1.5px solid #dce6f0;
          border-radius: 8px;
          font-size: 14px;
          font-family: 'DM Sans', sans-serif;
          color: #1a2a3a;
          background: #f8fbff;
          transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
          outline: none;
        }

        .rf-input:focus, .rf-select:focus, .rf-textarea:focus {
          border-color: #1565c0;
          background: #fff;
          box-shadow: 0 0 0 3px rgba(21,101,192,0.1);
        }

        .rf-input.error, .rf-select.error {
          border-color: #e74c3c;
          background: #fff8f8;
        }

        .rf-error-msg {
          font-size: 12px;
          color: #c0392b;
          font-weight: 500;
        }

        .rf-textarea {
          resize: vertical;
          min-height: 80px;
        }

        /* ── Urgency selector ── */
        .urgency-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
        }

        .urgency-card {
          border: 2px solid #dce6f0;
          border-radius: 10px;
          padding: 12px 10px;
          cursor: pointer;
          transition: all 0.2s;
          background: #f8fbff;
          text-align: center;
          position: relative;
          overflow: hidden;
        }

        .urgency-card:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }

        .urgency-card.selected {
          transform: translateY(-1px);
          box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        }

        .urgency-dot {
          width: 10px; height: 10px;
          border-radius: 50%;
          margin: 0 auto 8px;
        }

        .urgency-dot.pulse {
          animation: pulse-dot 1.4s ease-in-out infinite;
        }

        @keyframes pulse-dot {
          0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(231,76,60,0.4); }
          50% { transform: scale(1.2); box-shadow: 0 0 0 6px rgba(231,76,60,0); }
        }

        .urgency-label {
          font-size: 13px;
          font-weight: 600;
          margin-bottom: 3px;
        }

        .urgency-desc {
          font-size: 10px;
          line-height: 1.4;
          opacity: 0.7;
        }

        /* ── Medicine rows ── */
        .med-row {
          display: grid;
          grid-template-columns: 1fr 100px 36px;
          gap: 8px;
          align-items: start;
          margin-bottom: 8px;
          animation: fadeIn 0.2s ease;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .med-remove {
          width: 36px; height: 38px;
          border: 1.5px solid #fdb8b8;
          background: #fff5f5;
          border-radius: 8px;
          color: #e74c3c;
          cursor: pointer;
          font-size: 16px;
          display: flex; align-items: center; justify-content: center;
          transition: all 0.15s;
          margin-top: 0;
        }

        .med-remove:hover {
          background: #fde8e8;
          border-color: #e74c3c;
        }

        .add-med-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 14px;
          border: 1.5px dashed #1565c0;
          border-radius: 8px;
          background: transparent;
          color: #1565c0;
          font-size: 13px;
          font-weight: 500;
          font-family: 'DM Sans', sans-serif;
          cursor: pointer;
          transition: all 0.2s;
          width: 100%;
          justify-content: center;
          margin-top: 4px;
        }

        .add-med-btn:hover {
          background: #f0f5ff;
        }

        /* ── GPS button ── */
        .gps-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          border-radius: 8px;
          font-size: 13px;
          font-weight: 500;
          font-family: 'DM Sans', sans-serif;
          cursor: pointer;
          transition: all 0.2s;
          border: 1.5px solid;
          width: 100%;
          justify-content: center;
        }

        .gps-btn.idle {
          border-color: #1565c0;
          background: #f0f5ff;
          color: #1565c0;
        }

        .gps-btn.idle:hover { background: #e0eaff; }

        .gps-btn.loading {
          border-color: #aaa;
          background: #f5f5f5;
          color: #888;
          cursor: wait;
        }

        .gps-btn.success {
          border-color: #27ae60;
          background: #edfaf3;
          color: #1a6b3c;
        }

        .gps-btn.error {
          border-color: #e74c3c;
          background: #fff5f5;
          color: #c0392b;
        }

        .gps-coords {
          font-size: 12px;
          color: #1a6b3c;
          background: #edfaf3;
          border: 1px solid #a9dfbf;
          border-radius: 6px;
          padding: 6px 10px;
          margin-top: 6px;
          font-family: monospace;
        }

        .spin {
          animation: spin 1s linear infinite;
          display: inline-block;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        /* ── Submit button ── */
        .rf-submit {
          width: 100%;
          padding: 14px;
          background: linear-gradient(135deg, #0a3d62, #1565c0);
          color: white;
          border: none;
          border-radius: 10px;
          font-size: 15px;
          font-weight: 600;
          font-family: 'DM Sans', sans-serif;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          margin-top: 8px;
          letter-spacing: 0.3px;
        }

        .rf-submit:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 6px 20px rgba(21,101,192,0.35);
        }

        .rf-submit:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        /* ── Status messages ── */
        .rf-status {
          margin-top: 14px;
          padding: 12px 16px;
          border-radius: 8px;
          font-size: 13px;
          font-weight: 500;
          display: flex;
          align-items: center;
          gap: 8px;
          animation: fadeIn 0.3s ease;
        }

        .rf-status.queued {
          background: #fff3cd;
          border: 1px solid #ffc107;
          color: #856404;
        }

        .rf-status.synced {
          background: #edfaf3;
          border: 1px solid #27ae60;
          color: #1a6b3c;
        }

        .rf-status.error {
          background: #fff5f5;
          border: 1px solid #e74c3c;
          color: #c0392b;
        }

        @media (max-width: 520px) {
          .rf-body, .rf-header { padding: 20px 18px; }
          .rf-row { grid-template-columns: 1fr; }
          .urgency-grid { grid-template-columns: 1fr; }
          .med-row { grid-template-columns: 1fr 80px 36px; }
        }
      `}</style>

      <div className="rf-wrap">
        {/* ── Header ── */}
        <div className="rf-header">
          <div className="rf-header-badge">
            <span>🏥</span>
            <span>EMERGENCY REQUEST</span>
          </div>
          <h1>Medical Request Form</h1>
          <p>Works offline — your request is saved locally and synced when connected</p>
        </div>

        {/* ── Body ── */}
        <div className="rf-body">
          <form onSubmit={handleSubmit} noValidate>

            {/* ── Patient Info ── */}
            <div className="rf-section">
              <div className="rf-section-title">Patient Information</div>
              <div className="rf-row">
                <div className="rf-field">
                  <label className="rf-label">Full Name *</label>
                  <input
                    className={`rf-input${errors.patientName ? " error" : ""}`}
                    placeholder="e.g. Saman Perera"
                    value={form.patientName}
                    onChange={(e) => setForm({ ...form, patientName: e.target.value })}
                  />
                  {errors.patientName && <span className="rf-error-msg">{errors.patientName}</span>}
                </div>

                <div className="rf-field">
                  <label className="rf-label">Age *</label>
                  <input
                    className={`rf-input${errors.age ? " error" : ""}`}
                    type="number"
                    placeholder="e.g. 34"
                    min="0" max="120"
                    value={form.age}
                    onChange={(e) => setForm({ ...form, age: e.target.value })}
                  />
                  {errors.age && <span className="rf-error-msg">{errors.age}</span>}
                </div>
              </div>
            </div>

            {/* ── Urgency ── */}
            <div className="rf-section">
              <div className="rf-section-title">Urgency Level *</div>
              <div className="urgency-grid">
                {URGENCY_LEVELS.map((u) => (
                  <div
                    key={u.value}
                    className={`urgency-card${form.urgency === u.value ? " selected" : ""}`}
                    style={
                      form.urgency === u.value
                        ? { borderColor: u.border, background: u.bg }
                        : {}
                    }
                    onClick={() => setForm({ ...form, urgency: u.value })}
                  >
                    <div
                      className={`urgency-dot${u.pulse ? " pulse" : ""}`}
                      style={{ background: u.color }}
                    />
                    <div className="urgency-label" style={{ color: form.urgency === u.value ? u.color : "#2c3e50" }}>
                      {u.label}
                    </div>
                    <div className="urgency-desc">{u.description}</div>
                  </div>
                ))}
              </div>
              {errors.urgency && <div className="rf-error-msg" style={{ marginTop: 6 }}>{errors.urgency}</div>}
            </div>

            {/* ── Medical Need ── */}
            <div className="rf-section">
              <div className="rf-section-title">Medical Need</div>
              <div className="rf-field">
                <label className="rf-label">Type of Emergency *</label>
                <select
                  className={`rf-select${errors.medicalNeed ? " error" : ""}`}
                  value={form.medicalNeed}
                  onChange={(e) => setForm({ ...form, medicalNeed: e.target.value })}
                >
                  <option value="">— Select type —</option>
                  {MEDICAL_NEEDS.map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
                {errors.medicalNeed && <span className="rf-error-msg">{errors.medicalNeed}</span>}
              </div>
            </div>

            {/* ── Medicines ── */}
            <div className="rf-section">
              <div className="rf-section-title">Required Medicines</div>

              {/* Column headers */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 100px 36px", gap: "8px", marginBottom: "6px" }}>
                <span style={{ fontSize: "12px", color: "#888", fontWeight: 500 }}>Medicine Name</span>
                <span style={{ fontSize: "12px", color: "#888", fontWeight: 500 }}>Amount (g/mg)</span>
                <span />
              </div>

              {form.medicines.map((med, i) => (
                <div key={med.id} className="med-row">
                  <div>
                    <input
                      className={`rf-input${errors[`med_name_${i}`] ? " error" : ""}`}
                      placeholder="e.g. Paracetamol"
                      value={med.name}
                      onChange={(e) => updateMedicine(med.id, "name", e.target.value)}
                    />
                    {errors[`med_name_${i}`] && <div className="rf-error-msg">{errors[`med_name_${i}`]}</div>}
                  </div>
                  <div>
                    <input
                      className={`rf-input${errors[`med_grams_${i}`] ? " error" : ""}`}
                      placeholder="500mg"
                      value={med.grams}
                      onChange={(e) => updateMedicine(med.id, "grams", e.target.value)}
                    />
                    {errors[`med_grams_${i}`] && <div className="rf-error-msg">{errors[`med_grams_${i}`]}</div>}
                  </div>
                  <button
                    type="button"
                    className="med-remove"
                    onClick={() => removeMedicine(med.id)}
                    disabled={form.medicines.length === 1}
                    title="Remove"
                  >
                    ×
                  </button>
                </div>
              ))}

              <button type="button" className="add-med-btn" onClick={addMedicine}>
                + Add Another Medicine
              </button>
            </div>

            {/* ── GPS Location ── */}
            <div className="rf-section">
              <div className="rf-section-title">Location</div>
              <button
                type="button"
                className={`gps-btn ${gpsStatus}`}
                onClick={captureGPS}
                disabled={gpsStatus === "loading"}
              >
                {gpsStatus === "idle"    && <><span>📍</span> Capture GPS Location</>}
                {gpsStatus === "loading" && <><span className="spin">⏳</span> Getting location...</>}
                {gpsStatus === "success" && <><span>✅</span> Location Captured — tap to update</>}
                {gpsStatus === "error"   && <><span>⚠️</span> GPS unavailable — tap to retry</>}
              </button>

              {form.location && (
                <div className="gps-coords">
                  📍 {form.location.lat}, {form.location.lng}
                  <span style={{ marginLeft: 10, opacity: 0.7 }}>±{form.location.accuracy}m</span>
                </div>
              )}
            </div>

            {/* ── Notes ── */}
            <div className="rf-section">
              <div className="rf-section-title">Additional Notes</div>
              <textarea
                className="rf-textarea"
                placeholder="Any additional details about the patient's condition..."
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
              />
            </div>

            {/* ── Submit ── */}
            <button
              type="submit"
              className="rf-submit"
              disabled={submitStatus === "saving"}
            >
              {submitStatus === "saving"
                ? <><span className="spin">⏳</span> Saving...</>
                : <><span>🚨</span> Submit Emergency Request</>
              }
            </button>

            {/* ── Status feedback ── */}
            {submitStatus === "queued" && (
              <div className="rf-status queued">
                🟡 Saved offline — will sync automatically when internet is restored
              </div>
            )}
            {submitStatus === "synced" && (
              <div className="rf-status synced">
                ✅ Request submitted and synced to the server successfully
              </div>
            )}
            {submitStatus === "error" && (
              <div className="rf-status error">
                ❌ Failed to save request — please try again
              </div>
            )}

          </form>
        </div>
      </div>
    </>
  );
}
