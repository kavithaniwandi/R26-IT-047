import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Navigation from "../components/Navigation";
import Footer from "../components/Footer";
import "./PriorityQueue.css";

const SESSION_KEY = "severityQueueSession";
const STORAGE_KEY = "priorityApplications";
const SEV_ORDER = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
const SEV_COLOR = { CRITICAL: "#b91c1c", HIGH: "#c2410c", MEDIUM: "#b45309", LOW: "#15803d" };
const SEV_BG = { CRITICAL: "#fef1ee", HIGH: "#fef1ee", MEDIUM: "#fef6e8", LOW: "#ebf7f0" };
const ROLE_CLASS = { "Senior MO": "senior", "Medical Officer": "mo", Resident: "resident", Intern: "intern" };

function initials(name) {
  return (
    (name || "?")
      .trim()
      .split(" ")
      .map((word) => word[0])
      .slice(0, 2)
      .join("")
      .toUpperCase() || "?"
  );
}

export default function PriorityQueue() {
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [patients, setPatients] = useState([]);
  const [unassigned, setUnassigned] = useState([]);

  useEffect(() => {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) {
      navigate("/camp-setup");
      return;
    }

    const parsedSession = JSON.parse(raw);
    const allPatients = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    const mos = parsedSession.mos.map((mo) => ({
      ...mo,
      patients: allPatients
        .filter((patient) => patient.assigned_mo_id === mo.id)
        .sort((first, second) => (SEV_ORDER[first.severity] ?? 3) - (SEV_ORDER[second.severity] ?? 3)),
    }));

    setSession({ ...parsedSession, mos });
    setPatients(allPatients);
    setUnassigned(allPatients.filter((patient) => !patient.assigned_mo_id));
  }, [navigate]);

  const counts = {
    CRITICAL: patients.filter((patient) => patient.severity === "CRITICAL").length,
    HIGH: patients.filter((patient) => patient.severity === "HIGH").length,
    MEDIUM: patients.filter((patient) => patient.severity === "MEDIUM").length,
    LOW: patients.filter((patient) => patient.severity === "LOW").length,
  };

  if (!session) return null;

  return (
    <div className="priority-page">
      <Navigation />

      <main className="priority-container">
        <section className="priority-header">
          <span>{session.camp.code} - {session.camp.name}</span>
          <h1>MO Queue</h1>
          <p>Patient cases ranked by severity within each Medical Officer queue.</p>
        </section>

        <div className="priority-stat-row">
          {["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((severity) => (
            <div key={severity} className="priority-stat-box">
              <div className="priority-stat-num" style={{ color: SEV_COLOR[severity] }}>
                {counts[severity]}
              </div>
              <div className="priority-stat-lbl">{severity}</div>
            </div>
          ))}
        </div>

        <section className="priority-toolbar">
          <p>{patients.length} patient{patients.length !== 1 ? "s" : ""} in session</p>
          <Link to="/priority-application">New Patient</Link>
        </section>

        {patients.length === 0 ? (
          <section className="priority-empty">
            <h2>No patients yet</h2>
            <p>Classified patient cases will appear here, grouped by assigned MO.</p>
            <Link to="/priority-application">Add First Patient</Link>
          </section>
        ) : (
          <section className="priority-mo-grid">
            {session.mos.map((mo) => {
              const moPatients = mo.patients || [];
              const highCount = moPatients.filter(
                (patient) => patient.severity === "HIGH" || patient.severity === "CRITICAL"
              ).length;
              const roleClass = ROLE_CLASS[mo.role] || "mo";

              return (
                <div key={mo.id} className="priority-mo-card">
                  <div className="priority-mo-header">
                    <div className="priority-mo-avatar">{initials(mo.name)}</div>
                    <div className="priority-mo-info">
                      <div className="priority-mo-name">
                        {mo.name}
                        <span className="priority-mo-id">{mo.id}</span>
                      </div>
                      <div className="priority-mo-meta">
                        {mo.specialty}
                        <span className={`priority-role-tag ${roleClass}`}>{mo.role}</span>
                        {mo.shift && <span>Shift ends {mo.shift}</span>}
                      </div>
                    </div>
                    <div className="priority-mo-counts">
                      {highCount > 0 && (
                        <span className="priority-high-badge">{highCount} high</span>
                      )}
                      <span className="priority-total-badge">
                        {moPatients.length} case{moPatients.length !== 1 ? "s" : ""}
                      </span>
                    </div>
                  </div>

                  <div className="priority-mo-body">
                    {!moPatients.length ? (
                      <div className="priority-mo-empty">No cases assigned yet.</div>
                    ) : (
                      moPatients.map((patient) => {
                        const symptomText = patient.symptoms || patient.description || "";
                        return (
                          <div
                            key={patient.id}
                            className="priority-patient-card"
                            style={{ borderLeftColor: SEV_COLOR[patient.severity] || "#94a3b8" }}
                          >
                            <div className="ppc-top">
                              <div>
                                <div className="ppc-id">{patient.id}</div>
                                <div className="ppc-symptoms">
                                  {symptomText.slice(0, 95)}
                                  {symptomText.length > 95 ? "..." : ""}
                                </div>
                              </div>
                              <span
                                className="ppc-sev-badge"
                                style={{
                                  background: SEV_BG[patient.severity],
                                  color: SEV_COLOR[patient.severity],
                                }}
                              >
                                {patient.severity}
                              </span>
                            </div>
                            <div className="ppc-bottom">
                              {patient.age && <span className="ppc-tag">Age {patient.age}</span>}
                              {patient.condition_group && <span className="ppc-tag">{patient.condition_group}</span>}
                              <span className="ppc-tag">Risk {patient.risk_score}/100</span>
                              {patient.red_flags?.map((flag) => (
                                <span key={flag} className="ppc-redflag">{flag.replace(/_/g, " ")}</span>
                              ))}
                              {patient.critical_trigger && (
                                <span className="ppc-redflag">{patient.critical_trigger}</span>
                              )}
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              );
            })}

            {unassigned.length > 0 && (
              <div className="priority-mo-card priority-unassigned">
                <div className="priority-mo-header priority-unassigned-header">
                  <div className="priority-mo-avatar priority-unassigned-avatar">!</div>
                  <div className="priority-mo-info">
                    <div className="priority-mo-name">Unassigned - no eligible MO</div>
                    <div className="priority-mo-meta">Manual assignment required</div>
                  </div>
                  <div className="priority-mo-counts">
                    <span className="priority-high-badge">
                      {unassigned.length} case{unassigned.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                </div>
                <div className="priority-mo-body">
                  {unassigned.map((patient) => (
                    <div
                      key={patient.id}
                      className="priority-patient-card"
                      style={{ borderLeftColor: SEV_COLOR[patient.severity] || "#b91c1c" }}
                    >
                      <div className="ppc-top">
                        <div>
                          <div className="ppc-id">{patient.id}</div>
                          <div className="ppc-symptoms">{(patient.symptoms || "").slice(0, 95)}</div>
                        </div>
                        <span
                          className="ppc-sev-badge"
                          style={{
                            background: SEV_BG[patient.severity],
                            color: SEV_COLOR[patient.severity],
                          }}
                        >
                          {patient.severity}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}
      </main>

      <Footer />
    </div>
  );
}
