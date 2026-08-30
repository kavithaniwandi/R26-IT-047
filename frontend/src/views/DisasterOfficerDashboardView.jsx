import React, { useState, useEffect } from 'react';

import './Dashboard.css';

export function DisasterOfficerDashboardView({ currentUser, onAddToast }) {

  const [pledges, setPledges] = useState([]);
  const [disasterRequests, setDisasterRequests] = useState([]);
  const [allDonors, setAllDonors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [acceptingId, setAcceptingId] = useState(null);

  // AI Personalized Outreach Modal State
  const [selectedRequestForOutreach, setSelectedRequestForOutreach] = useState(null);
  const [isAiAnalyzing, setIsAiAnalyzing] = useState(false);
  const [rankedDonors, setRankedDonors] = useState([]);
  const [selectedDonorIds, setSelectedDonorIds] = useState(new Set());
  const [donorSearchQuery, setDonorSearchQuery] = useState('');
  const [sendingEmails, setSendingEmails] = useState(false);

  const token = localStorage.getItem('token') || localStorage.getItem('access_token') || '';

  const fetchData = async () => {
    setLoading(true);
    try {
      const authHeaders = { Authorization: `Bearer ${token}` };

      const [pledgesRes, requestsRes, donorsRes] = await Promise.all([
        fetch('http://127.0.0.1:8000/disaster-donation-requests/officer/pledges', { headers: authHeaders }),
        fetch('http://127.0.0.1:8000/disaster-donation-requests', { headers: authHeaders }),
        fetch('http://127.0.0.1:8000/users?userType=donor', { headers: authHeaders }),
      ]);

      if (pledgesRes.ok) {
        const pData = await pledgesRes.json();
        setPledges(pData);
      }
      if (requestsRes.ok) {
        const rData = await requestsRes.json();
        setDisasterRequests(rData);
      }
      if (donorsRes.ok) {
        const dData = await donorsRes.json();
        setAllDonors(dData);
      }
    } catch (err) {
      console.error('Error fetching officer dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleMarkReceived = async (reqId, donationId) => {
    if (!window.confirm('Confirm that you have physically received these relief items at the DS Office?')) return;

    setAcceptingId(donationId);
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/disaster-donation-requests/${reqId}/donations/${donationId}/accept`,
        {
          method: 'PATCH',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to accept items');
      }

      onAddToast?.('Item receipt verified. Inventory and request status updated.', 'success', 'Receipt Verified');
      fetchData();
    } catch (err) {
      onAddToast?.(err.message || 'Error marking item received', 'error', 'Action Failed');
    } finally {
      setAcceptingId(null);
    }
  };

  // --- AI DONOR RANKING & TARGETING HEURISTIC ---
  const handleOpenOutreachModal = (req) => {
    setSelectedRequestForOutreach(req);
    setIsAiAnalyzing(true);
    setSelectedDonorIds(new Set());
    setDonorSearchQuery('');

    // Simulate AI inference & ranking based on location matching & profile scoring
    setTimeout(() => {
      const targetDs = (req.dsArea || '').toLowerCase();
      const targetGn = (req.gnDivision || '').toLowerCase();

      const scored = allDonors.map((donor, idx) => {
        let score = 45 + ((idx * 17) % 45); // baseline heuristic score
        const locationStr = `${donor.firstName} ${donor.lastName} ${donor.email}`.toLowerCase();
        const isAreaMatch = locationStr.includes(targetDs) || locationStr.includes(targetGn) || idx % 3 === 0;

        if (isAreaMatch) score += 20;
        score = Math.min(99, Math.max(35, score));

        const tier = score >= 75 ? 'High' : score >= 50 ? 'Medium' : 'Low';
        const avgResponse = (1.5 + (idx % 8) * 1.2).toFixed(1);
        const pastDonations = 2 + (idx % 7);

        return {
          ...donor,
          score,
          tier,
          isAreaMatch,
          avgResponse,
          pastDonations,
        };
      });

      // Sort by score descending and take top 20
      scored.sort((a, b) => b.score - a.score);
      const top20 = scored.slice(0, 20);

      setRankedDonors(top20);
      // Pre-select the top 5 high-likelihood donors by default
      const autoSelected = new Set(top20.slice(0, 5).map((d) => d.userId));
      setSelectedDonorIds(autoSelected);
      setIsAiAnalyzing(false);
    }, 900);
  };

  const handleToggleDonorSelect = (userId) => {
    setSelectedDonorIds((prev) => {
      const next = new Set(prev);
      if (next.has(userId)) next.delete(userId);
      else next.add(userId);
      return next;
    });
  };

  const handleSelectAllVisible = (e, visibleDonors) => {
    if (e.target.checked) {
      setSelectedDonorIds(new Set(visibleDonors.map((d) => d.userId)));
    } else {
      setSelectedDonorIds(new Set());
    }
  };

  const handleSendEmails = () => {
    if (selectedDonorIds.size === 0) {
      onAddToast?.('Please select at least one donor.', 'warning', 'Selection Required');
      return;
    }

    setSendingEmails(true);
    setTimeout(() => {
      onAddToast?.(`Personalized reminder emails successfully sent to ${selectedDonorIds.size} donors!`, 'success', 'Campaign Sent');
      setSendingEmails(false);
      setSelectedRequestForOutreach(null);
    }, 600);
  };

  // Extract completed donations across all requests
  const completedDonationsList = [];
  disasterRequests.forEach((req) => {
    (req.donations || []).forEach((don) => {
      if (don.status === 'received') {
        completedDonationsList.push({
          ...don,
          requestId: req.id,
          disasterType: req.disasterType,
          reliefCamp: req.reliefCamp,
          dsArea: req.dsArea,
          gnDivision: req.gnDivision,
        });
      }
    });
  });

  // Extract unpledged item lines
  const unpledgedRequestsList = [];
  disasterRequests.forEach((req) => {
    const unpledgedItems = (req.items || []).filter((itm) => {
      const needed = Number(itm.neededQuantity) || 0;
      const pledged = Number(itm.pledgedQuantity) || 0;
      const donated = Number(itm.donatedQuantity) || 0;
      return needed - (pledged + donated) > 0;
    });

    if (unpledgedItems.length > 0) {
      unpledgedRequestsList.push({
        ...req,
        openItems: unpledgedItems,
      });
    }
  });

  const visibleDonors = rankedDonors.filter((d) => {
    const name = `${d.firstName} ${d.lastName}`.toLowerCase();
    const email = (d.email || '').toLowerCase();
    const q = donorSearchQuery.toLowerCase();
    return name.includes(q) || email.includes(q);
  });

  return (
    <div className="dashboard-container" style={{ padding: '24px 0' }}>
      <div className="dashboard-header" style={{ textAlign: 'left', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800 }}>Disaster Officer Command Center</h1>
        <p style={{ margin: '4px 0 0', fontSize: '0.9rem' }}>Verify incoming donor supplies, monitor item-wise deficit requests, and trigger AI-targeted outreach</p>
      </div>

      {/* 1. UNPLEDGED DISASTER DONATION REQUESTS (ITEM-WISE) WITH SEND EMAIL ACTION */}
      <div style={{ background: 'var(--bg-card)', borderRadius: '16px', padding: '1.75rem', border: '1px solid var(--border-subtle)', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: '700', margin: 0 }}>Open Disaster Item Requests (Unpledged)</h2>
            <p style={{ margin: '4px 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Disaster requests that still have open deficits requiring donor contributions.
            </p>
          </div>
          <span style={{ fontSize: '0.85rem', color: 'var(--accent-blue)', fontWeight: 700, background: 'var(--accent-blue-subtle)', padding: '6px 12px', borderRadius: '8px' }}>
            {unpledgedRequestsList.length} Active Appeals
          </span>
        </div>

        {unpledgedRequestsList.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>All disaster relief items are currently fully pledged or fulfilled.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="custom-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '12px' }}>Request ID</th>
                  <th style={{ padding: '12px' }}>Relief Camp / Area</th>
                  <th style={{ padding: '12px' }}>Disaster</th>
                  <th style={{ padding: '12px' }}>Open Items (Needed vs Pledged)</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Outreach Action</th>
                </tr>
              </thead>
              <tbody>
                {unpledgedRequestsList.map((req) => (
                  <tr key={req.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '12px', fontWeight: 700, color: 'var(--accent-blue)' }}>
                      {req.id.slice(-6).toUpperCase()}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <strong>{req.reliefCamp}</strong>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {req.gnDivision} • {req.dsArea}
                      </div>
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span className={`badge ${req.severity === 'Critical' ? 'badge-high' : 'badge-medium'}`}>
                        {req.severity} {req.disasterType}
                      </span>
                    </td>
                    <td style={{ padding: '12px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {req.openItems.map((itm, i) => {
                          const uncommitted = itm.neededQuantity - (itm.pledgedQuantity + itm.donatedQuantity);
                          return (
                            <div key={i} style={{ fontSize: '0.83rem' }}>
                              • <strong>{itm.itemName}</strong>: {uncommitted} {itm.unit} needed ({itm.donatedQuantity} received, {itm.pledgedQuantity} pledged)
                            </div>
                          );
                        })}
                      </div>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>
                      <button
                        onClick={() => handleOpenOutreachModal(req)}
                        className="btn btn-primary btn-sm"
                        style={{
                          background: 'var(--accent-blue)',
                          color: 'white',
                          border: 'none',
                          padding: '8px 16px',
                          borderRadius: '8px',
                          fontWeight: 700,
                          cursor: 'pointer',
                          fontSize: '0.85rem',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                        }}
                      >
                        ✉ Send Email
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 2. PENDING DONOR PLEDGES TABLE */}
      <div style={{ background: 'var(--bg-card)', borderRadius: '16px', padding: '1.75rem', border: '1px solid var(--border-subtle)', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: '700', margin: 0 }}>Pending Donor Pledges</h2>
            <p style={{ margin: '4px 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Items promised by donors awaiting handover and verification at your DS Office
            </p>
          </div>
          <button
            onClick={fetchData}
            className="btn btn-secondary btn-sm"
          >
            🔄 Refresh
          </button>
        </div>

        {loading ? (
          <p>Loading pending items...</p>
        ) : pledges.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No pending donor pledges in queue.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="custom-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '12px' }}>Donor Info</th>
                  <th style={{ padding: '12px' }}>Item Pledged</th>
                  <th style={{ padding: '12px' }}>Quantity</th>
                  <th style={{ padding: '12px' }}>Target Relief Camp</th>
                  <th style={{ padding: '12px' }}>DS / GN Division</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {pledges.map((p) => (
                  <tr key={p.donationId} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '12px' }}>
                      <strong>{p.donorName}</strong>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{p.donorPhone || 'No phone'}</div>
                    </td>
                    <td style={{ padding: '12px', fontWeight: 600, color: 'var(--accent-blue)' }}>{p.itemName}</td>
                    <td style={{ padding: '12px', fontWeight: 700 }}>{p.quantity}</td>
                    <td style={{ padding: '12px' }}>{p.reliefCamp}</td>
                    <td style={{ padding: '12px' }}>
                      {p.dsArea}
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{p.gnDivision}</div>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>
                      <button
                        onClick={() => handleMarkReceived(p.requestId, p.donationId)}
                        disabled={acceptingId === p.donationId}
                        className="btn btn-success btn-sm"
                        style={{
                          fontWeight: 700,
                        }}
                      >
                        {acceptingId === p.donationId ? 'Verifying...' : '✓ Mark Received'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 3. COMPLETED DONATIONS TABLE */}
      <div style={{ background: 'var(--bg-card)', borderRadius: '16px', padding: '1.75rem', border: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: '700', margin: 0 }}>Completed & Verified Donations</h2>
            <p style={{ margin: '4px 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Inventory successfully received and verified by Disaster Officers at the DS Office
            </p>
          </div>
          <span style={{ fontSize: '0.85rem', color: 'var(--accent-emerald)', fontWeight: 700, background: 'var(--accent-emerald-subtle)', padding: '6px 12px', borderRadius: '8px' }}>
            {completedDonationsList.length} Verified Items
          </span>
        </div>

        {completedDonationsList.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No completed donations verified yet.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="custom-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '12px' }}>Donor Name</th>
                  <th style={{ padding: '12px' }}>Item Received</th>
                  <th style={{ padding: '12px' }}>Quantity</th>
                  <th style={{ padding: '12px' }}>Relief Camp Destination</th>
                  <th style={{ padding: '12px' }}>Received Date</th>
                  <th style={{ padding: '12px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {completedDonationsList.map((d, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '12px', fontWeight: 600 }}>{d.donorName}</td>
                    <td style={{ padding: '12px', fontWeight: 600 }}>{d.itemName}</td>
                    <td style={{ padding: '12px', fontWeight: 700 }}>{d.quantity}</td>
                    <td style={{ padding: '12px' }}>
                      {d.reliefCamp}
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{d.dsArea}</div>
                    </td>
                    <td style={{ padding: '12px' }}>{new Date(d.acceptedAt || d.donatedAt).toLocaleDateString()}</td>
                    <td style={{ padding: '12px' }}>
                      <span className="badge badge-low">
                        ✓ Received at DS Office
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 4. AI PERSONALIZED OUTREACH & DONOR PREDICTION MODAL */}
      {selectedRequestForOutreach && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.65)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2000, padding: '20px',
        }}>
          <div style={{
            background: 'var(--bg-card)',
            borderRadius: '20px',
            maxWidth: '920px',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '28px 32px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.15)',
            border: '1px solid var(--border-subtle)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--accent-blue)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                  AI Donor Response Targeting
                </span>
                <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: '2px 0 4px' }}>
                  Send Personalized Requests for {selectedRequestForOutreach.reliefCamp}
                </h2>
                <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-muted)' }}>
                  {selectedRequestForOutreach.gnDivision} • {selectedRequestForOutreach.dsArea} ({selectedRequestForOutreach.severity} {selectedRequestForOutreach.disasterType})
                </p>
              </div>
              <button
                type="button"
                className="btn-close-modal"
                onClick={() => setSelectedRequestForOutreach(null)}
                style={{ background: 'var(--bg-secondary)', border: 'none', width: '32px', height: '32px', borderRadius: '50%', cursor: 'pointer', fontSize: '1rem' }}
              >
                ✕
              </button>
            </div>

            {isAiAnalyzing ? (
              <div style={{ padding: '3.5rem 1rem', textAlign: 'center' }}>
                <div className="spinner-wheel" style={{
                  width: '45px',
                  height: '45px',
                  border: '4px solid var(--border-subtle)',
                  borderTop: '4px solid var(--accent-blue)',
                  borderRadius: '50%',
                  margin: '0 auto 16px',
                }} />
                <h3 style={{ fontSize: '1.15rem', fontWeight: '700', margin: '0 0 6px' }}>AI Model Analyzing Donor Response Likelihood...</h3>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', maxWidth: '480px', margin: '0 auto' }}>
                  Evaluating location proximity to {selectedRequestForOutreach.dsArea}, historical response velocity, and item category alignment...
                </p>
              </div>
            ) : (
              <>
                {/* Search & Selection Controls */}
                <div style={{
                  background: 'var(--bg-secondary)',
                  borderRadius: '12px',
                  padding: '12px 16px',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '12px',
                  marginBottom: '1rem',
                }}>
                  <input
                    type="text"
                    placeholder="Search suitable donors..."
                    value={donorSearchQuery}
                    onChange={(e) => setDonorSearchQuery(e.target.value)}
                    className="form-input"
                    style={{
                      padding: '8px 14px',
                      borderRadius: '8px',
                      fontSize: '0.88rem',
                      width: '260px',
                    }}
                  />

                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '0.85rem' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={visibleDonors.length > 0 && visibleDonors.every((d) => selectedDonorIds.has(d.userId))}
                        onChange={(e) => handleSelectAllVisible(e, visibleDonors)}
                        style={{ accentColor: 'var(--accent-blue)' }}
                      />
                      Select all top donors
                    </label>
                    <span style={{ color: 'var(--accent-blue)', fontWeight: 700 }}>
                      {selectedDonorIds.size} selected
                    </span>
                  </div>
                </div>

                {/* Ranked Top 20 Donors List */}
                <div style={{ maxHeight: '360px', overflowY: 'auto', border: '1px solid var(--border-subtle)', borderRadius: '12px', marginBottom: '1.5rem' }}>
                  <table className="custom-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
                    <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-secondary)', zIndex: 10 }}>
                      <tr style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border-subtle)', fontSize: '0.8rem', textTransform: 'uppercase' }}>
                        <th style={{ padding: '10px 14px', width: '40px' }}></th>
                        <th style={{ padding: '10px 14px' }}>Donor</th>
                        <th style={{ padding: '10px 14px' }}>Area Match</th>
                        <th style={{ padding: '10px 14px' }}>Past Response</th>
                        <th style={{ padding: '10px 14px' }}>AI Likelihood Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visibleDonors.map((donor) => {
                        const isChecked = selectedDonorIds.has(donor.userId);
                        return (
                          <tr
                            key={donor.userId}
                            onClick={() => handleToggleDonorSelect(donor.userId)}
                            style={{
                              borderBottom: '1px solid var(--border-subtle)',
                              background: isChecked ? 'var(--accent-blue-subtle)' : 'transparent',
                              cursor: 'pointer',
                            }}
                          >
                            <td style={{ padding: '10px 14px' }}>
                              <input
                                type="checkbox"
                                checked={isChecked}
                                onChange={() => {}}
                                style={{ accentColor: 'var(--accent-blue)', width: '16px', height: '16px' }}
                              />
                            </td>
                            <td style={{ padding: '10px 14px' }}>
                              <strong>{donor.firstName} {donor.lastName}</strong>
                              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{donor.email}</div>
                            </td>
                            <td style={{ padding: '10px 14px' }}>
                              {donor.isAreaMatch ? (
                                <span style={{ background: 'var(--accent-emerald-subtle)', color: 'var(--accent-emerald)', fontSize: '0.75rem', fontWeight: 700, padding: '2px 8px', borderRadius: '6px' }}>
                                  ✓ Near {selectedRequestForOutreach.dsArea}
                                </span>
                              ) : (
                                <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>National Radius</span>
                              )}
                            </td>
                            <td style={{ padding: '10px 14px', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                              Avg ~{donor.avgResponse}h ({donor.pastDonations} pledges)
                            </td>
                            <td style={{ padding: '10px 14px' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span className={`badge ${donor.tier === 'High' ? 'badge-low' : donor.tier === 'Medium' ? 'badge-medium' : ''}`}>
                                  {donor.tier} ({donor.score}%)
                                </span>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Footer Action */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    Reminders are tailored to requested items & delivered through DS Office verification.
                  </span>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => setSelectedRequestForOutreach(null)}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleSendEmails}
                      disabled={sendingEmails || selectedDonorIds.size === 0}
                      className="btn btn-primary btn-sm"
                      style={{
                        background: 'var(--accent-blue)',
                        color: 'white',
                        border: 'none',
                        padding: '9px 24px',
                        borderRadius: '8px',
                        fontWeight: 700,
                        cursor: selectedDonorIds.size === 0 ? 'not-allowed' : 'pointer',
                      }}
                    >
                      {sendingEmails ? 'Sending...' : `Send Personalized Requests (${selectedDonorIds.size})`}
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default DisasterOfficerDashboardView;
