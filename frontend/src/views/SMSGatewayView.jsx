import React, { useState, useEffect, useCallback } from 'react';
import {
  Radio,
  Send,
  MessageSquare,
  AlertTriangle,
  CheckCircle,
  Clock,
  RefreshCw,
  PhoneCall,
  Activity,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  X,
  Wifi,
  WifiOff,
  Filter,
} from 'lucide-react';
import { api } from '../api';

/* ─────────────────────────────────────────────────────────────────────────────
   Helper: badge colour from SMS status
───────────────────────────────────────────────────────────────────────────── */
function StatusBadge({ status }) {
  const MAP = {
    sent:       { bg: 'var(--accent-emerald-subtle)', color: 'var(--accent-emerald)',  label: 'Sent' },
    simulated:  { bg: 'var(--accent-blue-subtle)',    color: 'var(--accent-blue)',     label: 'Simulated' },
    delivered:  { bg: 'var(--accent-emerald-subtle)', color: 'var(--accent-emerald)',  label: 'Delivered' },
    received:   { bg: 'var(--accent-amber-subtle)',   color: 'var(--accent-amber)',    label: 'Received' },
    processed:  { bg: 'var(--accent-blue-subtle)',    color: 'var(--accent-blue)',     label: 'Processed' },
    failed:     { bg: 'var(--accent-rose-subtle)',    color: 'var(--accent-rose)',     label: 'Failed' },
  };
  const cfg = MAP[status] || { bg: 'var(--bg-secondary)', color: 'var(--text-muted)', label: status };
  return (
    <span style={{
      padding: '2px 8px',
      borderRadius: '99px',
      fontSize: '0.72rem',
      fontWeight: '700',
      backgroundColor: cfg.bg,
      color: cfg.color,
      letterSpacing: '0.03em',
    }}>
      {cfg.label}
    </span>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   Helper: intent badge
───────────────────────────────────────────────────────────────────────────── */
function IntentBadge({ intent }) {
  const MAP = {
    SOS_TRIGGER:          { color: 'var(--accent-rose)',    label: '🆘 SOS' },
    VICTIM_REGISTRATION:  { color: 'var(--accent-blue)',    label: '📋 REG' },
    STATUS_CHECK:         { color: 'var(--accent-amber)',   label: '📊 STATUS' },
    CAMP_QUERY:           { color: 'var(--accent-emerald)', label: '🏕 CAMP' },
    HELP:                 { color: 'var(--accent-violet)',  label: '❓ HELP' },
    SYSTEM_CONFIRMATION:  { color: 'var(--text-muted)',     label: '✉ CONFIRM' },
    BROADCAST_ALERT:      { color: 'var(--accent-rose)',    label: '📡 BROADCAST' },
  };
  const cfg = MAP[intent] || { color: 'var(--text-muted)', label: intent || '—' };
  return (
    <span style={{ fontSize: '0.72rem', fontWeight: '700', color: cfg.color }}>{cfg.label}</span>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   SMS Gateway Management View
───────────────────────────────────────────────────────────────────────────── */
export function SMSGatewayView({ onAddToast }) {
  const toast = useCallback((msg, type = 'info', title = null) => {
    if (onAddToast) onAddToast(msg, type, title);
  }, [onAddToast]);

  // --- gateway status ---
  const [gatewayStatus, setGatewayStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);

  // --- logs ---
  const [logs, setLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(true);
  const [dirFilter, setDirFilter] = useState('');
  const [statusLogFilter, setStatusLogFilter] = useState('');
  const [logsLimit, setLogsLimit] = useState(50);

  // --- simulate inbound ---
  const [simSender, setSimSender] = useState('+94771234567');
  const [simMessage, setSimMessage] = useState('SOS 5 Ranala 4 Need insulin immediately');
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);

  // --- send direct SMS ---
  const [sendRecipient, setSendRecipient] = useState('+94771234567');
  const [sendMessage, setSendMessage] = useState('');
  const [sendType, setSendType] = useState('SYSTEM_NOTIFICATION');
  const [sendLoading, setSendLoading] = useState(false);

  // --- broadcast ---
  const [bcMessage, setBcMessage] = useState('');
  const [bcDistrict, setBcDistrict] = useState('');
  const [bcUrgency, setBcUrgency] = useState('HIGH');
  const [bcLoading, setBcLoading] = useState(false);

  // --- quick examples ---
  const QUICK_MSGS = [
    { label: 'SOS – Trapped Family', msg: 'SOS 5 Ranala 4 Diabetic patient trapped 2nd floor. Insulin needed.' },
    { label: 'SOS – Flood (Children)', msg: 'SOS 5 Kelaniya 6 3 children trapped, flood rising fast, please help!' },
    { label: 'SOS – Landslide (Elderly)', msg: 'SOS 4 Nuwara Eliya 2 Elderly couple trapped by landslide. Bedridden.' },
    { label: 'Registration', msg: 'REG Kamal Perera 198512345678 Colombo 5 Asthma, Insulin' },
    { label: 'Status Check', msg: 'STATUS' },
    { label: 'Camp Query', msg: 'CAMP Colombo' },
    { label: 'Help', msg: 'HELP' },
  ];

  /* ─── Data Fetching ─── */
  const fetchGatewayStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const data = await api.getSMSGatewayStatus();
      setGatewayStatus(data);
    } catch (err) {
      toast('Failed to load gateway status: ' + err.message, 'error', 'Gateway Error');
    } finally {
      setStatusLoading(false);
    }
  }, [toast]);

  const fetchLogs = useCallback(async () => {
    setLogsLoading(true);
    try {
      const params = { limit: logsLimit };
      if (dirFilter) params.direction = dirFilter;
      if (statusLogFilter) params.status = statusLogFilter;
      const data = await api.getSMSLogs(params);
      setLogs(data);
    } catch (err) {
      toast('Failed to load SMS logs: ' + err.message, 'error', 'Logs Error');
    } finally {
      setLogsLoading(false);
    }
  }, [dirFilter, statusLogFilter, logsLimit, toast]);

  useEffect(() => { fetchGatewayStatus(); fetchLogs(); }, []);
  useEffect(() => { fetchLogs(); }, [dirFilter, statusLogFilter, logsLimit]);

  /* ─── Simulate Inbound ─── */
  const handleSimulate = async (e) => {
    e.preventDefault();
    setSimLoading(true);
    setSimResult(null);
    try {
      const result = await api.simulateInboundSMS({ sender: simSender, message: simMessage });
      setSimResult(result);
      toast(
        `Intent: ${result.intent} | ${result.auto_reply_message.slice(0, 80)}`,
        result.intent === 'SOS_TRIGGER' ? 'error' : 'success',
        'SMS Processed',
      );
      fetchLogs();
      fetchGatewayStatus();
    } catch (err) {
      toast('Simulation failed: ' + err.message, 'error', 'Simulate Error');
    } finally {
      setSimLoading(false);
    }
  };

  /* ─── Send Direct ─── */
  const handleSendDirect = async (e) => {
    e.preventDefault();
    setSendLoading(true);
    try {
      const result = await api.sendDirectSMS({
        recipient: sendRecipient,
        message: sendMessage,
        message_type: sendType,
      });
      toast(`SMS ${result.status} to ${result.recipient}`, 'success', 'SMS Sent');
      setSendMessage('');
      fetchLogs();
    } catch (err) {
      toast('Send failed: ' + err.message, 'error', 'Send Error');
    } finally {
      setSendLoading(false);
    }
  };

  /* ─── Broadcast ─── */
  const handleBroadcast = async (e) => {
    e.preventDefault();
    setBcLoading(true);
    try {
      const result = await api.broadcastSMS({
        message: bcMessage,
        district: bcDistrict || null,
        urgency: bcUrgency,
      });
      toast(result.message, 'success', 'Broadcast Sent');
      setBcMessage('');
      fetchLogs();
    } catch (err) {
      toast('Broadcast failed: ' + err.message, 'error', 'Broadcast Error');
    } finally {
      setBcLoading(false);
    }
  };

  /* ─────────────────────────────────────────────────────────────────────────
     RENDER
  ───────────────────────────────────────────────────────────────────────── */
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

      {/* ── Gateway Status Card ────────────────────────────────────────────── */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {gatewayStatus?.twilio_enabled
                ? <Wifi size={18} style={{ color: 'var(--accent-emerald)' }} />
                : <WifiOff size={18} style={{ color: 'var(--accent-amber)' }} />}
              SMS Gateway Status
            </h2>
            <p className="card-subtitle">
              {statusLoading ? 'Loading…' : gatewayStatus?.gateway_status}
            </p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => { fetchGatewayStatus(); fetchLogs(); }}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>

        {gatewayStatus && !statusLoading && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '14px' }}>
            {[
              { label: 'Mode', value: gatewayStatus.twilio_enabled ? '🔴 LIVE / Twilio' : '🟡 Simulation', highlight: gatewayStatus.twilio_enabled },
              { label: 'Carrier', value: gatewayStatus.active_carrier },
              { label: 'Inbound Received', value: gatewayStatus.total_inbound_processed },
              { label: 'Outbound Sent', value: gatewayStatus.total_outbound_sent },
              { label: 'Sent via Twilio', value: gatewayStatus.sent_count ?? 0 },
              { label: 'Simulated', value: gatewayStatus.simulated_count ?? 0 },
              { label: 'Failed', value: gatewayStatus.failed_count ?? 0 },
              { label: 'Active SOS', value: gatewayStatus.active_emergency_alerts },
              { label: 'Success Rate', value: `${gatewayStatus.delivery_success_rate}%` },
            ].map((stat, i) => (
              <div key={i} style={{
                backgroundColor: 'var(--bg-secondary)',
                borderRadius: 'var(--radius-md)',
                padding: '12px 14px',
                border: '1px solid var(--border-subtle)',
              }}>
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>{stat.label.toUpperCase()}</p>
                <p style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)', wordBreak: 'break-word' }}>
                  {stat.value}
                </p>
              </div>
            ))}
          </div>
        )}

        {!gatewayStatus?.twilio_enabled && (
          <div style={{
            marginTop: '14px',
            padding: '10px 14px',
            backgroundColor: 'var(--accent-amber-subtle)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid hsla(38, 92%, 50%, 0.25)',
            fontSize: '0.82rem',
            color: 'var(--accent-amber)',
          }}>
            <strong>⚠ Simulation Mode:</strong> Real SMS is not being sent.
            To activate Twilio, set <code>TWILIO_ENABLED=true</code> in <code>backend/.env</code> and fill in your Twilio credentials.
            Get your free credentials at <strong>console.twilio.com</strong>.
          </div>
        )}
      </div>

      {/* ── Two columns: Simulate & Quick Messages ─────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>

        {/* Simulate Inbound */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title" style={{ fontSize: '1rem' }}>
                <PhoneCall size={16} style={{ display: 'inline', marginRight: '6px', color: 'var(--accent-rose)' }} />
                Simulate Inbound SMS
              </h3>
              <p className="card-subtitle">Test emergency message parsing without a SIM card</p>
            </div>
          </div>

          {/* Quick example buttons */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '14px' }}>
            {QUICK_MSGS.map((q) => (
              <button
                key={q.label}
                className="btn btn-secondary btn-sm"
                style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                onClick={() => setSimMessage(q.msg)}
              >
                {q.label}
              </button>
            ))}
          </div>

          <form onSubmit={handleSimulate} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="form-group">
              <label className="form-label">Sender Phone (E.164)</label>
              <input
                type="text"
                className="form-input"
                value={simSender}
                onChange={(e) => setSimSender(e.target.value)}
                placeholder="+94771234567"
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">SMS Message</label>
              <textarea
                className="form-textarea"
                rows="3"
                value={simMessage}
                onChange={(e) => setSimMessage(e.target.value)}
                placeholder="e.g. SOS 5 Ranala 4 Need insulin"
                required
              />
            </div>
            <button type="submit" className="btn btn-danger" disabled={simLoading}>
              {simLoading
                ? <><RefreshCw size={14} className="spin" /> Processing…</>
                : <><Radio size={14} /> Send Simulated SMS</>}
            </button>
          </form>

          {/* Result panel */}
          {simResult && (
            <div style={{
              marginTop: '14px',
              padding: '12px 14px',
              backgroundColor: 'var(--bg-secondary)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.82rem',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <IntentBadge intent={simResult.intent} />
                {simResult.sos_id && (
                  <span style={{ color: 'var(--accent-rose)', fontWeight: '700' }}>
                    SOS #{simResult.sos_id}
                  </span>
                )}
                {simResult.ml_priority_score && (
                  <span style={{ color: 'var(--accent-amber)', fontWeight: '700' }}>
                    Priority: {simResult.ml_priority_score}/100
                  </span>
                )}
                <StatusBadge status={simResult.sms_dispatch_status} />
              </div>
              <div style={{
                padding: '8px 10px',
                backgroundColor: 'var(--bg-card)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                fontFamily: 'monospace',
                fontSize: '0.8rem',
                color: 'var(--text-secondary)',
                lineHeight: '1.5',
              }}>
                {simResult.auto_reply_message}
              </div>
              <div style={{ marginTop: '8px', display: 'flex', gap: '16px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {simResult.extracted_district && <span>📍 {simResult.extracted_district}</span>}
                {simResult.affected_people > 0 && <span>👥 {simResult.affected_people} people</span>}
                {simResult.medical_needs && <span>🏥 {simResult.medical_needs.slice(0, 40)}</span>}
              </div>
            </div>
          )}
        </div>

        {/* Send Direct SMS */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title" style={{ fontSize: '1rem' }}>
                <Send size={16} style={{ display: 'inline', marginRight: '6px', color: 'var(--accent-blue)' }} />
                Send Direct SMS
              </h3>
              <p className="card-subtitle">Dispatch targeted outbound SMS to any number</p>
            </div>
          </div>
          <form onSubmit={handleSendDirect} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="form-group">
              <label className="form-label">Recipient Phone (E.164)</label>
              <input
                type="text"
                className="form-input"
                value={sendRecipient}
                onChange={(e) => setSendRecipient(e.target.value)}
                placeholder="+94771234567"
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Message Type</label>
              <select
                className="form-select"
                value={sendType}
                onChange={(e) => setSendType(e.target.value)}
              >
                <option value="SYSTEM_NOTIFICATION">System Notification</option>
                <option value="CAMP_ALERT">Camp Alert</option>
                <option value="EVACUATION_ORDER">Evacuation Order</option>
                <option value="MEDICAL_SUPPLY_ALERT">Medical Supply Alert</option>
                <option value="SOS_UPDATE">SOS Status Update</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Message</label>
              <textarea
                className="form-textarea"
                rows="4"
                value={sendMessage}
                onChange={(e) => setSendMessage(e.target.value)}
                placeholder="Type your outbound message…"
                maxLength={1600}
                required
              />
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', float: 'right' }}>
                {sendMessage.length}/1600
              </span>
            </div>
            <button type="submit" className="btn btn-primary" disabled={sendLoading}>
              {sendLoading
                ? <><RefreshCw size={14} className="spin" /> Sending…</>
                : <><Send size={14} /> Dispatch SMS</>}
            </button>
          </form>

          {/* Broadcast section */}
          <div style={{
            marginTop: '20px',
            paddingTop: '16px',
            borderTop: '1px solid var(--border-subtle)',
          }}>
            <h4 style={{ fontSize: '0.88rem', fontWeight: '700', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Activity size={14} style={{ color: 'var(--accent-rose)' }} />
              Emergency Broadcast
            </h4>
            <form onSubmit={handleBroadcast} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div className="form-group">
                  <label className="form-label">District (optional)</label>
                  <select className="form-select" value={bcDistrict} onChange={(e) => setBcDistrict(e.target.value)}>
                    <option value="">All Districts</option>
                    <option value="Colombo">Colombo</option>
                    <option value="Gampaha">Gampaha</option>
                    <option value="Nuwara Eliya">Nuwara Eliya</option>
                    <option value="Ratnapura">Ratnapura</option>
                    <option value="Kalutara">Kalutara</option>
                    <option value="Kandy">Kandy</option>
                    <option value="Badulla">Badulla</option>
                    <option value="Matara">Matara</option>
                    <option value="Galle">Galle</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Urgency</label>
                  <select className="form-select" value={bcUrgency} onChange={(e) => setBcUrgency(e.target.value)}>
                    <option value="CRITICAL">🔴 CRITICAL</option>
                    <option value="HIGH">🟠 HIGH</option>
                    <option value="MEDIUM">🟡 MEDIUM</option>
                    <option value="LOW">🟢 LOW</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Alert Message</label>
                <textarea
                  className="form-textarea"
                  rows="2"
                  value={bcMessage}
                  onChange={(e) => setBcMessage(e.target.value)}
                  placeholder="e.g. Evacuate immediately — Kelani River flood level CRITICAL"
                  maxLength={500}
                  required
                />
              </div>
              <button type="submit" className="btn btn-danger" disabled={bcLoading}>
                {bcLoading
                  ? <><RefreshCw size={14} className="spin" /> Broadcasting…</>
                  : <><ShieldAlert size={14} /> Broadcast Emergency Alert</>}
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* ── SMS Transaction Logs ───────────────────────────────────────────── */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">
              <MessageSquare size={16} style={{ display: 'inline', marginRight: '6px' }} />
              SMS Transaction Logs
            </h3>
            <p className="card-subtitle">Showing {logs.length} records — most recent first</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <select className="form-select" style={{ width: '130px' }} value={dirFilter} onChange={(e) => setDirFilter(e.target.value)}>
              <option value="">All Direction</option>
              <option value="inbound">Inbound</option>
              <option value="outbound">Outbound</option>
            </select>
            <select className="form-select" style={{ width: '140px' }} value={statusLogFilter} onChange={(e) => setStatusLogFilter(e.target.value)}>
              <option value="">All Status</option>
              <option value="sent">Sent</option>
              <option value="simulated">Simulated</option>
              <option value="failed">Failed</option>
              <option value="received">Received</option>
              <option value="processed">Processed</option>
            </select>
            <select className="form-select" style={{ width: '100px' }} value={logsLimit} onChange={(e) => setLogsLimit(Number(e.target.value))}>
              <option value={25}>25 rows</option>
              <option value={50}>50 rows</option>
              <option value={100}>100 rows</option>
              <option value={200}>200 rows</option>
            </select>
            <button className="btn btn-secondary btn-sm" onClick={fetchLogs}>
              <RefreshCw size={14} />
            </button>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                {['#', 'Dir', 'From', 'To', 'Intent', 'Message', 'SOS', 'Status', 'Provider', 'Time'].map((h) => (
                  <th key={h} style={{ padding: '8px 10px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: '600', fontSize: '0.72rem', whiteSpace: 'nowrap' }}>
                    {h.toUpperCase()}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {logsLoading ? (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                    Loading SMS logs…
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                    No SMS logs found. Use the Simulate tool above to generate some.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr
                    key={log.id}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      backgroundColor: log.direction === 'inbound' ? 'transparent' : 'var(--bg-secondary)',
                    }}
                  >
                    <td style={{ padding: '8px 10px', fontWeight: '700', color: 'var(--text-muted)' }}>
                      #{log.id}
                    </td>
                    <td style={{ padding: '8px 10px' }}>
                      <span style={{
                        fontSize: '0.7rem',
                        fontWeight: '700',
                        color: log.direction === 'inbound' ? 'var(--accent-blue)' : 'var(--accent-emerald)',
                      }}>
                        {log.direction === 'inbound' ? '↓ IN' : '↑ OUT'}
                      </span>
                    </td>
                    <td style={{ padding: '8px 10px', fontFamily: 'monospace', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                      {log.sender}
                    </td>
                    <td style={{ padding: '8px 10px', fontFamily: 'monospace', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                      {log.recipient}
                    </td>
                    <td style={{ padding: '8px 10px' }}>
                      <IntentBadge intent={log.parsed_intent || log.message_type} />
                    </td>
                    <td style={{ padding: '8px 10px', maxWidth: '260px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-primary)' }}>
                      {log.message_text}
                    </td>
                    <td style={{ padding: '8px 10px', color: 'var(--accent-rose)', fontWeight: '700' }}>
                      {log.sos_request_id ? `#${log.sos_request_id}` : '—'}
                    </td>
                    <td style={{ padding: '8px 10px' }}>
                      <StatusBadge status={log.status} />
                    </td>
                    <td style={{ padding: '8px 10px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      {log.gateway_provider}
                    </td>
                    <td style={{ padding: '8px 10px', fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {new Date(log.created_at).toLocaleTimeString()}<br />
                      <span style={{ fontSize: '0.68rem' }}>{new Date(log.created_at).toLocaleDateString()}</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
