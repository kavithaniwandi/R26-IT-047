import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import "./CampAnalyzer.css";

const SESSION_KEY = "severityQueueSession";
const PATIENT_KEY = "priorityApplications";
const ARCHIVE_KEY = "severityQueueSessions";
const ACTIVATION_KEY = "campActivationState";

const SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const SEV_COLOR = {
  CRITICAL: "#b91c1c",
  HIGH: "#c2410c",
  MEDIUM: "#b45309",
  LOW: "#15803d",
};

const safeJson = (key, fallback) => {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
};

const countBy = (items, selector) =>
  items.reduce((acc, item) => {
    const key = selector(item) || "Unknown";
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

const formatTime = (value) => {
  if (!value) return "Not recorded";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not recorded";
  return date.toLocaleString();
};

const complaintText = (patient) =>
  patient.complaint_text ||
  patient.symptoms ||
  patient.original_symptoms_text ||
  patient.description ||
  patient.model_symptoms ||
  "No complaint recorded";

const complaintStatus = (patient) => {
  if (patient.mapped_complaints?.length) {
    return patient.mapped_complaints.join(", ");
  }
  if (patient.mapping_review_reason) {
    return patient.mapping_review_reason;
  }
  if (patient.matched_rules?.some((rule) => String(rule).includes("complaint not recognised"))) {
    return "complaint not recognised - review";
  }
  return "Recorded";
};

export default function CampAnalyzer() {
  const [camps, setCamps] = useState([]);
  const [dbPatients, setDbPatients] = useState([]);
  const [remoteArchives, setRemoteArchives] = useState([]);
  const [selectedArchive, setSelectedArchive] = useState(null);
  const [archiveLoading, setArchiveLoading] = useState(false);
  const [loadError, setLoadError] = useState("");

  const session = safeJson(SESSION_KEY, null);
  const localPatients = safeJson(PATIENT_KEY, []);
  const livePatients = dbPatients.length ? dbPatients : localPatients;
  const patients = selectedArchive?.patients || livePatients;
  const localArchives = safeJson(ARCHIVE_KEY, []);
  const activation = safeJson(ACTIVATION_KEY, {});
  const archives = remoteArchives.length ? remoteArchives : localArchives;

  useEffect(() => {
    let alive = true;

    Promise.allSettled([
      api.getCamps({ status_filter: "approved" }),
      api.getTriagePatients({
        limit: 500,
        ...(session?.session_id ? { session_id: session.session_id } : {}),
      }),
      api.getTriageArchives({ limit: 100 }),
    ]).then(([campResult, patientResult, archiveResult]) => {
      if (!alive) return;

      if (campResult.status === "fulfilled") {
        setCamps(Array.isArray(campResult.value) ? campResult.value : []);
      } else {
        setLoadError(campResult.reason?.message || "Could not load camp list.");
      }

      if (patientResult.status === "fulfilled") {
        setDbPatients(Array.isArray(patientResult.value?.patients) ? patientResult.value.patients : []);
      } else {
        setLoadError(patientResult.reason?.message || "Could not load patient records from database.");
      }

      if (archiveResult.status === "fulfilled") {
        setRemoteArchives(Array.isArray(archiveResult.value?.archives) ? archiveResult.value.archives : []);
      }
    });

    return () => {
      alive = false;
    };
  }, [session?.session_id]);

  const analytics = useMemo(() => {
    const severityCounts = Object.fromEntries(SEVERITIES.map((severity) => [severity, 0]));
    patients.forEach((patient) => {
      severityCounts[patient.severity] = (severityCounts[patient.severity] || 0) + 1;
    });

    const assignedCount = patients.filter((patient) => patient.assigned_mo_id).length;
    const unassignedCount = patients.length - assignedCount;
    const riskValues = patients
      .map((patient) => Number(patient.risk_score))
      .filter((value) => Number.isFinite(value));
    const avgRisk = riskValues.length
      ? Math.round(riskValues.reduce((sum, value) => sum + value, 0) / riskValues.length)
      : 0;
    const conditionCounts = countBy(patients, (patient) => patient.condition_group);
    const moCounts = countBy(patients, (patient) => patient.assigned_mo_name || "Unassigned");

    return {
      severityCounts,
      assignedCount,
      unassignedCount,
      avgRisk,
      conditionCounts,
      moCounts,
    };
  }, [patients]);

  const handleArchiveSelect = async (archive) => {
    setLoadError("");
    setArchiveLoading(true);

    if (archive.patients) {
      setSelectedArchive(archive);
      setArchiveLoading(false);
      return;
    }

    try {
      const detail = await api.getTriageArchive(archive.session_id);
      setSelectedArchive(detail);
    } catch (err) {
      setLoadError(err?.message || "Could not load archived session details.");
    } finally {
      setArchiveLoading(false);
    }
  };

  const handleLiveSelect = () => {
    setSelectedArchive(null);
  };

  const activeCampIds = new Set(
    Object.entries(activation)
      .filter(([, active]) => active)
      .map(([campId]) => String(campId))
  );

  const currentCampId = session?.camp?.id ? String(session.camp.id) : null;
  const activeCamps = camps.filter((camp) => activeCampIds.has(String(camp.id)));
  const archiveTotal = Math.max(localArchives.length, remoteArchives.length);
  const analyzedSession = selectedArchive || session;
  const analyzedCamp = analyzedSession?.camp;
  const analyzedStartedAt = selectedArchive
    ? selectedArchive.started_at || selectedArchive.startedAt
    : session?.startedAt;
  const analyzedEndedAt = selectedArchive?.ended_at || selectedArchive?.endedAt;

  return (
    <div className="ca-page">
      <main className="ca-container">
        <section className="ca-header">
          <div>
            <span>Camp intelligence</span>
            <h1>Camp Analyzer</h1>
            <p>
              Review active camp status, triage workload, patient severity patterns, and saved
              session history.
            </p>
          </div>
          <div className="ca-header-actions">
            <Link to="/camp-setup">Camp setup</Link>
            <Link to="/priority-queue">Queue</Link>
          </div>
        </section>

        {loadError && <div className="ca-warning">{loadError}</div>}
        {archiveLoading && <div className="ca-warning">Loading archived session analytics...</div>}

        <section className="ca-scope">
          <button
            type="button"
            className={!selectedArchive ? "active" : ""}
            onClick={handleLiveSelect}
          >
            Live/current session
          </button>
          <span>
            {selectedArchive
              ? `Viewing past session ${selectedArchive.session_id}`
              : "Viewing current database patient stream"}
          </span>
        </section>

        <section className="ca-metrics">
          <div className="ca-metric">
            <span>Approved camps</span>
            <strong>{camps.length}</strong>
          </div>
          <div className="ca-metric">
            <span>Active camps</span>
            <strong>{activeCamps.length}</strong>
          </div>
          <div className="ca-metric">
            <span>Patients analyzed</span>
            <strong>{patients.length}</strong>
          </div>
          <div className="ca-metric">
            <span>Archived sessions</span>
            <strong>{archiveTotal}</strong>
          </div>
          <div className="ca-metric">
            <span>Average risk</span>
            <strong>{analytics.avgRisk}</strong>
          </div>
        </section>

        <section className="ca-grid">
          <div className="ca-panel">
            <div className="ca-panel-head">
              <h2>Analyzed Session</h2>
              <span>{selectedArchive ? "Past session" : session ? "Live session" : "No live session"}</span>
            </div>
            {analyzedSession ? (
              <div className="ca-current">
                <strong>{analyzedCamp?.name || "Unknown camp"}</strong>
                <p>{[analyzedCamp?.district, analyzedCamp?.ds_division, analyzedCamp?.gn_division].filter(Boolean).join(" / ") || "Location not recorded"}</p>
                <div className="ca-detail-grid">
                  <div><span>Started</span><strong>{formatTime(analyzedStartedAt)}</strong></div>
                  <div><span>Ended</span><strong>{selectedArchive ? formatTime(analyzedEndedAt) : "Active"}</strong></div>
                  <div><span>MOs</span><strong>{analyzedSession.mos?.length || 0}</strong></div>
                  <div><span>Capacity</span><strong>{analyzedCamp?.estimated_capacity || "N/A"}</strong></div>
                  <div><span>Assigned</span><strong>{analytics.assignedCount}</strong></div>
                </div>
              </div>
            ) : (
              <div className="ca-empty">
                Start a camp session from Camp Setup or select a past session below.
              </div>
            )}
          </div>

          <div className="ca-panel">
            <div className="ca-panel-head">
              <h2>Severity Mix</h2>
              <span>{patients.length} total</span>
            </div>
            <div className="ca-severity-list">
              {SEVERITIES.map((severity) => {
                const count = analytics.severityCounts[severity] || 0;
                const width = patients.length ? Math.max(4, (count / patients.length) * 100) : 0;
                return (
                  <div key={severity} className="ca-severity-row">
                    <div>
                      <span>{severity}</span>
                      <strong>{count}</strong>
                    </div>
                    <div className="ca-bar">
                      <span style={{ width: `${width}%`, background: SEV_COLOR[severity] }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        <section className="ca-grid">
          <div className="ca-panel">
            <div className="ca-panel-head">
              <h2>Camp Data</h2>
              <span>{activeCamps.length} active</span>
            </div>
            <div className="ca-table-wrap">
              <table className="ca-table">
                <thead>
                  <tr>
                    <th>Camp</th>
                    <th>District</th>
                    <th>Status</th>
                    <th>Capacity</th>
                  </tr>
                </thead>
                <tbody>
                  {camps.map((camp) => {
                    const active = activeCampIds.has(String(camp.id));
                    const current = currentCampId === String(camp.id);
                    return (
                      <tr key={camp.id} className={current ? "current" : ""}>
                        <td>{camp.name}</td>
                        <td>{camp.district || "N/A"}</td>
                        <td>{current ? "Current" : active ? "Active" : "Standby"}</td>
                        <td>{camp.estimated_capacity || "N/A"}</td>
                      </tr>
                    );
                  })}
                  {!camps.length && (
                    <tr>
                      <td colSpan="4">No camp records loaded.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="ca-panel">
            <div className="ca-panel-head">
              <h2>MO Load</h2>
              <span>{analytics.unassignedCount} unassigned</span>
            </div>
            <div className="ca-rank-list">
              {Object.entries(analytics.moCounts).map(([name, count]) => (
                <div key={name} className="ca-rank-row">
                  <span>{name}</span>
                  <strong>{count}</strong>
                </div>
              ))}
              {!patients.length && <div className="ca-empty compact">No patient workload yet.</div>}
            </div>
          </div>
        </section>

        <section className="ca-panel">
          <div className="ca-panel-head">
            <h2>Patient Details</h2>
            <span>
              {selectedArchive ? "Archived records" : dbPatients.length ? "Database records" : "Local records"} / {patients.length}
            </span>
          </div>
          <div className="ca-table-wrap">
            <table className="ca-table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Complaint</th>
                  <th>Severity</th>
                  <th>Age</th>
                  <th>Condition</th>
                  <th>Assigned MO</th>
                  <th>Risk</th>
                  <th>Submitted</th>
                </tr>
              </thead>
              <tbody>
                {patients.map((patient) => (
                  <tr key={patient._id || patient.id}>
                    <td>
                      <strong>{patient.id}</strong>
                      <span>{complaintStatus(patient)}</span>
                    </td>
                    <td>{complaintText(patient)}</td>
                    <td style={{ color: SEV_COLOR[patient.severity] || "#475569", fontWeight: 800 }}>
                      {patient.severity || "N/A"}
                    </td>
                    <td>{patient.age || "N/A"}</td>
                    <td>{patient.condition_group || "N/A"}</td>
                    <td>{patient.assigned_mo_name || "Unassigned"}</td>
                    <td>{patient.risk_score ?? "N/A"}</td>
                    <td>{formatTime(patient.submittedAt || patient.submitted_at)}</td>
                  </tr>
                ))}
                {!patients.length && (
                  <tr>
                    <td colSpan="8">No patient details yet. Submit patient cases from Patient Severity Application.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="ca-grid">
          <div className="ca-panel">
            <div className="ca-panel-head">
              <h2>Condition Groups</h2>
              <span>{Object.keys(analytics.conditionCounts).length} groups</span>
            </div>
            <div className="ca-rank-list">
              {Object.entries(analytics.conditionCounts).map(([condition, count]) => (
                <div key={condition} className="ca-rank-row">
                  <span>{condition}</span>
                  <strong>{count}</strong>
                </div>
              ))}
              {!patients.length && <div className="ca-empty compact">No condition data yet.</div>}
            </div>
          </div>

          <div className="ca-panel">
            <div className="ca-panel-head">
              <h2>Recent Archives</h2>
              <span>{archiveTotal} sessions</span>
            </div>
            <div className="ca-archive-list">
              {archives.slice(0, 8).map((archive) => (
                <button
                  key={archive._id || archive.session_id}
                  type="button"
                  className={`ca-archive-row ${selectedArchive?.session_id === archive.session_id ? "active" : ""}`}
                  onClick={() => handleArchiveSelect(archive)}
                >
                  <strong>{archive.camp?.name || "Archived camp"}</strong>
                  <span>
                    {archive.summary?.total || archive.patients?.length || 0} patients / ended {formatTime(archive.ended_at || archive.endedAt)}
                  </span>
                </button>
              ))}
              {!archiveTotal && <div className="ca-empty compact">No archived sessions yet.</div>}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
