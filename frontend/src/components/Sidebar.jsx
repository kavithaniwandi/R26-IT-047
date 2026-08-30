import React from 'react';
import { 
  ShieldAlert, 
  Activity, 
  Users, 
  MapPin, 
  Tent, 
  HeartHandshake, 
  Bell, 
  LogOut, 
  ShieldCheck,
  Truck, 
  Radio, 
  ExternalLink,
  Sparkles,
  Server,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Cpu,
  Database,
  Home,
  LayoutDashboard
} from 'lucide-react';
import { PORTAL_CONFIG, getPortalUrl } from '../portalConfig';

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
    { id: 'home', label: 'Public Home', icon: Home, color: 'blue', port: PORTAL_CONFIG.home.port },
    { id: 'admin', label: 'Admin Command', icon: ShieldCheck, color: 'rose', port: PORTAL_CONFIG.admin.port },
    { id: 'victim', label: 'Victim SOS Portal', icon: ShieldAlert, color: 'rose', port: PORTAL_CONFIG.victim.port },
    { id: 'authority', label: 'Medical Authority', icon: Activity, color: 'blue', port: PORTAL_CONFIG.authority.port },
    { id: 'donor', label: 'Donor Marketplace', icon: HeartHandshake, color: 'emerald', port: PORTAL_CONFIG.donor.port },
    { id: 'volunteer', label: 'Volunteer Dispatch', icon: Truck, color: 'amber', port: PORTAL_CONFIG.volunteer.port },
    { id: 'volunteer_dash', label: 'Volunteer Dashboard', icon: LayoutDashboard, color: 'amber', port: PORTAL_CONFIG.volunteer_dash.port },
    { id: 'officer_dash', label: 'Disaster Officer', icon: ShieldCheck, color: 'blue', port: PORTAL_CONFIG.officer_dash.port },
    { id: 'donation_req_dash', label: 'Donation Requests', icon: HeartHandshake, color: 'rose', port: PORTAL_CONFIG.donation_req_dash.port },
  ];

  const adminNavItems = [
    { id: 'overview', label: 'Executive Overview', icon: Activity, badge: null },
    { id: 'analytics', label: 'ML Analytics Engine', icon: BarChart3, badge: '4 Models', badgeColor: 'violet' },
    { id: 'sos', label: 'SOS Alerts & Triage', icon: ShieldAlert, badge: 'Live', badgeColor: 'rose' },
    { id: 'heatmap', label: 'GIS Hazard Heatmap', icon: MapPin, badge: null },
    { id: 'camps', label: 'Medical Camps Hub', icon: Tent, badge: null },
    { id: 'donations', label: 'Supply Matchmaking', icon: HeartHandshake, badge: null },
    { id: 'users', label: 'User RBAC Directory', icon: Users, badge: null },
    { id: 'notifications', label: 'Audit Log Trail', icon: Bell, badge: null },
  ];

  const getRoleBadgeStyle = (role) => {
    switch (role) {
      case 'admin': return { bg: 'var(--accent-rose-subtle)', text: 'var(--accent-rose)', border: 'hsla(350, 89%, 60%, 0.35)' };
      case 'authority': return { bg: 'var(--accent-blue-subtle)', text: 'var(--accent-blue)', border: 'hsla(217, 91%, 60%, 0.35)' };
      case 'donor': return { bg: 'var(--accent-emerald-subtle)', text: 'var(--accent-emerald)', border: 'hsla(150, 84%, 42%, 0.35)' };
      case 'volunteer': return { bg: 'var(--accent-amber-subtle)', text: 'var(--accent-amber)', border: 'hsla(38, 92%, 50%, 0.35)' };
      case 'victim': return { bg: 'var(--accent-rose-subtle)', text: 'var(--accent-rose)', border: 'hsla(350, 89%, 60%, 0.35)' };
      default: return { bg: 'var(--border-subtle)', text: 'var(--text-secondary)', border: 'transparent' };
    }
  };

  const roleStyle = getRoleBadgeStyle(user?.role);

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

      {/* Stakeholder Portals Section */}
      <div className="sidebar-section-container">
        {!isCollapsed && <span className="sidebar-section-title">Dedicated Portals</span>}
        <div className="portal-switch-group">
          {portals.map((p) => {
            const Icon = p.icon;
            const isCurrent = currentPortal === p.id;
            return (
              <div
                key={p.id}
                className={`portal-btn ${isCurrent ? 'active' : ''}`}
                onClick={() => setPortal(p.id)}
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
        ) : (
          <div className="portal-side-banner">
            {!isCollapsed && (
              <div className="active-portal-info-box">
                <div className="active-portal-info-title">Active Dedicated Portal</div>
                <div className="active-portal-info-name">
                  {portals.find((p) => p.id === currentPortal)?.label}
                </div>
                <p className="active-portal-info-desc">
                  You are currently operating in the dedicated stakeholder interface.
                </p>
                <button
                  className="btn btn-secondary btn-sm"
                  style={{ width: '100%', marginTop: '12px' }}
                  onClick={() => setPortal('admin')}
                >
                  <ShieldCheck size={14} style={{ color: 'var(--accent-rose)' }} />
                  <span>Return to Admin</span>
                </button>
              </div>
            )}
          </div>
        )}
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

      {/* User Profile Card & Logout Footer */}
      <div className="sidebar-footer">
        <div className="user-profile-card">
          <div className="user-avatar" style={{
            background: roleStyle.bg,
            color: roleStyle.text,
            border: `1px solid ${roleStyle.border}`
          }}>
            {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
          </div>
          {!isCollapsed && (
            <div className="user-info">
              <div className="user-name" title={user?.full_name || 'Guest User'}>
                {user?.full_name || 'Guest User'}
              </div>
              <div
                className="user-role-tag"
                style={{
                  backgroundColor: roleStyle.bg,
                  color: roleStyle.text,
                  border: `1px solid ${roleStyle.border}`
                }}
              >
                {user?.role || 'Stakeholder'}
              </div>
            </div>
          )}
          <button
            className="sidebar-logout-btn"
            onClick={onLogout}
            title="Sign Out / Switch Stakeholder"
            aria-label="Sign Out"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}
