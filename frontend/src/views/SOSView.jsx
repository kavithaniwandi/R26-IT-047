import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  MapPin, 
  Users, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  PlusCircle, 
  HeartHandshake,
  Activity,
  Filter,
  X
} from 'lucide-react';
import { api } from '../api';

export function SOSView({ onAddDonationNeed }) {
  const [sosList, setSosList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [districtFilter, setDistrictFilter] = useState('');
  const [showSimulateModal, setShowSimulateModal] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // New SOS form
  const [formData, setFormData] = useState({
    latitude: 6.936419,
    longitude: 79.957216,
    district: 'Colombo',
    ds_division: 'Kaduwela',
    gn_division: 'Ranala',
    address_text: '45 River View Lane, Ranala',
    urgency_level: 5,
    affected_people: 14,
    affected_families: 3,
    has_elderly: true,
    has_children: true,
    has_disabled: false,
    medical_needs_summary: 'Insulin, Saline 500ml, Trauma Kits, Clean Water',
  });

  const loadSOS = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSOSRequests({
        status_filter: statusFilter,
        district_filter: districtFilter,
      });
      setSosList(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSOS();
  }, [statusFilter, districtFilter]);

  const handleStatusChange = async (sosId, newStatus) => {
    try {
      await api.updateSOSStatus(sosId, newStatus);
      setSuccessMsg(`SOS #${sosId} status updated to '${newStatus}'.`);
      loadSOS();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSimulateSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await api.createSOS(formData);
      setSuccessMsg(`Emergency SOS #${res.id} submitted! ML Priority Score calculated: ${res.priority_score}/100.`);
      setShowSimulateModal(false);
      loadSOS();
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err) {
      setError(err.message);
    }
  };

  const getPriorityBadge = (score) => {
    if (score >= 85) return <span className="badge badge-critical">CRITICAL ({score})</span>;
    if (score >= 70) return <span className="badge badge-medium">HIGH ({score})</span>;
    return <span className="badge badge-low">MODERATE ({score})</span>;
  };

  return (
    <div>
      {/* Alert Notifications */}
      {successMsg && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: 'var(--accent-emerald-subtle)',
          border: '1px solid hsla(150, 84%, 42%, 0.3)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--accent-emerald)',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <CheckCircle size={18} />
          <span>{successMsg}</span>
        </div>
      )}

      {error && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: 'var(--accent-rose-subtle)',
          border: '1px solid hsla(350, 89%, 60%, 0.3)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--accent-rose)',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Action Header */}
      <div className="card" style={{ marginBottom: '20px', padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <select
              className="form-select"
              style={{ width: '180px' }}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="active">Active (Pending)</option>
              <option value="triaged">Triaged</option>
              <option value="camp_assigned">Camp Assigned</option>
              <option value="resolved">Resolved</option>
            </select>

            <select
              className="form-select"
              style={{ width: '180px' }}
              value={districtFilter}
              onChange={(e) => setDistrictFilter(e.target.value)}
            >
              <option value="">All Districts</option>
              <option value="Colombo">Colombo (Kelani)</option>
              <option value="Gampaha">Gampaha</option>
              <option value="Nuwara Eliya">Nuwara Eliya (Landslide)</option>
            </select>
          </div>

          <button
            className="btn btn-danger"
            onClick={() => setShowSimulateModal(true)}
          >
            <ShieldAlert size={16} />
            <span>Simulate Emergency SOS Alert</span>
          </button>
        </div>
      </div>

      {/* SOS List */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Active Emergency Incident Alerts & Triage</h2>
            <p className="card-subtitle">Showing {sosList.length} incident tickets sorted by Model 4 Priority Score</p>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
              Loading emergency alerts...
            </div>
          ) : sosList.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
              No emergency SOS records found.
            </div>
          ) : (
            sosList.map((sos) => (
              <div
                key={sos.id}
                style={{
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '18px 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '1.05rem', fontWeight: '800', color: 'var(--text-primary)' }}>
                      SOS #{sos.id}
                    </span>
                    {getPriorityBadge(sos.priority_score)}
                    <span className={`badge badge-${sos.status}`}>
                      {sos.status.replace('_', ' ')}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {sos.status === 'active' && (
                      <button
                        className="btn btn-success btn-sm"
                        onClick={() => handleStatusChange(sos.id, 'triaged')}
                      >
                        <CheckCircle size={13} />
                        <span>Mark Triaged</span>
                      </button>
                    )}
                    {sos.status === 'triaged' && (
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => handleStatusChange(sos.id, 'camp_assigned')}
                      >
                        <CheckCircle size={13} />
                        <span>Assign Camp</span>
                      </button>
                    )}
                    {sos.status !== 'resolved' && (
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleStatusChange(sos.id, 'resolved')}
                      >
                        <span>Resolve Ticket</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Details Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', fontSize: '0.84rem' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>LOCATION & GPS</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontWeight: '600', marginTop: '2px' }}>
                      <MapPin size={14} style={{ color: 'var(--accent-rose)' }} />
                      <span>{sos.gn_division || sos.ds_division}, {sos.district}</span>
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                      ({sos.latitude.toFixed(4)}, {sos.longitude.toFixed(4)})
                    </span>
                  </div>

                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>CASUALTIES / DEMOGRAPHICS</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontWeight: '600', marginTop: '2px' }}>
                      <Users size={14} style={{ color: 'var(--accent-blue)' }} />
                      <span>{sos.affected_people} People ({sos.affected_families} Families)</span>
                    </div>
                    <div style={{ display: 'flex', gap: '4px', marginTop: '4px' }}>
                      {sos.has_elderly && <span className="badge badge-medium" style={{ fontSize: '0.65rem' }}>Elderly</span>}
                      {sos.has_children && <span className="badge badge-medium" style={{ fontSize: '0.65rem' }}>Children</span>}
                      {sos.has_disabled && <span className="badge badge-critical" style={{ fontSize: '0.65rem' }}>Disabled</span>}
                    </div>
                  </div>

                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>CONTACT / REPORTER</span>
                    <span style={{ fontWeight: '600', display: 'block', marginTop: '2px' }}>{sos.user_name || 'Public Victim'}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{sos.user_phone || 'Direct Telemetry'}</span>
                  </div>

                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>TIMESTAMP</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginTop: '2px', color: 'var(--text-secondary)' }}>
                      <Clock size={14} />
                      <span>{new Date(sos.created_at).toLocaleTimeString()} · {new Date(sos.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                {/* Medical Needs Summary */}
                {sos.medical_needs_summary && (
                  <div style={{
                    padding: '10px 14px',
                    backgroundColor: 'var(--bg-card)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.82rem'
                  }}>
                    <strong style={{ color: 'var(--accent-amber)' }}>Reported Medical Supplies: </strong>
                    <span style={{ color: 'var(--text-secondary)' }}>{sos.medical_needs_summary}</span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Simulate SOS Modal */}
      {showSimulateModal && (
        <div className="modal-overlay" onClick={() => setShowSimulateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title">Simulate Real-Time Emergency SOS</h3>
                <p className="card-subtitle">Generates live telemetry and triggers Model 4 priority scoring</p>
              </div>
              <button className="modal-close-btn" onClick={() => setShowSimulateModal(false)}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSimulateSubmit}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Latitude</label>
                  <input
                    type="number"
                    step="0.000001"
                    className="form-input"
                    value={formData.latitude}
                    onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Longitude</label>
                  <input
                    type="number"
                    step="0.000001"
                    className="form-input"
                    value={formData.longitude}
                    onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">District</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.district}
                    onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">GN Division</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.gn_division}
                    onChange={(e) => setFormData({ ...formData, gn_division: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Urgency Level (1-5)</label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    className="form-input"
                    value={formData.urgency_level}
                    onChange={(e) => setFormData({ ...formData, urgency_level: parseInt(e.target.value) })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Affected People</label>
                  <input
                    type="number"
                    min="1"
                    className="form-input"
                    value={formData.affected_people}
                    onChange={(e) => setFormData({ ...formData, affected_people: parseInt(e.target.value) })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Families</label>
                  <input
                    type="number"
                    min="1"
                    className="form-input"
                    value={formData.affected_families}
                    onChange={(e) => setFormData({ ...formData, affected_families: parseInt(e.target.value) })}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Vulnerable Demographics</label>
                <div style={{ display: 'flex', gap: '16px', marginTop: '4px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
                    <input
                      type="checkbox"
                      checked={formData.has_elderly}
                      onChange={(e) => setFormData({ ...formData, has_elderly: e.target.checked })}
                    />
                    <span>Elderly Present</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
                    <input
                      type="checkbox"
                      checked={formData.has_children}
                      onChange={(e) => setFormData({ ...formData, has_children: e.target.checked })}
                    />
                    <span>Children / Infants</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
                    <input
                      type="checkbox"
                      checked={formData.has_disabled}
                      onChange={(e) => setFormData({ ...formData, has_disabled: e.target.checked })}
                    />
                    <span>Disabled / Injured</span>
                  </label>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Medical Needs Description</label>
                <textarea
                  className="form-textarea"
                  rows="2"
                  value={formData.medical_needs_summary}
                  onChange={(e) => setFormData({ ...formData, medical_needs_summary: e.target.value })}
                  placeholder="e.g. Saline, Insulin, Antibiotics..."
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowSimulateModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-danger">
                  Trigger Emergency SOS
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
