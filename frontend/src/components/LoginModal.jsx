import React, { useState } from 'react';
import { 
  X, 
  Lock, 
  Mail, 
  AlertCircle, 
  Shield, 
  CheckCircle2, 
  ShieldAlert, 
  Activity, 
  HeartHandshake, 
  Truck, 
  Sparkles,
  ArrowRight,
  KeyRound
} from 'lucide-react';
import { api, setAuthToken, setStoredUser } from '../api';

export function LoginModal({ isOpen, onClose, onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('quick'); // 'quick' or 'manual'

  if (!isOpen) return null;

  const presets = [
    {
      label: 'System Administrator',
      email: 'admin@disaster.relief.lk',
      pw: 'Admin@2026!',
      role: 'admin',
      badge: 'Full Command',
      desc: 'National emergency triage, 4 ML predictive pipelines, user RBAC orchestration.',
      icon: Shield,
      color: 'rose',
      port: 5173
    },
    {
      label: 'Medical Authority (MOH)',
      email: 'authority@moh.gov.lk',
      pw: 'Authority@2026!',
      role: 'authority',
      badge: 'MOH Health',
      desc: 'Medical camp spatial approvals, disease outbreak surveillance, and epidemic risk index.',
      icon: Activity,
      color: 'blue',
      port: 5175
    },
    {
      label: 'Relief Donor (Red Cross)',
      email: 'donor@redcross.lk',
      pw: 'Donor@2026!',
      role: 'donor',
      badge: 'Supply Pledges',
      desc: 'Demand-driven medical supply fulfillment, priority matching, and certified shipments.',
      icon: HeartHandshake,
      color: 'emerald',
      port: 5176
    },
    {
      label: 'Field Volunteer Dispatch',
      email: 'volunteer@relief.lk',
      pw: 'Volunteer@2026!',
      role: 'volunteer',
      badge: 'Rescue Missions',
      desc: 'On-ground disaster response, turn-by-turn routing, victim status verification.',
      icon: Truck,
      color: 'amber',
      port: 5177
    },
    {
      label: 'Disaster Victim (Public)',
      email: 'victim@kaduwela.lk',
      pw: 'Victim@2026!',
      role: 'victim',
      badge: 'Public SOS',
      desc: 'Instant GPS satellite distress beacons, nearby medical camp locator, safe shelters.',
      icon: ShieldAlert,
      color: 'rose',
      port: 5174
    },
  ];

  const handleInstantLogin = async (preset) => {
    setError(null);
    setLoading(true);
    try {
      const res = await api.login(preset.email, preset.pw);
      setAuthToken(res.access_token);
      const me = await api.getMe();
      setStoredUser(me);
      onLoginSuccess(me);
      onClose();
    } catch (err) {
      setError(err.message || 'Login failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await api.login(email, password);
      setAuthToken(res.access_token);
      const me = await api.getMe();
      setStoredUser(me);
      onLoginSuccess(me);
      onClose();
    } catch (err) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content auth-modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div className="brand-icon" style={{ width: '40px', height: '40px', borderRadius: 'var(--radius-md)' }}>
              <Lock size={20} />
            </div>
            <div>
              <h2 className="modal-title">Stakeholder Authentication</h2>
              <p className="card-subtitle">FastAPI JWT Role-Based Access Control (RBAC)</p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close">
            <X size={20} />
          </button>
        </div>

        {/* Mode Selector Tabs */}
        <div className="auth-tab-switch">
          <button
            className={`auth-tab-btn ${activeTab === 'quick' ? 'active' : ''}`}
            onClick={() => setActiveTab('quick')}
          >
            <Sparkles size={15} />
            <span>1-Click Stakeholder Switch</span>
          </button>
          <button
            className={`auth-tab-btn ${activeTab === 'manual' ? 'active' : ''}`}
            onClick={() => setActiveTab('manual')}
          >
            <KeyRound size={15} />
            <span>Manual Credentials</span>
          </button>
        </div>

        {error && (
          <div className="auth-error-banner">
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Tab 1: 1-Click Role Switch */}
        {activeTab === 'quick' && (
          <div className="auth-presets-container">
            <p className="auth-presets-help">
              Select any stakeholder role below to immediately authenticate and preview their dedicated portal:
            </p>
            <div className="auth-presets-grid">
              {presets.map((p) => {
                const Icon = p.icon;
                return (
                  <div
                    key={p.role}
                    className="auth-preset-card"
                    onClick={() => !loading && handleInstantLogin(p)}
                  >
                    <div className="auth-preset-top">
                      <div
                        className="auth-preset-icon"
                        style={{
                          backgroundColor: `var(--accent-${p.color}-subtle)`,
                          color: `var(--accent-${p.color})`,
                          border: `1px solid hsla(var(--accent-${p.color}), 0.3)`
                        }}
                      >
                        <Icon size={18} />
                      </div>
                      <div className="auth-preset-badge font-mono">
                        Port :{p.port}
                      </div>
                    </div>
                    <div className="auth-preset-name">{p.label}</div>
                    <p className="auth-preset-desc">{p.desc}</p>
                    <div className="auth-preset-footer">
                      <span className="auth-preset-email font-mono">{p.email}</span>
                      <div className="auth-preset-arrow">
                        <ArrowRight size={14} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Tab 2: Manual Credentials Form */}
        {activeTab === 'manual' && (
          <form onSubmit={handleManualSubmit} className="auth-form">
            <div className="form-group">
              <label className="form-label">
                <Mail size={14} />
                <span>Stakeholder Email Address</span>
              </label>
              <input
                type="email"
                required
                className="custom-input"
                placeholder="e.g. admin@disaster.relief.lk"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                <Lock size={14} />
                <span>Account Password</span>
              </label>
              <input
                type="password"
                required
                className="custom-input"
                placeholder="Enter password..."
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={onClose}
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? 'Authenticating...' : 'Sign In to Portal'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
