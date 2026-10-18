import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Plus, RefreshCw } from "lucide-react";
import { api } from "../api";
import { compareQueuedPatients } from "../utils/queueOrdering";
import "./PriorityQueue.css";
import { readTriageSession, loadSessionPatients, readPendingPatients, recoverLocalPatients, cacheSessionPatients } from "../utils/triagePersistence";

const SESSION_KEY = "severityQueueSession";
const ARCHIVE_KEY = "severityQueueSessions";
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

function EndSessionModal({ session, patients, counts, onConfirm, onCancel, saving }) {
  return (
    <div className="esm-overlay" role="dialog" aria-modal="true" aria-labelledby="end-session-title">
      <div className="esm-modal">
        <div className="esm-header">
          <div className="esm-icon">!</div>
          <h2 id="end-session-title">End Triage Session?</h2>
          <p>
            This will close the active session for <strong>{session.camp.name}</strong>,
            archive all patient records, and return to camp setup.
          </p>
        </div>

        <div className="esm-summary">
          <div className="esm-summary-title">Session Summary</div>
          <div className="esm-summary-grid">
            <div className="esm-summary-item">
              <span className="esm-summary-num">{patients.length}</span>
              <span className="esm-summary-lbl">Total</span>
            </div>
            {["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((severity) => (
              <div key={severity} className="esm-summary-item">
                <span className="esm-summary-num" style={{ color: SEV_COLOR[severity] }}>
                  {counts[severity]}
                </span>
                <span className="esm-summary-lbl">{severity}</span>
              </div>
            ))}
            <div className="esm-summary-item">
              <span className="esm-summary-num">{session.mos.length}</span>
              <span className="esm-summary-lbl">MOs</span>
            </div>
          </div>
        </div>

        <div className="esm-actions">
          <button className="esm-btn-cancel" type="button" disabled={saving} onClick={onCancel}>
            Keep Session Active
          </button>
          <button className="esm-btn-confirm" type="button" disabled={saving} onClick={onConfirm}>
            {saving ? "Archiving..." : "End Session & Archive"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function PriorityQueue() {
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [patients, setPatients] = useState([]);
  const [unassigned, setUnassigned] = useState([]);
  const [showEndModal, setShowEndModal] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [ending, setEnding] = useState(false);
  const [pendingCount, setPendingCount] = useState(0);
  const [refresh, setRefresh] = useState(0);
  const endLock = useRef(false);
  const sessionActive = Boolean(session);

  const refreshSavedRecords = () => {
    if (loading || ending) return;
    setLoading(true);
    setRefresh((value) => value + 1);
  };

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const parsedSession = readTriageSession();
        if (!parsedSession) { navigate("/camp-setup"); return; }
        setSession(parsedSession);
        const allPatients = await loadSessionPatients(api, parsedSession.session_id);
        if (cancelled) return;
        recoverLocalPatients(parsedSession, allPatients);
        setPendingCount(readPendingPatients(parsedSession.session_id).length);
        const queued = [...allPatients].sort(compareQueuedPatients);
        const mos = parsedSession.mos.map((mo) => ({
          ...mo,
          queueDepth: queued.filter((p) => p.assigned_mo_id === mo.id).length,
          patients: queued.filter((p) => p.assigned_mo_id === mo.id)
            .sort(compareQueuedPatients),
        }));
        setSession({ ...parsedSession, mos });
        setPatients(allPatients);
        setUnassigned(queued.filter((p) => !p.assigned_mo_id || !mos.some((mo) => mo.id === p.assigned_mo_id)));
        try {
          cacheSessionPatients(parsedSession, allPatients);
          localStorage.setItem(SESSION_KEY, JSON.stringify({ ...parsedSession, mos }));
        } catch (cacheError) { console.warn("[triage] Browser cache update failed:", cacheError); }
      } catch (err) {
        if (!cancelled) {
          console.error("[triage] Queue load failed:", err);
          setError(`Unable to load confirmed records: ${err.message}`);
        }
      } finally { if (!cancelled) setLoading(false); }
    };
    load();
    return () => { cancelled = true; };
  }, [navigate, refresh]);

  useEffect(() => {
    const handleBeforeUnload = (event) => {
      if (!session) return;
      event.preventDefault();
      event.returnValue = "";
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [session]);

  useEffect(() => {
    if (!sessionActive) return undefined;

    window.history.pushState({ severityQueueGuard: true }, "", window.location.href);
    const handlePopState = () => {
      if (!localStorage.getItem(SESSION_KEY)) return;
      setShowEndModal(true);
      window.history.pushState({ severityQueueGuard: true }, "", window.location.href);
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [sessionActive]);

  const counts = {
    CRITICAL: patients.filter((patient) => patient.severity === "CRITICAL").length,
    HIGH: patients.filter((patient) => patient.severity === "HIGH").length,
    MEDIUM: patients.filter((patient) => patient.severity === "MEDIUM").length,
    LOW: patients.filter((patient) => patient.severity === "LOW").length,
  };
  const specialtyUnmatchedCount = patients.filter(
    (patient) => patient.specialty_unmatched
  ).length;

  const handleEndSession = useCallback(async () => {
    if (!session || loading || endLock.current) return;
    endLock.current = true;
    setEnding(true);
    setError("");
    try {
      if (readPendingPatients(session.session_id).length) {
        throw new Error("A complaint is awaiting save confirmation. Return to New Patient and retry it first.");
      }
      // Fetch again so an archive includes records saved from other tabs.
      const confirmedPatients = await loadSessionPatients(api, session.session_id);
      const summary = { total: confirmedPatients.length };
      for (const severity of Object.keys(SEV_ORDER)) {
        summary[severity] = confirmedPatients.filter((p) => p.severity === severity).length;
      }
      await api.endTriageSession({
        session_id: session.session_id,
        session: { ...session, started_at: session.startedAt },
        patients: confirmedPatients,
        summary,
      });
      // Clear local state only after server acknowledgement.
      try {
        const archive = JSON.parse(localStorage.getItem(ARCHIVE_KEY) || "[]");
        if (Array.isArray(archive)) {
          localStorage.setItem(ARCHIVE_KEY, JSON.stringify([
            ...archive.filter((s) => s.session_id !== session.session_id),
            { ...session, patients: confirmedPatients, endedAt: new Date().toISOString(), summary },
          ]));
        }
      } catch (cacheError) { console.warn("[triage] Archive saved; local cache failed:", cacheError); }
      localStorage.removeItem(SESSION_KEY);
      try { cacheSessionPatients(session, []); } catch (cacheError) { console.warn("[triage] Old cache retained:", cacheError); }
      setShowEndModal(false);
      navigate("/camp-setup");
    } catch (err) {
      console.error("[triage] Session archive not confirmed:", err);
      setError(`Unable to end session: ${err.message}`);
      setShowEndModal(false);
    } finally { endLock.current = false; setEnding(false); }
  }, [loading, navigate, session]);

  if (!session) return <div role="alert">{error || "Loading session..."}</div>;

  return (
    <div className="priority-page">
      {showEndModal && (
        <EndSessionModal
          saving={ending}
          session={session}
          patients={patients}
          counts={counts}
          onConfirm={handleEndSession}
          onCancel={() => setShowEndModal(false)}
        />
      )}

      <main className="priority-container">
        {error && <div className="priority-feedback" role="alert">{error} <button className="priority-btn-refresh" type="button" disabled={loading || ending} onClick={refreshSavedRecords}>Retry loading</button></div>}
        {pendingCount > 0 && <p role="alert">{pendingCount} locally stored complaint(s) need save confirmation. <Link to="/priority-application">Review and retry pending complaints</Link></p>}
        <section className="priority-header">
          <div className="priority-header-copy">
            <span className="priority-camp-label">{[session.camp.code, session.camp.name].filter(Boolean).join(" - ")}</span>
            <h1>MO Queue</h1>
            <p>CRITICAL → HIGH → MEDIUM → LOW. Arrival order within each level.</p>
          </div>
          <div className="priority-header-actions" role="group" aria-label="Queue actions">
            <button className="priority-action priority-btn-refresh" type="button" aria-label={loading ? "Refreshing saved records" : "Refresh saved records"} aria-busy={loading} disabled={loading || ending} onClick={refreshSavedRecords}>
              <RefreshCw size={16} aria-hidden="true" />
              {loading ? "Refreshing..." : "Refresh"}
            </button>
            <Link to="/priority-application" className="priority-action priority-btn-new">
              <Plus size={16} aria-hidden="true" />
              New Patient
            </Link>
            <button
              disabled={loading || Boolean(error) || ending}
              className="priority-action priority-btn-end"
              type="button"
              onClick={() => setShowEndModal(true)}
            >
              End Session
            </button>
          </div>
        </section>
        {loading && <p className="priority-load-status" role="status">Loading saved complaints...</p>}

        <section className="priority-toolbar">
          <div className="priority-toolbar-summary">
            <p>
              <strong>{patients.length}</strong> patient{patients.length !== 1 ? "s" : ""} in session
            </p>
            {specialtyUnmatchedCount > 0 && (
              <span className="priority-specialty-unmatched-count">
                {specialtyUnmatchedCount} no matching specialist
              </span>
            )}
          </div>
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
        </section>

        {!loading && !error && patients.length === 0 ? (
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
                              <div className="ppc-left">
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
                              {patient.specialty_unmatched && (
                                <span className="ppc-specialty-unmatched">
                                  No matching specialist
                                </span>
                              )}
                              {patient.clinician_override && (
                                <span className="ppc-override">
                                  Override {patient.clinician_override.from} to {patient.clinician_override.to}
                                </span>
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
                        <div className="ppc-left">
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
                        {patient.specialty_unmatched && (
                          <span className="ppc-specialty-unmatched">
                            No matching specialist
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
