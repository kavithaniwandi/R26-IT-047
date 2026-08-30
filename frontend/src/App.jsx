import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import { Header } from './components/Header';
import { LoginModal } from './components/LoginModal';
import { CommandPalette } from './components/CommandPalette';
import { ToastContainer } from './components/Toast';

// Views
import { OverviewView } from './views/OverviewView';
import { UsersView } from './views/UsersView';
import { SOSView } from './views/SOSView';
import { HeatmapView } from './views/HeatmapView';
import { CampsView } from './views/CampsView';
import { DonationsView } from './views/DonationsView';
import { NotificationsView } from './views/NotificationsView';
import { AnalyticsDashboardView } from './views/AnalyticsDashboardView';
import { VolunteerDashboardView } from './views/VolunteerDashboardView';
import { DisasterOfficerDashboardView } from './views/DisasterOfficerDashboardView';
import { DisasterDonationRequestView } from './views/DisasterDonationRequestView';

// Specialized Stakeholder Portals
import { HomeView } from './views/HomeView';
import { VictimPortalView } from './views/VictimPortalView';
import { AuthorityPortalView } from './views/AuthorityPortalView';
import { DonorPortalView } from './views/DonorPortalView';
import { VolunteerPortalView } from './views/VolunteerPortalView';

// Public and specialized workflow pages
import Home from './pages/Home';
import Map from './pages/Map';
import Donations from './pages/Donations';
import Contacts from './pages/Contacts';
import SignIn from './pages/SignIn';
import SOS from './pages/SOS';
import Profile from './pages/Profile';
import Donation_Appeal from './pages/Donation_Appeal';
import DonationAppealAnalyzer from './pages/DonationAppealAnalyzer';
import CampSetup from './pages/CampSetup';
import PriorityApplication from './pages/PriorityApplication';
import PriorityQueue from './pages/PriorityQueue';
import { AuthProvider } from './context/AuthContext';

import { api, getStoredUser, removeAuthToken, setAuthToken, setStoredUser } from './api';
import { PORTAL_CONFIG, detectCurrentPortal } from './portalConfig';
import {
  playEmergencyBeep,
  playSuccessChime,
  playNotificationPing,
  toggleSound,
  isSoundEnabled
} from './utils/audioAlert';
import { Radio } from 'lucide-react';

function DashboardApp() {
  const [currentPortal, setCurrentPortal] = useState(() => detectCurrentPortal());
  const [currentTab, setCurrentTab] = useState('overview');
  const [user, setUser] = useState(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [soundActive, setSoundActive] = useState(() => isSoundEnabled());
  const [toasts, setToasts] = useState([]);
  const [stats, setStats] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Toast Management helper
  const addToast = useCallback((message, type = 'info', title = null) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type, title }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Audio Toggle
  const handleToggleSound = () => {
    const newState = toggleSound();
    setSoundActive(newState);
    if (newState) {
      playNotificationPing();
      addToast('Emergency sound alerts enabled', 'info', 'Audio Active');
    } else {
      addToast('Audio alert effects muted', 'info', 'Audio Muted');
    }
  };

  // Keyboard shortcut for Command Palette (Ctrl+K or Cmd+K)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setShowCommandPalette((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Auto-login with role matching detected portal
  useEffect(() => {
    const initSession = async () => {
      const stored = getStoredUser();
      const detected = detectCurrentPortal();
      const portalConfig = PORTAL_CONFIG[detected] || PORTAL_CONFIG.admin;

      if (stored && stored.role === portalConfig.defaultRole) {
        setUser(stored);
        fetchStats();
      } else {
        try {
          const res = await api.login(portalConfig.defaultEmail, portalConfig.defaultPassword);
          setAuthToken(res.access_token);
          const me = await api.getMe();
          setStoredUser(me);
          setUser(me);
          fetchStats();
        } catch {
          setShowLoginModal(true);
        }
      }
    };
    initSession();
  }, [currentPortal]);

  const fetchStats = async () => {
    setIsRefreshing(true);
    try {
      const data = await api.getAdminStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleLogout = () => {
    removeAuthToken();
    setUser(null);
    setShowLoginModal(true);
    addToast('Signed out of active session.', 'info', 'Logged Out');
  };

  const handleLoginSuccess = (loggedInUser) => {
    setUser(loggedInUser);
    playSuccessChime();
    addToast(`Authenticated as ${loggedInUser.full_name} (${loggedInUser.role.toUpperCase()})`, 'success', 'Login Verified');

    if (loggedInUser.role === 'victim') setCurrentPortal('victim');
    else if (loggedInUser.role === 'authority') setCurrentPortal('authority');
    else if (loggedInUser.role === 'donor') setCurrentPortal('donor');
    else if (loggedInUser.role === 'volunteer') setCurrentPortal('volunteer');
    else setCurrentPortal('admin');

    fetchStats();
  };

  const handleResolveSOS = async (sosId, newStatus) => {
    try {
      await api.updateSOSStatus(sosId, newStatus);
      playSuccessChime();
      addToast(`SOS Beacon #${sosId} status updated to '${newStatus}'.`, 'success', 'Triage Complete');
      fetchStats();
    } catch (err) {
      playEmergencyBeep();
      addToast('Error updating SOS: ' + err.message, 'error', 'Action Failed');
    }
  };

  const getPortalTitle = () => {
    switch (currentPortal) {
      case 'victim':
        return { 
          title: 'Victim & Public Emergency SOS Portal', 
          sub: `Dedicated Port :${PORTAL_CONFIG.victim.port} - Satellite GPS Telemetry & Multi-Channel Alert Dispatch`
        };
      case 'authority':
        return { 
          title: 'Medical Authority Command Console', 
          sub: `Dedicated Port :${PORTAL_CONFIG.authority.port} - Ministry of Health (MOH): Triage, Camp Approval & ML Analytics`
        };
      case 'donor':
        return { 
          title: 'Relief Donor & Supply Matching Marketplace', 
          sub: `Dedicated Port :${PORTAL_CONFIG.donor.port} - Priority Medical Demands & Verified Pledges`
        };
      case 'volunteer':
        return { 
          title: 'Field Volunteer & Rapid Responder Client', 
          sub: `Dedicated Port :${PORTAL_CONFIG.volunteer.port} - On-Ground Rescue Missions & GPS Navigation`
        };
      case 'officer_dash':
        return {
          title: 'Disaster Officer Command Console',
          sub: `Dedicated Port :${PORTAL_CONFIG.officer_dash.port} · Verify incoming donor supplies & trigger AI-targeted outreach`
        };
      case 'donation_req_dash':
        return {
          title: 'Disaster Donation Requests Manager',
          sub: `Dedicated Port :${PORTAL_CONFIG.donation_req_dash.port} · Coordinate population crowd estimation & supply requests`
        };
      default:
        switch (currentTab) {
          case 'overview': return { title: 'Executive Disaster Relief Command Center', sub: `Dedicated Port :${PORTAL_CONFIG.admin.port} - National Triage & Resource Allocation` };
          case 'sos': return { title: 'Emergency SOS Incident Triage Queue', sub: 'Real-Time Alert Dispatch & Model 4 Urgency Scoring' };
          case 'heatmap': return { title: 'Geospatial Hazard Heatmap & ML Inference', sub: 'Kelani Basin Flood & Nuwara Eliya Landslide Predictors' };
          case 'camps': return { title: 'Temporary Medical Camps Planning Hub', sub: 'Model 3 Spatial Suitability Scoring & Official Approvals' };
          case 'donations': return { title: 'Demand-Driven Smart Donation Matching', sub: 'Priority-Ranked Medical Requirements & Pledges' };
          case 'users': return { title: 'Stakeholder Role & Access Control Directory', sub: '5-Role Claims-Based Authorization Management' };
          case 'notifications': return { title: 'Multi-Channel Alert Dispatch Audit Trail', sub: 'Logged SMS Broadcasts & Emergency Transmissions' };
          case 'analytics': return { title: 'Predictive ML Intelligence Dashboard', sub: '4 Machine Learning Models: Outbreak, Camps, Demands & Urgency' };
          default: return { title: 'Admin Command Panel', sub: 'Disaster Relief System' };
        }
    }
  };

  const { title, sub } = getPortalTitle();

  return (
    <div className="app-container">
      {/* 0. Home / Landing Page */}
      {currentPortal === 'home' ? (
        <main className="main-content" style={{ width: '100%' }}>
          <HomeView
            onSelectPortal={(p) => {
              setCurrentPortal(p);
              playNotificationPing();
            }}
            onOpenLoginModal={() => setShowLoginModal(true)}
            onAddToast={addToast}
          />
        </main>
      ) : currentPortal === 'victim' ? (
        /* 1. Victim Portal (Dedicated Public Emergency Mode - Isolated from Admin UI) */
        <main className="main-content" style={{ width: '100%' }}>
          <VictimPortalView
            user={user}
            onAddToast={addToast}
            onReturnToAdmin={() => setCurrentPortal('admin')}
          />
        </main>
      ) : (
        <>
          {/* Collapsible Left Navigation Sidebar for Admin / Authorities */}
          <Sidebar
            currentPortal={currentPortal}
            setPortal={(p) => {
              setCurrentPortal(p);
              playNotificationPing();
            }}
            currentTab={currentTab}
            setTab={(t) => {
              setCurrentTab(t);
              playNotificationPing();
            }}
            user={user}
            onLogout={handleLogout}
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
          />

          {/* Main Canvas Area */}
          <main className="main-content">
            {/* Top Emergency Situational Ticker */}
            <div className="emergency-broadcast-ticker">
              <div className="ticker-left">
                <span className="ticker-beacon">
                  <Radio size={12} />
                  <span>LIVE ADVISORY</span>
                </span>
                <span className="ticker-message">
                  Kelani River Basin Alert: Moderate Risk upstream - 14 Medical Camps active in Western & Central Provinces - Model 4 Urgency Triage Online
                </span>
              </div>
              <div className="ticker-stats">
                <div className="ticker-stat-item">
                  <span>Active SOS:</span>
                  <strong style={{ color: 'var(--accent-rose)' }}>{stats?.sos?.active ?? 0}</strong>
                </div>
                <div className="ticker-stat-item">
                  <span>Camps:</span>
                  <strong style={{ color: 'var(--accent-blue)' }}>{(stats?.camps?.approved ?? 0) + (stats?.camps?.operational ?? 0)}</strong>
                </div>
              </div>
            </div>

            {/* Global Mission Control Header */}
            <Header
              title={title}
              subtitle={sub}
              portalId={currentPortal}
              onRefresh={() => {
                fetchStats();
                playNotificationPing();
                addToast('Synchronized latest telemetry from FastAPI Cloud.', 'info', 'Telemetry Synced');
              }}
              isRefreshing={isRefreshing}
              user={user}
              onSwitchUserClick={() => setShowLoginModal(true)}
              onOpenCommandPalette={() => setShowCommandPalette(true)}
              onToggleSidebar={() => setIsSidebarCollapsed((prev) => !prev)}
              soundEnabled={soundActive}
              onToggleSound={handleToggleSound}
            />

            {/* Dynamic View Body */}
            <div className="view-body">
              {/* 2. Authority Portal */}
              {currentPortal === 'authority' && (
                <AuthorityPortalView currentUser={user} onAddToast={addToast} />
              )}

              {/* 3. Donor Portal */}
              {currentPortal === 'donor' && (
                <DonorPortalView currentUser={user} onAddToast={addToast} />
              )}

              {/* 4. Volunteer Portal */}
              {currentPortal === 'volunteer' && (
                <VolunteerPortalView currentUser={user} onAddToast={addToast} />
              )}

              {/* 5. Admin Portal Views */}
              {currentPortal === 'admin' && (
                <>
                  {currentTab === 'overview' && (
                    <OverviewView
                      stats={stats}
                      onNavigate={setCurrentTab}
                      onResolveSOS={handleResolveSOS}
                      onAddToast={addToast}
                    />
                  )}

                  {currentTab === 'sos' && (
                    <SOSView onAddToast={addToast} />
                  )}

                  {currentTab === 'heatmap' && (
                    <HeatmapView onAddToast={addToast} />
                  )}

                  {currentTab === 'camps' && (
                    <CampsView currentUser={user} onAddToast={addToast} />
                  )}

                  {currentTab === 'donations' && (
                    <DonationsView currentUser={user} onAddToast={addToast} />
                  )}

                  {currentTab === 'users' && (
                    <UsersView currentUser={user} onAddToast={addToast} />
                  )}

                  {currentTab === 'notifications' && (
                    <NotificationsView onAddToast={addToast} />
                  )}

                  {currentTab === 'analytics' && (
                    <AnalyticsDashboardView stats={stats} onAddToast={addToast} />
                  )}
                </>
              )}

              {/* 6. Volunteer Field Command Dashboard */}
              {currentPortal === 'volunteer_dash' && (
                <VolunteerDashboardView
                  currentUser={user}
                  onNavigate={(tab) => {
                    setCurrentPortal('admin');
                    setCurrentTab(tab);
                  }}
                  onAddToast={addToast}
                />
              )}

              {/* 7. Disaster Officer Console */}
              {currentPortal === 'officer_dash' && (
                <DisasterOfficerDashboardView
                  currentUser={user}
                  onAddToast={addToast}
                />
              )}

              {/* 8. Disaster Donation Requests Manager */}
              {currentPortal === 'donation_req_dash' && (
                <DisasterDonationRequestView
                  currentUser={user}
                  onAddToast={addToast}
                />
              )}
            </div>
          </main>
        </>
      )}

      {/* Stakeholder Login & Quick Role Switch Modal */}
      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onLoginSuccess={handleLoginSuccess}
      />

      {/* Global Command Palette (Ctrl+K) */}
      <CommandPalette
        isOpen={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
        onSelectPortal={setCurrentPortal}
        onSelectTab={setCurrentTab}
        onOpenLoginModal={() => setShowLoginModal(true)}
        onToggleSound={handleToggleSound}
        soundEnabled={soundActive}
      />

      {/* Global Toast Notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}

function SystemWorkflowShell({ children, title, subtitle }) {
  const navigate = useNavigate();
  const [currentPortal, setCurrentPortal] = useState('authority');
  const [currentTab, setCurrentTab] = useState('camps');
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [soundActive, setSoundActive] = useState(() => isSoundEnabled());
  const [toasts, setToasts] = useState([]);
  const user = getStoredUser() || {
    full_name: 'Dr. Nihal Jayasinghe (MOH Officer)',
    role: 'authority',
  };

  const addToast = useCallback((message, type = 'info', toastTitle = null) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type, title: toastTitle }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 4500);
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const handlePortalSelect = (portal) => {
    setCurrentPortal(portal);
    navigate('/');
  };

  const handleTabSelect = (tab) => {
    setCurrentPortal('admin');
    setCurrentTab(tab);
    navigate('/');
  };

  const handleToggleSound = () => {
    const nextState = toggleSound();
    setSoundActive(nextState);
    addToast(
      nextState ? 'Emergency sound alerts enabled' : 'Audio alert effects muted',
      'info',
      nextState ? 'Audio Active' : 'Audio Muted'
    );
  };

  return (
    <div className="app-container">
      <Sidebar
        currentPortal={currentPortal}
        setPortal={handlePortalSelect}
        currentTab={currentTab}
        setTab={handleTabSelect}
        user={user}
        onLogout={() => navigate('/')}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
      />
      <main className="main-content">
        <div className="emergency-broadcast-ticker">
          <div className="ticker-left">
            <span className="ticker-beacon">
              <Radio size={12} />
              <span>LIVE ADVISORY</span>
            </span>
            <span className="ticker-message">
              Medical camp severity queue setup - MO routing and patient triage session control
            </span>
          </div>
        </div>
        <Header
          title={title}
          subtitle={subtitle}
          portalId="authority"
          onRefresh={() => addToast('Camp severity workflow refreshed.', 'info', 'Workflow Synced')}
          isRefreshing={false}
          user={user}
          onSwitchUserClick={() => navigate('/')}
          onOpenCommandPalette={() => setShowCommandPalette(true)}
          onToggleSidebar={() => setIsSidebarCollapsed((prev) => !prev)}
          soundEnabled={soundActive}
          onToggleSound={handleToggleSound}
        />
        <div className="view-body">{children}</div>
      </main>
      <CommandPalette
        isOpen={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
        onSelectPortal={handlePortalSelect}
        onSelectTab={handleTabSelect}
        onOpenLoginModal={() => navigate('/')}
        onToggleSound={handleToggleSound}
        soundEnabled={soundActive}
      />
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<DashboardApp />} />
          <Route path="/home" element={<Home />} />
          <Route path="/map" element={<Map />} />
          <Route path="/donations" element={<Donations />} />
          <Route path="/contacts" element={<Contacts />} />
          <Route path="/signin" element={<SignIn />} />
          <Route path="/sos-public" element={<SOS />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/donation-appeal" element={<Donation_Appeal />} />
          <Route path="/donation-appeal-analyzer" element={<DonationAppealAnalyzer />} />
          <Route
            path="/camp-setup"
            element={
              <SystemWorkflowShell
                title="Camp Severity Queue Setup"
                subtitle="Activate a medical camp, register MOs, and open the severity triage workflow"
              >
                <CampSetup />
              </SystemWorkflowShell>
            }
          />
          <Route
            path="/priority-application"
            element={
              <SystemWorkflowShell
                title="Patient Severity Application"
                subtitle="Classify clinical notes, assign medical officers, and submit cases to the camp queue"
              >
                <PriorityApplication />
              </SystemWorkflowShell>
            }
          />
          <Route
            path="/priority-queue"
            element={
              <SystemWorkflowShell
                title="Camp Severity Queue"
                subtitle="Review assigned patient queues by medical officer and severity level"
              >
                <PriorityQueue />
              </SystemWorkflowShell>
            }
          />
          <Route path="*" element={<DashboardApp />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;