import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  ShieldAlert,
  Activity,
  HeartHandshake,
  Truck,
  ShieldCheck,
  MapPin,
  Tent,
  Users,
  Bell,
  BarChart3,
  Layers
} from "lucide-react";
import { PORTAL_CONFIG } from "../portalConfig";

export function CommandPalette({
  isOpen,
  onClose,
  onSelectPortal,
  onSelectTab,
  onOpenLoginModal,
  onToggleSound,
  soundEnabled
}) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  const items = [
    // Dedicated Portals
    {
      category: 'Dedicated Portals',
      id: 'portal-home',
      title: 'National Disaster Relief Public Home',
      subtitle: 'Public overview, emergency distress beacon & live GIS map',
      icon: Layers,
      color: 'blue',
      action: () => { onSelectPortal('home'); onClose(); }
    },
    {
      category: 'Dedicated Portals',
      id: 'portal-admin',
      title: 'Admin Command Center',
      subtitle: `Port :${PORTAL_CONFIG.admin.port} · National triage orchestration`,
      icon: ShieldCheck,
      color: 'rose',
      action: () => { onSelectPortal('admin'); onSelectTab('overview'); onClose(); }
    },
    {
      category: 'Dedicated Portals',
      id: 'portal-victim',
      title: 'Victim Emergency SOS Portal',
      subtitle: `Port :${PORTAL_CONFIG.victim.port} · Satellite GPS & SOS submission`,
      icon: ShieldAlert,
      color: 'rose',
      action: () => { onSelectPortal('victim'); onClose(); }
    },
    {
      category: 'Dedicated Portals',
      id: 'portal-authority',
      title: 'Medical Authority Console (MOH)',
      subtitle: `Port :${PORTAL_CONFIG.authority.port} · Camp approvals & epidemic surveillance`,
      icon: Activity,
      color: 'blue',
      action: () => { onSelectPortal('authority'); onClose(); }
    },
    {
      category: 'Dedicated Portals',
      id: 'portal-donor',
      title: 'Relief Donor Marketplace',
      subtitle: `Port :${PORTAL_CONFIG.donor.port} · Demand-driven supplies & pledges`,
      icon: HeartHandshake,
      color: 'emerald',
      action: () => { onSelectPortal('donor'); onClose(); }
    },
    {
      category: 'Dedicated Portals',
      id: 'portal-volunteer',
      title: 'Field Volunteer Dispatch',
      subtitle: `Port :${PORTAL_CONFIG.volunteer.port} · On-ground rescue missions`,
      icon: Truck,
      color: 'amber',
      action: () => { onSelectPortal('volunteer'); onClose(); }
    },
    {
      category: 'Dedicated Portals',
      id: 'portal-volunteer-dashboard',
      title: 'Volunteer Field Command Dashboard',
      subtitle: `Port :${PORTAL_CONFIG.volunteer_dash.port} · Shelter population and relief requests`,
      icon: Layers,
      color: 'amber',
      action: () => { onSelectPortal('volunteer_dash'); onClose(); }
    },
    {
      category: 'Dedicated Portals',
      id: 'portal-disaster-officer',
      title: 'Disaster Officer Portal',
      subtitle: `Port :${PORTAL_CONFIG.disaster_officer?.port || 5179} · Camp triage, MO routing & patient severity queue`,
      icon: Shield,
      color: 'blue',
      action: () => { onSelectPortal('disaster_officer'); onClose(); }
    },
    {
      category: 'Dedicated Portals',
      id: 'portal-disaster-donation',
      title: 'Disaster Donation Hub',
      subtitle: `Port :${PORTAL_CONFIG.disaster_donation?.port || 5180} · Medical appeals, inventory shortages & public pledges`,
      icon: Gift,
      color: 'emerald',
      action: () => { onSelectPortal('disaster_donation'); onClose(); }
    },

    // Admin Console Views
    {
      category: 'Command Center Views',
      id: 'tab-overview',
      title: 'Executive Situational Overview',
      subtitle: 'KPIs, live interactive map & critical triage queue',
      icon: Activity,
      color: 'blue',
      action: () => { onSelectPortal('admin'); onSelectTab('overview'); onClose(); }
    },
    {
      category: 'Command Center Views',
      id: 'tab-analytics',
      title: 'ML Intelligence Analytics Dashboard',
      subtitle: 'Epidemic outbreak, camp placement & demand forecasting',
      icon: BarChart3,
      color: 'violet',
      action: () => { onSelectPortal('admin'); onSelectTab('analytics'); onClose(); }
    },
    {
      category: 'Command Center Views',
      id: 'tab-sos',
      title: 'SOS Alerts & Triage Queue',
      subtitle: 'Model 4 Urgency Scoring and dispatch status',
      icon: ShieldAlert,
      color: 'rose',
      action: () => { onSelectPortal('admin'); onSelectTab('sos'); onClose(); }
    },
    {
      category: 'Command Center Views',
      id: 'tab-heatmap',
      title: 'Geospatial Hazard Heatmap & GIS',
      subtitle: 'Kelani basin flood & Nuwara Eliya landslide zones',
      icon: Layers,
      color: 'blue',
      action: () => { onSelectPortal('admin'); onSelectTab('heatmap'); onClose(); }
    },
    {
      category: 'Command Center Views',
      id: 'tab-camps',
      title: 'Medical Relief Camps Hub',
      subtitle: 'Model 3 spatial suitability scoring and camp reviews',
      icon: Tent,
      color: 'blue',
      action: () => { onSelectPortal('admin'); onSelectTab('camps'); onClose(); }
    },
    {
      category: 'Command Center Views',
      id: 'tab-donations',
      title: 'Supply Shortages & Donor Matching',
      subtitle: 'Priority medical requirements and verified pledges',
      icon: HeartHandshake,
      color: 'emerald',
      action: () => { onSelectPortal('admin'); onSelectTab('donations'); onClose(); }
    },
    {
      category: 'Command Center Views',
      id: 'tab-donation-appeal',
      title: 'Donation Appeal Studio',
      subtitle: 'Generate donor-facing appeal copy and open the analyzer',
      icon: Sparkles,
      color: 'emerald',
      action: () => { navigate('/donation-appeal'); onClose(); }
    },
    {
      category: 'Command Center Views',
      id: 'tab-users',
      title: 'Stakeholder User Directory',
      subtitle: '5-Role RBAC authorization & permissions',
      icon: Users,
      color: 'blue',
      action: () => { onSelectPortal('admin'); onSelectTab('users'); onClose(); }
    },
    {
      category: 'Command Center Views',
      id: 'tab-notifications',
      title: 'Multi-Channel Alert Audit Trail',
      subtitle: 'Logged SMS and emergency transmissions',
      icon: Bell,
      color: 'amber',
      action: () => { onSelectPortal('admin'); onSelectTab('notifications'); onClose(); }
    },

    // Quick System Actions
    {
      category: 'Quick Actions',
      id: 'action-switch-user',
      title: 'Switch Stakeholder Account',
      subtitle: '1-Click demo authentication for Admin, MOH, Donor, Volunteer, Victim',
      icon: UserCheck,
      color: 'blue',
      action: () => { onClose(); onOpenLoginModal(); }
    },
    {
      category: 'Quick Actions',
      id: 'action-toggle-audio',
      title: soundEnabled ? 'Mute Audio Alert Sound' : 'Enable Emergency Audio Beeps',
      subtitle: soundEnabled ? 'Disable tactical audio chimes' : 'Enable synthesized mission-control sound effects',
      icon: soundEnabled ? VolumeX : Volume2,
      color: 'amber',
      action: () => { onToggleSound(); onClose(); }
    }
  ];

  const filteredItems = items.filter((item) => {
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return (
      item.title.toLowerCase().includes(q) ||
      item.subtitle.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q)
    );
  });

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onClose();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % (filteredItems.length || 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + (filteredItems.length || 1)) % (filteredItems.length || 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredItems[selectedIndex]) {
        filteredItems[selectedIndex].action();
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="command-palette-backdrop" onClick={onClose} onKeyDown={handleKeyDown}>
      <div className="command-palette-modal" onClick={(e) => e.stopPropagation()}>
        {/* Search Bar Input */}
        <div className="command-palette-input-wrap">
          <Search size={20} className="command-palette-search-icon" />
          <input
            ref={inputRef}
            type="text"
            className="command-palette-input"
            placeholder="Search portals, tabs, ML models, or actions... (Esc to exit)"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0); }}
          />
          {query && (
            <button className="command-palette-clear-btn" onClick={() => setQuery('')}>
              <X size={16} />
            </button>
          )}
          <span className="command-palette-badge">ESC</span>
        </div>

        {/* Results List */}
        <div className="command-palette-results">
          {filteredItems.length > 0 ? (
            filteredItems.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  className={`command-palette-item ${isSelected ? 'selected' : ''}`}
                  onClick={item.action}
                  onMouseEnter={() => setSelectedIndex(idx)}
                >
                  <div
                    className="command-palette-item-icon"
                    style={{
                      backgroundColor: `var(--accent-${item.color}-subtle)`,
                      color: `var(--accent-${item.color})`
                    }}
                  >
                    <Icon size={18} />
                  </div>
                  <div className="command-palette-item-text">
                    <div className="command-palette-item-title-row">
                      <span className="command-palette-item-title">{item.title}</span>
                      <span className="command-palette-item-category">{item.category}</span>
                    </div>
                    <span className="command-palette-item-sub">{item.subtitle}</span>
                  </div>
                  <ArrowRight size={14} className="command-palette-arrow" />
                </div>
              );
            })
          ) : (
            <div className="command-palette-empty">
              <Sparkles size={28} style={{ color: 'var(--text-muted)', marginBottom: '8px' }} />
              <p>No commands or navigation items found matching "{query}".</p>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Try searching for "SOS", "Admin", "MOH", "Map", or "ML"</span>
            </div>
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="command-palette-footer">
          <div className="command-palette-shortcuts">
            <span><kbd>&uarr;</kbd><kbd>&darr;</kbd> Navigate</span>
            <span><kbd>&crarr;</kbd> Select</span>
            <span><kbd>ESC</kbd> Close</span>
          </div>
          <span className="command-palette-brand">Disaster Relief Command Telemetry</span>
        </div>
      </div>
    </div>
  );
}
