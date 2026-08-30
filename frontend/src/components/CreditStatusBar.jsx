import React, { useState, useEffect } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const HEALTH_CONFIG = {
  healthy:  { bg: "#dcfce7", border: "#86efac", text: "#166534", dot: "#16a34a", label: "All systems operational" },
  degraded: { bg: "#fef3c7", border: "#fcd34d", text: "#92400e", dot: "#d97706", label: "Degraded"               },
  warning:  { bg: "#fff7ed", border: "#fed7aa", text: "#92400e", dot: "#ea580c", label: "Warning"                },
  critical: { bg: "#fee2e2", border: "#fecaca", text: "#991b1b", dot: "#dc2626", label: "Critical"               },
};

export default function CreditStatusBar() {
  const [status,  setStatus]  = useState(null);
  const [open,    setOpen]    = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const res  = await fetch(`${API_BASE_URL}/api/system/credit-status`);
      const data = await res.json();
      setStatus(data);
    } catch {
      setStatus(null);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/system/credit-reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      await fetchStatus();
    } catch (error) {
      console.error("Reset failed", error);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 60_000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !status) return null;

  const cfg = HEALTH_CONFIG[status.health] || HEALTH_CONFIG.healthy;

  return (
    <div style={{ position: "relative", display: "inline-block" }}>
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          background:   cfg.bg,
          border:       `1.5px solid ${cfg.border}`,
          borderRadius: "999px",
          color:        cfg.text,
          cursor:       "pointer",
          display:      "flex",
          alignItems:   "center",
          gap:          "0.4rem",
          fontSize:     "0.75rem",
          fontWeight:   "700",
          padding:      "0.25rem 0.75rem",
          whiteSpace:   "nowrap",
        }}
      >
        <span
          style={{
            width:       "8px",
            height:      "8px",
            borderRadius: "50%",
            background:  cfg.dot,
            flexShrink:  0,
            animation:   status.health !== "healthy" ? "csb-pulse 1.5s infinite" : "none",
          }}
        />
        API {cfg.label}
        <span style={{ fontSize: "0.7rem", opacity: 0.8 }}>{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div
          style={{
            position:     "absolute",
            top:          "calc(100% + 8px)",
            right:        0,
            background:   "#ffffff",
            border:       "1.5px solid #c7d7f5",
            borderRadius: "10px",
            boxShadow:    "0 4px 20px rgba(21,101,192,0.12)",
            padding:      "1rem",
            minWidth:     "280px",
            zIndex:       1000,
          }}
        >
          <p
            style={{
              color:         "#1565c0",
              fontSize:      "0.72rem",
              fontWeight:    "800",
              letterSpacing: "0.7px",
              textTransform: "uppercase",
              margin:        "0 0 0.75rem",
            }}
          >
            Provider Status
          </p>

          {status.message && (
            <p
              style={{
                background:   cfg.bg,
                border:       `1px solid ${cfg.border}`,
                borderRadius: "6px",
                color:        cfg.text,
                fontSize:     "0.78rem",
                padding:      "0.4rem 0.6rem",
                margin:       "0 0 0.75rem",
              }}
            >
              {status.message}
            </p>
          )}

          {status.providers?.map((p, i) => (
            <div
              key={i}
              style={{
                display:        "flex",
                justifyContent: "space-between",
                alignItems:     "center",
                padding:        "0.45rem 0",
                borderBottom:   "1px solid #e3f0ff",
                fontSize:       "0.8rem",
                gap:            "0.5rem",
              }}
            >
              <div>
                <span style={{ color: "#1e293b", fontWeight: "700" }}>{p.provider}</span>
                {p.calls_today > 0 && (
                  <span style={{ color: "#64748b", fontSize: "0.72rem", marginLeft: "0.4rem" }}>
                    {p.calls_today} calls
                  </span>
                )}
              </div>
              <span
                style={{
                  background: p.exhausted
                    ? "#fee2e2"
                    : p.status_label === "Active"
                      ? "#dcfce7"
                      : p.status_label === "Standby"
                        ? "#fef3c7"
                        : "#f1f5f9",
                  color: p.exhausted
                    ? "#991b1b"
                    : p.status_label === "Active"
                      ? "#166534"
                      : p.status_label === "Standby"
                        ? "#92400e"
                        : "#64748b",
                  borderRadius: "999px",
                  fontSize:     "0.68rem",
                  fontWeight:   "800",
                  padding:      "0.15rem 0.55rem",
                  whiteSpace:   "nowrap",
                }}
              >
                {p.status_label || (p.exhausted ? "Exhausted" : p.configured ? "Active" : "Not configured")}
              </span>
            </div>
          ))}

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginTop: "0.6rem",
              paddingTop: "0.5rem",
              borderTop: "1px solid #e3f0ff",
            }}
          >
            <span style={{ color: "#a0aec0", fontSize: "0.68rem" }}>
              Refreshes every 60s
            </span>
            <button
              onClick={handleReset}
              style={{
                background: "none",
                border: "1px solid #c7d7f5",
                borderRadius: "6px",
                color: "#3d5a9e",
                cursor: "pointer",
                fontSize: "0.68rem",
                fontWeight: "700",
                padding: "0.15rem 0.5rem",
              }}
            >
              Reset all
            </button>
          </div>
        </div>
      )}

      <style>{`
        @keyframes csb-pulse {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}
