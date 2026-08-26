import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Navigation from "../components/Navigation";
import Footer from "../components/Footer";
import "./CampSetup.css";

const SESSION_KEY = "severityQueueSession";
const ACTIVATION_KEY = "campActivationState";

const CAMPS = [
  { code: "KDW-001", name: "Nawagamuwa Primary School", loc: "Kaduwela · Flood response", district: "Colombo", type: "flood" },
  { code: "KDW-002", name: "Kothalawala Maha Vidyalaya", loc: "Kaduwela · Flood response", district: "Colombo", type: "flood" },
  { code: "KDW-003", name: "Ashokaramaya", loc: "Kaduwela · Flood response", district: "Colombo", type: "flood" },
  { code: "KDW-004", name: "Munidasa Kumaratunga Vidyalaya", loc: "Kaduwela · Flood response", district: "Colombo", type: "flood" },
  { code: "KDW-005", name: "Bomiriya National School", loc: "Kaduwela · Flood response", district: "Colombo", type: "flood" },
  { code: "KDW-006", name: "Welivita Community Hall", loc: "Kaduwela · Flood response", district: "Colombo", type: "flood" },
  { code: "NWL-001", name: "Nawalapitiya Central College", loc: "Pasbage Korale · Landslide response", district: "Kandy", type: "landslide" },
  { code: "NWL-002", name: "Jayathilaka Stadium", loc: "Pasbage Korale · Landslide response", district: "Kandy", type: "landslide" },
  { code: "NWL-003", name: "Pallegama Temple", loc: "Pasbage Korale · Landslide response", district: "Kandy", type: "landslide" },
  { code: "NWL-004", name: "Warakawa Temple", loc: "Pasbage Korale · Landslide response", district: "Kandy", type: "landslide" },
];

const SPECIALTIES = [
  "Emergency Medicine", "Cardiovascular", "Respiratory", "Neurological",
  "Gastrointestinal", "Trauma & Surgery", "Infection & Systemic",
  "Renal & Urinary", "Mental & Behavioral", "Obstetric & Gynecologic",
  "Endocrine & Metabolic", "Allergy & Immunology", "General Practice",
];

const SECONDARY_SKILLS = [
  "Cardiovascular", "Respiratory", "Neurological", "Gastrointestinal",
  "Trauma & Surgery", "Infection & Systemic", "Renal & Urinary",
  "Mental & Behavioral", "Obstetric & Gynecologic", "Endocrine & Metabolic",
  "Allergy & Immunology", "Emergency Medicine",
];

const ROLES = ["Senior MO", "Medical Officer", "Resident", "Intern"];
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
  const [activation, setActivation] = useState({});
  const [selectedCamp, setSelectedCamp] = useState(null);
  const [moCount, setMoCount] = useState(null);
  const [moIndex, setMoIndex] = useState(0);
  const [mos, setMos] = useState([]);
  const [form, setForm] = useState({ ...BLANK_MO });
  const [formError, setFormError] = useState("");
  const [registrationStarted, setRegistrationStarted] = useState(false);

  useEffect(() => {
    const raw = localStorage.getItem(ACTIVATION_KEY);
    if (raw) {
      setActivation(JSON.parse(raw));
      return;
    }

    const defaults = Object.fromEntries(CAMPS.map((camp) => [camp.code, false]));
    setActivation(defaults);
    localStorage.setItem(ACTIVATION_KEY, JSON.stringify(defaults));
  }, []);

  const handleToggle = (event, campCode) => {
    event.stopPropagation();
    setActivation((previous) => {
      const updated = { ...previous, [campCode]: !previous[campCode] };
      localStorage.setItem(ACTIVATION_KEY, JSON.stringify(updated));

      if (selectedCamp?.code === campCode && !updated[campCode]) {
        setSelectedCamp(null);
      }

      return updated;
    });
  };

  const handleCampSelect = (camp) => {
    if (!activation[camp.code]) return;
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

  const handleSaveMO = () => {
    if (!form.name.trim()) {
      setFormError("Full name is required.");
      return;
    }
    if (!form.role) {
      setFormError("Please select a role.");
      return;
    }
    if (!form.specialty) {
      setFormError("Please select a primary specialty.");
      return;
    }
    if (!form.supervisor) {
      setFormError("Please indicate supervisor availability.");
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
      localStorage.setItem(SESSION_KEY, JSON.stringify({ camp: selectedCamp, mos: updated }));
      navigate("/priority-application");
      return;
    }

    setMoIndex(moIndex + 1);
    setForm({ ...BLANK_MO });
  };

  const initials = (name) =>
    name.trim().split(" ").map((word) => word[0]).slice(0, 2).join("").toUpperCase() || "?";
  const roleClass = {
    "Senior MO": "senior",
    "Medical Officer": "mo",
    Resident: "resident",
    Intern: "intern",
  };
  const activeCount = Object.values(activation).filter(Boolean).length;

  return (
    <div className="cs-page">
      <Navigation />

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

            <div className="cs-activation-bar">
              <span className="cs-activation-count">
                <span className="cs-activation-dot active" />
                {activeCount} active
              </span>
              <span className="cs-activation-count">
                <span className="cs-activation-dot standby" />
                {CAMPS.length - activeCount} standby
              </span>
              <span className="cs-activation-hint">
                Use the toggle on each card to activate or deactivate a camp.
              </span>
            </div>

            <div className="cs-camp-grid">
              {CAMPS.map((camp) => {
                const isActive = !!activation[camp.code];
                const isSelected = selectedCamp?.code === camp.code;

                return (
                  <div
                    key={camp.code}
                    className={`cs-camp-card ${isActive ? "" : "standby"} ${isSelected ? "selected" : ""}`}
                    onClick={() => handleCampSelect(camp)}
                  >
                    <div className="cs-toggle-row">
                      <span className={`cs-camp-status ${isActive ? "active" : "standby"}`}>
                        {isActive ? "● Active" : "◌ Standby"}
                      </span>
                      <label
                        className="cs-toggle"
                        onClick={(event) => handleToggle(event, camp.code)}
                        title={isActive ? "Deactivate camp" : "Activate camp"}
                      >
                        <input
                          type="checkbox"
                          checked={isActive}
                          onChange={() => {}}
                        />
                        <span className="cs-toggle-slider" />
                      </label>
                    </div>

                    <div className="cs-camp-code">{camp.code}</div>
                    <div className="cs-camp-name">{camp.name}</div>
                    <div className="cs-camp-meta">{camp.loc}</div>

                    {!isActive && (
                      <div className="cs-standby-notice">
                        Activate to select this camp
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {selectedCamp && (
              <div className="cs-confirm-bar">
                <div className="cs-alert-info">
                  <span>ℹ</span>
                  <div>
                    <strong>{selectedCamp.name}</strong>
                    <br />
                    <span>{selectedCamp.loc}</span>
                  </div>
                </div>
                <button className="cs-btn-primary" onClick={handleConfirmCamp}>
                  Confirm camp &amp; register MOs →
                </button>
              </div>
            )}
          </section>
        )}

        {step === 2 && (
          <section className="cs-section">
            <span className="cs-eyebrow">{selectedCamp.code} — {selectedCamp.name}</span>
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
                      onChange={(event) => setForm({ ...form, name: event.target.value })}
                    />
                  </div>
                  <div className="cs-field">
                    <label>Staff ID</label>
                    <input
                      type="text"
                      placeholder="SLMC-12345"
                      value={form.staffId}
                      onChange={(event) => setForm({ ...form, staffId: event.target.value })}
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
                        onClick={() => setForm({ ...form, role })}
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
                    onChange={(event) => setForm({ ...form, specialty: event.target.value })}
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
                        onClick={() => setForm({ ...form, supervisor: value })}
                      >
                        {label}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="cs-field">
                  <label>Shift end time</label>
                  <input
                    type="text"
                    placeholder="e.g. 18:00"
                    value={form.shift}
                    onChange={(event) => setForm({ ...form, shift: event.target.value })}
                  />
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

      <Footer />
    </div>
  );
}
