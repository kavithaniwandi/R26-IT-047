import React, { useState, useEffect } from 'react';
import { 
  HeartHandshake, 
  Package, 
  CheckCircle2, 
  Search, 
  Filter, 
  ShieldCheck, 
  Clock, 
  Truck, 
  MapPin, 
  Award,
  Sparkles,
  AlertCircle,
  X
} from 'lucide-react';
import { api } from '../api';

export function DonorPortalView({ currentUser, onAddToast }) {
  const [needs, setNeeds] = useState([]);
  const [pledges, setPledges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [activeTab, setActiveTab] = useState('feed'); // 'feed' | 'my_pledges' | 'impact'
  
  const [selectedItem, setSelectedItem] = useState(null);
  const [pledgeQty, setPledgeQty] = useState(10);
  const [showPledgeModal, setShowPledgeModal] = useState(false);
  const [successMsg, setSuccessMsg] = useState(null);
  const [error, setError] = useState(null);

  const loadDonorData = async () => {
    setLoading(true);
    try {
      const needsData = await api.getDonationNeeds({ category_filter: categoryFilter });
      setNeeds(needsData);
      const pledgesData = await api.getAllPledges();
      setPledges(pledgesData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDonorData();
  }, [categoryFilter]);

  const handlePledgeSubmit = async (e) => {
    e.preventDefault();
    if (!selectedItem) return;
    try {
      const res = await api.pledgeDonation({
        donation_item_id: selectedItem.id,
        quantity_pledged: pledgeQty,
      });
      const msg = `Pledge confirmed! Tracking Code: ${res.tracking_code} (${res.quantity_pledged} ${res.unit} of ${res.item_name}).`;
      setSuccessMsg(msg);
      if (onAddToast) {
        onAddToast(msg, 'success', 'Pledge Recorded');
      }
      setShowPledgeModal(false);
      loadDonorData();
      setActiveTab('my_pledges');
      setTimeout(() => setSuccessMsg(null), 8000);
    } catch (err) {
      setError(err.message);
      if (onAddToast) {
        onAddToast(err.message, 'error', 'Pledge Failed');
      }
    }
  };

  const totalItemsPledged = pledges.reduce((acc, p) => acc + p.quantity_pledged, 0);

  return (
    <div>
      {/* Donor Banner */}
      <div style={{
        background: 'linear-gradient(135deg, hsla(150, 84%, 42%, 0.15), hsla(220, 20%, 14%, 1))',
        border: '1px solid hsla(150, 84%, 42%, 0.35)',
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
            backgroundColor: 'var(--accent-emerald)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            boxShadow: '0 0 24px hsla(150, 84%, 42%, 0.5)'
          }}>
            <HeartHandshake size={30} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.45rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
              Relief Donor & Priority Smart Matching Marketplace
            </h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Directly match and pledge verified medical supplies to high-priority disaster clusters with atomic tracking codes.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <div style={{
            padding: '8px 16px',
            backgroundColor: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            textAlign: 'right'
          }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase' }}>YOUR DONOR PLEDGES</span>
            <strong style={{ fontSize: '1.15rem', color: 'var(--accent-emerald)' }}>{pledges.length} Shipments ({totalItemsPledged} Units)</strong>
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' }}>
        <button
          className={`btn ${activeTab === 'feed' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('feed')}
        >
          <Package size={16} />
          <span>Priority Medical Demands ({needs.length})</span>
        </button>
        <button
          className={`btn ${activeTab === 'my_pledges' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('my_pledges')}
        >
          <Truck size={16} />
          <span>My Confirmed Pledges ({pledges.length})</span>
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

      {/* Tab 1: Priority Demands Feed */}
      {activeTab === 'feed' && (
        <div>
          {/* Filter Bar */}
          <div className="card" style={{ marginBottom: '20px', padding: '14px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Filter size={16} style={{ color: 'var(--text-muted)' }} />
              <select
                className="form-select"
                style={{ width: '220px' }}
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <option value="">All Supply Categories</option>
                <option value="Medicine">Medicine & Prescription Drugs</option>
                <option value="Consumables">Medical Consumables (Bandages, Gauze)</option>
                <option value="Equipment">Emergency Equipment & Stretchers</option>
                <option value="Water">Clean Drinking Water</option>
                <option value="Nutrition">Therapeutic Emergency Nutrition</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '18px' }}>
            {needs.map((item) => {
              const pct = item.quantity_required > 0
                ? Math.min(100, Math.round((item.quantity_fulfilled / item.quantity_required) * 100))
                : 0;
              return (
                <div
                  key={item.id}
                  style={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <span className="badge badge-medium" style={{ marginBottom: '6px' }}>{item.category}</span>
                      <h3 style={{ fontSize: '1.05rem', fontWeight: '800', color: 'var(--text-primary)' }}>{item.item_name}</h3>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                        <MapPin size={12} style={{ color: 'var(--accent-rose)' }} />
                        <span>Incident Location: {item.district || 'Kelani Flood Zone'}</span>
                      </div>
                    </div>
                    <span className="badge badge-critical">
                      Priority: {item.priority_score}
                    </span>
                  </div>

                  {/* Progress Bar */}
                  <div style={{ backgroundColor: 'var(--bg-card)', padding: '12px', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '6px' }}>
                      <span>Fulfilled: <strong>{item.quantity_fulfilled} / {item.quantity_required} {item.unit}</strong></span>
                      <strong style={{ color: 'var(--accent-emerald)' }}>{pct}%</strong>
                    </div>
                    <div className="progress-bar-bg">
                      <div
                        className="progress-bar-fill"
                        style={{
                          width: `${pct}%`,
                          backgroundColor: pct >= 100 ? 'var(--accent-emerald)' : 'var(--accent-amber)'
                        }}
                      />
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--accent-rose)', marginTop: '6px', fontWeight: '700' }}>
                      Remaining Unmet Need: {item.remaining_needed} {item.unit}
                    </div>
                  </div>

                  <div style={{ marginTop: 'auto', paddingTop: '8px' }}>
                    <button
                      className="btn btn-success"
                      style={{ width: '100%', padding: '10px' }}
                      onClick={() => {
                        setSelectedItem(item);
                        setPledgeQty(Math.min(25, item.remaining_needed));
                        setShowPledgeModal(true);
                      }}
                    >
                      <HeartHandshake size={16} />
                      <span>Pledge Supply Donation</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 2: My Pledges & Verification Codes */}
      {activeTab === 'my_pledges' && (
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">My Supply Pledges & Verification Drop-Off Codes</h2>
              <p className="card-subtitle">Show this tracking code at approved medical camps during physical hand-off</p>
            </div>
          </div>

          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Pledge ID</th>
                  <th>Verification Tracking Code</th>
                  <th>Relief Item</th>
                  <th>Category</th>
                  <th>Quantity Pledged</th>
                  <th>Delivery Status</th>
                  <th>Date Pledged</th>
                </tr>
              </thead>
              <tbody>
                {pledges.map((p) => (
                  <tr key={p.id}>
                    <td style={{ fontWeight: '700' }}>#{p.id}</td>
                    <td>
                      <code style={{
                        padding: '4px 8px',
                        backgroundColor: 'var(--accent-blue-subtle)',
                        border: '1px solid hsla(217, 91%, 60%, 0.3)',
                        borderRadius: 'var(--radius-sm)',
                        color: 'var(--accent-blue)',
                        fontWeight: '800',
                        fontSize: '0.85rem'
                      }}>
                        {p.tracking_code}
                      </code>
                    </td>
                    <td style={{ fontWeight: '700', color: 'var(--text-primary)' }}>{p.item_name}</td>
                    <td><span className="badge badge-medium">{p.category}</span></td>
                    <td style={{ fontWeight: '800' }}>{p.quantity_pledged} {p.unit}</td>
                    <td><span className={`badge badge-${p.delivery_status}`}>{p.delivery_status}</span></td>
                    <td style={{ fontSize: '0.78rem' }}>{new Date(p.pledged_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pledge Modal */}
      {showPledgeModal && selectedItem && (
        <div className="modal-overlay" onClick={() => setShowPledgeModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title">Pledge Medical & Relief Supplies</h3>
                <p className="card-subtitle">{selectedItem.item_name} ({selectedItem.category})</p>
              </div>
              <button className="modal-close-btn" onClick={() => setShowPledgeModal(false)}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handlePledgeSubmit}>
              <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '14px', borderRadius: 'var(--radius-md)', marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Remaining Needed:</span>
                  <strong style={{ color: 'var(--accent-rose)' }}>{selectedItem.remaining_needed} {selectedItem.unit}</strong>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Units You Wish to Pledge</label>
                <input
                  type="number"
                  min="1"
                  className="form-input"
                  value={pledgeQty}
                  onChange={(e) => setPledgeQty(parseInt(e.target.value) || 1)}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowPledgeModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-success">
                  Confirm Pledge & Generate Tracking Code
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
