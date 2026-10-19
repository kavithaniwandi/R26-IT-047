import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  MapPin, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Activity, 
  RefreshCw,
  Package
} from 'lucide-react';
import { api } from '../api';

const formatSriLankaDateTime = (value) => new Intl.DateTimeFormat('en-LK', {
  timeZone: 'Asia/Colombo',
  year: 'numeric',
  month: 'short',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  hour12: true,
}).format(new Date(value));

export default function DisasterOfficer({ currentUser, onAddToast }) {
  const [activeTab, setActiveTab] = useState('unpledged'); // 'unpledged' | 'pending_pledges' | 'completed'
  const [loading, setLoading] = useState(false);
  const [acceptingId, setAcceptingId] = useState(null);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Core Data Lists
  const [pledges, setPledges] = useState([]);
  const [disasterRequests, setDisasterRequests] = useState([]);

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

  const handleMarkReceived = async (pledgeGroup) => {
    setAcceptingId(pledgeGroup.key);
    try {
      const cleanReqId = pledgeGroup.requestId ? pledgeGroup.requestId.replace('REQ-', '') : '';
      if (pledgeGroup.pledgeBatchId) {
        await api.acceptDisasterPledgeBatch(cleanReqId, pledgeGroup.pledgeBatchId);
      } else {
        await api.acceptDisasterPledge(cleanReqId, pledgeGroup.items[0].donationId);
      }

      const itemCount = pledgeGroup.items.length;
      const msg = `${itemCount} pledged item${itemCount === 1 ? '' : 's'} verified at the DS Office. Inventory and request status updated.`;
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

  const unpledgedRequestsByGn = Object.entries(
    unpledgedRequestsList.reduce((groups, request) => {
      const gnDivision = request.gnDivision || 'Unassigned GN Division';
      if (!groups[gnDivision]) groups[gnDivision] = [];
      groups[gnDivision].push(request);
      return groups;
    }, {})
  ).sort(([left], [right]) => left.localeCompare(right));

  const pendingPledgeGroups = Object.values(
    pledges.reduce((groups, pledge) => {
      const key = pledge.pledgeBatchId
        ? `${pledge.requestId}:${pledge.pledgeBatchId}`
        : `${pledge.requestId}:legacy:${pledge.donationId}`;
      if (!groups[key]) {
        groups[key] = {
          key,
          pledgeBatchId: pledge.pledgeBatchId,
          requestId: pledge.requestId,
          donorName: pledge.donorName,
          donorPhone: pledge.donorPhone,
          reliefCamp: pledge.reliefCamp,
          dsArea: pledge.dsArea,
          gnDivision: pledge.gnDivision,
          donatedAt: pledge.donatedAt,
          expiresAt: pledge.expiresAt,
          items: [],
        };
      }
      groups[key].items.push(pledge);
      return groups;
    }, {})
  );

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
              {currentUser?.assigned_ds_area
                ? `${currentUser.assigned_ds_area} DS Area · GN-level donation request coordination`
                : 'Verify incoming donor supplies and monitor item-wise deficit requests.'}
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
          <span>Pending Handover Pledges ({pendingPledgeGroups.length})</span>
        </button>
        <button
          className={`btn ${activeTab === 'completed' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('completed')}
        >
          <CheckCircle2 size={16} />
          <span>Verified at DS Office ({completedDonationsList.length})</span>
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
              <p className="card-subtitle">
                {currentUser?.assigned_ds_area || 'Assigned'} DS Area requests, separated by GN Division
              </p>
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
              unpledgedRequestsByGn.map(([gnDivision, requests]) => (
                <React.Fragment key={gnDivision}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--accent-blue-subtle)',
                    border: '1px solid hsla(217, 91%, 60%, 0.25)',
                    color: 'var(--accent-blue)',
                  }}>
                    <strong style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                      <MapPin size={15} /> {gnDivision} GN Division
                    </strong>
                    <span className="badge badge-info">
                      {requests.length} request{requests.length === 1 ? '' : 's'}
                    </span>
                  </div>
                  {requests.map((req) => (
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
                  ))}
                </React.Fragment>
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

          {pendingPledgeGroups.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
              No pending donor pledges in queue.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {pendingPledgeGroups.map((pledgeGroup) => (
                <div
                  key={pledgeGroup.key}
                  style={{
                    padding: '18px',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-lg)',
                    backgroundColor: 'var(--bg-secondary)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                        <strong style={{ color: 'var(--text-primary)', fontSize: '1rem' }}>
                          {pledgeGroup.donorName || 'Verified Donor'}
                        </strong>
                        <span className="badge badge-info">
                          {pledgeGroup.items.length} item{pledgeGroup.items.length === 1 ? '' : 's'}
                        </span>
                        {pledgeGroup.pledgeBatchId && (
                          <span className="badge font-mono">{pledgeGroup.pledgeBatchId}</span>
                        )}
                      </div>
                      <div style={{ marginTop: '5px', color: 'var(--text-muted)', fontSize: '0.77rem' }}>
                        {pledgeGroup.donorPhone || 'No Phone Registered'}
                      </div>
                    </div>

                    <button
                      className="btn btn-success btn-sm"
                      onClick={() => handleMarkReceived(pledgeGroup)}
                      disabled={acceptingId === pledgeGroup.key}
                    >
                      <CheckCircle2 size={13} />
                      <span>{acceptingId === pledgeGroup.key ? 'Verifying...' : `Mark ${pledgeGroup.items.length > 1 ? 'All ' : ''}Received`}</span>
                    </button>
                  </div>

                  <div style={{ display: 'flex', gap: '18px', flexWrap: 'wrap', marginTop: '12px', color: 'var(--text-secondary)', fontSize: '0.78rem' }}>
                    <span><MapPin size={13} style={{ verticalAlign: '-2px', marginRight: '4px' }} />{pledgeGroup.dsArea} / {pledgeGroup.gnDivision}</span>
                    <span>Drop-off: <strong>{pledgeGroup.dsArea} Divisional Secretariat Office</strong></span>
                    {pledgeGroup.expiresAt ? (
                      <>
                        <span>
                          Pledged: <strong>{formatSriLankaDateTime(pledgeGroup.donatedAt)}</strong>
                        </span>
                        <span style={{ color: 'var(--accent-amber)', fontWeight: '700' }}>
                          <Clock size={13} style={{ verticalAlign: '-2px', marginRight: '4px' }} />
                          Deadline: {formatSriLankaDateTime(pledgeGroup.expiresAt)}
                        </span>
                      </>
                    ) : (
                      <span style={{ color: 'var(--accent-amber)', fontWeight: '700' }}>
                        <Clock size={13} style={{ verticalAlign: '-2px', marginRight: '4px' }} />Legacy pledge
                      </span>
                    )}
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '9px', marginTop: '14px' }}>
                    {pledgeGroup.items.map((item) => (
                      <div
                        key={item.donationId}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          gap: '12px',
                          padding: '11px 13px',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-md)',
                          backgroundColor: 'var(--bg-card)',
                        }}
                      >
                        <strong style={{ color: 'var(--accent-blue)' }}>{item.itemName}</strong>
                        <strong style={{ color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
                          {item.quantity} {item.unit || 'units'}
                        </strong>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
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

    </div>
  );
}
