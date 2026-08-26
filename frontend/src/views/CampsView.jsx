import React, { useState, useEffect } from 'react';
import { 
  Tent, 
  MapPin, 
  CheckCircle2, 
  Clock, 
  PlusCircle, 
  Users, 
  ShieldCheck, 
  AlertCircle,
  Building,
  Activity,
  X
} from 'lucide-react';
import { api } from '../api';

export function CampsView({ currentUser }) {
  const [camps, setCamps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Form for new proposed camp
  const [formData, setFormData] = useState({
    name: 'Kaduwela Community Medical Post',
    latitude: 6.935000,
    longitude: 79.975000,
    district: 'Colombo',
    ds_division: 'Kaduwela',
    gn_division: 'Wekewatta',
    estimated_capacity: 200,
  });

  const loadCamps = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getCamps({ status_filter: statusFilter });
      setCamps(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCamps();
  }, [statusFilter]);

  const handleApproveCamp = async (campId) => {
    try {
      const updated = await api.approveCamp(campId);
      setSuccessMsg(`Camp '${updated.name}' officially approved by ${updated.approved_by || 'Authority'}!`);
      loadCamps();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await api.createCamp(formData);
      setSuccessMsg(`Medical Camp '${res.name}' proposed. Model 3 suitability score: ${res.suitability_score}/100.`);
      setShowCreateModal(false);
      loadCamps();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err.message);
    }
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
          <CheckCircle2 size={18} />
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
          <AlertCircle size={18} />
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
              <option value="">All Camp Statuses</option>
              <option value="proposed">Proposed (Pending)</option>
              <option value="approved">Approved</option>
              <option value="operational">Operational</option>
            </select>
          </div>

          <button
            className="btn btn-primary"
            onClick={() => setShowCreateModal(true)}
          >
            <PlusCircle size={16} />
            <span>Propose New Medical Camp</span>
          </button>
        </div>
      </div>

      {/* Camps Grid */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Temporary Relief Medical Camps & Field Posts</h2>
            <p className="card-subtitle">Locations evaluated with Model 3 (Camp Suitability Scorer)</p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '18px' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)', gridColumn: '1 / -1' }}>
              Loading medical camps...
            </div>
          ) : camps.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)', gridColumn: '1 / -1' }}>
              No medical camps found.
            </div>
          ) : (
            camps.map((camp) => (
              <div
                key={camp.id}
                style={{
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '14px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <span style={{ fontSize: '1.05rem', fontWeight: '800', color: 'var(--text-primary)' }}>
                      {camp.name}
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      <MapPin size={13} style={{ color: 'var(--accent-blue)' }} />
                      <span>{camp.gn_division || camp.ds_division}, {camp.district}</span>
                    </div>
                  </div>
                  <span className={`badge badge-${camp.status}`}>
                    {camp.status}
                  </span>
                </div>

                {/* Score & Capacity Stats */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', backgroundColor: 'var(--bg-card)', padding: '12px', borderRadius: 'var(--radius-md)' }}>
                  <div>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>ML SUITABILITY</span>
                    <div style={{ fontSize: '1.25rem', fontWeight: '800', color: 'var(--accent-emerald)', marginTop: '2px' }}>
                      {camp.suitability_score} / 100
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>CAPACITY</span>
                    <div style={{ fontSize: '1.25rem', fontWeight: '800', color: 'var(--text-primary)', marginTop: '2px' }}>
                      {camp.current_occupancy} / {camp.estimated_capacity}
                    </div>
                  </div>
                </div>

                {/* Approver Info & Actions */}
                <div style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {camp.status === 'approved' || camp.status === 'operational' ? (
                      <span style={{ color: 'var(--accent-emerald)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <CheckCircle2 size={12} />
                        <span>Approved by {camp.approved_by || 'Authority'}</span>
                      </span>
                    ) : (
                      <span>Pending Authority Verification</span>
                    )}
                  </div>

                  {camp.status === 'proposed' && (
                    <button
                      className="btn btn-success btn-sm"
                      onClick={() => handleApproveCamp(camp.id)}
                    >
                      <ShieldCheck size={14} />
                      <span>Approve Camp</span>
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Propose Camp Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title">Propose Temporary Medical Camp</h3>
                <p className="card-subtitle">Model 3 evaluates road access, hazard distance, and SOS density</p>
              </div>
              <button className="modal-close-btn" onClick={() => setShowCreateModal(false)}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit}>
              <div className="form-group">
                <label className="form-label">Camp Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

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

              <div className="form-group">
                <label className="form-label">Target Patient Capacity</label>
                <input
                  type="number"
                  min="10"
                  className="form-input"
                  value={formData.estimated_capacity}
                  onChange={(e) => setFormData({ ...formData, estimated_capacity: parseInt(e.target.value) })}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Calculate Suitability & Propose
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
