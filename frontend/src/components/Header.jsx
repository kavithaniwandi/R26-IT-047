import React, { useState, useEffect } from 'react';
import { 
  UserCheck, 
  RefreshCw, 
  Radio, 
  Search, 
  Volume2, 
  VolumeX, 
  Clock, 
  ShieldAlert, 
  AlertTriangle,
  Sparkles,
  ChevronRight,
  Menu
} from 'lucide-react';
import { PORTAL_CONFIG } from '../portalConfig';

export function Header({
  title,
  subtitle,
  portalId,
  onRefresh,
  isRefreshing,
  user,
  onSwitchUserClick,
  onOpenCommandPalette,
  onToggleSidebar,
  soundEnabled,
  onToggleSound
}) {
  const [timeString, setTimeString] = useState('');
  const [timeZoneString, setTimeZoneString] = useState('LK (UTC+5:30)');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const options = {
        timeZone: 'Asia/Colombo',
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      };
      try {
        const formatted = new Intl.DateTimeFormat('en-GB', options).format(now);
        setTimeString(formatted);
      } catch {
        setTimeString(now.toTimeString().split(' ')[0]);
      }
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const portalInfo = PORTAL_CONFIG[portalId] || PORTAL_CONFIG.admin;

  return (
    <header className="top-header">
      {/* Left side: Hamburger (for mobile/toggle), Portal Breadcrumb & Title */}
      <div className="header-left">
        <button
          className="header-icon-btn sidebar-toggle-btn"
          onClick={onToggleSidebar}
          title="Toggle Sidebar Navigation"
          aria-label="Toggle Sidebar"
        >
          <Menu size={19} />
        </button>

        <div className="header-title-area">
          <div className="header-breadcrumbs">
            <span className="breadcrumb-portal-tag" style={{
              backgroundColor: `var(--accent-${portalInfo.color}-subtle)`,
              color: `var(--accent-${portalInfo.color})`,
              border: `1px solid hsla(var(--accent-${portalInfo.color}), 0.3)`
            }}>
              {portalInfo.badge}
            </span>
            <ChevronRight size={13} className="breadcrumb-separator" />
            <span className="breadcrumb-current-name">{portalInfo.name}</span>
          </div>
          <h1 className="header-title">{title}</h1>
          {subtitle && <p className="header-subtitle">{subtitle}</p>}
        </div>
      </div>

      {/* Center/Right side: Live Status Telemetry, Clock, Command Search & Actions */}
      <div className="header-actions">
        {/* Live SL Clock widget */}
        <div className="header-clock-widget" title="Live Sri Lanka Emergency Dispatch Time">
          <Clock size={14} className="clock-icon" />
          <span className="clock-digits font-mono">{timeString || '00:00:00'}</span>
          <span className="clock-tz">{timeZoneString}</span>
        </div>

        {/* Global Command Palette search button */}
        <button
          className="header-search-trigger"
          onClick={onOpenCommandPalette}
          title="Search Command Palette (Ctrl+K)"
        >
          <Search size={14} />
          <span className="search-trigger-text">Quick Search...</span>
          <span className="search-trigger-kbd">⌘K</span>
        </button>

        {/* Sound toggle button */}
        <button
          className={`header-icon-btn ${soundEnabled ? 'active-audio' : ''}`}
          onClick={onToggleSound}
          title={soundEnabled ? 'Mute Alert Sound Effects' : 'Enable Alert Sound Effects'}
          aria-label="Toggle Audio"
        >
          {soundEnabled ? <Volume2 size={16} style={{ color: 'var(--accent-amber)' }} /> : <VolumeX size={16} style={{ color: 'var(--text-muted)' }} />}
        </button>

        {/* Sync button */}
        <button
          className="btn btn-secondary btn-sm sync-btn"
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Refresh Real-Time Data from FastAPI Cloud"
        >
          <RefreshCw size={14} className={isRefreshing ? 'spin' : ''} />
          <span className="sync-text">{isRefreshing ? 'Syncing...' : 'Sync Live'}</span>
        </button>

        {/* User profile / Switch account button */}
        <button
          className="btn btn-secondary btn-sm user-switch-btn"
          onClick={onSwitchUserClick}
          title="Switch Stakeholder Role / Account"
        >
          <div className="user-switch-avatar" style={{
            backgroundColor: `var(--accent-${portalInfo.color}-subtle)`,
            color: `var(--accent-${portalInfo.color})`
          }}>
            <UserCheck size={14} />
          </div>
          <div className="user-switch-label">
            <span className="user-switch-role">{user?.role?.toUpperCase() || 'SWITCH ROLE'}</span>
          </div>
        </button>
      </div>
    </header>
  );
}
