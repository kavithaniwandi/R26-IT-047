import React, { useState, useEffect } from 'react';
import { 
  User, 
  HeartHandshake, 
  Phone, 
  Mail, 
  Award, 
  RefreshCw,
  AlertCircle,
  MapPin
} from 'lucide-react';
import { api } from '../api';

export default function DonorDetailsView({ onAddToast }) {
  const [donors, setDonors] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadDonors = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getDonors();
      setDonors(data || []);
      if (data && data.length > 0 && !selectedId) {
        setSelectedId(data[0].id);
      }
    } catch (err) {
      setError(err.message || 'Failed to load donors.');
    } finally {
      setLoading(false);
    }
  };

  const loadDetail = async (id) => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getDonorDetail(id);
      setDetail(data);
    } catch (err) {
      setError(err.message || 'Failed to load donor details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDonors();
  }, []);

  useEffect(() => {
    if (selectedId) loadDetail(selectedId);
  }, [selectedId]);

  return (
    <div>
      {/* Donor Registry Banner */}
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
            <User size={30} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.45rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--text-primary)', margin: 0 }}>
              Verified Donor Registry & Contribution Ledger
            </h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '4px 0 0' }}>
              Inspect donor profiles, cumulative contribution totals, and itemized handover history.
            </p>
          </div>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadDonors} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

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

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px', alignItems: 'start' }}>
        {/* Donor Selector List */}
        <div className="card" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
          <div className="card-header">
            <h2 className="card-title">Donor Directory</h2>
            <span className="badge badge-medium">{donors.length}</span>
          </div>
          {donors.length === 0 && !loading ? (
            <div style={{ padding: '28px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No verified donors on record yet.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {donors.map((d) => (
                <button
                  key={d.id}
                  onClick={() => setSelectedId(d.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '12px',
                    borderRadius: 'var(--radius-md)',
                    border: selectedId === d.id ? '1px solid var(--accent-emerald)' : '1px solid var(--border-subtle)',
                    background: selectedId === d.id ? 'var(--accent-emerald-subtle)' : 'var(--bg-secondary)',
                    cursor: 'pointer',
                    textAlign: 'left',
                    width: '100%'
                  }}
                >
                  <div style={{
                    width: '34px',
                    height: '34px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--accent-emerald-subtle)',
                    color: 'var(--accent-emerald)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: '800',
                    flexShrink: 0
                  }}>
                    {d.name.charAt(0).toUpperCase()}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: '700', color: 'var(--text-primary)', fontSize: '0.9rem' }}>{d.name}</div>
                    <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                      {d.requests_supported} shipment{d.requests_supported > 1 ? 's' : ''} · {Math.round(d.total_donated)} units
                    </div>
                  </div>
                  <Award size={14} style={{ color: 'var(--accent-emerald)', flexShrink: 0 }} />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Donor Detail Panel */}
        <div className="card">
          {loading ? (
            <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
              Loading donor ledger...
            </div>
          ) : detail ? (
            <>
              <div className="card-header" style={{ flexWrap: 'wrap', gap: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <div style={{
                    width: '54px',
                    height: '54px',
                    borderRadius: 'var(--radius-lg)',
                    backgroundColor: 'var(--accent-emerald-subtle)',
                    color: 'var(--accent-emerald)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: '800',
                    fontSize: '1.3rem'
                  }}>
                    {detail.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <span className="badge badge-success">Verified Donor</span>
                    <h2 className="card-title" style={{ marginTop: '4px' }}>{detail.name}</h2>
                  </div>
                </div>
                <span className="badge badge-medium font-mono">
                  #{detail.id.slice(-8).toUpperCase()}
                </span>
              </div>

              {/* Metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px', marginBottom: '20px' }}>
                <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Contributed</div>
                  <strong style={{ fontSize: '1.3rem', color: 'var(--accent-emerald)' }}>{detail.total_donated} <span style={{ fontSize: '0.85rem' }}>units</span></strong>
                </div>
                <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Requests Supported</div>
                  <strong style={{ fontSize: '1.3rem', color: 'var(--text-primary)' }}>{detail.requests_supported}</strong>
                </div>
                <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Fulfilled Handovers</div>
                  <strong style={{ fontSize: '1.3rem', color: 'var(--accent-blue)' }}>{detail.fulfilled_count}</strong>
                </div>
              </div>

              {/* Contact Info */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '20px' }}>
                {detail.email && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                    <Mail size={14} style={{ color: 'var(--accent-blue)' }} /> {detail.email}
                  </div>
                )}
                {detail.phone && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                    <Phone size={14} style={{ color: 'var(--accent-blue)' }} /> {detail.phone}
                  </div>
                )}
              </div>

              {/* Donation History */}
              <h3 className="card-title">Donation & Handover History</h3>
              <div className="table-container">
                <table className="custom-table">
                  <thead>
                    <tr>
                      <th>Relief Item</th>
                      <th>Quantity</th>
                      <th>Camp Destination</th>
                      <th>Disaster</th>
                      <th>Status</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.history.length === 0 ? (
                      <tr>
                        <td colSpan="6" style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                          No donation records for this donor yet.
                        </td>
                      </tr>
                    ) : (
                      detail.history.map((h, i) => (
                        <tr key={i}>
                          <td style={{ fontWeight: '700', color: 'var(--text-primary)' }}>{h.itemName}</td>
                          <td style={{ fontWeight: '800' }}>{h.quantity}</td>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <MapPin size={12} style={{ color: 'var(--accent-rose)' }} />
                              <span>{h.reliefCamp || 'Relief Camp'}</span>
                            </div>
                          </td>
                          <td><span className="badge badge-medium">{h.disasterType || 'General'}</span></td>
                          <td>
                            <span className={`badge ${h.status === 'received' ? 'badge-success' : 'badge-medium'}`}>
                              {h.status === 'received' ? '✓ Received' : h.status}
                            </span>
                          </td>
                          <td style={{ fontSize: '0.78rem' }}>
                            {h.acceptedAt ? new Date(h.acceptedAt).toLocaleDateString() : '—'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--text-muted)' }}>
              <HeartHandshake size={40} style={{ marginBottom: '12px', opacity: 0.7 }} />
              <p>Select a donor from the directory to view their contribution ledger.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
