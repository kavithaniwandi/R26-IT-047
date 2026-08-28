import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Users, 
  Tent, 
  HeartHandshake, 
  Activity, 
  ArrowUpRight, 
  CheckCircle2, 
  MapPin,
  Layers,
  Zap,
  Filter,
  Copy,
  Download,
  Share2,
  AlertTriangle,
  Clock
} from 'lucide-react';
import { RealTimeMap } from '../components/RealTimeMap';
import { api } from '../api';

export function OverviewView({ stats, onNavigate, onResolveSOS, onAddToast }) {
  const [heatmapData, setHeatmapData] = useState(null);
  const [filterStatus, setFilterStatus] = useState('all'); // 'all', 'active', 'triaged'

  useEffect(() => {
    const fetchHeatmap = async () => {
      try {
        const data = await api.getHeatmap();
        setHeatmapData(data);
      } catch (err) {
        console.error('Overview map load error:', err);
      }
    };
    fetchHeatmap();
  }, []);

  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text);
    if (onAddToast) {
      onAddToast(`Copied ${label} to clipboard: ${text}`, 'info', 'Copied');
    }
  };

  const handleExportSummary = () => {
    if (!stats) return;
    const summary = {
      generatedAt: new Date().toISOString(),
      activeEmergencies: stats.sos.active,
      triagedEmergencies: stats.sos.triaged,
      resolvedEmergencies: stats.sos.resolved,
      approvedCamps: stats.camps.approved,
      shortfalls: stats.donations.unmet,
      verifiedPledges: stats.donations.total_pledges,
      recentCriticalSOS: stats.recent_critical_sos
    };
    const blob = new Blob([JSON.stringify(summary, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `disaster_relief_triage_summary_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    if (onAddToast) {
      onAddToast('National triage summary exported successfully.', 'success', 'Exported');
    }
  };

  if (!stats) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--text-muted)' }}>
        <div className="spin" style={{ display: 'inline-block', marginBottom: '16px' }}>
          <Activity size={32} style={{ color: 'var(--accent-blue)' }} />
        </div>
        <p style={{ fontWeight: '600', fontSize: '0.95rem' }}>Loading national telemetry and metrics...</p>
      </div>
    );
  }

  const { users, sos, camps, donations, recent_critical_sos } = stats;

  const filteredSOS = (recent_critical_sos || []).filter((item) => {
    if (filterStatus === 'active') return item.status === 'active';
    if (filterStatus === 'triaged') return item.status === 'triaged' || item.status === 'resolved';
    return true;
  });

  return (
    <div>
      {/* Top KPI Metric Cards */}
      <div className="kpi-grid">
        <div className="kpi-card" onClick={() => onNavigate('sos')} style={{ cursor: 'pointer' }}>
          <div className="kpi-top">
            <span className="kpi-label">Active Emergencies</span>
            <div className="kpi-icon-wrap" style={{ backgroundColor: 'var(--accent-rose-subtle)', color: 'var(--accent-rose)' }}>
              <ShieldAlert size={20} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: 'var(--accent-rose)' }}>
            {sos.active}
          </div>
          <div className="kpi-footer">
            <span style={{ color: 'var(--accent-amber)', fontWeight: '700' }}>{sos.triaged} Triaged</span>
            <span>&bull;</span>
            <span style={{ color: 'var(--accent-emerald)', fontWeight: '700' }}>{sos.resolved} Resolved</span>
          </div>
        </div>

        <div className="kpi-card" onClick={() => onNavigate('camps')} style={{ cursor: 'pointer' }}>
          <div className="kpi-top">
            <span className="kpi-label">Medical Relief Camps</span>
            <div className="kpi-icon-wrap" style={{ backgroundColor: 'var(--accent-blue-subtle)', color: 'var(--accent-blue)' }}>
              <Tent size={20} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: 'var(--accent-blue)' }}>
            {camps.approved + camps.operational}
          </div>
          <div className="kpi-footer">
            <span style={{ color: 'var(--accent-blue)', fontWeight: '700' }}>{camps.proposed} Proposed for Review</span>
          </div>
        </div>

        <div className="kpi-card" onClick={() => onNavigate('donations')} style={{ cursor: 'pointer' }}>
          <div className="kpi-top">
            <span className="kpi-label">Supply Shortfalls</span>
            <div className="kpi-icon-wrap" style={{ backgroundColor: 'var(--accent-amber-subtle)', color: 'var(--accent-amber)' }}>
              <HeartHandshake size={20} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: 'var(--accent-amber)' }}>
            {donations.unmet + donations.partially_met}
          </div>
          <div className="kpi-footer">
            <span style={{ color: 'var(--accent-emerald)', fontWeight: '700' }}>{donations.total_pledges} Donor Pledges</span>
          </div>
        </div>

        <div className="kpi-card" onClick={() => onNavigate('users')} style={{ cursor: 'pointer' }}>
          <div className="kpi-top">
            <span className="kpi-label">Active Stakeholders</span>
            <div className="kpi-icon-wrap" style={{ backgroundColor: 'var(--accent-emerald-subtle)', color: 'var(--accent-emerald)' }}>
              <Users size={20} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: 'var(--accent-emerald)' }}>
            {users.total}
          </div>
          <div className="kpi-footer">
            <span style={{ color: 'var(--text-secondary)' }}>5 RBAC System Roles</span>
          </div>
        </div>
      </div>

      {/* REAL-TIME INTERACTIVE MAP PREVIEW */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div>
            <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={18} style={{ color: 'var(--accent-blue)' }} />
              <span>Real-Time Situational Awareness Map</span>
            </h2>
            <p className="card-subtitle">
              Live OpenStreetMap GIS telemetry rendering Kelani river basin, Nuwara Eliya landslide zones, and active SOS beacons
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn btn-secondary btn-sm" onClick={handleExportSummary} title="Export Triage Snapshot">
              <Download size={14} />
              <span>Export Triage Summary</span>
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('heatmap')}>
              <span>Open Full GIS & ML Predictor</span>
              <ArrowUpRight size={14} />
            </button>
          </div>
        </div>

        <RealTimeMap
          sosPoints={heatmapData?.sos_clusters || []}
          hazardZones={heatmapData?.hazard_zones || []}
          camps={heatmapData?.medical_camps || []}
          height="420px"
          onResolveSOS={onResolveSOS}
          autoRefreshInterval={8000}
        />
      </div>

      {/* Main Grid: Priority Triage Queue + Role Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: '2.2fr 1fr', gap: '24px' }}>
        {/* Critical Triage Queue */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Live Critical SOS Triage Queue</h2>
              <p className="card-subtitle">Ranked by ML Model 4 Urgency Priority Algorithm</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {/* Quick filter chips */}
              <div style={{ display: 'flex', background: 'var(--bg-secondary)', padding: '2px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <button
                  className={`btn-sm ${filterStatus === 'all' ? 'btn-secondary' : ''}`}
                  style={{ border: 'none', background: filterStatus === 'all' ? 'var(--bg-card)' : 'transparent', color: filterStatus === 'all' ? 'var(--text-primary)' : 'var(--text-muted)', cursor: 'pointer', borderRadius: 'var(--radius-xs)', padding: '3px 8px', fontSize: '0.72rem', fontWeight: '700' }}
                  onClick={() => setFilterStatus('all')}
                >
                  All
                </button>
                <button
                  className={`btn-sm ${filterStatus === 'active' ? 'btn-secondary' : ''}`}
                  style={{ border: 'none', background: filterStatus === 'active' ? 'var(--bg-card)' : 'transparent', color: filterStatus === 'active' ? 'var(--accent-rose)' : 'var(--text-muted)', cursor: 'pointer', borderRadius: 'var(--radius-xs)', padding: '3px 8px', fontSize: '0.72rem', fontWeight: '700' }}
                  onClick={() => setFilterStatus('active')}
                >
                  Active ({sos.active})
                </button>
                <button
                  className={`btn-sm ${filterStatus === 'triaged' ? 'btn-secondary' : ''}`}
                  style={{ border: 'none', background: filterStatus === 'triaged' ? 'var(--bg-card)' : 'transparent', color: filterStatus === 'triaged' ? 'var(--accent-emerald)' : 'var(--text-muted)', cursor: 'pointer', borderRadius: 'var(--radius-xs)', padding: '3px 8px', fontSize: '0.72rem', fontWeight: '700' }}
                  onClick={() => setFilterStatus('triaged')}
                >
                  Triaged
                </button>
              </div>

              <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('sos')}>
                <span>View Full Queue ({sos.total})</span>
                <ArrowUpRight size={14} />
              </button>
            </div>
          </div>

          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Incident</th>
                  <th>Location</th>
                  <th>Affected</th>
                  <th>Urgency</th>
                  <th>ML Priority</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredSOS && filteredSOS.length > 0 ? (
                  filteredSOS.slice(0, 7).map((item) => (
                    <tr key={item.id}>
                      <td style={{ fontWeight: '800', color: 'var(--text-primary)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <span>#{item.id}</span>
                          <button
                            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '2px' }}
                            onClick={() => copyToClipboard(`#${item.id}`, 'Incident ID')}
                            title="Copy ID"
                          >
                            <Copy size={11} />
                          </button>
                        </div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <MapPin size={14} style={{ color: 'var(--accent-rose)', flexShrink: 0 }} />
                          <span style={{ fontWeight: '600' }}>{item.gn_division || item.ds_division || item.district}</span>
                        </div>
                      </td>
                      <td>{item.affected_people} Persons</td>
                      <td>
                        <span className="badge badge-medium">Level {item.urgency_level} / 5</span>
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            item.priority_score >= 85
                              ? 'badge-critical'
                              : item.priority_score >= 70
                              ? 'badge-high'
                              : 'badge-low'
                          }`}
                        >
                          {item.priority_score} / 100
                        </span>
                      </td>
                      <td>
                        <span className={`badge badge-${item.status}`}>{item.status}</span>
                      </td>
                      <td>
                        {item.status === 'active' ? (
                          <button
                            className="btn btn-success btn-sm"
                            onClick={() => onResolveSOS(item.id, 'triaged')}
                          >
                            <CheckCircle2 size={13} />
                            <span>Triage</span>
                          </button>
                        ) : (
                          <span style={{ fontSize: '0.75rem', color: 'var(--accent-emerald)', fontWeight: '700', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                            <CheckCircle2 size={12} />
                            <span>Triaged</span>
                          </span>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                      No emergency alerts found matching the current filter.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Stakeholder RBAC Breakdown & Inference Status */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <h2 className="card-title">System Role Distribution</h2>
            <p className="card-subtitle">Active Verified Stakeholder Profiles</p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {Object.entries(users.by_role || {}).map(([role, count]) => {
              const pct = users.total > 0 ? Math.round((count / users.total) * 100) : 0;
              return (
                <div key={role}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '6px' }}>
                    <span style={{ textTransform: 'capitalize', fontWeight: '700', color: 'var(--text-primary)' }}>{role}</span>
                    <span style={{ color: 'var(--text-muted)' }}>{count} ({pct}%)</span>
                  </div>
                  <div style={{ height: '6px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        width: `${pct}%`,
                        borderRadius: 'var(--radius-full)',
                        backgroundColor:
                          role === 'admin'
                            ? 'var(--accent-rose)'
                            : role === 'authority'
                            ? 'var(--accent-blue)'
                            : role === 'donor'
                            ? 'var(--accent-emerald)'
                            : role === 'volunteer'
                            ? 'var(--accent-amber)'
                            : 'var(--accent-violet)'
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{
            marginTop: 'auto',
            padding: '16px',
            backgroundColor: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <Zap size={16} style={{ color: 'var(--accent-emerald)' }} />
              <span style={{ fontSize: '0.86rem', fontWeight: '800', color: 'var(--text-primary)' }}>ML Engine Operational</span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              All 4 Random Forest models active in-memory. Response latency: <strong>&lt; 2.2ms</strong>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
