import React from 'react';
import { 
  ShieldAlert, 
  Activity, 
  Users, 
  MapPin, 
  Tent, 
  HeartHandshake, 
  Bell, 
  ShieldCheck,
  Truck, 
  Radio, 
  Server,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Cpu,
  Database,
  LayoutDashboard,
  Shield, 
  Gift,
  Building2,
  Target
} from 'lucide-react';
import { PORTAL_CONFIG } from '../portalConfig';

export function Sidebar({ 
  currentPortal, 
  setPortal, 
  currentTab, 
  setTab, 
  user, 
  onLogout,
  isCollapsed,
  onToggleCollapse
}) {
  const portals = [
    { id: 'admin', label: 'Admin Command', icon: ShieldCheck, color: 'rose', port: PORTAL_CONFIG.admin.port },
    { id: 'victim', label: 'Victim SOS Portal', icon: ShieldAlert, color: 'rose', port: PORTAL_CONFIG.victim.port },
    { id: 'authority', label: 'Medical Authority', icon: Activity, color: 'blue', port: PORTAL_CONFIG.authority.port },
    { id: 'volunteer', label: 'Volunteer Dispatch', icon: Truck, color: 'amber', port: PORTAL_CONFIG.volunteer.port },
    { id: 'volunteer_dash', label: 'Volunteer Dashboard', icon: LayoutDashboard, color: 'amber', port: PORTAL_CONFIG.volunteer_dash.port },
    { id: 'disaster_officer', label: 'Disaster Officer', icon: Shield, color: 'blue', port: PORTAL_CONFIG.disaster_officer.port },
    { id: 'donor_matching', label: 'Donor Matching', icon: Target, color: 'violet', port: PORTAL_CONFIG.donor_matching.port },
    { id: 'donor', label: 'Donor Donations', icon: HeartHandshake, color: 'emerald', port: PORTAL_CONFIG.donor.port },
    { id: 'disaster_donation', label: 'Disaster Donation', icon: Gift, color: 'emerald', port: PORTAL_CONFIG.disaster_donation.port },
    {
      id: 'relief-camps',
      label: 'Disaster Relief Camps',
      icon: Building2,
      color: 'amber',
      port: PORTAL_CONFIG.admin.port,
      targetPortal: 'admin',
      targetTab: 'relief-camps',
    },
  ];

  const visiblePortals = user?.role === 'admin'
    ? portals
    : portals.filter((portal) => (
        PORTAL_CONFIG[portal.id]?.defaultRole === user?.role
      ));

  const adminNavItems = [
    { id: 'overview', label: 'Executive Overview', icon: Activity, badge: null },
    { id: 'analytics', label: 'ML Analytics Engine', icon: BarChart3, badge: '4 Models', badgeColor: 'violet' },
    { id: 'sos', label: 'SOS Alerts & Triage', icon: ShieldAlert, badge: 'Live', badgeColor: 'rose' },
    { id: 'heatmap', label: 'GIS Hazard Heatmap', icon: MapPin, badge: null },
    { id: 'camps', label: 'Medical Camps Hub', icon: Tent, badge: null },
    { id: 'donations', label: 'Supply Matchmaking', icon: HeartHandshake, badge: null },
    { id: 'users', label: 'User RBAC Directory', icon: Users, badge: null },
    { id: 'notifications', label: 'Audit Log Trail', icon: Bell, badge: null },
    { id: 'sms', label: 'SMS Gateway', icon: Radio, badge: 'Twilio', badgeColor: 'rose' },
  ];

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      {/* Brand Header */}
      <div className="sidebar-header">
        <div className="brand-icon">
          <Radio size={20} />
        </div>
        {!isCollapsed && (
          <div className="brand-text-block">
            <div className="brand-title">DISASTER RELIEF</div>
            <div className="brand-subtitle">Smart Medical Cloud</div>
          </div>
        )}
        <button
          className="sidebar-collapse-btn"
          onClick={onToggleCollapse}
          title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          aria-label="Collapse Sidebar"
        >
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Scrollable Middle Body */}
      <div className="sidebar-middle-scroll">
        {/* Stakeholder Portals Section */}
        <div className="sidebar-section-container">
          {!isCollapsed && <span className="sidebar-section-title">Dedicated Portals</span>}
          <div className="portal-switch-group">
            {visiblePortals.map((p) => {
              const Icon = p.icon;
              const targetPortal = p.targetPortal || p.id;
              const isCurrent = p.targetTab
                ? currentPortal === targetPortal && currentTab === p.targetTab
                : currentPortal === targetPortal && !portals.some((candidate) => (
                  candidate.targetPortal === targetPortal && candidate.targetTab === currentTab
                ));
              return (
                <div
                  key={p.id}
                  className={`portal-btn ${isCurrent ? 'active' : ''}`}
                  onClick={() => {
                    setPortal(targetPortal);
                    if (p.targetTab) {
                      setTab(p.targetTab);
                    } else if (targetPortal === 'admin') {
                      setTab('overview');
                    }
                  }}
                  title={`${p.label} (Port :${p.port})`}
                >
                  <div
                    className="portal-btn-icon"
                    style={{
                      backgroundColor: `var(--accent-${p.color}-subtle)`,
                      color: `var(--accent-${p.color})`,
                      border: `1px solid hsla(var(--accent-${p.color}), 0.25)`
                    }}
                  >
                    <Icon size={15} />
                  </div>
                  {!isCollapsed && (
                    <div className="portal-btn-info">
                      <div className="portal-btn-label">{p.label}</div>
                      <div className="portal-btn-port font-mono">:{p.port}</div>
                    </div>
                  )}
                  {!isCollapsed && isCurrent && (
                    <div className="portal-active-indicator" style={{ backgroundColor: `var(--accent-${p.color})` }} />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Navigation Links (when in Admin mode or global nav) */}
        <div className="sidebar-nav-container">
          {currentPortal === 'admin' ? (
            <>
              {!isCollapsed && <span className="sidebar-section-title">Command Navigation</span>}
              <nav className="sidebar-nav">
                {adminNavItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = currentTab === item.id;
                  return (
                    <button
                      key={item.id}
                      className={`nav-item ${isActive ? 'active' : ''}`}
                      onClick={() => setTab(item.id)}
                      title={item.label}
                    >
                      <div className="nav-item-content">
                        <Icon size={17} />
                        {!isCollapsed && <span>{item.label}</span>}
                      </div>
                      {!isCollapsed && item.badge && (
                        <span className={`nav-badge ${item.badgeColor || 'blue'}`}>
                          {item.badge}
                        </span>
                      )}
                    </button>
                  );
                })}
              </nav>
            </>
          ) : null}
        </div>

        {/* System Telemetry Status Footer */}
        {!isCollapsed && (
          <div className="sidebar-telemetry-box">
            <div className="telemetry-header">
              <span className="telemetry-title">System Status</span>
              <span className="telemetry-live-badge">99.9% ONLINE</span>
            </div>
            <div className="telemetry-grid">
              <div className="telemetry-row">
                <span className="telemetry-label"><Server size={11} /> API Backend</span>
                <span className="telemetry-val font-mono" style={{ color: 'var(--accent-emerald)' }}>OK (14ms)</span>
              </div>
              <div className="telemetry-row">
                <span className="telemetry-label"><Cpu size={11} /> ML Engine</span>
                <span className="telemetry-val font-mono" style={{ color: 'var(--accent-violet)' }}>4/4 Active</span>
              </div>
              <div className="telemetry-row">
                <span className="telemetry-label"><Database size={11} /> DB Storage</span>
                <span className="telemetry-val font-mono" style={{ color: 'var(--accent-blue)' }}>SQLite GIS</span>
              </div>
            </div>
          </div>
        )}
      </div>

    </aside>
  );
}
