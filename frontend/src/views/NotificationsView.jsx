import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Bell, 
  Send, 
  CheckCircle2, 
  Phone, 
  Mail, 
  Smartphone, 
  RefreshCw, 
  Radio, 
  Signal, 
  AlertTriangle, 
  MessageSquare, 
  Plus, 
  X,
  Layers,
  Search,
  HeartHandshake
} from 'lucide-react';
import { api } from '../api';

export function NotificationsView() {
  const navigate = useNavigate();
  const [logs, setLogs] = useState([]);
  const [smsLogs, setSmsLogs] = useState([]);
  const [gatewayStatus, setGatewayStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('sms_logs'); // 'sms_logs' | 'all_audit'
  const [directionFilter, setDirectionFilter] = useState('all'); // 'all' | 'inbound' | 'outbound'
  const [searchTerm, setSearchTerm] = useState('');

  // Modals
  const [showBroadcastModal, setShowBroadcastModal] = useState(false);
  const [showDirectSMSModal, setShowDirectSMSModal] = useState(false);

  // Broadcast Form
  const [broadcastForm, setBroadcastForm] = useState({
    district: 'Colombo',
    role: '',
    urgency: 'CRITICAL',
    message: 'HEAVY FLOOD WARNING: Kelani river water levels at Nagalagam Street exceeded Minor Flood Level. Evacuate low-lying river areas to designated relief posts immediately.',
  });
  const [broadcastLoading, setBroadcastLoading] = useState(false);

  // Direct SMS Form
  const [directSMSForm, setDirectSMSForm] = useState({
    recipient: '+94771234567',
    message_type: 'RESCUE_UPDATE',
    message: 'Disaster Relief Unit: Navy rescue boat #04 is en route to your GN division. Please ensure all elderly and children are on roof/upper deck.',
  });
  const [directSMSLoading, setDirectSMSLoading] = useState(false);

  const [feedbackMsg, setFeedbackMsg] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [notifData, sLogs, gStatus] = await Promise.all([
        api.getNotifications(100),
        api.getSMSLogs({ limit: 100 }),
        api.getSMSGatewayStatus().catch(() => null),
      ]);
      setLogs(notifData || []);
      setSmsLogs(sLogs || []);
      setGatewayStatus(gStatus);
    } catch (err) {
      console.error('Failed to load notification/SMS data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleBroadcast = async (e) => {
    e.preventDefault();
    setBroadcastLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.broadcastSMS(broadcastForm);
      setFeedbackMsg(`Emergency Broadcast dispatched to ${res.recipients_count} mobile recipients in ${broadcastForm.district || 'all districts'}!`);
      setShowBroadcastModal(false);
      loadData();
      setTimeout(() => setFeedbackMsg(null), 8000);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to dispatch broadcast alert.');
    } finally {
      setBroadcastLoading(false);
    }
  };

  const handleDirectSMS = async (e) => {
    e.preventDefault();
    setDirectSMSLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.sendDirectSMS(directSMSForm);
      setFeedbackMsg(`Direct SMS successfully transmitted to ${res.recipient} via Dialog/Mobitel SMSC Gateway.`);
      setShowDirectSMSModal(false);
      loadData();
      setTimeout(() => setFeedbackMsg(null), 8000);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to send direct SMS.');
    } finally {
      setDirectSMSLoading(false);
    }
  };

  const getChannelIcon = (channel) => {
    switch (channel) {
      case 'SMS': return <Phone size={14} style={{ color: 'var(--accent-emerald)' }} />;
      case 'Email': return <Mail size={14} style={{ color: 'var(--accent-blue)' }} />;
      default: return <Smartphone size={14} style={{ color: 'var(--accent-amber)' }} />;
    }
  };

  const filteredSMSLogs = smsLogs.filter((log) => {
    if (directionFilter !== 'all' && log.direction !== directionFilter) return false;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      return (
        log.sender.toLowerCase().includes(term) ||
        log.recipient.toLowerCase().includes(term) ||
        log.message_text.toLowerCase().includes(term) ||
        (log.parsed_intent && log.parsed_intent.toLowerCase().includes(term))
      );
    }
    return true;
  });

  return (
    <div>
      {/* Feedback Messages */}
      {feedbackMsg && (
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
          <strong>{feedbackMsg}</strong>
        </div>
      )}

      {errorMsg && (
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
          <AlertTriangle size={20} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Top Gateway Telemetry Card */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: 'var(--accent-emerald)',
                boxShadow: '0 0 10px var(--accent-emerald)'
              }} />
              <h2 className="card-title" style={{ margin: 0 }}>
                Telecom SMS Gateway Hub & Multi-Channel Broadcast Center
              </h2>
            </div>
            <p className="card-subtitle" style={{ marginTop: '4px' }}>
              Live Cellular MO/MT Gateway (Dialog Axiata 1919 & SLT-Mobitel), SMS emergency trigger parsing & multi-subscriber alerts
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => navigate('/donation-appeal')}
            >
              <HeartHandshake size={14} />
              <span>Donation Appeal</span>
            </button>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => setShowDirectSMSModal(true)}
            >
              <Send size={14} />
              <span>Send Direct SMS</span>
            </button>
            <button
              className="btn btn-danger btn-sm"
              onClick={() => setShowBroadcastModal(true)}
            >
              <Radio size={14} />
              <span>Broadcast Emergency SMS Alert</span>
            </button>
            <button className="btn btn-secondary btn-sm" onClick={loadData} disabled={loading}>
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Live Gateway Metrics Ribbon */}
        {gatewayStatus && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '12px',
            marginTop: '16px',
            paddingTop: '16px',
            borderTop: '1px solid var(--border-subtle)'
          }}>
            <div style={{ padding: '10px 14px', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Gateway Status</div>
              <strong style={{ color: 'var(--accent-emerald)', fontSize: '0.88rem' }}>{gatewayStatus.gateway_status}</strong>
            </div>
            <div style={{ padding: '10px 14px', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Delivery Success Rate</div>
              <strong style={{ color: 'var(--accent-blue)', fontSize: '0.88rem' }}>{gatewayStatus.delivery_success_rate}%</strong>
            </div>
            <div style={{ padding: '10px 14px', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Inbound MO Processed</div>
              <strong style={{ color: 'var(--text-primary)', fontSize: '0.88rem' }}>{gatewayStatus.total_inbound_processed} msgs</strong>
            </div>
            <div style={{ padding: '10px 14px', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Outbound MT Dispatched</div>
              <strong style={{ color: 'var(--text-primary)', fontSize: '0.88rem' }}>{gatewayStatus.total_outbound_sent} msgs</strong>
            </div>
            <div style={{ padding: '10px 14px', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Signal Quality</div>
              <strong style={{ color: 'var(--accent-amber)', fontSize: '0.88rem' }}>{gatewayStatus.signal_strength}</strong>
            </div>
          </div>
        )}
      </div>

      {/* Tabs Switcher */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className={`btn ${activeTab === 'sms_logs' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('sms_logs')}
          >
            <MessageSquare size={16} />
            <span>Cellular SMS Transmission Logs ({smsLogs.length})</span>
          </button>
          <button
            className={`btn ${activeTab === 'all_audit' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('all_audit')}
          >
            <Bell size={16} />
            <span>All Channels Multi-Dispatch Audit ({logs.length})</span>
          </button>
        </div>

        {activeTab === 'sms_logs' && (
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: '4px' }}>
              <button
                className={`btn btn-sm ${directionFilter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setDirectionFilter('all')}
              >
                All
              </button>
              <button
                className={`btn btn-sm ${directionFilter === 'inbound' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setDirectionFilter('inbound')}
              >
                Inbound
              </button>
              <button
                className={`btn btn-sm ${directionFilter === 'outbound' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setDirectionFilter('outbound')}
              >
                Outbound
              </button>
            </div>

            <div className="search-box" style={{ width: '220px' }}>
              <Search className="search-icon" size={14} />
              <input
                type="text"
                className="form-input search-input"
                placeholder="Search SMS logs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
        )}
      </div>

      {/* TAB 1: CELLULAR SMS TRANSMISSION LOGS */}
      {activeTab === 'sms_logs' && (
        <div className="card">
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Log ID</th>
                  <th>Direction</th>
                  <th>Sender</th>
                  <th>Recipient</th>
                  <th>Message Content</th>
                  <th>Intent / Type</th>
                  <th>Associated ID</th>
                  <th>Status</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="9" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                      Loading cellular SMS gateway logs...
                    </td>
                  </tr>
                ) : filteredSMSLogs.length === 0 ? (
                  <tr>
                    <td colSpan="9" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                      No SMS transmission logs matching filter.
                    </td>
                  </tr>
                ) : (
                  filteredSMSLogs.map((log) => (
                    <tr key={log.id}>
                      <td style={{ fontWeight: '700' }}>#{log.id}</td>
                      <td>
                        <span
                          className={`badge ${log.direction === 'inbound' ? 'badge-medium' : 'badge-low'}`}
                          style={{ fontSize: '0.72rem', fontWeight: '800' }}
                        >
                          {log.direction === 'inbound' ? 'INBOUND' : 'OUTBOUND'}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'monospace', fontWeight: '700', color: 'var(--text-primary)' }}>
                        {log.sender}
                      </td>
                      <td style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                        {log.recipient}
                      </td>
                      <td style={{ maxWidth: '360px', fontSize: '0.82rem', color: 'var(--text-primary)', wordBreak: 'break-word' }}>
                        {log.message_text}
                      </td>
                      <td>
                        <span className="badge badge-medium" style={{ fontSize: '0.7rem' }}>
                          {log.parsed_intent || log.message_type}
                        </span>
                      </td>
                      <td>
                        {log.sos_request_id && (
                          <span className="badge badge-critical" style={{ fontSize: '0.7rem' }}>
                            SOS #{log.sos_request_id}
                          </span>
                        )}
                        {log.victim_id && (
                          <span className="badge badge-low" style={{ fontSize: '0.7rem' }}>
                            Victim #{log.victim_id}
                          </span>
                        )}
                        {!log.sos_request_id && !log.victim_id && (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>—</span>
                        )}
                      </td>
                      <td>
                        <span className="badge badge-low" style={{ fontSize: '0.72rem', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          <CheckCircle2 size={12} />
                          <span>{log.status}</span>
                        </span>
                      </td>
                      <td style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: ALL DISPATCH AUDIT LOGS */}
      {activeTab === 'all_audit' && (
        <div className="card">
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Channel</th>
                  <th>Trigger Event</th>
                  <th>Target Recipient</th>
                  <th>Dispatched Content</th>
                  <th>Status</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                      Loading audit trail...
                    </td>
                  </tr>
                ) : logs.length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                      No dispatched notification logs found.
                    </td>
                  </tr>
                ) : (
                  logs.map((item) => (
                    <tr key={item.id}>
                      <td style={{ fontWeight: '700' }}>#{item.id}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '600' }}>
                          {getChannelIcon(item.channel)}
                          <span>{item.channel}</span>
                        </div>
                      </td>
                      <td>
                        <span className="badge badge-medium" style={{ fontSize: '0.72rem' }}>
                          {item.message_type}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'monospace', color: 'var(--text-primary)', fontWeight: '600' }}>
                        {item.recipient_target}
                      </td>
                      <td style={{ maxWidth: '400px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {item.message_content}
                      </td>
                      <td>
                        <span className="badge badge-low" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          <CheckCircle2 size={12} />
                          <span>{item.dispatch_status}</span>
                        </span>
                      </td>
                      <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        {new Date(item.dispatched_at).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ────────────────────────────────────────────────────────────────────────── */}
      {/* MODAL 1: EMERGENCY SMS BROADCAST */}
      {/* ────────────────────────────────────────────────────────────────────────── */}
      {showBroadcastModal && (
        <div className="modal-overlay" onClick={() => setShowBroadcastModal(false)}>
          <div className="modal-content" style={{ maxWidth: '560px' }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div className="brand-icon" style={{ width: '32px', height: '32px', backgroundColor: 'var(--accent-rose)' }}>
                  <Radio size={18} />
                </div>
                <div>
                  <h2 className="modal-title">Broadcast Emergency SMS Alert</h2>
                  <p className="card-subtitle">Multi-subscriber emergency dispatch via Telecom Cellular Gateway</p>
                </div>
              </div>
              <button className="modal-close-btn" onClick={() => setShowBroadcastModal(false)}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleBroadcast}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Target District</label>
                  <select
                    className="form-input"
                    value={broadcastForm.district}
                    onChange={(e) => setBroadcastForm({ ...broadcastForm, district: e.target.value })}
                  >
                    <option value="Colombo">Colombo (Kelani Basin)</option>
                    <option value="Gampaha">Gampaha</option>
                    <option value="Kalutara">Kalutara</option>
                    <option value="Nuwara Eliya">Nuwara Eliya (Landslide Hotspot)</option>
                    <option value="Ratnapura">Ratnapura</option>
                    <option value="">All Registered Disaster Zones</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Urgency Priority</label>
                  <select
                    className="form-input"
                    value={broadcastForm.urgency}
                    onChange={(e) => setBroadcastForm({ ...broadcastForm, urgency: e.target.value })}
                  >
                    <option value="CRITICAL">CRITICAL (Immediate Evacuation)</option>
                    <option value="HIGH">HIGH (Severe Weather Alert)</option>
                    <option value="MEDIUM">MEDIUM (Relief Camp Notice)</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <label className="form-label">Emergency Broadcast Message Text</label>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {broadcastForm.message.length} chars
                  </span>
                </div>
                <textarea
                  className="form-input"
                  rows={4}
                  value={broadcastForm.message}
                  onChange={(e) => setBroadcastForm({ ...broadcastForm, message: e.target.value })}
                  required
                />
              </div>

              <button
                type="submit"
                className="btn btn-danger"
                style={{ width: '100%', padding: '12px', fontWeight: '800', marginTop: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                disabled={broadcastLoading}
              >
                <Radio size={16} />
                <span>{broadcastLoading ? 'Transmitting Cellular Broadcast...' : 'Transmit Multi-Subscriber Alert'}</span>
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ────────────────────────────────────────────────────────────────────────── */}
      {/* MODAL 2: DIRECT OUTBOUND SMS */}
      {/* ────────────────────────────────────────────────────────────────────────── */}
      {showDirectSMSModal && (
        <div className="modal-overlay" onClick={() => setShowDirectSMSModal(false)}>
          <div className="modal-content" style={{ maxWidth: '520px' }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div className="brand-icon" style={{ width: '32px', height: '32px', backgroundColor: 'var(--accent-blue)' }}>
                  <Send size={18} />
                </div>
                <div>
                  <h2 className="modal-title">Send Direct Emergency SMS</h2>
                  <p className="card-subtitle">Transmit single point-to-point SMS to any citizen or rescue team</p>
                </div>
              </div>
              <button className="modal-close-btn" onClick={() => setShowDirectSMSModal(false)}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleDirectSMS}>
              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Recipient Mobile Number</label>
                  <input
                    type="text"
                    className="form-input"
                    value={directSMSForm.recipient}
                    onChange={(e) => setDirectSMSForm({ ...directSMSForm, recipient: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Message Category</label>
                  <select
                    className="form-input"
                    value={directSMSForm.message_type}
                    onChange={(e) => setDirectSMSForm({ ...directSMSForm, message_type: e.target.value })}
                  >
                    <option value="RESCUE_UPDATE">Rescue Team Update</option>
                    <option value="CAMP_ADMISSION">Medical Camp Admission</option>
                    <option value="SUPPLY_CONFIRMATION">Donation Supply Alert</option>
                    <option value="GENERAL_ALERT">General Alert</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">SMS Content</label>
                <textarea
                  className="form-input"
                  rows={4}
                  value={directSMSForm.message}
                  onChange={(e) => setDirectSMSForm({ ...directSMSForm, message: e.target.value })}
                  required
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: '100%', padding: '12px', fontWeight: '700', marginTop: '10px' }}
                disabled={directSMSLoading}
              >
                <Send size={16} />
                <span>{directSMSLoading ? 'Transmitting SMS...' : 'Send SMS via Gateway'}</span>
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
