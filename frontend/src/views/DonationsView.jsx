import React, { useState, useEffect } from 'react';
import { 
  HeartHandshake, 
  Package, 
  CheckCircle2, 
  Clock, 
  PlusCircle, 
  Search, 
  Filter, 
  ShieldCheck,
  AlertCircle,
  Truck,
  X
} from 'lucide-react';
import { api } from '../api';

export function DonationsView({ currentUser }) {
  const [needs, setNeeds] = useState([]);
  const [pledges, setPledges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeSubTab, setActiveSubTab] = useState('needs'); // 'needs' or 'pledges'
  const [categoryFilter, setCategoryFilter] = useState('');
  
  // Pledge Modal
  const [selectedItem, setSelectedItem] = useState(null);
  const [pledgeQty, setPledgeQty] = useState(10);
  const [showPledgeModal, setShowPledgeModal] = useState(false);
  
  // Add item requirement modal
  const [showAddItemModal, setShowAddItemModal] = useState(false);
  const [itemFormData, setItemFormData] = useState({
    sos_request_id: 1,
    category: 'Medicine',
    item_name: 'Amoxicillin 500mg Capsules',
    quantity_required: 50,
    unit: 'boxes',
  });

  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
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
    loadData();
  }, [categoryFilter]);

  const handlePledgeSubmit = async (e) => {
    e.preventDefault();
    if (!selectedItem) return;
    try {
      const res = await api.pledgeDonation({
        donation_item_id: selectedItem.id,
        quantity_pledged: pledgeQty,
      });
      setSuccessMsg(`Pledge confirmed! Tracking Code: ${res.tracking_code} (${res.quantity_pledged} ${res.unit} of ${res.item_name}).`);
      setShowPledgeModal(false);
      loadData();
      setTimeout(() => setSuccessMsg(null), 6000);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleAddItemSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.createDonationItem(itemFormData);
      setSuccessMsg(`New supply requirement added for SOS #${itemFormData.sos_request_id}.`);
      setShowAddItemModal(false);
      loadData();
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

      {/* Navigation Sub-Tabs & Action Bar */}
      <div className="card" style={{ marginBottom: '20px', padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ display: 'flex', backgroundColor: 'var(--bg-secondary)', padding: '3px', borderRadius: 'var(--radius-md)' }}>
              <button
                className={`btn btn-sm ${activeSubTab === 'needs' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setActiveSubTab('needs')}
                style={{ border: 'none' }}
              >
                <span>Live Priority Supply Demands ({needs.length})</span>
              </button>
              <button
                className={`btn btn-sm ${activeSubTab === 'pledges' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setActiveSubTab('pledges')}
                style={{ border: 'none' }}
              >
                <span>Donor Pledges Audit ({pledges.length})</span>
              </button>
            </div>

            {activeSubTab === 'needs' && (
              <select
                className="form-select"
                style={{ width: '160px' }}
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <option value="">All Categories</option>
                <option value="Medicine">Medicine</option>
                <option value="Consumables">Consumables</option>
                <option value="Equipment">Equipment</option>
                <option value="Water">Clean Water</option>
              </select>
            )}
          </div>

          <button
            className="btn btn-primary"
            onClick={() => setShowAddItemModal(true)}
          >
            <PlusCircle size={16} />
            <span>Add Item Requirement</span>
          </button>
        </div>
      </div>

      {/* Main Table Views */}
      {activeSubTab === 'needs' ? (
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Priority-Ranked Unmet Medical Supply Needs</h2>
              <p className="card-subtitle">Automatically sorted by parent SOS Model 4 Emergency Priority Score</p>
            </div>
          </div>

          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Req ID</th>
                  <th>Parent SOS</th>
                  <th>Category</th>
                  <th>Item Name</th>
                  <th>Progress / Fulfillment</th>
                  <th>Remaining</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="8" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                      Loading supply requirements...
                    </td>
                  </tr>
                ) : needs.length === 0 ? (
                  <tr>
                    <td colSpan="8" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                      All current medical supply requirements are fully fulfilled.
                    </td>
                  </tr>
                ) : (
                  needs.map((item) => {
                    const pct = item.quantity_required > 0
                      ? Math.min(100, Math.round((item.quantity_fulfilled / item.quantity_required) * 100))
                      : 0;
                    return (
                      <tr key={item.id}>
                        <td style={{ fontWeight: '700' }}>#{item.id}</td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span style={{ fontWeight: '700', color: 'var(--text-primary)' }}>SOS #{item.sos_request_id}</span>
                            <span className="badge badge-critical" style={{ fontSize: '0.68rem' }}>
                              P: {item.priority_score}
                            </span>
                          </div>
                        </td>
                        <td>
                          <span className="badge badge-medium">{item.category}</span>
                        </td>
                        <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                          {item.item_name}
                        </td>
                        <td style={{ width: '220px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
                            <span>{item.quantity_fulfilled} / {item.quantity_required} {item.unit}</span>
                            <span>{pct}%</span>
                          </div>
                          <div className="progress-bar-bg">
                            <div
                              className="progress-bar-fill"
                              style={{
                                width: `${pct}%`,
                                backgroundColor: pct >= 100 ? 'var(--accent-emerald)' : pct > 0 ? 'var(--accent-amber)' : 'var(--accent-rose)'
                              }}
                            />
                          </div>
                        </td>
                        <td style={{ fontWeight: '700', color: item.remaining_needed > 0 ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>
                          {item.remaining_needed} {item.unit}
                        </td>
                        <td>
                          <span className={`badge badge-${item.status}`}>{item.status.replace('_', ' ')}</span>
                        </td>
                        <td>
                          {item.status !== 'fulfilled' ? (
                            <button
                              className="btn btn-success btn-sm"
                              onClick={() => {
                                setSelectedItem(item);
                                setPledgeQty(Math.min(20, item.remaining_needed));
                                setShowPledgeModal(true);
                              }}
                            >
                              <HeartHandshake size={14} />
                              <span>Pledge</span>
                            </button>
                          ) : (
                            <span style={{ fontSize: '0.75rem', color: 'var(--accent-emerald)', fontWeight: '700', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                              <CheckCircle2 size={12} />
                              <span>Fulfilled</span>
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Pledges Audit Log */
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">All Donor Pledges & Verification Tracking</h2>
              <p className="card-subtitle">Showing {pledges.length} confirmed pledges</p>
            </div>
          </div>

          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Pledge ID</th>
                  <th>Tracking Code</th>
                  <th>Donor Organization</th>
                  <th>Relief Item</th>
                  <th>Quantity Pledged</th>
                  <th>Delivery Status</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {pledges.length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                      No donor pledges recorded yet.
                    </td>
                  </tr>
                ) : (
                  pledges.map((p) => (
                    <tr key={p.id}>
                      <td style={{ fontWeight: '700' }}>#{p.id}</td>
                      <td>
                        <code style={{ color: 'var(--accent-blue)', fontWeight: '700', fontSize: '0.8rem' }}>
                          {p.tracking_code}
                        </code>
                      </td>
                      <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{p.donor_name}</td>
                      <td>{p.item_name} ({p.category})</td>
                      <td style={{ fontWeight: '700' }}>{p.quantity_pledged} {p.unit}</td>
                      <td>
                        <span className={`badge badge-${p.delivery_status}`}>
                          {p.delivery_status}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.78rem' }}>
                        {new Date(p.pledged_at).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
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
                <p className="card-subtitle">Item: {selectedItem.item_name} (SOS #{selectedItem.sos_request_id})</p>
              </div>
              <button className="modal-close-btn" onClick={() => setShowPledgeModal(false)}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handlePledgeSubmit}>
              <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '14px', borderRadius: 'var(--radius-md)', marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Target Quantity Required:</span>
                  <strong>{selectedItem.quantity_required} {selectedItem.unit}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginTop: '6px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Remaining Unmet:</span>
                  <strong style={{ color: 'var(--accent-rose)' }}>{selectedItem.remaining_needed} {selectedItem.unit}</strong>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Units to Pledge</label>
                <input
                  type="number"
                  min="1"
                  max={selectedItem.remaining_needed * 2}
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
                  Confirm Supply Pledge
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Item Requirement Modal */}
      {showAddItemModal && (
        <div className="modal-overlay" onClick={() => setShowAddItemModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title">Add Itemized Medical Requirement</h3>
                <p className="card-subtitle">Attach a relief need to an active SOS request</p>
              </div>
              <button className="modal-close-btn" onClick={() => setShowAddItemModal(false)}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleAddItemSubmit}>
              <div className="form-group">
                <label className="form-label">Parent SOS Request ID</label>
                <input
                  type="number"
                  min="1"
                  className="form-input"
                  value={itemFormData.sos_request_id}
                  onChange={(e) => setItemFormData({ ...itemFormData, sos_request_id: parseInt(e.target.value) })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Category</label>
                <select
                  className="form-select"
                  value={itemFormData.category}
                  onChange={(e) => setItemFormData({ ...itemFormData, category: e.target.value })}
                >
                  <option value="Medicine">Medicine (Insulin, Antibiotics, IV Fluids)</option>
                  <option value="Consumables">Consumables (Bandages, Gauze, Syringes)</option>
                  <option value="Equipment">Equipment (Stretchers, Splints, Nebulizers)</option>
                  <option value="Water">Clean Water & Hydration</option>
                  <option value="Nutrition">Emergency Nutrition</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Item Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={itemFormData.item_name}
                  onChange={(e) => setItemFormData({ ...itemFormData, item_name: e.target.value })}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Quantity</label>
                  <input
                    type="number"
                    min="1"
                    className="form-input"
                    value={itemFormData.quantity_required}
                    onChange={(e) => setItemFormData({ ...itemFormData, quantity_required: parseInt(e.target.value) })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Unit</label>
                  <input
                    type="text"
                    className="form-input"
                    value={itemFormData.unit}
                    onChange={(e) => setItemFormData({ ...itemFormData, unit: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowAddItemModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Publish Requirement
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
