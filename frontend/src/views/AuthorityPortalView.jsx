import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Activity, 
  Tent, 
  MapPin, 
  CheckCircle2, 
  Clock, 
  PlusCircle, 
  AlertCircle,
  Play,
  HeartHandshake,
  Droplets,
  Mountain,
  Users,
  X
} from 'lucide-react';
import { api } from '../api';

export function AuthorityPortalView({ currentUser, onAddToast }) {
  const [sosList, setSosList] = useState([]);
  const [camps, setCamps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('triage'); // 'triage' | 'camps_approval' | 'ml_eval' | 'requisitions'
  const [successMsg, setSuccessMsg] = useState(null);
  const [error, setError] = useState(null);

  // New Requisition Item state
  const [showItemModal, setShowItemModal] = useState(false);
  const [selectedSOSId, setSelectedSOSId] = useState(1);
  const [itemData, setItemData] = useState({
    category: 'Medicine',
    item_name: 'IV Normal Saline 0.9% 500ml',
    quantity_required: 100,
    unit: 'bottles',
  });

  const loadAuthorityData = async () => {
    setLoading(true);
    try {
      const sosData = await api.getSOSRequests();
      setSosList(sosData);
      const campData = await api.getCamps();
      setCamps(campData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuthorityData();
  }, []);

  const handleTriageAction = async (sosId, newStatus) => {
    try {
      await api.updateSOSStatus(sosId, newStatus);
      const msg = `SOS Alert #${sosId} triage status updated to '${newStatus}'.`;
      setSuccessMsg(msg);
      if (onAddToast) {
        onAddToast(msg, 'success', 'Triage Status Updated');
      }
      loadAuthorityData();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err.message);
      if (onAddToast) {
        onAddToast(err.message, 'error', 'Triage Action Failed');
      }
    }
  };

  const handleApproveCamp = async (campId) => {
    try {
      const updated = await api.approveCamp(campId);
      const msg = `Medical Camp '${updated.name}' officially authorized and published to public map!`;
      setSuccessMsg(msg);
      if (onAddToast) {
        onAddToast(msg, 'success', 'Camp Authorized');
      }
      loadAuthorityData();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err.message);
      if (onAddToast) {
        onAddToast(err.message, 'error', 'Authorization Failed');
      }
    }
  };

  const handleCreateRequisition = async (e) => {
    e.preventDefault();
    try {
      await api.createDonationItem({
        sos_request_id: selectedSOSId,
        ...itemData,
      });
      const msg = `Medical supply requisition for '${itemData.item_name}' published to Donor Matching Queue.`;
      setSuccessMsg(msg);
      if (onAddToast) {
        onAddToast(msg, 'success', 'Requisition Created');
      }
      setShowItemModal(false);
      loadAuthorityData();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err.message);
      if (onAddToast) {
        onAddToast(err.message, 'error', 'Creation Failed');
      }
    }
  };

  const criticalSOS = sosList.filter(s => s.priority_score >= 80);
  const proposedCamps = camps.filter(c => c.status === 'proposed');

  return (
    <div>
      {/* Authority Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, hsla(217, 91%, 60%, 0.15), hsla(220, 20%, 14%, 1))',
        border: '1px solid hsla(217, 91%, 60%, 0.35)',
        borderRadius: 'var(--radius-xl)',
        padding: '24px 28px',
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '54px',
            height: '54px',
            borderRadius: 'var(--radius-lg)',
            backgroundColor: 'var(--accent-blue)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            boxShadow: '0 0 24px hsla(217, 91%, 60%, 0.5)'
          }}>
            <ShieldCheck size={30} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.45rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
              Medical Authority & Disaster Response Command
            </h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Official Ministry of Health (MOH) Portal: Emergency Triage, Camp Authorizations & ML Risk Evaluation.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <div style={{
            padding: '8px 14px',
            backgroundColor: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.85rem'
          }}>
            <span style={{ color: 'var(--text-muted)' }}>Authority Officer: </span>
            <strong style={{ color: 'var(--accent-blue)' }}>{currentUser?.full_name || 'Dr. Nihal Jayasinghe (MOH)'}</strong>
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' }}>
        <button
          className={`btn ${activeTab === 'triage' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('triage')}
        >
          <Activity size={16} />
          <span>Priority Triage Queue ({sosList.length})</span>
          {criticalSOS.length > 0 && (
            <span className="nav-badge rose">{criticalSOS.length} Critical</span>
          )}
        </button>
        <button
          className={`btn ${activeTab === 'camps_approval' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('camps_approval')}
        >
          <Tent size={16} />
          <span>Camp Approvals & Deployment</span>
          {proposedCamps.length > 0 && (
            <span className="nav-badge blue">{proposedCamps.length} Pending</span>
          )}
        </button>
      </div>

      {/* Alert Notices */}
      {successMsg && (
        <div style={{
          padding: '14px 18px',
          backgroundColor: 'var(--accent-emerald-subtle)',
          border: '1px solid hsla(150, 84%, 42%, 0.4)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--accent-emerald)',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <CheckCircle2 size={20} />
          <strong style={{ fontSize: '0.9rem' }}>{successMsg}</strong>
        </div>
      )}

      {error && (
        <div style={{
          padding: '14px 18px',
          backgroundColor: 'var(--accent-rose-subtle)',
          border: '1px solid hsla(350, 89%, 60%, 0.4)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--accent-rose)',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* View 1: Triage Queue */}
      {activeTab === 'triage' && (
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">National Disaster Emergency Triage List</h2>
              <p className="card-subtitle">Ranked by Model 4 AI Priority Score (Casualties, Demographics & Local Risk)</p>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {sosList.map((sos) => (
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
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '1.05rem', fontWeight: '800', color: 'var(--text-primary)' }}>
                      Incident #{sos.id} · {sos.gn_division || sos.ds_division}
                    </span>
                    <span className={`badge ${sos.priority_score >= 85 ? 'badge-critical' : sos.priority_score >= 70 ? 'badge-medium' : 'badge-low'}`}>
                      Priority: {sos.priority_score} / 100
                    </span>
                    <span className={`badge badge-${sos.status}`}>{sos.status}</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => {
                        setSelectedSOSId(sos.id);
                        setShowItemModal(true);
                      }}
                    >
                      <PlusCircle size={13} />
                      <span>+ Medical Requisition</span>
                    </button>
                    {sos.status === 'active' && (
                      <button
                        className="btn btn-success btn-sm"
                        onClick={() => handleTriageAction(sos.id, 'triaged')}
                      >
                        <CheckCircle2 size={13} />
                        <span>Accept & Triage</span>
                      </button>
                    )}
                    {sos.status === 'triaged' && (
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleTriageAction(sos.id, 'camp_assigned')}
                      >
                        <span>Assign Camp</span>
                      </button>
                    )}
                    {sos.status !== 'resolved' && (
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleTriageAction(sos.id, 'resolved')}
                      >
                        <span>Close Incident</span>
                      </button>
                    )}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', fontSize: '0.84rem' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.74rem' }}>COORDINATES</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                      <MapPin size={13} style={{ color: 'var(--accent-rose)' }} />
                      <span style={{ fontFamily: 'monospace' }}>({sos.latitude.toFixed(4)}, {sos.longitude.toFixed(4)})</span>
                    </div>
                  </div>

                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.74rem' }}>POPULATION IMPACT</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: '600', marginTop: '2px' }}>
                      <Users size={13} style={{ color: 'var(--accent-blue)' }} />
                      <span>{sos.affected_people} Persons ({sos.affected_families} Families)</span>
                    </div>
                  </div>

                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.74rem' }}>VULNERABILITIES</span>
                    <div style={{ display: 'flex', gap: '4px', marginTop: '2px' }}>
                      {sos.has_elderly && <span className="badge badge-medium" style={{ fontSize: '0.65rem' }}>Elderly</span>}
                      {sos.has_children && <span className="badge badge-medium" style={{ fontSize: '0.65rem' }}>Children</span>}
                      {sos.has_disabled && <span className="badge badge-critical" style={{ fontSize: '0.65rem' }}>Disabled</span>}
                      {!sos.has_elderly && !sos.has_children && !sos.has_disabled && <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>None</span>}
                    </div>
                  </div>
                </div>

                {sos.medical_needs_summary && (
                  <div style={{
                    padding: '8px 12px',
                    backgroundColor: 'var(--bg-card)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.8rem',
                    color: 'var(--text-secondary)'
                  }}>
                    <strong style={{ color: 'var(--accent-amber)' }}>Reported Medical Need: </strong>
                    <span>{sos.medical_needs_summary}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* View 2: Camp Approvals Hub */}
      {activeTab === 'camps_approval' && (
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Temporary Medical Relief Camp Authorization Queue</h2>
              <p className="card-subtitle">Proposed locations scored by Model 3 Spatial Suitability Algorithm</p>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
            {camps.map((camp) => (
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
                    <h3 style={{ fontSize: '1.05rem', fontWeight: '800', color: 'var(--text-primary)' }}>{camp.name}</h3>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      <MapPin size={12} style={{ color: 'var(--accent-blue)' }} />
                      <span>{camp.gn_division || camp.ds_division}, {camp.district}</span>
                    </div>
                  </div>
                  <span className={`badge badge-${camp.status}`}>
                    {camp.status.toUpperCase()}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', backgroundColor: 'var(--bg-card)', padding: '12px', borderRadius: 'var(--radius-md)' }}>
                  <div>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>AI SUITABILITY</span>
                    <div style={{ fontSize: '1.25rem', fontWeight: '800', color: 'var(--accent-emerald)', marginTop: '2px' }}>
                      {camp.suitability_score} / 100
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>CAPACITY</span>
                    <div style={{ fontSize: '1.25rem', fontWeight: '800', color: 'var(--text-primary)', marginTop: '2px' }}>
                      {camp.estimated_capacity} beds
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: 'auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    {camp.status === 'approved' ? `Approved by ${camp.approved_by || 'Authority'}` : 'Requires Authorization'}
                  </span>

                  {camp.status === 'proposed' && (
                    <button
                      className="btn btn-success btn-sm"
                      onClick={() => handleApproveCamp(camp.id)}
                    >
                      <ShieldCheck size={14} />
                      <span>Officially Authorize</span>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add Requisition Modal */}
      {showItemModal && (
        <div className="modal-overlay" onClick={() => setShowItemModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title">Create Medical Supply Requisition</h3>
                <p className="card-subtitle">For Emergency Incident #{selectedSOSId}</p>
              </div>
              <button className="modal-close-btn" onClick={() => setShowItemModal(false)}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateRequisition}>
              <div className="form-group">
                <label className="form-label">Supply Category</label>
                <select
                  className="form-select"
                  value={itemData.category}
                  onChange={(e) => setItemData({ ...itemData, category: e.target.value })}
                >
                  <option value="Medicine">Medicine (Insulin, Antibiotics, IV Saline)</option>
                  <option value="Consumables">Consumables (Sterile Gauze, Bandages, Syringes)</option>
                  <option value="Equipment">Equipment (Trauma Stretchers, Oxygen Cylinders)</option>
                  <option value="Water">Clean Water & Hydration</option>
                  <option value="Nutrition">Emergency Therapeutic Nutrition</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Specific Item Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={itemData.item_name}
                  onChange={(e) => setItemData({ ...itemData, item_name: e.target.value })}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Quantity Needed</label>
                  <input
                    type="number"
                    min="1"
                    className="form-input"
                    value={itemData.quantity_required}
                    onChange={(e) => setItemData({ ...itemData, quantity_required: parseInt(e.target.value) })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Unit of Measure</label>
                  <input
                    type="text"
                    className="form-input"
                    value={itemData.unit}
                    onChange={(e) => setItemData({ ...itemData, unit: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowItemModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Publish to Donor Marketplace
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
