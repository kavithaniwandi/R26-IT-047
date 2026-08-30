import React, { useState, useEffect } from 'react';
import { 
  Gift, 
  Package, 
  Truck, 
  CheckCircle2, 
  AlertCircle, 
  Filter, 
  Plus, 
  MapPin, 
  X 
} from 'lucide-react';
import { api } from '../api';

export default function DisasterDonation({ currentUser, onAddToast }) {
  const [activeTab, setActiveTab] = useState('inventory'); // 'inventory' | 'campaigns' | 'shipments'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Filters
  const [categoryFilter, setCategoryFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Modal State
  const [showAppealModal, setShowAppealModal] = useState(false);
  const [appealForm, setAppealForm] = useState({
    item_name: '',
    quantity_required: 100,
    unit: 'units',
    disaster_type: 'Flood',
    severity: 'High',
    ds_area: 'Kaduwela',
    gn_division: 'Ranala',
    relief_camp: '',
  });

  const [donationItems, setDonationItems] = useState([]);

  const loadDonations = async () => {
    setLoading(true);
    setError(null);
    try {
      const requests = await api.getDisasterRequests();
      const items = (requests || []).flatMap((request) =>
        (request.items || [])
          .filter((item) => Number(item.remainingQuantity) > 0)
          .map((item) => ({
            id: `${request.id}-${item.itemId || item.itemName}`,
            request_id: request.id,
            item_name: item.itemName,
            category: request.disasterType,
            quantity_required: item.neededQuantity,
            quantity_fulfilled: item.donatedQuantity,
            remaining_needed: item.remainingQuantity,
            unit: item.unit,
            district: `${request.gnDivision}, ${request.dsArea}`,
            relief_camp: request.reliefCamp,
            priority_score: request.severity,
          }))
      );
      setDonationItems(items);
    } catch (err) {
      setError(err.message || 'Failed to load disaster donation records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDonations();
  }, [categoryFilter]);

  const handleAppealSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.createDisasterRequest({
        disasterType: appealForm.disaster_type,
        severity: appealForm.severity,
        dsArea: appealForm.ds_area,
        gnDivision: appealForm.gn_division,
        reliefCamp: appealForm.relief_camp,
        people_count: 1,
        items: [{
          itemName: appealForm.item_name,
          unit: appealForm.unit,
          neededQuantity: appealForm.quantity_required,
        }],
      });
      const msg = `Disaster supply request for ${appealForm.quantity_required} ${appealForm.unit} of '${appealForm.item_name}' published.`;
      setSuccessMsg(msg);
      if (onAddToast) onAddToast(msg, 'success', 'Request Published');
      setShowAppealModal(false);
      await loadDonations();
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err) {
      setError(err.message || 'Failed to publish the disaster supply request.');
    } finally {
      setLoading(false);
    }
  };

  const visibleItems = donationItems.filter((item) => {
    const matchesType = !categoryFilter || item.category === categoryFilter;
    const query = searchQuery.trim().toLowerCase();
    return matchesType && (!query || [item.item_name, item.district, item.relief_camp].some((value) => (value || '').toLowerCase().includes(query)));
  });
  const totalUnmet = donationItems.reduce((acc, item) => acc + (item.remaining_needed || 0), 0);

  return (
    <div>
      {/* Donation Marketplace Banner */}
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
            <Gift size={30} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.45rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--text-primary)', margin: 0 }}>
              Disaster Relief Donation & Resource Matchmaking
            </h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '4px 0 0' }}>
              Publish supply demands, coordinate donor pledges, and oversee atomic tracking logistics.
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
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase' }}>SUPPLY DEFICIT</span>
            <strong style={{ fontSize: '1.15rem', color: 'var(--accent-emerald)' }}>{totalUnmet} Units Required</strong>
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' }}>
        <button
          className={`btn ${activeTab === 'inventory' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('inventory')}
        >
          <Package size={16} />
          <span>Priority Supply Shortages ({visibleItems.length})</span>
        </button>
        <button
          className={`btn ${activeTab === 'shipments' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('shipments')}
        >
          <Truck size={16} />
          <span>Tracking & Shipments</span>
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

      {/* Tab 1: Priority Supply Shortages */}
      {activeTab === 'inventory' && (
        <div>
          {/* Action Filter Bar */}
          <div className="card" style={{ marginBottom: '20px', padding: '14px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Filter size={16} style={{ color: 'var(--text-muted)' }} />
                <select
                  className="form-select"
                  style={{ width: '220px' }}
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                >
                  <option value="">All Disaster Types</option>
                  <option value="Flood">Flood</option>
                  <option value="Landslide">Landslide</option>
                  <option value="Tsunami">Tsunami</option>
                  <option value="Drought">Drought</option>
                  <option value="Fire">Fire</option>
                  <option value="Other">Other</option>
                </select>
                <input
                  className="form-input"
                  placeholder="Search item, camp, or area"
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  style={{ width: '240px' }}
                />
              </div>

              <button className="btn btn-primary" onClick={() => setShowAppealModal(true)}>
                <Plus size={16} />
                <span>Publish Item Appeal</span>
              </button>
            </div>
          </div>

          {/* Supply Needs Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '18px' }}>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)', gridColumn: '1 / -1' }}>
                Loading supply shortages...
              </div>
            ) : visibleItems.length === 0 ? (
              <div style={{
                backgroundColor: 'var(--bg-secondary)',
                borderRadius: 'var(--radius-lg)',
                padding: '48px 20px',
                textAlign: 'center',
                border: '1px dashed var(--border-subtle)',
                gridColumn: '1 / -1'
              }}>
                <Package size={40} style={{ color: 'var(--accent-emerald)', marginBottom: '12px', opacity: 0.8 }} />
                <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)', margin: '0 0 6px' }}>No Active Supply Demands</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '440px', margin: '0 auto 16px' }}>
                  There are currently no unmet relief item requirements in the registry.
                </p>
                <button className="btn btn-secondary btn-sm" onClick={() => setShowAppealModal(true)}>
                  <Plus size={14} />
                  <span>Create Item Demand</span>
                </button>
              </div>
            ) : (
              visibleItems.map((item) => {
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
                        <h3 style={{ fontSize: '1.05rem', fontWeight: '800', color: 'var(--text-primary)', margin: '0 0 4px' }}>{item.item_name}</h3>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                          <MapPin size={12} style={{ color: 'var(--accent-rose)' }} />
                          <span>{item.relief_camp} &bull; {item.district}</span>
                        </div>
                      </div>
                      <span className="badge badge-critical">
                        Priority: {item.priority_score || 'High'}
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
                        Remaining Unmet: {item.remaining_needed} {item.unit}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Shipments Tracking */}
      {activeTab === 'shipments' && (
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Verified Donation Shipments & Drop-Off Log</h2>
              <p className="card-subtitle">Track incoming certified medical and relief supplies</p>
            </div>
          </div>

          <div style={{
            backgroundColor: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-lg)',
            padding: '40px 20px',
            textAlign: 'center',
            border: '1px dashed var(--border-subtle)',
          }}>
            <Truck size={40} style={{ color: 'var(--accent-emerald)', marginBottom: '12px', opacity: 0.8 }} />
            <h3 style={{ fontSize: '1.05rem', color: 'var(--text-primary)', margin: '0 0 6px' }}>No Shipments in Transit</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '440px', margin: '0 auto' }}>
              All matched pledges have been fulfilled or are awaiting pickup confirmation.
            </p>
          </div>
        </div>
      )}

      {/* Appeal Modal */}
      {showAppealModal && (
        <div className="modal-overlay" onClick={() => setShowAppealModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title">Publish Disaster Supply Appeal</h3>
                <p className="card-subtitle">Broadcast critical requirements to verified donors</p>
              </div>
              <button className="modal-close-btn" onClick={() => setShowAppealModal(false)}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleAppealSubmit}>
              <div className="form-group">
                <label className="form-label">Disaster Type</label>
                <select
                  className="form-select"
                  value={appealForm.disaster_type}
                  onChange={(e) => setAppealForm({ ...appealForm, disaster_type: e.target.value })}
                >
                  <option value="Flood">Flood</option>
                  <option value="Landslide">Landslide</option>
                  <option value="Tsunami">Tsunami</option>
                  <option value="Drought">Drought</option>
                  <option value="Fire">Fire</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">DS Area</label>
                  <input required className="form-input" value={appealForm.ds_area} onChange={(e) => setAppealForm({ ...appealForm, ds_area: e.target.value })} />
                </div>
                <div className="form-group">
                  <label className="form-label">GN Division</label>
                  <input required className="form-input" value={appealForm.gn_division} onChange={(e) => setAppealForm({ ...appealForm, gn_division: e.target.value })} />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Relief Camp</label>
                <input required className="form-input" placeholder="Assigned relief camp name" value={appealForm.relief_camp} onChange={(e) => setAppealForm({ ...appealForm, relief_camp: e.target.value })} />
              </div>

              <div className="form-group">
                <label className="form-label">Severity</label>
                <select className="form-select" value={appealForm.severity} onChange={(e) => setAppealForm({ ...appealForm, severity: e.target.value })}>
                  <option value="Low">Low</option>
                  <option value="Moderate">Moderate</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Item Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Human Insulin 100 IU/ml Vials"
                  className="form-input"
                  value={appealForm.item_name}
                  onChange={(e) => setAppealForm({ ...appealForm, item_name: e.target.value })}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Quantity Needed</label>
                  <input
                    type="number"
                    min="1"
                    className="form-input"
                    value={appealForm.quantity_required}
                    onChange={(e) => setAppealForm({ ...appealForm, quantity_required: parseInt(e.target.value) || 1 })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Unit of Measurement</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. vials, bottles, packs"
                    className="form-input"
                    value={appealForm.unit}
                    onChange={(e) => setAppealForm({ ...appealForm, unit: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowAppealModal(false)}
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
