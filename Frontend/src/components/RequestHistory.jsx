import { useState, useEffect, useCallback } from "react";

const URGENCY_CONFIG = {
  critical: { label: "Critical", color: "#c0392b", bg: "#fdf0ef", border: "#e74c3c", dot: true },
  high:     { label: "High",     color: "#d35400", bg: "#fef5ec", border: "#e67e22", dot: false },
  normal:   { label: "Normal",   color: "#1a6b3c", bg: "#edfaf3", border: "#27ae60", dot: false },
};

const SYNC_CONFIG = {
  pending: { label: "Pending Sync", color: "#856404", bg: "#fff3cd", border: "#ffc107", icon: "🕐" },
  synced:  { label: "Synced",       color: "#1a6b3c", bg: "#edfaf3", border: "#27ae60", icon: "✅" },
  failed:  { label: "Failed",       color: "#c0392b", bg: "#fdf0ef", border: "#e74c3c", icon: "❌" },
};

function formatTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("en-GB", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export default function RequestHistory() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [filter, setFilter]     = useState("all");
  const [search, setSearch]     = useState("");

  const loadRequests = useCallback(() => {
    setLoading(true);
    try {
      // Get requests from localStorage
      const storedRequests = JSON.parse(localStorage.getItem('emergencyRequests') || '[]');
      storedRequests.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      setRequests(storedRequests);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadRequests(); }, [loadRequests]);

  const handleSync = () => {
    // For demo purposes, just show a message
    alert('Sync functionality requires backend server. Requests are stored locally.');
  };

  const counts = {
    all:      requests.length,
    pending:  requests.filter(r => r.syncStatus === "pending").length,
    synced:   requests.filter(r => r.syncStatus === "synced").length,
    critical: requests.filter(r => r.urgency === "critical").length,
    high:     requests.filter(r => r.urgency === "high").length,
    normal:   requests.filter(r => r.urgency === "normal").length,
  };

  const filtered = requests.filter((r) => {
    const matchFilter =
      filter === "all"     ? true :
      filter === "pending" ? r.syncStatus === "pending" :
      filter === "synced"  ? r.syncStatus === "synced"  :
      r.urgency === filter;

    const matchSearch =
      search.trim() === "" ||
      r.patientName?.toLowerCase().includes(search.toLowerCase()) ||
      r.medicalNeed?.toLowerCase().includes(search.toLowerCase());

    return matchFilter && matchSearch;
  });

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

        .rh-wrap {
          font-family: 'DM Sans', sans-serif;
          max-width: 900px;
          margin: 0 auto;
          padding: 0 16px 48px;
        }

        .rh-header {
          background: linear-gradient(135deg, #0a3d62 0%, #1565c0 100%);
          border-radius: 16px 16px 0 0;
          padding: 28px 36px 24px;
          color: white;
          position: relative;
          overflow: hidden;
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 12px;
        }

        .rh-header::before {
          content: '';
          position: absolute;
          top: -40px; right: -40px;
          width: 180px; height: 180px;
          border-radius: 50%;
          background: rgba(255,255,255,0.05);
          pointer-events: none;
        }

        .rh-header h1 {
          font-family: 'DM Serif Display', serif;
          font-size: 26px;
          font-weight: 400;
          margin: 0 0 4px;
        }

        .rh-header p { margin: 0; font-size: 13px; opacity: 0.7; }

        .rh-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 9px 18px;
          border-radius: 8px;
          border: 1.5px solid rgba(255,255,255,0.4);
          background: rgba(255,255,255,0.1);
          color: white;
          font-size: 13px;
          font-weight: 500;
          font-family: 'DM Sans', sans-serif;
          cursor: pointer;
          transition: all 0.2s;
        }

        .rh-btn:hover:not(:disabled) { background: rgba(255,255,255,0.2); }
        .rh-btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .rh-stats {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          background: #fff;
          border: 1px solid #e3eaf3;
          border-top: none;
        }

        .rh-stat {
          padding: 16px 20px;
          border-right: 1px solid #e3eaf3;
          text-align: center;
        }

        .rh-stat:last-child { border-right: none; }

        .rh-stat-num {
          font-size: 28px;
          font-family: 'DM Serif Display', serif;
          line-height: 1;
          margin-bottom: 4px;
        }

        .rh-stat-label {
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.8px;
          color: #888;
          font-weight: 500;
        }

        .rh-controls {
          background: #f8fbff;
          border: 1px solid #e3eaf3;
          border-top: none;
          padding: 14px 24px;
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
          align-items: center;
        }

        .rh-search {
          flex: 1;
          min-width: 180px;
          padding: 9px 14px 9px 36px;
          border: 1.5px solid #dce6f0;
          border-radius: 8px;
          font-size: 14px;
          font-family: 'DM Sans', sans-serif;
          background: #fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23999' stroke-width='2'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cpath d='m21 21-4.35-4.35'/%3E%3C/svg%3E") 10px center no-repeat;
          outline: none;
          transition: border-color 0.2s;
        }

        .rh-search:focus { border-color: #1565c0; }

        .rh-filters { display: flex; gap: 6px; flex-wrap: wrap; }

        .rh-filter-btn {
          padding: 6px 12px;
          border-radius: 20px;
          border: 1.5px solid #dce6f0;
          background: #fff;
          font-size: 12px;
          font-weight: 500;
          font-family: 'DM Sans', sans-serif;
          cursor: pointer;
          transition: all 0.15s;
          color: #555;
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .rh-filter-btn:hover { border-color: #1565c0; color: #1565c0; }
        .rh-filter-btn.active { background: #1565c0; border-color: #1565c0; color: #fff; }
        .rh-filter-btn.critical.active { background: #c0392b; border-color: #c0392b; }
        .rh-filter-btn.high.active     { background: #d35400; border-color: #d35400; }
        .rh-filter-btn.normal.active   { background: #1a6b3c; border-color: #1a6b3c; }

        .fc { background: rgba(255,255,255,0.25); border-radius: 10px; padding: 1px 6px; font-size: 11px; }
        .rh-filter-btn:not(.active) .fc { background: #f0f4f8; color: #888; }

        .rh-body {
          background: #fff;
          border: 1px solid #e3eaf3;
          border-top: none;
          border-radius: 0 0 16px 16px;
          overflow: hidden;
          box-shadow: 0 8px 32px rgba(13,61,98,0.08);
        }

        .rh-empty {
          padding: 60px 24px;
          text-align: center;
          color: #aaa;
        }

        .rh-empty-icon { font-size: 48px; margin-bottom: 12px; }
        .rh-empty h3 { margin: 0 0 6px; color: #555; font-weight: 500; }
        .rh-empty p  { margin: 0; font-size: 14px; }

        .rh-card { border-bottom: 1px solid #f0f4f8; transition: background 0.15s; }
        .rh-card:last-child { border-bottom: none; }
        .rh-card:hover { background: #fafcff; }

        .rh-card-row {
          padding: 16px 24px;
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 1fr 36px;
          gap: 12px;
          align-items: center;
          cursor: pointer;
        }

        .rh-name  { font-weight: 600; font-size: 15px; color: #1a2a3a; margin-bottom: 2px; }
        .rh-meta  { font-size: 12px; color: #888; }
        .rh-time  { font-size: 12px; color: #999; white-space: nowrap; }

        .badge {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 600;
          border: 1px solid;
          width: fit-content;
        }

        .dot-pulse {
          width: 7px; height: 7px;
          border-radius: 50%;
          animation: dotpulse 1.4s ease-in-out infinite;
          flex-shrink: 0;
        }

        @keyframes dotpulse {
          0%,100% { box-shadow: 0 0 0 0 rgba(231,76,60,0.5); }
          50%      { box-shadow: 0 0 0 4px rgba(231,76,60,0); }
        }

        .expand-btn {
          background: none;
          border: none;
          cursor: pointer;
          font-size: 18px;
          color: #aaa;
          transition: transform 0.2s, color 0.2s;
          padding: 0;
          line-height: 1;
        }

        .expand-btn.open { transform: rotate(180deg); color: #1565c0; }

        .rh-detail {
          padding: 0 24px 20px;
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          border-top: 1px solid #f0f4f8;
          animation: slideDown 0.2s ease;
        }

        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-6px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        .detail-section { padding-top: 16px; }

        .detail-label {
          font-size: 10px;
          font-weight: 600;
          letter-spacing: 1px;
          text-transform: uppercase;
          color: #1565c0;
          margin-bottom: 8px;
        }

        .med-table { width: 100%; border-collapse: collapse; font-size: 13px; }
        .med-table th {
          text-align: left;
          padding: 6px 10px;
          background: #f0f4f8;
          color: #555;
          font-weight: 500;
          font-size: 12px;
        }
        .med-table td { padding: 7px 10px; border-bottom: 1px solid #f5f5f5; color: #2c3e50; }

        .gps-box {
          background: #f0f4f8;
          border-radius: 8px;
          padding: 10px 14px;
          font-family: monospace;
          font-size: 13px;
          color: #2c3e50;
        }

        .notes-box {
          background: #f8fbff;
          border: 1px solid #e3eaf3;
          border-radius: 8px;
          padding: 10px 14px;
          font-size: 13px;
          color: #555;
          line-height: 1.6;
          min-height: 48px;
        }

        .rh-loading {
          padding: 48px;
          text-align: center;
          color: #aaa;
        }

        .spinner {
          width: 32px; height: 32px;
          border: 3px solid #e3eaf3;
          border-top-color: #1565c0;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
          margin: 0 auto 12px;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        @media (max-width: 640px) {
          .rh-card-row { grid-template-columns: 1fr 1fr 36px; }
          .rh-card-row > :nth-child(3),
          .rh-card-row > :nth-child(4) { display: none; }
          .rh-detail { grid-template-columns: 1fr; }
          .rh-stats  { grid-template-columns: repeat(2, 1fr); }
          .rh-header { padding: 20px 18px; }
        }
      `}</style>

      <div className="rh-wrap">

        {/* Header */}
        <div className="rh-header">
          <div>
            <h1>Request History</h1>
            <p>All locally stored emergency requests</p>
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button className="rh-btn" onClick={loadRequests}>🔄 Refresh</button>
            {counts.pending > 0 && (
              <button className="rh-btn" onClick={handleSync}>
                ⬆ Sync {counts.pending} Pending
              </button>
            )}
          </div>
        </div>

        {/* Stats */}
        <div className="rh-stats">
          <div className="rh-stat">
            <div className="rh-stat-num" style={{ color: "#1565c0" }}>{counts.all}</div>
            <div className="rh-stat-label">Total</div>
          </div>
          <div className="rh-stat">
            <div className="rh-stat-num" style={{ color: "#c0392b" }}>{counts.critical}</div>
            <div className="rh-stat-label">Critical</div>
          </div>
          <div className="rh-stat">
            <div className="rh-stat-num" style={{ color: "#856404" }}>{counts.pending}</div>
            <div className="rh-stat-label">Pending Sync</div>
          </div>
          <div className="rh-stat">
            <div className="rh-stat-num" style={{ color: "#1a6b3c" }}>{counts.synced}</div>
            <div className="rh-stat-label">Synced</div>
          </div>
        </div>

        {/* Controls */}
        <div className="rh-controls">
          <input
            className="rh-search"
            placeholder="Search by patient name or medical need..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <div className="rh-filters">
            {["all","critical","high","normal","pending","synced"].map((f) => (
              <button
                key={f}
                className={`rh-filter-btn ${f} ${filter === f ? "active" : ""}`}
                onClick={() => setFilter(f)}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
                <span className="fc">{counts[f] ?? 0}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Body */}
        <div className="rh-body">
          {loading ? (
            <div className="rh-loading">
              <div className="spinner" />
              Loading requests...
            </div>
          ) : filtered.length === 0 ? (
            <div className="rh-empty">
              <div className="rh-empty-icon">📋</div>
              <h3>{requests.length === 0 ? "No requests yet" : "No results found"}</h3>
              <p>
                {requests.length === 0
                  ? "Submit an emergency request to see it here"
                  : "Try adjusting your search or filter"}
              </p>
            </div>
          ) : (
            filtered.map((req) => {
              const urg    = URGENCY_CONFIG[req.urgency] || URGENCY_CONFIG.normal;
              const sync   = SYNC_CONFIG[req.syncStatus]  || SYNC_CONFIG.pending;
              const isOpen = expanded === req.localId;

              return (
                <div className="rh-card" key={req.localId}>

                  {/* Row */}
                  <div
                    className="rh-card-row"
                    onClick={() => setExpanded(isOpen ? null : req.localId)}
                  >
                    <div>
                      <div className="rh-name">{req.patientName}</div>
                      <div className="rh-meta">Age {req.age} &nbsp;·&nbsp; {req.medicalNeed || "—"}</div>
                    </div>

                    <div className="badge" style={{ color: urg.color, background: urg.bg, borderColor: urg.border }}>
                      {urg.dot && <span className="dot-pulse" style={{ background: urg.color }} />}
                      {urg.label}
                    </div>

                    <div className="badge" style={{ color: sync.color, background: sync.bg, borderColor: sync.border }}>
                      {sync.icon} {sync.label}
                    </div>

                    <div className="rh-time">{formatTime(req.timestamp)}</div>

                    <button className={`expand-btn ${isOpen ? "open" : ""}`}>▾</button>
                  </div>

                  {/* Expanded */}
                  {isOpen && (
                    <div className="rh-detail">
                      <div>
                        <div className="detail-section">
                          <div className="detail-label">Required Medicines</div>
                          {req.medicines?.filter(m => m.name).length > 0 ? (
                            <table className="med-table">
                              <thead>
                                <tr><th>Medicine</th><th>Amount</th></tr>
                              </thead>
                              <tbody>
                                {req.medicines.filter(m => m.name).map((m, i) => (
                                  <tr key={i}>
                                    <td>{m.name}</td>
                                    <td>{m.grams || "—"}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          ) : (
                            <div style={{ fontSize: 13, color: "#aaa" }}>No medicines listed</div>
                          )}
                        </div>

                        <div className="detail-section">
                          <div className="detail-label">Notes</div>
                          <div className="notes-box">
                            {req.notes || <span style={{ color: "#bbb" }}>No additional notes</span>}
                          </div>
                        </div>
                      </div>

                      <div>
                        <div className="detail-section">
                          <div className="detail-label">GPS Location</div>
                          {req.location ? (
                            <div className="gps-box">
                              📍 {req.location.lat}, {req.location.lng}
                              {req.location.accuracy && (
                                <span style={{ opacity: 0.6, fontSize: 11, marginLeft: 8 }}>
                                  ±{req.location.accuracy}m
                                </span>
                              )}
                            </div>
                          ) : (
                            <div style={{ fontSize: 13, color: "#aaa" }}>No GPS captured</div>
                          )}
                        </div>

                        <div className="detail-section">
                          <div className="detail-label">Record Info</div>
                          <div style={{ fontSize: 13, color: "#555", lineHeight: 2 }}>
                            <div>🕐 Saved: {formatTime(req.timestamp)}</div>
                            <div>
                              🔁 Status:&nbsp;
                              <span style={{ color: sync.color, fontWeight: 600 }}>
                                {sync.icon} {sync.label}
                              </span>
                            </div>
                            <div style={{ fontSize: 11, color: "#bbb", fontFamily: "monospace" }}>
                              ID: #{req.localId}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </>
  );
}
