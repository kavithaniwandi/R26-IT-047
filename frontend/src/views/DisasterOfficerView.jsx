import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  MapPin, 
  Users, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Filter, 
  Plus, 
  Search, 
  Radio, 
  FileText, 
  Activity, 
  X, 
  RefreshCw,
  Mail,
  Send,
  Package,
  Truck,
  Sparkles,
  Check
} from 'lucide-react';
import { api } from '../api';

export default function DisasterOfficer({ currentUser, onAddToast }) {
  const [activeTab, setActiveTab] = useState('unpledged'); // 'unpledged' | 'pending_pledges' | 'completed' | 'assessments'
  const [loading, setLoading] = useState(false);
  const [acceptingId, setAcceptingId] = useState(null);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Core Data Lists
  const [pledges, setPledges] = useState([]);
  const [disasterRequests, setDisasterRequests] = useState([]);

  // AI Personalized Outreach Modal State
  const [selectedRequestForOutreach, setSelectedRequestForOutreach] = useState(null);
  const [isAiAnalyzing, setIsAiAnalyzing] = useState(false);
  const [rankedDonors, setRankedDonors] = useState([]);
  const [selectedDonorIds, setSelectedDonorIds] = useState(new Set());
  const [donorSearchQuery, setDonorSearchQuery] = useState('');
  const [sendingEmails, setSendingEmails] = useState(false);

  // Field Assessment Modal State
  const [showAssessmentModal, setShowAssessmentModal] = useState(false);
  const [assessmentForm, setAssessmentForm] = useState({
    district: 'Colombo',
    ds_division: 'Kaduwela',
    gn_division: 'Ranala',
    risk_level: 'High',
    affected_households: 25,
    critical_notes: 'Kelani riverbank water levels rising rapidly. Evacuation access road flooded.',
    immediate_actions: 'Deploy rescue boats and establish emergency rations drop.',
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [pledgeData, requestData] = await Promise.all([
        api.getOfficerPledges(),
        api.getDisasterRequests(),
      ]);
      setPledges(pledgeData || []);
      setDisasterRequests(requestData || []);
    } catch (err) {
      console.error('Error fetching officer data:', err);
      setError('Failed to connect to Disaster Officer telemetry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleMarkReceived = async (reqId, donationId) => {
    setAcceptingId(donationId);
    try {
      const cleanReqId = reqId ? reqId.replace('REQ-', '') : '';
      await api.acceptDisasterPledge(cleanReqId, donationId);

      const msg = 'Item receipt verified at DS Office. Inventory and request status updated.';
      setSuccessMsg(msg);
      if (onAddToast) onAddToast(msg, 'success', 'Received Verified');
      fetchData();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err.message || 'Error marking item received');
      if (onAddToast) onAddToast(err.message, 'error', 'Action Failed');
    } finally {
      setAcceptingId(null);
    }
  };

  // AI Donor Ranking & Outreach Analysis
  const handleOpenOutreachModal = async (req) => {
    setSelectedRequestForOutreach(req);
    setIsAiAnalyzing(true);
    setSelectedDonorIds(new Set());
    setDonorSearchQuery('');
    try {
      const scored = await api.getDonationDonorMatches(req.id);
      const ranked = (scored || []).slice(0, 20).map((donor) => ({
        ...donor,
        id: donor.donorId,
        displayName: donor.name,
        tier: donor.score >= 70 ? 'High' : donor.score >= 45 ? 'Medium' : 'Low',
        isAreaMatch: donor.proximityTier === 'Same GN division' || donor.proximityTier === 'Same DS area',
        avgResponse: 'N/A',
        pastDonations: donor.historyCount,
      }));
      setRankedDonors(ranked);
      const previous = ranked.filter((donor) => donor.alreadyTargeted).map((donor) => donor.donorId);
      const recommended = ranked.filter((donor) => donor.score >= 50).slice(0, 5).map((donor) => donor.donorId);
      setSelectedDonorIds(new Set([...previous, ...recommended]));
    } catch (err) {
      setError(err.message || 'Unable to calculate donor matches.');
      onAddToast?.(err.message, 'error', 'Matching Failed');
    } finally {
      setIsAiAnalyzing(false);
    }
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
      setSelectedDonorIds(new Set(visibleDonors.map((d) => d.id || d.userId)));
    } else {
      setSelectedDonorIds(new Set());
    }
  };

  const handleSendEmails = async () => {
    const donorIds = rankedDonors
      .filter((donor) => selectedDonorIds.has(donor.donorId) && !donor.alreadyTargeted)
      .map((donor) => donor.donorId);
    if (donorIds.length === 0) {
      if (onAddToast) onAddToast('Please select at least one donor for outreach.', 'warning', 'No Donors Selected');
      return;
    }

    setSendingEmails(true);
    try {
      const result = await api.sendDonationOutreach(selectedRequestForOutreach.id, donorIds);
      const msg = result.message;
      setSuccessMsg(msg);
      if (onAddToast) onAddToast(msg, 'success', 'Outreach Dispatched');
      setSelectedRequestForOutreach(null);
      fetchData();
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err) {
      setError(err.message || 'Unable to publish personalized requests.');
      onAddToast?.(err.message, 'error', 'Outreach Failed');
    } finally {
      setSendingEmails(false);
    }
  };

  const handleAssessmentSubmit = (e) => {
    e.preventDefault();
    const msg = `Ground damage assessment for ${assessmentForm.gn_division} (${assessmentForm.district}) logged.`;
    setSuccessMsg(msg);
    if (onAddToast) onAddToast(msg, 'success', 'Assessment Logged');
    setShowAssessmentModal(false);
    setTimeout(() => setSuccessMsg(null), 5000);
  };

  // Completed Donations List
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

  // Open Unpledged Item Deficits
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
    const name = (d.displayName || '').toLowerCase();
    const email = (d.email || '').toLowerCase();
    const q = donorSearchQuery.toLowerCase();
    return name.includes(q) || email.includes(q);
  });
  const newOutreachCount = rankedDonors.filter((donor) =>
    selectedDonorIds.has(donor.donorId) && !donor.alreadyTargeted
  ).length;

  return (
    <div>
      {/* Officer Command Banner */}
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
            <Shield size={30} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.45rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--text-primary)', margin: 0 }}>
              Disaster Officer Command Center
            </h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '4px 0 0' }}>
              Verify incoming donor supplies, monitor item-wise deficit requests, and trigger AI-targeted outreach.
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
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase' }}>FIELD OFFICER IN CHARGE</span>
            <strong style={{ fontSize: '1.1rem', color: 'var(--accent-blue)' }}>{currentUser?.full_name || 'Disaster Officer (Western Division)'}</strong>
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' }}>
        <button
          className={`btn ${activeTab === 'unpledged' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('unpledged')}
        >
          <Activity size={16} />
          <span>Open Item Deficits ({unpledgedRequestsList.length})</span>
        </button>
        <button
          className={`btn ${activeTab === 'pending_pledges' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('pending_pledges')}
        >
          <Clock size={16} />
          <span>Pending Handover Pledges ({pledges.length})</span>
        </button>
        <button
          className={`btn ${activeTab === 'completed' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('completed')}
        >
          <CheckCircle2 size={16} />
          <span>Verified at DS Office ({completedDonationsList.length})</span>
        </button>
        <button
          className={`btn ${activeTab === 'assessments' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('assessments')}
        >
          <FileText size={16} />
          <span>Damage Assessments</span>
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

      {/* TAB 1: OPEN DISASTER ITEM REQUESTS (UNPLEDGED) */}
      {activeTab === 'unpledged' && (
        <div className="card">
          <div className="card-header" style={{ flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 className="card-title">Open Disaster Item Requests (Unpledged Deficits)</h2>
              <p className="card-subtitle">Supply shortages requiring proactive targeted donor outreach</p>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={fetchData} disabled={loading}>
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
              <span>Refresh</span>
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                Loading open relief requirements...
              </div>
            ) : unpledgedRequestsList.length === 0 ? (
              <div style={{
                backgroundColor: 'var(--bg-secondary)',
                borderRadius: 'var(--radius-lg)',
                padding: '48px 20px',
                textAlign: 'center',
                border: '1px dashed var(--border-subtle)',
              }}>
                <Package size={40} style={{ color: 'var(--accent-emerald)', marginBottom: '12px', opacity: 0.8 }} />
                <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)', margin: '0 0 6px' }}>All Items Fully Pledged</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '440px', margin: '0 auto' }}>
                  All active disaster relief demands currently have matching pledges.
                </p>
              </div>
            ) : (
              unpledgedRequestsList.map((req) => (
                <div
                  key={req.id}
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
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                        <span style={{ fontSize: '1.05rem', fontWeight: '800', color: 'var(--text-primary)' }}>
                          {req.reliefCamp || 'Relief Camp'}
                        </span>
                        <span className={`badge ${req.severity === 'Critical' ? 'badge-critical' : 'badge-medium'}`}>
                          {req.severity} {req.disasterType}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        <MapPin size={12} style={{ color: 'var(--accent-rose)' }} />
                        <span>{req.gnDivision} &bull; {req.dsArea}</span>
                      </div>
                    </div>

                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => handleOpenOutreachModal(req)}
                      style={{ padding: '8px 14px' }}
                    >
                      <Sparkles size={14} />
                      <span>AI Donor Outreach</span>
                    </button>
                  </div>

                  {/* Open Item Deficit Pill Matrix */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '10px' }}>
                    {req.openItems.map((itm, i) => {
                      const uncommitted = (Number(itm.neededQuantity) || 0) - ((Number(itm.pledgedQuantity) || 0) + (Number(itm.donatedQuantity) || 0));
                      return (
                        <div
                          key={i}
                          style={{
                            backgroundColor: 'var(--bg-card)',
                            padding: '10px 14px',
                            borderRadius: 'var(--radius-md)',
                            border: '1px solid var(--border-subtle)',
                            fontSize: '0.83rem'
                          }}
                        >
                          <div style={{ fontWeight: '700', color: 'var(--text-primary)', marginBottom: '2px' }}>
                            {itm.itemName}
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.78rem' }}>
                            <span>Deficit: <strong style={{ color: 'var(--accent-rose)' }}>{uncommitted} {itm.unit}</strong></span>
                            <span>({itm.donatedQuantity || 0} received, {itm.pledgedQuantity || 0} pledged)</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 2: PENDING DONOR PLEDGES (AWAITING DS OFFICE VERIFICATION) */}
      {activeTab === 'pending_pledges' && (
        <div className="card">
          <div className="card-header" style={{ flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 className="card-title">Pending Donor Pledges Awaiting Handover</h2>
              <p className="card-subtitle">Items promised by donors awaiting drop-off and physical intake verification</p>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={fetchData} disabled={loading}>
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
              <span>Refresh</span>
            </button>
          </div>

          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Donor Info</th>
                  <th>Item Pledged</th>
                  <th>Quantity</th>
                  <th>Drop-off Office</th>
                  <th>DS / GN Division</th>
                  <th>Deadline</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {pledges.length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                      No pending donor pledges in queue.
                    </td>
                  </tr>
                ) : (
                  pledges.map((p) => (
                    <tr key={p.donationId || p.id}>
                      <td>
                        <div style={{ fontWeight: '700', color: 'var(--text-primary)' }}>{p.donorName || 'Verified Donor'}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{p.donorPhone || 'No Phone Registered'}</div>
                      </td>
                      <td style={{ fontWeight: '700', color: 'var(--accent-blue)' }}>{p.itemName}</td>
                      <td style={{ fontWeight: '800' }}>{p.quantity} {p.unit || 'units'}</td>
                      <td>{p.dsArea} Divisional Secretariat Office</td>
                      <td>
                        <div>{p.dsArea}</div>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{p.gnDivision}</span>
                      </td>
                      <td style={{ color: 'var(--accent-amber)', fontWeight: '700', fontSize: '0.75rem' }}>
                        {p.expiresAt ? new Date(p.expiresAt).toLocaleString() : 'Legacy pledge'}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button
                          className="btn btn-success btn-sm"
                          onClick={() => handleMarkReceived(p.requestId, p.donationId)}
                          disabled={acceptingId === p.donationId}
                        >
                          <CheckCircle2 size={13} />
                          <span>{acceptingId === p.donationId ? 'Verifying...' : 'Mark Received'}</span>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: COMPLETED & VERIFIED DONATIONS */}
      {activeTab === 'completed' && (
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Completed & Verified Inventory</h2>
              <p className="card-subtitle">Relief supplies received and officially stocked by Disaster Officers</p>
            </div>
            <span className="badge badge-success font-mono">
              {completedDonationsList.length} Verified Records
            </span>
          </div>

          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Donor Name</th>
                  <th>Item Received</th>
                  <th>Quantity</th>
                  <th>Camp Destination</th>
                  <th>Received Date</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {completedDonationsList.length === 0 ? (
                  <tr>
                    <td colSpan="6" style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                      No completed donations recorded yet.
                    </td>
                  </tr>
                ) : (
                  completedDonationsList.map((d, i) => (
                    <tr key={i}>
                      <td style={{ fontWeight: '700' }}>{d.donorName}</td>
                      <td style={{ fontWeight: '700', color: 'var(--text-primary)' }}>{d.itemName}</td>
                      <td style={{ fontWeight: '800' }}>{d.quantity}</td>
                      <td>{d.reliefCamp}</td>
                      <td>{new Date(d.acceptedAt || d.donatedAt || Date.now()).toLocaleDateString()}</td>
                      <td>
                        <span className="badge badge-success">✓ Received at DS Office</span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: DAMAGE ASSESSMENTS */}
      {activeTab === 'assessments' && (
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Divisional Secretariat Damage Assessments</h2>
              <p className="card-subtitle">Official verified ground logs for disaster relief deployment</p>
            </div>
            <button className="btn btn-primary btn-sm" onClick={() => setShowAssessmentModal(true)}>
              <Plus size={14} />
              <span>New Assessment</span>
            </button>
          </div>

          <div style={{
            backgroundColor: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-lg)',
            padding: '40px 20px',
            textAlign: 'center',
            border: '1px dashed var(--border-subtle)',
          }}>
            <FileText size={40} style={{ color: 'var(--accent-blue)', marginBottom: '12px', opacity: 0.8 }} />
            <h3 style={{ fontSize: '1.05rem', color: 'var(--text-primary)', margin: '0 0 6px' }}>Damage Surveys Up to Date</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '440px', margin: '0 auto 16px' }}>
              Log ground damage evaluations to generate automatic relief allocation tickets.
            </p>
            <button className="btn btn-secondary btn-sm" onClick={() => setShowAssessmentModal(true)}>
              <Plus size={14} />
              <span>Create Initial Assessment</span>
            </button>
          </div>
        </div>
      )}

      {/* MODAL 1: AI DONOR OUTREACH & LIKELIHOOD TARGETING */}
      {selectedRequestForOutreach && (
        <div className="modal-overlay" onClick={() => setSelectedRequestForOutreach(null)}>
          <div className="modal-content" style={{ maxWidth: '820px' }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'var(--accent-blue)', fontSize: '0.74rem', fontWeight: '800', textTransform: 'uppercase', marginBottom: '4px' }}>
                  <Sparkles size={14} />
                  <span>AI Donor Response Targeting Engine</span>
                </div>
                <h3 className="modal-title">Personalized Outreach: {selectedRequestForOutreach.reliefCamp}</h3>
                <p className="card-subtitle">{selectedRequestForOutreach.gnDivision} &bull; {selectedRequestForOutreach.dsArea} ({selectedRequestForOutreach.severity} {selectedRequestForOutreach.disasterType})</p>
              </div>
              <button className="modal-close-btn" onClick={() => setSelectedRequestForOutreach(null)}>
                <X size={20} />
              </button>
            </div>

            {isAiAnalyzing ? (
              <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--text-muted)' }}>
                <div className="spin" style={{ display: 'inline-block', marginBottom: '16px' }}>
                  <Activity size={36} style={{ color: 'var(--accent-blue)' }} />
                </div>
                <h4 style={{ color: 'var(--text-primary)', fontSize: '1.1rem', margin: '0 0 6px' }}>
                  Calculating Donor Suitability...
                </h4>
                <p style={{ fontSize: '0.84rem', maxWidth: '420px', margin: '0 auto' }}>
                  Comparing registered address proximity, donation history, item relevance, and request urgency for {selectedRequestForOutreach.dsArea}...
                </p>
              </div>
            ) : (
              <>
                {/* Search & Bulk Toggle Toolbar */}
                <div style={{
                  backgroundColor: 'var(--bg-secondary)',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '12px',
                  marginBottom: '16px'
                }}>
                  <div className="search-box" style={{ width: '240px' }}>
                    <Search className="search-icon" size={14} />
                    <input
                      type="text"
                      className="form-input search-input"
                      placeholder="Search suitable donors..."
                      value={donorSearchQuery}
                      onChange={(e) => setDonorSearchQuery(e.target.value)}
                      style={{ padding: '6px 10px 6px 32px', fontSize: '0.82rem' }}
                    />
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '0.82rem' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                      <input
                        type="checkbox"
                        checked={visibleDonors.length > 0 && visibleDonors.every((d) => selectedDonorIds.has(d.id || d.userId))}
                        onChange={(e) => handleSelectAllVisible(e, visibleDonors)}
                      />
                      <span>Select All Top Matched</span>
                    </label>
                    <span style={{ color: 'var(--accent-blue)', fontWeight: '800' }}>
                      {selectedDonorIds.size} Selected
                    </span>
                  </div>
                </div>

                {/* Ranked Donors Table */}
                <div style={{ maxHeight: '340px', overflowY: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', marginBottom: '20px' }}>
                  <table className="custom-table" style={{ margin: 0 }}>
                    <thead>
                      <tr>
                        <th style={{ width: '36px' }}></th>
                        <th>Donor</th>
                        <th>Proximity</th>
                        <th>History</th>
                        <th>Match Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visibleDonors.map((donor) => {
                        const dId = donor.id || donor.userId;
                        const isChecked = selectedDonorIds.has(dId);
                        return (
                          <tr
                            key={dId}
                            onClick={() => !donor.alreadyTargeted && handleToggleDonorSelect(dId)}
                            style={{
                              backgroundColor: isChecked ? 'var(--accent-blue-subtle)' : 'transparent',
                              cursor: 'pointer'
                            }}
                          >
                            <td onClick={(e) => e.stopPropagation()}>
                              <input
                                type="checkbox"
                                checked={isChecked}
                                disabled={donor.alreadyTargeted}
                                onChange={() => handleToggleDonorSelect(dId)}
                              />
                            </td>
                            <td>
                              <div style={{ fontWeight: '700', color: 'var(--text-primary)' }}>
                                {donor.displayName}
                              </div>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{donor.email}</div>
                            </td>
                            <td>
                              {donor.isAreaMatch ? (
                                <span className="badge badge-success">✓ Near {selectedRequestForOutreach.dsArea}</span>
                              ) : (
                                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{donor.proximityTier}</span>
                              )}
                            </td>
                            <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                              {donor.pastDonations} previous pledge(s)
                            </td>
                            <td>
                              <span className={`badge ${donor.tier === 'High' ? 'badge-critical' : donor.tier === 'Medium' ? 'badge-medium' : 'badge-low'}`}>
                                {donor.tier} ({donor.score}%)
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Footer Controls */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    Selected requests appear under “For You” in each donor's portal.
                  </span>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => setSelectedRequestForOutreach(null)}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={handleSendEmails}
                      disabled={sendingEmails || newOutreachCount === 0}
                    >
                      <Mail size={15} />
                      <span>{sendingEmails ? 'Publishing...' : `Send Personalized Requests (${newOutreachCount})`}</span>
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* MODAL 2: FIELD ASSESSMENT */}
      {showAssessmentModal && (
        <div className="modal-overlay" onClick={() => setShowAssessmentModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title">Log Field Damage Assessment</h3>
                <p className="card-subtitle">Official ground survey recording</p>
              </div>
              <button className="modal-close-btn" onClick={() => setShowAssessmentModal(false)}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleAssessmentSubmit}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">District</label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    value={assessmentForm.district}
                    onChange={(e) => setAssessmentForm({ ...assessmentForm, district: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">DS Division</label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    value={assessmentForm.ds_division}
                    onChange={(e) => setAssessmentForm({ ...assessmentForm, ds_division: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">GN Division</label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    value={assessmentForm.gn_division}
                    onChange={(e) => setAssessmentForm({ ...assessmentForm, gn_division: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Risk Severity Level</label>
                  <select
                    className="form-select"
                    value={assessmentForm.risk_level}
                    onChange={(e) => setAssessmentForm({ ...assessmentForm, risk_level: e.target.value })}
                  >
                    <option value="Critical">Critical (Immediate Danger)</option>
                    <option value="High">High (Flood / Landslide Path)</option>
                    <option value="Moderate">Moderate</option>
                    <option value="Low">Low</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Estimated Affected Households</label>
                <input
                  type="number"
                  min="1"
                  className="form-input"
                  value={assessmentForm.affected_households}
                  onChange={(e) => setAssessmentForm({ ...assessmentForm, affected_households: parseInt(e.target.value, 10) || 1 })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Critical Field Notes & Observations</label>
                <textarea
                  rows="3"
                  className="form-textarea"
                  value={assessmentForm.critical_notes}
                  onChange={(e) => setAssessmentForm({ ...assessmentForm, critical_notes: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowAssessmentModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Submit Official Assessment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
