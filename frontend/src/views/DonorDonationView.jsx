import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertCircle, CheckCircle2, ChevronDown, Clock3, Gift, History,
  MapPin, Minus, PackageCheck, Plus, RefreshCw, ShieldCheck, Sparkles, X,
} from 'lucide-react';
import { api } from '../api';

const panel = {
  background: 'var(--bg-card)',
  border: '1px solid var(--border-subtle)',
  borderRadius: 16,
  boxShadow: '0 2px 6px rgba(15, 23, 42, 0.06)',
};

const INITIAL_NOW = Date.now();

const severityColors = {
  Critical: ['#fee2e2', '#b91c1c'],
  High: ['#ffedd5', '#c2410c'],
  Moderate: ['#fef3c7', '#a16207'],
  Low: ['#dcfce7', '#15803d'],
};

const requestIsOpen = (request) => request.status !== 'fulfilled'
  && (request.items || []).some((item) => Number(item.remainingQuantity || 0) > 0);

const quantityKey = (requestId, item) => `${requestId}:${item.itemId || item.itemName}`;

const formatQuantity = (value) => Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });

const getDropOffOffice = (request) => {
  const location = `${request?.dsArea || ''} ${request?.gnDivision || ''}`.toLowerCase();

  if (location.includes('nawalapitiya') || location.includes('ambagamuwa')) {
    return 'Ambagamuwa Korale Divisional Secretariat Office';
  }
  if (location.includes('kaduwela')) {
    return 'Kaduwela Divisional Secretariat Office';
  }
  return `${request?.dsArea || 'Relevant'} Divisional Secretariat Office`;
};

function timeRemaining(expiresAt, now) {
  if (!expiresAt) return 'Legacy pledge';
  const milliseconds = new Date(expiresAt).getTime() - now;
  if (milliseconds <= 0) return 'Expired';
  const hours = Math.floor(milliseconds / 3_600_000);
  const minutes = Math.floor((milliseconds % 3_600_000) / 60_000);
  return `${hours}h ${minutes}m remaining`;
}

export function DonorDonationView({ currentUser, onAddToast }) {
  const [activeTab, setActiveTab] = useState('personalized');
  const [requests, setRequests] = useState([]);
  const [personalizedIds, setPersonalizedIds] = useState(new Set());
  const [history, setHistory] = useState([]);
  const [quantities, setQuantities] = useState({});
  const [expanded, setExpanded] = useState(new Set());
  const [confirmation, setConfirmation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [now, setNow] = useState(INITIAL_NOW);

  const loadRequests = useCallback(async (scope) => {
    const requestData = await api.getDisasterRequests({ scope });
    let open = (requestData || []).filter(requestIsOpen);
    if (scope === 'personalized') {
      open = open.slice(0, 10);
    }
    setRequests(open);
    const topScoring = open.filter((r) => (r.compatibilityScore || 0) >= 40);
    setPersonalizedIds(new Set(topScoring.map((request) => request.id)));
    setExpanded(new Set());
  }, []);

  const loadHistory = useCallback(async () => {
    const data = await api.getDonationHistory();
    setHistory(data || []);
  }, []);

  const loadActiveView = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      if (activeTab === 'personalized' || activeTab === 'all') {
        await loadRequests(activeTab);
      } else {
        await loadHistory();
      }
    } catch (err) {
      setError(err.message || 'Unable to load donation information.');
    } finally {
      setLoading(false);
    }
  }, [activeTab, loadHistory, loadRequests]);

  useEffect(() => { loadActiveView(); }, [loadActiveView]);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 60_000);
    return () => window.clearInterval(timer);
  }, []);

  const pledgedItems = useMemo(
    () => history.filter((entry) => entry.status === 'pledged' || entry.status === 'cancelled'),
    [history],
  );
  const completedItems = useMemo(
    () => history.filter((entry) => entry.status === 'received'),
    [history],
  );

  const updateQuantity = (requestId, item, nextValue) => {
    const max = Math.max(0, Math.floor(Number(item.remainingQuantity || 0)));
    const value = Math.max(0, Math.min(max, Math.floor(Number(nextValue) || 0)));
    setQuantities((current) => ({ ...current, [quantityKey(requestId, item)]: value }));
  };

  const selectedForRequest = (request) => (request.items || [])
    .map((item) => ({
      itemId: item.itemId,
      itemName: item.itemName,
      unit: item.unit,
      quantity: Number(quantities[quantityKey(request.id, item)] || 0),
    }))
    .filter((item) => item.quantity > 0);

  const openConfirmation = (request) => {
    const pledges = selectedForRequest(request);
    if (pledges.length === 0) {
      onAddToast?.('Choose at least one item quantity before pledging.', 'warning', 'Nothing Selected');
      return;
    }
    setConfirmation({ request, pledges });
  };

  const submitPledge = async () => {
    if (!confirmation) return;
    setSubmitting(true);
    setError('');
    try {
      await api.pledgeDisasterRequest(confirmation.request.id, confirmation.pledges);
      const itemCount = confirmation.pledges.length;
      const message = `Pledge confirmed for ${itemCount} item type${itemCount === 1 ? '' : 's'}. Deliver them to the ${getDropOffOffice(confirmation.request)} within 12 hours.`;
      setSuccess(message);
      onAddToast?.(message, 'success', 'Pledge Confirmed');
      setQuantities({});
      setConfirmation(null);
      setActiveTab('pledges');
    } catch (err) {
      setError(err.message || 'Unable to confirm this pledge.');
      onAddToast?.(err.message, 'error', 'Pledge Failed');
    } finally {
      setSubmitting(false);
    }
  };

  const toggleExpanded = (requestId) => setExpanded((current) => {
    const next = new Set(current);
    if (next.has(requestId)) next.delete(requestId); else next.add(requestId);
    return next;
  });

  const tabs = [
    ['personalized', 'For You', Sparkles],
    ['all', 'All Donation Requests', Gift],
    ['pledges', 'My Pledges', Clock3],
    ['completed', 'Completed Donations', History],
  ];

  const historyRows = activeTab === 'completed' ? completedItems : pledgedItems;

  return (
    <div style={{ display: 'grid', gap: 20 }}>
      <section style={{ ...panel, padding: '22px 26px', background: 'linear-gradient(120deg, #ecfdf5, var(--bg-card) 65%)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 15 }}>
          <div style={{ width: 54, height: 54, borderRadius: 15, display: 'grid', placeItems: 'center', background: '#059669', color: 'white' }}><Gift size={29} /></div>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.45rem' }}>Donor Donation Portal</h1>
            <p style={{ margin: '5px 0 0', color: 'var(--text-muted)', fontSize: '.86rem' }}>Choose requested supplies, pledge available quantities, and deliver them to the relevant Divisional Secretariat Office.</p>
          </div>
        </div>
        <div style={{ padding: '10px 13px', borderRadius: 11, background: '#fff7ed', color: '#9a3412', fontSize: '.76rem', maxWidth: 330 }}>
          <Clock3 size={15} style={{ verticalAlign: -3, marginRight: 7 }} />Pledges expire after 12 hours unless a disaster officer confirms receipt.
        </div>
      </section>

      <nav style={{ ...panel, padding: 8, display: 'flex', gap: 7, flexWrap: 'wrap' }} aria-label="Donation portal sections">
        {tabs.map(([id, label, Icon]) => (
          <button key={id} onClick={() => setActiveTab(id)} className={`btn ${activeTab === id ? 'btn-primary' : 'btn-secondary'}`} style={{ flex: '1 1 170px', justifyContent: 'center' }}>
            <Icon size={16} /> {label}
          </button>
        ))}
      </nav>

      {currentUser?.role === 'admin' && activeTab === 'personalized' && (
        <div style={{ ...panel, padding: 13, color: '#1d4ed8', background: '#eff6ff', fontSize: '.8rem' }}>
          Admin preview shows all requests. A donor account sees only requests selected for that donor by Donor Matching.
        </div>
      )}
      {success && <div style={{ ...panel, padding: 14, borderColor: '#a7f3d0', background: '#ecfdf5', color: '#047857', display: 'flex', gap: 9 }}><CheckCircle2 size={19} />{success}</div>}
      {error && <div style={{ ...panel, padding: 14, borderColor: '#fecaca', background: '#fef2f2', color: '#b91c1c', display: 'flex', gap: 9 }}><AlertCircle size={19} />{error}</div>}

      {(activeTab === 'personalized' || activeTab === 'all') && (
        <section style={{ display: 'grid', gap: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'end', gap: 12 }}>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.15rem' }}>{activeTab === 'personalized' ? 'Personalized for you · Top 10 best matching requests' : 'All open donation requests'}</h2>
              <p style={{ margin: '4px 0 0', color: 'var(--text-muted)', fontSize: '.8rem' }}>
                {activeTab === 'personalized'
                  ? 'Top 10 relief appeals ranked automatically by your AI compatibility score (category, proximity & capacity fit)'
                  : `${requests.length} open request${requests.length === 1 ? '' : 's'}`}
              </p>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={loadActiveView}><RefreshCw size={14} /> Refresh</button>
          </div>

          {loading ? <div style={{ ...panel, padding: 44, textAlign: 'center', color: 'var(--text-muted)' }}>Loading donation requests...</div> : requests.map((request) => {
            const [severityBg, severityText] = severityColors[request.severity] || severityColors.Moderate;
            const selected = selectedForRequest(request);
            const isExpanded = expanded.has(request.id);
            const isPersonalizedTab = activeTab === 'personalized';
            const personalized = isPersonalizedTab && (personalizedIds.has(request.id) || (request.compatibilityScore || 0) >= 40);
            const dropOffOffice = getDropOffOffice(request);
            const showMatchScore = isPersonalizedTab && request.compatibilityScore != null && request.compatibilityScore > 0;
            return (
              <article key={request.id} style={{ ...panel, overflow: 'hidden' }}>
                <button type="button" onClick={() => toggleExpanded(request.id)} style={{ width: '100%', border: 0, background: 'transparent', padding: '18px 20px', display: 'flex', justifyContent: 'space-between', gap: 14, cursor: 'pointer', textAlign: 'left', color: 'var(--text-primary)' }}>
                  <div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                      <strong style={{ fontSize: '1.02rem' }}>{dropOffOffice}</strong>
                      {showMatchScore && (
                        <span style={{
                          padding: '3px 9px',
                          borderRadius: 12,
                          background: request.compatibilityScore >= 60 ? '#ede9fe' : request.compatibilityScore >= 40 ? '#ecfdf5' : '#f8fafc',
                          color: request.compatibilityScore >= 60 ? '#6d28d9' : request.compatibilityScore >= 40 ? '#047857' : '#475569',
                          fontSize: '.68rem',
                          fontWeight: 800,
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 4,
                        }}>
                          <Sparkles size={11} /> {request.compatibilityScore}% MATCH
                        </span>
                      )}
                      <span style={{ padding: '3px 8px', borderRadius: 12, background: severityBg, color: severityText, fontSize: '.65rem', fontWeight: 800 }}>{request.severity?.toUpperCase()}</span>
                    </div>
                    <div style={{ marginTop: 7, color: 'var(--text-muted)', fontSize: '.78rem', display: 'flex', gap: 13, flexWrap: 'wrap' }}>
                      <span><MapPin size={13} style={{ verticalAlign: -2 }} /> {request.gnDivision}, {request.dsArea}</span>
                      <span>Origin: {request.reliefCamp}</span>
                      <span>{request.disasterType}</span>
                    </div>
                  </div>
                  <ChevronDown size={20} style={{ transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform .15s' }} />
                </button>

                {isExpanded && <div style={{ borderTop: '1px solid var(--border-subtle)' }}>
                  {showMatchScore ? (
                    <div style={{ margin: '16px 20px', padding: '12px 16px', borderRadius: 10, background: '#f5f3ff', border: '1px solid #ddd6fe', color: '#4c1d95', fontSize: '.82rem', lineHeight: 1.55 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 4 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 700, fontSize: '.86rem', color: '#6d28d9' }}>
                          <Sparkles size={15} /> AI Recommendation Match: {request.compatibilityScore}%
                        </div>
                        {request.factorScores && (
                          <div style={{ fontSize: '.74rem', color: '#7c3aed', display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                            <span>Category Fit: <strong>{request.factorScores.category}%</strong></span>
                            <span>Proximity: <strong>{request.factorScores.proximity}%</strong></span>
                            <span>Capacity: <strong>{request.factorScores.capacity}%</strong></span>
                            {request.factorScores.reliability != null && <span>Reliability: <strong>{request.factorScores.reliability}%</strong></span>}
                          </div>
                        )}
                      </div>
                      {request.matchReasons && request.matchReasons.length > 0 && (
                        <div style={{ fontSize: '.76rem', color: '#5b21b6', marginTop: 4 }}>
                          {request.matchReasons.join(' · ')}
                        </div>
                      )}
                      <div style={{ marginTop: 6, fontSize: '.78rem', color: '#4c1d95' }}>
                        Deliver pledged donations to the <strong>{dropOffOffice}</strong> within 12 hours so disaster officers can verify and distribute them quickly to affected people at <strong>{request.reliefCamp}</strong>.
                      </div>
                    </div>
                  ) : isPersonalizedTab && personalized ? (
                    <div style={{ margin: '16px 20px', padding: '13px 15px', borderRadius: 10, background: '#f5f3ff', border: '1px solid #ddd6fe', color: '#4c1d95', fontSize: '.82rem', lineHeight: 1.55 }}>
                      A {request.severity?.toLowerCase() || 'priority'} {request.disasterType?.toLowerCase() || 'disaster'} relief request from <strong>{request.reliefCamp}</strong> in the <strong>{request.gnDivision} GN Division</strong> has been selected for you. Please pledge any of the requested supplies you can provide. Deliver pledged donations to the <strong>{dropOffOffice}</strong> within 12 hours so disaster officers can verify and distribute them quickly to affected people.
                    </div>
                  ) : null}
                  <div className="donor-request-item-grid donor-request-item-head" style={{ padding: '10px 20px', color: 'var(--text-muted)', fontSize: '.68rem', fontWeight: 800, textTransform: 'uppercase' }}>
                    <span>Requested item</span><span>Needed</span><span>Still available</span><span>Your quantity</span>
                  </div>
                  {(request.items || []).filter((item) => Number(item.remainingQuantity || 0) > 0).map((item) => {
                    const value = Number(quantities[quantityKey(request.id, item)] || 0);
                    const max = Math.max(0, Math.floor(Number(item.remainingQuantity || 0)));
                    return <div key={item.itemId || item.itemName} className="donor-request-item-grid" style={{ padding: '14px 20px', borderTop: '1px solid var(--border-subtle)', alignItems: 'center' }}>
                      <div><strong>{item.itemName}</strong><div style={{ color: 'var(--text-muted)', fontSize: '.72rem', marginTop: 3 }}>{formatQuantity(item.donatedQuantity)} already received · {formatQuantity(item.pledgedQuantity)} pledged</div></div>
                      <span>{formatQuantity(item.neededQuantity)} {item.unit}</span>
                      <strong style={{ color: '#b91c1c' }}>{formatQuantity(item.remainingQuantity)} {item.unit}</strong>
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
                        <button type="button" className="btn btn-secondary btn-sm" aria-label={`Decrease ${item.itemName}`} onClick={() => updateQuantity(request.id, item, value - 1)} disabled={value <= 0}><Minus size={14} /></button>
                        <input aria-label={`Pledge quantity for ${item.itemName}`} type="number" min="0" max={max} value={value} onChange={(event) => updateQuantity(request.id, item, event.target.value)} style={{ width: 66, textAlign: 'center', padding: 8, border: '1px solid var(--border-default)', borderRadius: 8, background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontWeight: 800 }} />
                        <button type="button" className="btn btn-secondary btn-sm" aria-label={`Increase ${item.itemName}`} onClick={() => updateQuantity(request.id, item, value + 1)} disabled={value >= max}><Plus size={14} /></button>
                      </div>
                    </div>;
                  })}
                  <div style={{ padding: '15px 20px', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap', background: 'var(--bg-secondary)' }}>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '.78rem' }}>{selected.length ? `${selected.length} item type${selected.length === 1 ? '' : 's'} selected` : 'Choose quantities using + and −'}</span>
                    <button className="btn btn-success" disabled={selected.length === 0} onClick={() => openConfirmation(request)}><PackageCheck size={16} /> Pledge Selected Items</button>
                  </div>
                </div>}
              </article>
            );
          })}
          {!loading && requests.length === 0 && <div style={{ ...panel, padding: 50, textAlign: 'center', color: 'var(--text-muted)' }}><Sparkles size={28} style={{ marginBottom: 9 }} /><strong style={{ display: 'block', color: 'var(--text-primary)', marginBottom: 5 }}>{activeTab === 'personalized' ? 'No personalized requests right now' : 'No open donation requests'}</strong>{activeTab === 'personalized' ? 'Use “All Donation Requests” to browse every open requirement.' : 'All current requirements have been fulfilled.'}</div>}
        </section>
      )}

      {(activeTab === 'pledges' || activeTab === 'completed') && (
        <section style={{ ...panel, overflow: 'hidden' }}>
          <div style={{ padding: '18px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div><h2 style={{ margin: 0, fontSize: '1.1rem' }}>{activeTab === 'completed' ? 'Completed donations' : 'Items you pledged'}</h2><p style={{ margin: '4px 0 0', color: 'var(--text-muted)', fontSize: '.77rem' }}>{activeTab === 'completed' ? 'Donations confirmed as received by a disaster officer.' : 'Active pledges and automatically cancelled pledges.'}</p></div>
            <button className="btn btn-secondary btn-sm" onClick={loadActiveView}><RefreshCw size={14} /> Refresh</button>
          </div>
          {loading ? <div style={{ padding: 44, textAlign: 'center', color: 'var(--text-muted)' }}>Loading donation history...</div> : (
            <div style={{ overflowX: 'auto' }}><table className="custom-table"><thead><tr><th>Pledge</th><th>Item</th><th>Quantity</th><th>Drop-off office</th><th>Status</th><th>{activeTab === 'completed' ? 'Received' : 'Deadline'}</th></tr></thead><tbody>
              {historyRows.map((entry) => <tr key={entry.donationId}>
                <td><strong>{entry.pledgeBatchId || `PLG-${String(entry.donationId || '').slice(-8).toUpperCase()}`}</strong></td>
                <td><strong>{entry.itemName}</strong><div style={{ color: 'var(--text-muted)', fontSize: '.7rem' }}>{entry.reliefCamp}</div></td>
                <td>{formatQuantity(entry.quantity)} {entry.unit || 'units'}</td>
                <td>{entry.dsArea} Divisional Secretariat Office</td>
                <td><span className={`badge ${entry.status === 'received' ? 'badge-low' : entry.status === 'cancelled' ? 'badge-critical' : 'badge-medium'}`}>{entry.status}</span></td>
                <td>{activeTab === 'completed' ? (entry.acceptedAt ? new Date(entry.acceptedAt).toLocaleString() : 'Confirmed') : <span style={{ color: entry.status === 'cancelled' ? '#b91c1c' : '#a16207', fontWeight: 700 }}>{entry.status === 'cancelled' ? 'Expired — quantity released' : timeRemaining(entry.expiresAt, now)}</span>}</td>
              </tr>)}
              {historyRows.length === 0 && <tr><td colSpan="6" style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>No records in this section.</td></tr>}
            </tbody></table></div>
          )}
        </section>
      )}

      {confirmation && <div className="modal-overlay" onClick={() => !submitting && setConfirmation(null)}>
        <div className="modal-content" onClick={(event) => event.stopPropagation()}>
          <div className="modal-header"><div><h2 className="modal-title">Confirm your donation pledge</h2><p className="card-subtitle">Drop off at {getDropOffOffice(confirmation.request)}</p></div><button className="modal-close-btn" disabled={submitting} onClick={() => setConfirmation(null)}><X size={20} /></button></div>
          <div style={{ padding: 14, borderRadius: 10, background: '#fff7ed', color: '#9a3412', fontSize: '.8rem', marginBottom: 15 }}><Clock3 size={16} style={{ verticalAlign: -3, marginRight: 7 }} />You must deliver these items within 12 hours. The pledge will be cancelled automatically if an officer has not confirmed receipt by then.</div>
          <div style={{ display: 'grid', gap: 8, marginBottom: 18 }}>{confirmation.pledges.map((pledge) => <div key={pledge.itemId || pledge.itemName} style={{ display: 'flex', justifyContent: 'space-between', padding: 11, borderRadius: 9, background: 'var(--bg-secondary)' }}><strong>{pledge.itemName}</strong><span>{pledge.quantity} {pledge.unit}</span></div>)}</div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 9 }}><button className="btn btn-secondary" disabled={submitting} onClick={() => setConfirmation(null)}>Go Back</button><button className="btn btn-success" disabled={submitting} onClick={submitPledge}><ShieldCheck size={16} />{submitting ? 'Confirming...' : 'Confirm Pledge'}</button></div>
        </div>
      </div>}
    </div>
  );
}
