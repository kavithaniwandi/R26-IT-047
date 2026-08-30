import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import "./CampSetup.css";

const SESSION_KEY = "severityQueueSession";
const ACTIVATION_KEY = "campActivationState";

const campSubtitle = (camp) =>
  [camp.district, camp.ds_division].filter(Boolean).join(" · ");

const SPECIALTIES = [
  "Emergency Medicine", "Cardiovascular", "Respiratory", "Neurological",
  "Gastrointestinal", "Trauma & Surgery", "Orthopedic", "Rheumatology",
  "Pediatric", "Geriatric", "Infection & Systemic",
  "Renal & Urinary", "Mental & Behavioral", "Obstetric & Gynecologic",
  "Endocrine & Metabolic", "Allergy & Immunology", "General Practice",
];

const SECONDARY_SKILLS = [
  "Cardiovascular", "Respiratory", "Neurological", "Gastrointestinal",
  "Trauma & Surgery", "Orthopedic", "Rheumatology", "Pediatric", "Geriatric",
  "Infection & Systemic", "Renal & Urinary",
  "Mental & Behavioral", "Obstetric & Gynecologic", "Endocrine & Metabolic",
  "Allergy & Immunology", "Emergency Medicine",
];

const ROLES = ["Medical Administrator", "Senior MO", "Medical Officer", "Resident", "Intern"];

const SHIFT_HOURS = Array.from({ length: 24 }, (_, hour) => {
  const value = String(hour).padStart(2, "0");
  const period = hour < 12 ? "AM" : "PM";
  const displayHour = hour % 12 || 12;
  return { value, label: `${displayHour} ${period}` };
});

const SHIFT_MINUTES = ["00", "15", "30", "45"];

const SHIFT_PRESETS = [
  { label: "Noon", value: "12:00" },
  { label: "3:00 PM", value: "15:00" },
  { label: "6:00 PM", value: "18:00" },
  { label: "9:00 PM", value: "21:00" },
];

const BLANK_MO = {
  name: "",
  staffId: "",
  role: "",
  specialty: "",
  skills: [],
  supervisor: "",
  shift: "",
};

export default function CampSetup() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [camps, setCamps] = useState([]);
  const [campsLoading, setCampsLoading] = useState(true);
  const [campsError, setCampsError] = useState("");
  const [activation, setActivation] = useState({});
  const [selectedCamp, setSelectedCamp] = useState(null);
  const [moCount, setMoCount] = useState(null);
  const [moIndex, setMoIndex] = useState(0);
  const [mos, setMos] = useState([]);
  const [form, setForm] = useState({ ...BLANK_MO });
  const [formError, setFormError] = useState("");
  const [registrationStarted, setRegistrationStarted] = useState(false);
  const [shiftHour = "", shiftMinute = ""] = form.shift ? form.shift.split(":") : ["", ""];

  useEffect(() => {
    setCampsLoading(true);
    api.getCamps({ status_filter: "approved" })
      .then((data) => {
        const list = Array.isArray(data) ? data : [];
        setCamps(list);
        const savedMap = JSON.parse(localStorage.getItem(ACTIVATION_KEY) || "{}");
        const merged = Object.fromEntries(list.map((c) => [c.id, savedMap[c.id] ?? false]));
        setActivation(merged);
        localStorage.setItem(ACTIVATION_KEY, JSON.stringify(merged));
      })
      .catch((err) => setCampsError(err?.message || "Failed to load camps."))
      .finally(() => setCampsLoading(false));
  }, []);

  const handleToggle = (event, campId) => {
    event.stopPropagation();
    setActivation((previous) => {
      const nextActive = !previous[campId];
      const updated = { ...previous, [campId]: nextActive };
      localStorage.setItem(ACTIVATION_KEY, JSON.stringify(updated));

      if (selectedCamp?.id === campId && !nextActive) {
        setSelectedCamp(null);
      }

      if (nextActive) {
        const camp = camps.find((item) => item.id === campId);
        setSelectedCamp(camp || null);
      }

      return updated;
    });
  };

  const handleCampSelect = (camp) => {
    if (!activation[camp.id]) return;
    setSelectedCamp(camp);
  };

  const handleConfirmCamp = () => {
    if (!selectedCamp) return;
    setStep(2);
  };

  const handleStartRegistration = () => {
    if (!moCount) return;
    setMoIndex(0);
    setMos([]);
    setForm({ ...BLANK_MO });
    setFormError("");
    setRegistrationStarted(true);
  };

  const updateFormField = (field, value) => {
    setForm((previous) => ({ ...previous, [field]: value }));
  };

  const updateShiftPart = (part, value) => {
    const nextHour = part === "hour" ? value : shiftHour;
    const nextMinute = part === "minute" ? value : shiftMinute;

    if (!nextHour && !nextMinute) {
      updateFormField("shift", "");
      return;
    }

    updateFormField("shift", `${nextHour || "00"}:${nextMinute || "00"}`);
  };

  const toggleSkill = (skill) => {
    setForm((previous) => {
      const exists = previous.skills.find((selectedSkill) => selectedSkill.name === skill);
      if (exists) {
        return {
          ...previous,
          skills: previous.skills.filter((selectedSkill) => selectedSkill.name !== skill),
        };
      }
      return {
        ...previous,
        skills: [...previous.skills, { name: skill, confidence: 2 }],
      };
    });
  };

  const setSkillConfidence = (skill, confidence) => {
    setForm((previous) => ({
      ...previous,
      skills: previous.skills.map((selectedSkill) =>
        selectedSkill.name === skill
          ? { ...selectedSkill, confidence: Number(confidence) }
          : selectedSkill
      ),
    }));
  };

  const validateMOForm = () => {
    const name = form.name.trim();
    const staffId = form.staffId.trim();
    const shift = form.shift.trim();

    if (!name) {
      return "Full name is required.";
    }
    if (name.length < 3 || !/[a-zA-Z]/.test(name)) {
      return "Enter a valid name with at least 3 letters.";
    }

    if (staffId && !/^\d{3,20}$/.test(staffId)) {
      return "Staff ID must be 3-20 digits only.";
    }

    if (!form.role) {
      return "Select the officer role.";
    }

    if (!form.specialty) {
      return "Select a primary specialty.";
    }

    if (form.skills.length === 0) {
      return "Select at least one secondary skill.";
    }

    if (!form.supervisor) {
      return "Choose supervisor availability.";
    }

    if (shift && !/^([01]?\d|2[0-3])[:.]([0-5]\d)$/.test(shift)) {
      return "Shift end time must use 24-hour time, for example 15:00.";
    }

    return "";
  };

  const handleSaveMO = () => {
    const validationError = validateMOForm();
    if (validationError) {
      setFormError(validationError);
      window.alert(validationError);
      return;
    }
    setFormError("");

    const saved = {
      id: form.staffId.trim() || `MO-${String(mos.length + 1).padStart(3, "0")}`,
      name: form.name.trim(),
      role: form.role,
      specialty: form.specialty,
      skills: form.skills,
      supervisor: form.supervisor,
      shift: form.shift.trim(),
      queueDepth: 0,
      patients: [],
    };

    const updated = [...mos, saved];
    setMos(updated);

    if (moIndex + 1 >= moCount) {
      const startedAt = new Date().toISOString();
      const sessionObj = {
        session_id: `${selectedCamp.id}-${Date.now()}`,
        startedAt,
        camp: {
          id: selectedCamp.id,
          name: selectedCamp.name,
          district: selectedCamp.district,
          ds_division: selectedCamp.ds_division,
          gn_division: selectedCamp.gn_division,
          estimated_capacity: selectedCamp.estimated_capacity,
        },
        mos: updated,
      };

      localStorage.setItem(SESSION_KEY, JSON.stringify(sessionObj));
      api.startTriageSession(sessionObj).catch((error) => {
        console.warn("[triage] session start:", error);
      });
      navigate("/priority-application");
      return;
    }

    setMoIndex(moIndex + 1);
    setForm({ ...BLANK_MO });
  };

  const initials = (name) =>
    name.trim().split(" ").map((word) => word[0]).slice(0, 2).join("").toUpperCase() || "?";
  const roleClass = {
    "Medical Administrator": "admin",
    "Senior MO": "senior",
    "Medical Officer": "mo",
    Resident: "resident",
    Intern: "intern",
  };
  const activeCount = Object.values(activation).filter(Boolean).length;

  return (
    <div className="cs-page">
      <main className="cs-container">
        <div className="cs-steps">
          <div className={`cs-step-item ${step === 1 ? "active" : "done"}`}>
            <div className="cs-dot">{step > 1 ? "✓" : "1"}</div>
            <span>Safety camp</span>
          </div>
          <div className={`cs-connector ${step > 1 ? "done" : ""}`} />
          <div className={`cs-step-item ${step === 2 ? "active" : ""}`}>
            <div className="cs-dot">2</div>
            <span>MO registration</span>
          </div>
        </div>

        {step === 1 && (
          <section className="cs-section">
            <span className="cs-eyebrow">Session setup</span>
            <h1 className="cs-title">Select your safety camp</h1>
            <p className="cs-desc">
              Activate the camps that are operational, then select the one this session is
              operating under. Standby camps cannot be selected until activated.
            </p>

            {campsLoading && (
              <div className="cs-alert-info">
                <span>⏳</span>
                <span>Loading camps…</span>
              </div>
            )}

            {campsError && (
              <div className="cs-alert-warn">
                <span>⚠</span>
                <span>{campsError}</span>
              </div>
            )}

            {!campsLoading && !campsError && camps.length === 0 && (
              <div className="cs-alert-info">
                <span>ℹ</span>
                <span>No operational camps found.</span>
              </div>
            )}

            {!campsLoading && camps.length > 0 && (
              <>
                <div className="cs-activation-bar">
                  <span className="cs-activation-count">
                    <span className="cs-activation-dot active" />
                    {activeCount} active
                  </span>
                  <span className="cs-activation-count">
                    <span className="cs-activation-dot standby" />
                    {camps.length - activeCount} standby
                  </span>
                  <span className="cs-activation-hint">
                    Use the toggle on each card to activate or deactivate a camp.
                  </span>
                </div>

                <div className="cs-camp-grid">
                  {camps.map((camp) => {
                    const isActive = !!activation[camp.id];
                    const isSelected = selectedCamp?.id === camp.id;

                    return (
                      <div
                        key={camp.id}
                        className={`cs-camp-card ${isActive ? "" : "standby"} ${isSelected ? "selected" : ""}`}
                        onClick={() => handleCampSelect(camp)}
                      >
                        <div className="cs-toggle-row">
                          <span className={`cs-camp-status ${isActive ? "active" : "standby"}`}>
                            {isActive ? "● Active" : "◌ Standby"}
                          </span>
                          <button
                            type="button"
                            className={`cs-toggle ${isActive ? "on" : ""}`}
                            onClick={(event) => handleToggle(event, camp.id)}
                            title={isActive ? "Deactivate camp" : "Activate camp"}
                            aria-label={isActive ? "Deactivate camp" : "Activate camp"}
                            aria-pressed={isActive}
                          >
                            <span className="cs-toggle-slider" />
                          </button>
                        </div>

                        <div className="cs-camp-code">{camp.district}</div>
                        <div className="cs-camp-name">{camp.name}</div>
                        <div className="cs-camp-meta">{campSubtitle(camp)}</div>

                        {!isActive && (
                          <div className="cs-standby-notice">
                            Activate to select this camp
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {!selectedCamp && (
                  <div className="cs-confirm-bar empty">
                    <div className="cs-alert-info">
                      <span>Next step</span>
                      <div>
                        <strong>Select an active camp</strong>
                        <br />
                        <span>Activate a camp, then continue to MO registration.</span>
                      </div>
                    </div>
                    <button className="cs-btn-primary" onClick={handleConfirmCamp} disabled>
                      Confirm camp &amp; register MOs
                    </button>
                  </div>
                )}

                {selectedCamp && (
                  <div className="cs-confirm-bar">
                    <div className="cs-alert-info">
                      <span>ℹ</span>
                      <div>
                        <strong>{selectedCamp.name}</strong>
                        <br />
                        <span>{campSubtitle(selectedCamp)}</span>
                      </div>
                    </div>
                    <button className="cs-btn-primary" onClick={handleConfirmCamp}>
                      Confirm camp &amp; register MOs →
                    </button>
                  </div>
                )}
              </>
            )}
          </section>
        )}

        {step === 2 && (
          <section className="cs-section">
            <span className="cs-eyebrow">{selectedCamp.district} — {selectedCamp.name}</span>
            <h1 className="cs-title">Register medical officers</h1>
            <p className="cs-desc">
              Set the number of MOs on duty, then fill in each profile. Role,
              specialty and skills determine how patient cases are routed.
            </p>

            {!registrationStarted && (
              <div className="cs-card">
                <div className="cs-card-label">How many MOs are on duty this session?</div>
                <div className="cs-mo-count-row">
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((count) => (
                    <div
                      key={count}
                      className={`cs-count-pill ${moCount === count ? "selected" : ""}`}
                      onClick={() => setMoCount(count)}
                    >
                      {count}
                    </div>
                  ))}
                </div>
                <button
                  className="cs-btn-primary"
                  onClick={handleStartRegistration}
                  disabled={!moCount}
                >
                  Start registration →
                </button>
              </div>
            )}

            {registrationStarted && (
              <div className="cs-progress-track">
                {Array.from({ length: moCount }).map((_, index) => (
                  <React.Fragment key={index}>
                    <div className={`cs-track-dot ${index < moIndex ? "done" : index === moIndex ? "current" : "pending"}`}>
                      {index < moIndex ? "✓" : index + 1}
                    </div>
                    {index < moCount - 1 && <div className="cs-track-line" />}
                  </React.Fragment>
                ))}
              </div>
            )}

            {registrationStarted && moIndex < moCount && (
              <div className="cs-card">
                <div className="cs-mo-form-header">
                  <div className="cs-mo-num">{moIndex + 1}</div>
                  <div>
                    <div className="cs-mo-form-title">Medical officer {moIndex + 1}</div>
                    <div className="cs-mo-form-sub">{moIndex + 1} of {moCount}</div>
                  </div>
                </div>

                <div className="cs-row2">
                  <div className="cs-field">
                    <label>Full name <span className="cs-req">*</span></label>
                    <input
                      type="text"
                      placeholder="Dr. Nimal Perera"
                      value={form.name}
                      onChange={(event) => updateFormField("name", event.target.value)}
                    />
                  </div>
                  <div className="cs-field">
                    <label>Staff ID</label>
                    <input
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      placeholder="12345"
                      value={form.staffId}
                      onChange={(event) => updateFormField("staffId", event.target.value)}
                    />
                  </div>
                </div>

                <div className="cs-field">
                  <label>Role <span className="cs-req">*</span></label>
                  <div className="cs-role-options">
                    {ROLES.map((role) => (
                      <div
                        key={role}
                        className={`cs-role-pill ${form.role === role ? "selected" : ""}`}
                        onClick={() => updateFormField("role", role)}
                      >
                        {role}
                      </div>
                    ))}
                  </div>
                  {["Intern", "Resident"].includes(form.role) && form.supervisor !== "yes" && (
                    <p className="cs-hint-warn">
                      ⚠ Interns and residents without a supervisor will not be assigned HIGH severity cases.
                    </p>
                  )}
                </div>

                <div className="cs-field">
                  <label>Primary specialty <span className="cs-req">*</span></label>
                  <select
                    value={form.specialty}
                    onChange={(event) => updateFormField("specialty", event.target.value)}
                  >
                    <option value="">Select specialty…</option>
                    {SPECIALTIES.map((specialty) => <option key={specialty}>{specialty}</option>)}
                  </select>
                </div>

                <div className="cs-field">
                  <label>
                    Secondary skills
                    <span className="cs-field-note"> (select all that apply, rate confidence)</span>
                  </label>
                  <div className="cs-skill-grid">
                    {SECONDARY_SKILLS.map((skill) => {
                      const selected = form.skills.find((selectedSkill) => selectedSkill.name === skill);

                      return (
                        <div
                          key={skill}
                          className={`cs-skill-item ${selected ? "selected" : ""}`}
                          onClick={() => toggleSkill(skill)}
                        >
                          <div className="cs-sk-name">{skill}</div>
                          {selected && (
                            <select
                              value={selected.confidence}
                              onClick={(event) => event.stopPropagation()}
                              onChange={(event) => setSkillConfidence(skill, event.target.value)}
                            >
                              <option value={1}>Basic (1)</option>
                              <option value={2}>Proficient (2)</option>
                              <option value={3}>Expert (3)</option>
                            </select>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="cs-field">
                  <label>Supervisor on-site? <span className="cs-req">*</span></label>
                  <div className="cs-role-options">
                    {[
                      ["yes", "Yes — named supervisor present"],
                      ["no", "No — working independently"],
                    ].map(([value, label]) => (
                      <div
                        key={value}
                        className={`cs-role-pill ${form.supervisor === value ? "selected" : ""}`}
                        onClick={() => updateFormField("supervisor", value)}
                      >
                        {label}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="cs-field">
                  <label>Shift end time</label>
                  <div className="cs-shift-control">
                    <select
                      aria-label="Shift end hour"
                      value={shiftHour}
                      onChange={(event) => updateShiftPart("hour", event.target.value)}
                    >
                      <option value="">Hour</option>
                      {SHIFT_HOURS.map((hour) => (
                        <option key={hour.value} value={hour.value}>
                          {hour.label}
                        </option>
                      ))}
                    </select>
                    <span className="cs-shift-separator">:</span>
                    <select
                      aria-label="Shift end minute"
                      value={shiftMinute}
                      onChange={(event) => updateShiftPart("minute", event.target.value)}
                    >
                      <option value="">Min</option>
                      {SHIFT_MINUTES.map((minute) => (
                        <option key={minute} value={minute}>
                          {minute}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="cs-shift-presets" aria-label="Common shift end times">
                    {SHIFT_PRESETS.map((preset) => (
                      <button
                        key={preset.value}
                        type="button"
                        className={`cs-shift-preset ${form.shift === preset.value ? "selected" : ""}`}
                        onClick={() => updateFormField("shift", preset.value)}
                      >
                        {preset.label}
                      </button>
                    ))}
                    {form.shift && (
                      <button
                        type="button"
                        className="cs-shift-clear"
                        onClick={() => updateFormField("shift", "")}
                      >
                        Clear
                      </button>
                    )}
                  </div>
                </div>

                {formError && (
                  <div className="cs-alert-warn">
                    <span>⚠</span>
                    <span>{formError}</span>
                  </div>
                )}

                <button className="cs-btn-primary" onClick={handleSaveMO}>
                  {moIndex === moCount - 1 ? "Save & open queue →" : "Save & next →"}
                </button>
              </div>
            )}

            {mos.length > 0 && (
              <div className="cs-roster">
                <div className="cs-roster-title">
                  Registered MOs this session
                  <span className="cs-roster-badge">{mos.length}</span>
                </div>
                {mos.map((mo) => (
                  <div key={mo.id} className="cs-mo-row">
                    <div className="cs-mo-avatar">{initials(mo.name)}</div>
                    <div className="cs-mo-info">
                      <div className="cs-mo-name">
                        {mo.name} <span className="cs-mo-id">{mo.id}</span>
                      </div>
                      <div className="cs-mo-meta">
                        {mo.specialty} · Secondary:{" "}
                        {mo.skills.length ? mo.skills.map((skill) => skill.name).join(", ") : "None"}
                      </div>
                    </div>
                    <span className={`cs-role-tag ${roleClass[mo.role] || "mo"}`}>{mo.role}</span>
                    <div className="cs-mo-queue-ct">0 cases</div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}
      </main>

    </div>
  );
}
