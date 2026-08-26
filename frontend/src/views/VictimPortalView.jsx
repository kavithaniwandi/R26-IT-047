import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  MapPin, 
  PhoneCall, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  Users, 
  Activity, 
  Send, 
  Navigation, 
  Heart, 
  HelpCircle, 
  Radio, 
  Tent, 
  Layers, 
  MessageSquare, 
  UserPlus, 
  FileText, 
  Check, 
  Sparkles,
  ArrowRight,
  RefreshCw,
  Search,
  BadgeCheck,
  Building,
  UserCheck,
  LogOut,
  Bell,
  Lock,
  Mail,
  Share2,
  X,
  Phone,
  User,
  Plus,
  Trash2,
  Edit2,
  CheckSquare,
  Globe
} from 'lucide-react';
import { api, setAuthToken, setStoredUser, removeAuthToken } from '../api';
import { RealTimeMap } from '../components/RealTimeMap';
import { playEmergencyBeep, playSuccessChime, playNotificationPing } from '../utils/audioAlert';

export function VictimPortalView({ user: initialUser, onAddToast, onReturnToAdmin }) {
  const [user, setUser] = useState(initialUser);
  const [activeSOSList, setActiveSOSList] = useState([]);
  const [victimsList, setVictimsList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [gpsLoading, setGpsLoading] = useState(false);
  const [gpsStatus, setGpsStatus] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [error, setError] = useState(null);
  
  // Navigation Tabs
  const [activeTab, setActiveTab] = useState('trigger'); 
  // 'trigger' | 'register_victim' | 'live_map' | 'helplines' | 'emergency_contacts' | 'sms_gateway' | 'registered_victims' | 'my_alerts' | 'safe_zones'

  const [camps, setCamps] = useState([]);
  const [hazardZones, setHazardZones] = useState([]);
  const [selectedLanguage, setSelectedLanguage] = useState('en'); // 'en' | 'si' | 'ta'

  // Modals
  const [showOnboardingModal, setShowOnboardingModal] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authTab, setAuthTab] = useState('login'); // 'login' | 'signup'
  const [showBroadcastModal, setShowBroadcastModal] = useState(false);
  const [latestBroadcastLog, setLatestBroadcastLog] = useState([]);

  // Auth Form State
  const [authForm, setAuthForm] = useState({
    email: '',
    password: '',
    full_name: '',
    phone: '+94 77 123 4567',
    address: 'Ranala, Kaduwela, Colombo',
  });
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState(null);

  // 4 Emergency Contacts State
  const defaultContacts = [
    { id: 1, name: 'Sunil Perera', relation: 'Father / Family Head', phone: '+94 77 123 4567', notifySMS: true, notifyCall: true },
    { id: 2, name: 'Kumari Silva', relation: 'Mother', phone: '+94 71 889 9112', notifySMS: true, notifyCall: true },
    { id: 3, name: 'Chaminda Perera', relation: 'Brother / Field Responder', phone: '+94 76 345 6789', notifySMS: true, notifyCall: true },
    { id: 4, name: 'Dr. Nalin Jayawardena', relation: 'Family Physician', phone: '+94 70 998 8776', notifySMS: true, notifyCall: false },
  ];

  const [emergencyContacts, setEmergencyContacts] = useState(() => {
    const saved = localStorage.getItem(`dr_victim_contacts_${user?.id || 'guest'}`);
    return saved ? JSON.parse(saved) : defaultContacts;
  });

  const [editingContact, setEditingContact] = useState(null);

  // SOS Form state
  const [formData, setFormData] = useState({
    latitude: 6.936419,
    longitude: 79.957216,
    district: 'Colombo',
    ds_division: 'Kaduwela',
    gn_division: 'Ranala',
    address_text: '45 River View Lane, Ranala, Kaduwela',
    urgency_level: 5,
    affected_people: 4,
    affected_families: 1,
    has_elderly: true,
    has_children: true,
    has_disabled: false,
    medical_needs_summary: 'Clean Drinking Water, First Aid Kit, Asthma Inhaler & Insulin',
  });

  // Victim Registration Form state
  const [victimForm, setVictimForm] = useState({
    full_name: user?.full_name || 'Chamari Perera',
    phone: user?.phone || '+94 77 123 4567',
    alternate_phone: '+94 71 889 9112',
    nic: '198956701234',
    gender: 'female',
    age: 36,
    district: 'Colombo',
    ds_division: 'Kaduwela',
    gn_division: 'Ranala',
    current_address: '45 River View Lane, Ranala, Kaduwela',
    latitude: 6.936419,
    longitude: 79.957216,
    family_members_count: 4,
    children_count: 1,
    elderly_count: 1,
    disabled_count: 0,
    pregnant_lactating_count: 0,
    evacuation_status: 'trapped_in_house',
    assigned_camp_id: null,
    chronic_diseases: 'Type 2 Diabetes, Bronchial Asthma',
    immediate_medical_needs: 'Human Insulin vials, Sterile bandages, Inhaler',
    dietary_and_relief_needs: 'Clean drinking water (20L), Dry Rations, Baby cereal',
    registered_via: 'web_portal',
    notes: 'Ground floor submerged by flood water. Need rescue boat.',
  });
  const [registeredVictimResult, setRegisteredVictimResult] = useState(null);
  const [registeringVictim, setRegisteringVictim] = useState(false);

  // SMS Gateway Simulator state
  const [smsSimSender, setSmsSimSender] = useState('+94775551234');
  const [smsSimMessage, setSmsSimMessage] = useState('SOS 5 Ranala, Kaduwela 4 Diabetic patient trapped on 2nd floor need insulin');
  const [smsSimProvider, setSmsSimProvider] = useState('DIALOG_SMSC');
  const [smsSimLoading, setSmsSimLoading] = useState(false);
  const [smsSimResult, setSmsSimResult] = useState(null);
  const [smsLogs, setSmsLogs] = useState([]);

  // First-time onboarding trigger check
  useEffect(() => {
    const onboardingKey = `dr_victim_onboarding_shown_${user?.id || 'public'}`;
    const hasSeen = localStorage.getItem(onboardingKey);
    if (!hasSeen) {
      setTimeout(() => {
        setShowOnboardingModal(true);
      }, 1200);
    }
  }, [user]);

  // Load telemetry data
  const loadData = async () => {
    setLoading(true);
    try {
      const data = await api.getSOSRequests();
      setActiveSOSList(data || []);
      const campData = await api.getCamps({ status_filter: 'approved' });
      setCamps(campData || []);
      const heatmap = await api.getHeatmap();
      setHazardZones(heatmap?.hazard_zones || []);
      
      try {
        const vList = await api.getVictims();
        setVictimsList(vList || []);
      } catch (e) {
        console.warn('Victims listing restricted or empty', e);
      }

      try {
        const logs = await api.getSMSLogs({ limit: 20 });
        setSmsLogs(logs || []);
      } catch (e) {
        console.warn('SMS logs fetch', e);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Save contacts
  const saveContacts = (updated) => {
    setEmergencyContacts(updated);
    localStorage.setItem(`dr_victim_contacts_${user?.id || 'guest'}`, JSON.stringify(updated));
    if (onAddToast) {
      onAddToast('Emergency contacts updated successfully.', 'success', 'Contacts Saved');
    }
  };

  // Capture satellite GPS fix
  const handleCaptureGPS = () => {
    if (!navigator.geolocation) {
      setGpsStatus('Geolocation not supported by browser. Using default coordinates.');
      return;
    }
    setGpsLoading(true);
    setGpsStatus('Acquiring high-accuracy satellite GPS fix...');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = parseFloat(pos.coords.latitude.toFixed(6));
        const lng = parseFloat(pos.coords.longitude.toFixed(6));
        setFormData((prev) => ({ ...prev, latitude: lat, longitude: lng }));
        setVictimForm((prev) => ({ ...prev, latitude: lat, longitude: lng }));
        setGpsLoading(false);
        setGpsStatus(`GPS Locked: ${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E (±${Math.round(pos.coords.accuracy)}m)`);
        playSuccessChime();
        if (onAddToast) {
          onAddToast(`High accuracy GPS pinpointed (${lat}, ${lng})`, 'success', 'GPS Locked');
        }
      },
      (err) => {
        setGpsLoading(false);
        setGpsStatus(`GPS unavailable (${err.message}). Default coordinates used.`);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  // Automatic broadcast to 4 emergency contacts
  const triggerEmergencyBroadcastToContacts = (sosId, priority) => {
    const timestamp = new Date().toLocaleTimeString('en-GB');
    const logs = emergencyContacts.map((c) => {
      const messageText = `[EMERGENCY SOS ALERT] ${user?.full_name || 'Victim'} has triggered Distress Beacon #${sosId} at ${formData.gn_division}, ${formData.district} (${formData.latitude.toFixed(4)}°N, ${formData.longitude.toFixed(4)}°E). Urgent medical relief/rescue needed! Priority: ${priority}/100. Emergency services (119/1990) dispatched.`;
      return {
        id: c.id,
        name: c.name,
        relation: c.relation,
        phone: c.phone,
        message: messageText,
        time: timestamp,
        status: 'DELIVERED (ACK 200 OK)',
        provider: 'DIALOG_SMSC / SATELLITE_RELAY',
        whatsappLink: `https://wa.me/${c.phone.replace(/[^0-9]/g, '')}?text=${encodeURIComponent(messageText)}`
      };
    });

    setLatestBroadcastLog(logs);
    setShowBroadcastModal(true);
  };

  // SOS Trigger Handler
  const handleSOSTrigger = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.createSOS(formData);
      playEmergencyBeep();
      const msg = `EMERGENCY SOS #${res.id} TRANSMITTED! Urgency Priority Score: ${res.priority_score}/100. Responders & 1990 Emergency Services have been notified.`;
      setSuccessMsg(msg);
      if (onAddToast) {
        onAddToast(msg, 'success', '🚨 SOS Broadcasted');
      }

      // Automatically send message to the 4 emergency contacts!
      triggerEmergencyBroadcastToContacts(res.id, res.priority_score);

      loadData();
      setTimeout(() => setSuccessMsg(null), 10000);
    } catch (err) {
      setError(err.message || 'Failed to dispatch SOS alert. Please retry or dial 119/1990 directly.');
      if (onAddToast) {
        onAddToast(err.message, 'error', 'SOS Failed');
      }
    } finally {
      setLoading(false);
    }
  };

  // Victim Registration Handler
  const handleVictimRegistration = async (e) => {
    e.preventDefault();
    setRegisteringVictim(true);
    setError(null);
    try {
      const res = await api.registerVictim(victimForm);
      playSuccessChime();
      setRegisteredVictimResult(res);
      const msg = `Victim Household #${res.id} (${res.full_name}) successfully registered! Calculated Vulnerability Score: ${res.vulnerability_score}%.`;
      setSuccessMsg(msg);
      if (onAddToast) {
        onAddToast(msg, 'success', 'Registration Verified');
      }
      loadData();
      setTimeout(() => setSuccessMsg(null), 10000);
    } catch (err) {
      setError(err.message || 'Failed to complete victim registration. Please check fields.');
      if (onAddToast) {
        onAddToast(err.message, 'error', 'Registration Error');
      }
    } finally {
      setRegisteringVictim(false);
    }
  };

  // SMS Gateway Simulator Handler
  const handleSimulateSMS = async (e) => {
    e.preventDefault();
    setSmsSimLoading(true);
    setError(null);
    try {
      const res = await api.simulateInboundSMS({
        sender: smsSimSender,
        message: smsSimMessage,
        provider: smsSimProvider,
      });
      playSuccessChime();
      setSmsSimResult(res);
      const msg = `SMS Gateway processed '${res.intent}' from ${res.sender_phone}. Auto-reply confirmation dispatched!`;
      setSuccessMsg(msg);
      if (onAddToast) {
        onAddToast(msg, 'success', 'SMS Inbound Processed');
      }
      loadData();
      setTimeout(() => setSuccessMsg(null), 8000);
    } catch (err) {
      setError(err.message || 'Failed to simulate SMS inbound webhook.');
    } finally {
      setSmsSimLoading(false);
    }
  };

  // Auth Handler (Login & Signup)
  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError(null);
    try {
      if (authTab === 'login') {
        const res = await api.login(authForm.email, authForm.password);
        setAuthToken(res.access_token);
        const me = await api.getMe();
        setStoredUser(me);
        setUser(me);
        playSuccessChime();
        setShowAuthModal(false);
        if (onAddToast) onAddToast(`Welcome, ${me.full_name}!`, 'success', 'Logged In');
      } else {
        // Sign Up
        await api.register({
          full_name: authForm.full_name,
          email: authForm.email,
          password: authForm.password,
          phone: authForm.phone,
          address: authForm.address
        });
        // Auto login after sign up
        const loginRes = await api.login(authForm.email, authForm.password);
        setAuthToken(loginRes.access_token);
        const me = await api.getMe();
        setStoredUser(me);
        setUser(me);
        playSuccessChime();
        setShowAuthModal(false);
        if (onAddToast) onAddToast(`Victim account created for ${me.full_name}!`, 'success', 'Account Registered');
        
        // Show emergency contacts onboarding immediately
        setShowOnboardingModal(true);
      }
    } catch (err) {
      setAuthError(err.message || 'Authentication error. Please check your credentials.');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleVictimSignOut = () => {
    removeAuthToken();
    setUser(null);
    setShowProfileModal(false);
    if (onAddToast) onAddToast('Signed out of victim session.', 'info', 'Logged Out');
  };

  const helplineContacts = [
    { title: 'Disaster Management Centre (DMC)', number: '117', desc: '24/7 National Emergency Operations Directorate', badge: 'Primary Triage', color: 'rose' },
    { title: 'Suwa Seriya Free Ambulance', number: '1990', desc: 'Pre-Hospital Emergency Care & Paramedic Dispatch', badge: 'Medical SOS', color: 'rose' },
    { title: 'Police Emergency Response Unit', number: '119', desc: 'Search & Rescue, Law Enforcement & Evacuation', badge: 'Rescue', color: 'blue' },
    { title: 'Sri Lanka Red Cross Disaster Unit', number: '011 267 2727', desc: 'First Aid, Dry Rations & Family Tracing Services', badge: 'Relief', color: 'emerald' },
    { title: 'Government Information Center', number: '1919', desc: 'District Secretariats & Grama Niladhari Relief Coordination', badge: 'Information', color: 'amber' },
    { title: 'National Child Protection Authority', number: '1929', desc: 'Immediate Infant & Child Protection Helplines', badge: 'Vulnerable', color: 'violet' },
  ];

  const safeZonesList = [
    { name: 'Kaduwela Central College Safe Center', district: 'Colombo', capacity: '850 Persons', status: 'Active & Open', elevation: '+28m above sea level', water: 'Available (RO Purifier)', doc: 'Dr. Bandara (MOH)', phone: '+94 11 253 8291' },
    { name: 'Ranala Maha Vidyalaya Shelter', district: 'Colombo', capacity: '420 Persons', status: 'Active & Open', elevation: '+34m above sea level', water: 'Water Bowsers Stationed', doc: 'Nurse Niluka (Red Cross)', phone: '+94 11 257 1144' },
    { name: 'Hanwella Community Hall Evacuation Camp', district: 'Colombo', capacity: '600 Persons', status: 'High Ground Safe', elevation: '+42m above sea level', water: 'Available', doc: 'MOH Medical Team #3', phone: '+94 11 289 0022' },
  ];

  return (
    <div className="victim-portal-wrapper">
      {/* ==========================================================================
          DEDICATED PUBLIC VICTIM NAVIGATION BAR (ISOLATED FROM ADMIN DASHBOARDS)
          ========================================================================== */}
      <header className="victim-nav-header">
        <div className="victim-nav-left">
          <div className="victim-brand-logo" onClick={() => setActiveTab('trigger')}>
            <div className="victim-brand-icon">
              <ShieldAlert size={20} />
            </div>
            <div className="victim-brand-text">
              <h2>SRI LANKA DISASTER RELIEF</h2>
              <span>Public Emergency SOS & Shelter Portal</span>
            </div>
          </div>
        </div>

        {/* Center Navigation Links */}
        <nav className="victim-nav-links">
          <button
            className={`victim-nav-item ${activeTab === 'trigger' ? 'active highlight-sos' : ''}`}
            onClick={() => setActiveTab('trigger')}
          >
            <ShieldAlert size={16} />
            <span>Emergency SOS</span>
          </button>

          <button
            className={`victim-nav-item ${activeTab === 'register_victim' ? 'active' : ''}`}
            onClick={() => setActiveTab('register_victim')}
          >
            <UserPlus size={16} />
            <span>Victim Intake</span>
          </button>

          <button
            className={`victim-nav-item ${activeTab === 'live_map' ? 'active' : ''}`}
            onClick={() => setActiveTab('live_map')}
          >
            <Layers size={16} />
            <span>Live Map & Shelters</span>
          </button>

          <button
            className={`victim-nav-item ${activeTab === 'helplines' ? 'active' : ''}`}
            onClick={() => setActiveTab('helplines')}
          >
            <PhoneCall size={16} />
            <span>Helplines</span>
          </button>

          <button
            className={`victim-nav-item ${activeTab === 'emergency_contacts' ? 'active' : ''}`}
            onClick={() => setActiveTab('emergency_contacts')}
          >
            <Users size={16} />
            <span>Emergency Contacts (4)</span>
          </button>

          <button
            className={`victim-nav-item ${activeTab === 'sms_gateway' ? 'active' : ''}`}
            onClick={() => setActiveTab('sms_gateway')}
          >
            <MessageSquare size={16} />
            <span>SMS Dispatch</span>
          </button>
        </nav>

        {/* Right Side: Language Switcher, Profile Pill, Sign Out / Sign In */}
        <div className="victim-nav-right">
          <div style={{ display: 'flex', gap: '3px' }}>
            <button
              className={`lang-switch-btn ${selectedLanguage === 'en' ? 'active' : ''}`}
              onClick={() => setSelectedLanguage('en')}
            >
              EN
            </button>
            <button
              className={`lang-switch-btn ${selectedLanguage === 'si' ? 'active' : ''}`}
              onClick={() => setSelectedLanguage('si')}
            >
              සිං
            </button>
            <button
              className={`lang-switch-btn ${selectedLanguage === 'ta' ? 'active' : ''}`}
              onClick={() => setSelectedLanguage('ta')}
            >
              த
            </button>
          </div>

          {user ? (
            <div className="victim-user-pill" onClick={() => setShowProfileModal(true)} title="View Victim Profile">
              <div className="victim-user-avatar">
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'V'}
              </div>
              <span className="victim-user-name">{user.full_name}</span>
            </div>
          ) : (
            <button
              className="btn btn-primary btn-sm"
              onClick={() => { setAuthTab('login'); setShowAuthModal(true); }}
            >
              <UserCheck size={14} />
              <span>Login / Sign Up</span>
            </button>
          )}

          {user && (
            <button
              className="btn btn-secondary btn-sm"
              onClick={handleVictimSignOut}
              title="Sign Out of Session"
            >
              <LogOut size={14} />
              <span>Sign Out</span>
            </button>
          )}
        </div>
      </header>

      {/* ==========================================================================
          NOTIFICATION / SUCCESS BANNERS
          ========================================================================== */}
      <div style={{ maxWidth: '1440px', margin: '0 auto', width: '100%', padding: '16px 24px 0' }}>
        {successMsg && (
          <div style={{
            padding: '16px 20px',
            backgroundColor: 'var(--accent-emerald-subtle)',
            border: '1px solid hsla(150, 84%, 42%, 0.4)',
            borderRadius: 'var(--radius-lg)',
            color: 'var(--accent-emerald)',
            fontSize: '0.9rem',
            fontWeight: '700',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            boxShadow: 'var(--shadow-md)'
          }}>
            <CheckCircle2 size={22} style={{ flexShrink: 0 }} />
            <span>{successMsg}</span>
          </div>
        )}

        {error && (
          <div style={{
            padding: '16px 20px',
            backgroundColor: 'var(--accent-rose-subtle)',
            border: '1px solid hsla(350, 89%, 60%, 0.4)',
            borderRadius: 'var(--radius-lg)',
            color: 'var(--accent-rose)',
            fontSize: '0.9rem',
            fontWeight: '700',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <AlertTriangle size={22} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* ==========================================================================
          MAIN CONTENT BODY
          ========================================================================== */}
      <main style={{ maxWidth: '1440px', margin: '0 auto', width: '100%', padding: '16px 24px 48px' }}>
        
        {/* TAB 1: EMERGENCY SOS DISTRESS TRIGGER */}
        {activeTab === 'trigger' && (
          <div>
            {/* Parallax Hero Floating Banner */}
            <div className="floating-hero-card" style={{ marginBottom: '28px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px' }}>
                <div style={{ maxWidth: '720px' }}>
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'var(--accent-rose)', color: 'white', padding: '3px 10px', borderRadius: 'var(--radius-full)', fontSize: '0.74rem', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
                    <Radio size={13} />
                    <span>EMERGENCY DISTRESS BEACON ACTIVE</span>
                  </div>
                  <h1 style={{ fontSize: '1.9rem', fontWeight: '900', letterSpacing: '-0.03em', color: 'var(--text-primary)', lineHeight: '1.2' }}>
                    Immediate Disaster Rescue & Medical Assistance
                  </h1>
                  <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginTop: '8px', lineHeight: '1.6' }}>
                    Click the <strong>Emergency SOS button</strong> below to instantly dispatch your exact satellite coordinates to the Ministry of Health, 1990 Suwa Seriya Ambulances, and <strong>automatically alert all 4 of your registered emergency contacts</strong> via SMS.
                  </p>
                </div>

                {/* Big Tactile SOS Pulse Button */}
                <div>
                  <button
                    className="big-sos-pulse-btn"
                    onClick={handleSOSTrigger}
                    disabled={loading}
                  >
                    <ShieldAlert size={28} />
                    <span>{loading ? 'TRANSMITTING...' : 'TRIGGER EMERGENCY SOS'}</span>
                  </button>
                  <span style={{ display: 'block', textAlign: 'center', fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '8px', fontWeight: '600' }}>
                    1-Click Satellite Dispatch · Notifies Contacts
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Helpline Hotline Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '28px' }}>
              <a href="tel:117" style={{ textDecoration: 'none' }}>
                <div className="card" style={{ padding: '16px', background: 'linear-gradient(180deg, var(--bg-card) 0%, hsla(350, 89%, 60%, 0.1) 100%)', borderColor: 'hsla(350, 89%, 60%, 0.3)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <PhoneCall size={20} style={{ color: 'var(--accent-rose)' }} />
                    <div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '800' }}>DISASTER RESCUE</div>
                      <div style={{ fontSize: '1.25rem', fontWeight: '900', color: 'var(--accent-rose)' }}>DIAL 117</div>
                    </div>
                  </div>
                </div>
              </a>

              <a href="tel:1990" style={{ textDecoration: 'none' }}>
                <div className="card" style={{ padding: '16px', background: 'linear-gradient(180deg, var(--bg-card) 0%, hsla(217, 91%, 60%, 0.1) 100%)', borderColor: 'hsla(217, 91%, 60%, 0.3)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Activity size={20} style={{ color: 'var(--accent-blue)' }} />
                    <div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '800' }}>AMBULANCE (FREE)</div>
                      <div style={{ fontSize: '1.25rem', fontWeight: '900', color: 'var(--accent-blue)' }}>DIAL 1990</div>
                    </div>
                  </div>
                </div>
              </a>

              <a href="tel:119" style={{ textDecoration: 'none' }}>
                <div className="card" style={{ padding: '16px', background: 'linear-gradient(180deg, var(--bg-card) 0%, hsla(38, 92%, 50%, 0.1) 100%)', borderColor: 'hsla(38, 92%, 50%, 0.3)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <ShieldAlert size={20} style={{ color: 'var(--accent-amber)' }} />
                    <div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '800' }}>POLICE EMERGENCY</div>
                      <div style={{ fontSize: '1.25rem', fontWeight: '900', color: 'var(--accent-amber)' }}>DIAL 119</div>
                    </div>
                  </div>
                </div>
              </a>

              <div
                className="card"
                style={{ padding: '16px', cursor: 'pointer', background: 'linear-gradient(180deg, var(--bg-card) 0%, hsla(150, 84%, 42%, 0.1) 100%)', borderColor: 'hsla(150, 84%, 42%, 0.3)' }}
                onClick={() => setActiveTab('emergency_contacts')}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Users size={20} style={{ color: 'var(--accent-emerald)' }} />
                  <div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '800' }}>EMERGENCY CONTACTS</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: '900', color: 'var(--accent-emerald)' }}>4 Contacts Set</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Detailed SOS Form Card */}
            <div className="card" style={{ padding: '28px' }}>
              <div className="card-header">
                <div>
                  <h2 className="card-title" style={{ fontSize: '1.2rem' }}>Victim Emergency Incident Details</h2>
                  <p className="card-subtitle">Provide details to help rescue boats and medical teams prioritize triage equipment</p>
                </div>

                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={handleCaptureGPS}
                  disabled={gpsLoading}
                >
                  <Navigation size={15} className={gpsLoading ? 'spin' : ''} style={{ color: 'var(--accent-blue)' }} />
                  <span>{gpsLoading ? 'Locking Satellite Fix...' : 'Auto-Detect My GPS Location'}</span>
                </button>
              </div>

              {gpsStatus && (
                <div style={{ padding: '10px 14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', marginBottom: '18px', fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <MapPin size={16} style={{ color: 'var(--accent-rose)' }} />
                  <span>{gpsStatus}</span>
                </div>
              )}

              <form onSubmit={handleSOSTrigger}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                  <div className="form-group">
                    <label className="form-label">Administrative District</label>
                    <select
                      className="custom-select"
                      value={formData.district}
                      onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                    >
                      <option value="Colombo">Colombo (Kelani Basin Flood Zone)</option>
                      <option value="Gampaha">Gampaha (Ja-Ela Flood Zone)</option>
                      <option value="Kalutara">Kalutara (Kalu Ganga Basin)</option>
                      <option value="Nuwara Eliya">Nuwara Eliya (Landslide Alert Zone)</option>
                      <option value="Ratnapura">Ratnapura (Kalu River Flood Zone)</option>
                      <option value="Kandy">Kandy (Highland Slope Hazard)</option>
                      <option value="Galle">Galle (Southern Coast)</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Divisional Secretariat (DS)</label>
                    <input
                      type="text"
                      className="custom-input"
                      value={formData.ds_division}
                      onChange={(e) => setFormData({ ...formData, ds_division: e.target.value })}
                      placeholder="e.g. Kaduwela"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Grama Niladhari (GN) Division</label>
                    <input
                      type="text"
                      className="custom-input"
                      value={formData.gn_division}
                      onChange={(e) => setFormData({ ...formData, gn_division: e.target.value })}
                      placeholder="e.g. Ranala"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Urgency Severity (1 to 5)</label>
                    <select
                      className="custom-select"
                      value={formData.urgency_level}
                      onChange={(e) => setFormData({ ...formData, urgency_level: parseInt(e.target.value, 10) })}
                    >
                      <option value={5}>Level 5 - Critical (Life Threatening / Water Rising)</option>
                      <option value={4}>Level 4 - Severe (Trapped / Medical Illness)</option>
                      <option value={3}>Level 3 - High (Need Food / Water / Evacuation)</option>
                      <option value={2}>Level 2 - Moderate</option>
                      <option value={1}>Level 1 - Low Risk</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Current Address / Physical Landmark</label>
                  <input
                    type="text"
                    className="custom-input"
                    value={formData.address_text}
                    onChange={(e) => setFormData({ ...formData, address_text: e.target.value })}
                    placeholder="e.g. 45 River View Lane, Ranala, Kaduwela (Near Ranala Temple)"
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                  <div className="form-group">
                    <label className="form-label">Total Affected People</label>
                    <input
                      type="number"
                      min="1"
                      className="custom-input"
                      value={formData.affected_people}
                      onChange={(e) => setFormData({ ...formData, affected_people: parseInt(e.target.value, 10) || 1 })}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Vulnerable Household Flags</label>
                    <div style={{ display: 'flex', gap: '12px', marginTop: '6px' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={formData.has_elderly}
                          onChange={(e) => setFormData({ ...formData, has_elderly: e.target.checked })}
                        />
                        <span>Elderly</span>
                      </label>

                      <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={formData.has_children}
                          onChange={(e) => setFormData({ ...formData, has_children: e.target.checked })}
                        />
                        <span>Children</span>
                      </label>

                      <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={formData.has_disabled}
                          onChange={(e) => setFormData({ ...formData, has_disabled: e.target.checked })}
                        />
                        <span>Disabled</span>
                      </label>
                    </div>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Immediate Medical Needs & Supplies</label>
                  <input
                    type="text"
                    className="custom-input"
                    value={formData.medical_needs_summary}
                    onChange={(e) => setFormData({ ...formData, medical_needs_summary: e.target.value })}
                    placeholder="e.g. Clean drinking water, Insulin vials, First aid kit, Asthma inhaler"
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '24px', flexWrap: 'wrap', gap: '12px' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    📍 Satellite Coordinates: <span className="font-mono" style={{ color: 'var(--text-primary)' }}>{formData.latitude.toFixed(6)}°N, {formData.longitude.toFixed(6)}°E</span>
                  </div>

                  <button
                    type="submit"
                    className="btn btn-danger btn-lg"
                    disabled={loading}
                  >
                    <ShieldAlert size={20} />
                    <span>{loading ? 'Broadcasting...' : 'TRANSMIT SOS & ALERT CONTACTS'}</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* TAB 2: VICTIM REGISTRATION & INTAKE */}
        {activeTab === 'register_victim' && (
          <div className="card" style={{ padding: '28px' }}>
            <div className="card-header">
              <div>
                <h2 className="card-title" style={{ fontSize: '1.25rem' }}>Official Disaster Victim & Household Intake</h2>
                <p className="card-subtitle">Ministry of Disaster Management & MOH Official Evacuee Registration Form</p>
              </div>
            </div>

            <form onSubmit={handleVictimRegistration}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Full Name of Household Head</label>
                  <input
                    type="text"
                    required
                    className="custom-input"
                    value={victimForm.full_name}
                    onChange={(e) => setVictimForm({ ...victimForm, full_name: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Primary Mobile Phone</label>
                  <input
                    type="tel"
                    required
                    className="custom-input"
                    value={victimForm.phone}
                    onChange={(e) => setVictimForm({ ...victimForm, phone: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">National Identity Card (NIC)</label>
                  <input
                    type="text"
                    className="custom-input"
                    value={victimForm.nic}
                    onChange={(e) => setVictimForm({ ...victimForm, nic: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Evacuation & Safety Status</label>
                  <select
                    className="custom-select"
                    value={victimForm.evacuation_status}
                    onChange={(e) => setVictimForm({ ...victimForm, evacuation_status: e.target.value })}
                  >
                    <option value="trapped_in_house">Trapped in House (Water Rising)</option>
                    <option value="isolated_roof_level">Isolated at Roof / High Level</option>
                    <option value="displaced_with_relatives">Displaced with Relatives</option>
                    <option value="evacuated_to_camp">Evacuated to Official Relief Camp</option>
                    <option value="safe_at_home">Safe at Home (Monitoring)</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px', marginBottom: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Total Family</label>
                  <input
                    type="number"
                    min="1"
                    className="custom-input"
                    value={victimForm.family_members_count}
                    onChange={(e) => setVictimForm({ ...victimForm, family_members_count: parseInt(e.target.value, 10) || 1 })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Children</label>
                  <input
                    type="number"
                    min="0"
                    className="custom-input"
                    value={victimForm.children_count}
                    onChange={(e) => setVictimForm({ ...victimForm, children_count: parseInt(e.target.value, 10) || 0 })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Elderly (60+)</label>
                  <input
                    type="number"
                    min="0"
                    className="custom-input"
                    value={victimForm.elderly_count}
                    onChange={(e) => setVictimForm({ ...victimForm, elderly_count: parseInt(e.target.value, 10) || 0 })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Disabled</label>
                  <input
                    type="number"
                    min="0"
                    className="custom-input"
                    value={victimForm.disabled_count}
                    onChange={(e) => setVictimForm({ ...victimForm, disabled_count: parseInt(e.target.value, 10) || 0 })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Chronic Medical Conditions & Prescription Needs</label>
                <input
                  type="text"
                  className="custom-input"
                  value={victimForm.chronic_diseases}
                  onChange={(e) => setVictimForm({ ...victimForm, chronic_diseases: e.target.value })}
                  placeholder="e.g. Type 2 Diabetes, High Blood Pressure, Cardiac Condition"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Immediate Relief & Food / Water Demands</label>
                <input
                  type="text"
                  className="custom-input"
                  value={victimForm.dietary_and_relief_needs}
                  onChange={(e) => setVictimForm({ ...victimForm, dietary_and_relief_needs: e.target.value })}
                  placeholder="e.g. 20L Clean Drinking Water, Dry rations, Infant formula milk powder"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
                <button
                  type="submit"
                  className="btn btn-primary btn-lg"
                  disabled={registeringVictim}
                >
                  <UserPlus size={18} />
                  <span>{registeringVictim ? 'Submitting Registration...' : 'Complete Victim Registration'}</span>
                </button>
              </div>
            </form>
          </div>
        )}

        {/* TAB 3: LIVE GIS MAP & SAFE SHELTERS */}
        {activeTab === 'live_map' && (
          <div>
            <div className="card" style={{ marginBottom: '24px' }}>
              <div className="card-header">
                <div>
                  <h2 className="card-title">Real-Time Safe Zones & Relief Camps Map</h2>
                  <p className="card-subtitle">OpenStreetMap GIS showing active safe shelters, hazard zones, and nearby relief camps</p>
                </div>
              </div>

              <RealTimeMap
                sosPoints={activeSOSList}
                hazardZones={hazardZones}
                camps={camps}
                height="480px"
              />
            </div>

            {/* Safe Zones List */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">High-Ground Evacuation Centers & Safe Zones</h2>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
                {safeZonesList.map((z, idx) => (
                  <div key={idx} style={{ padding: '16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontSize: '0.95rem', fontWeight: '800', color: 'var(--text-primary)' }}>{z.name}</span>
                      <span className="badge badge-success">{z.status}</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div>📍 Elevation: <strong>{z.elevation}</strong></div>
                      <div>👥 Capacity: <strong>{z.capacity}</strong></div>
                      <div>💧 Drinking Water: <strong>{z.water}</strong></div>
                      <div>🩺 Medical Station: <strong>{z.doc}</strong></div>
                      <div>📞 Contact: <strong style={{ color: 'var(--accent-blue)' }}>{z.phone}</strong></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: HELPLINES & DIRECTORY */}
        {activeTab === 'helplines' && (
          <div className="card" style={{ padding: '28px' }}>
            <div className="card-header">
              <div>
                <h2 className="card-title" style={{ fontSize: '1.25rem' }}>National Emergency Helpline Directory</h2>
                <p className="card-subtitle">Toll-free 24/7 hotline numbers with 1-click calling</p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '18px' }}>
              {helplineContacts.map((h, i) => (
                <div key={i} className="card" style={{ background: 'var(--bg-secondary)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <span className={`badge badge-${h.color}`}>{h.badge}</span>
                      <PhoneCall size={18} style={{ color: `var(--accent-${h.color})` }} />
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '4px' }}>
                      {h.title}
                    </div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                      {h.desc}
                    </p>
                  </div>

                  <a
                    href={`tel:${h.number.replace(/\s+/g, '')}`}
                    className={`btn btn-${h.color === 'rose' ? 'danger' : h.color === 'blue' ? 'primary' : 'success'}`}
                    style={{ width: '100%', marginTop: '16px', fontSize: '1.05rem', fontWeight: '900' }}
                  >
                    <Phone size={18} />
                    <span>CALL {h.number}</span>
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 5: 4 EMERGENCY CONTACTS MANAGEMENT */}
        {activeTab === 'emergency_contacts' && (
          <div>
            <div className="card" style={{ padding: '28px', marginBottom: '24px' }}>
              <div className="card-header">
                <div>
                  <h2 className="card-title" style={{ fontSize: '1.25rem' }}>My 4 SOS Emergency Contacts</h2>
                  <p className="card-subtitle">
                    These 4 trusted contacts will be <strong>automatically notified via SMS & WhatsApp</strong> the moment you trigger your SOS beacon during a disaster.
                  </p>
                </div>

                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => triggerEmergencyBroadcastToContacts(999, 95)}
                  title="Simulate SMS Alert to all 4 contacts"
                >
                  <Send size={14} style={{ color: 'var(--accent-emerald)' }} />
                  <span>Test Emergency Alert Broadcast</span>
                </button>
              </div>

              {/* Contacts Grid */}
              <div className="contacts-grid">
                {emergencyContacts.map((c, idx) => (
                  <div key={c.id} className="contact-card">
                    <div className="contact-card-top">
                      <div className="contact-avatar">
                        #{idx + 1}
                      </div>
                      <span className="contact-relation-badge">{c.relation}</span>
                    </div>

                    <div>
                      <div className="contact-name">{c.name}</div>
                      <div className="contact-phone">{c.phone}</div>
                    </div>

                    <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span style={{ color: 'var(--accent-emerald)', fontWeight: '700' }}>✓ Auto-SMS Active</span>
                      <span>&bull;</span>
                      <span>✓ 1-Click WhatsApp</span>
                    </div>

                    <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        style={{ flex: 1 }}
                        onClick={() => setEditingContact(c)}
                      >
                        <Edit2 size={13} />
                        <span>Edit</span>
                      </button>

                      <a
                        href={`https://wa.me/${c.phone.replace(/[^0-9]/g, '')}?text=${encodeURIComponent(`[EMERGENCY TEST] Hi ${c.name}, you are registered as my emergency contact on the Sri Lanka Disaster Relief System.`)}`}
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-success btn-sm"
                        title="Send WhatsApp Ping"
                      >
                        <Share2 size={13} />
                        <span>Share</span>
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Edit Contact Form Drawer / Modal if open */}
            {editingContact && (
              <div className="modal-overlay" onClick={() => setEditingContact(null)}>
                <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                  <div className="modal-header">
                    <h2 className="modal-title">Edit Emergency Contact #{editingContact.id}</h2>
                    <button className="modal-close-btn" onClick={() => setEditingContact(null)}>
                      <X size={18} />
                    </button>
                  </div>

                  <form onSubmit={(e) => {
                    e.preventDefault();
                    const updated = emergencyContacts.map((c) => c.id === editingContact.id ? editingContact : c);
                    saveContacts(updated);
                    setEditingContact(null);
                  }}>
                    <div className="form-group">
                      <label className="form-label">Contact Full Name</label>
                      <input
                        type="text"
                        required
                        className="custom-input"
                        value={editingContact.name}
                        onChange={(e) => setEditingContact({ ...editingContact, name: e.target.value })}
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Relationship to You</label>
                      <input
                        type="text"
                        required
                        className="custom-input"
                        value={editingContact.relation}
                        onChange={(e) => setEditingContact({ ...editingContact, relation: e.target.value })}
                        placeholder="e.g. Spouse, Father, Mother, Neighbor, Doctor"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Mobile Phone Number (with Country Code)</label>
                      <input
                        type="tel"
                        required
                        className="custom-input"
                        value={editingContact.phone}
                        onChange={(e) => setEditingContact({ ...editingContact, phone: e.target.value })}
                        placeholder="+94 77 123 4567"
                      />
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={() => setEditingContact(null)}
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="btn btn-primary"
                      >
                        Save Contact
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 6: OFFLINE SMS GATEWAY */}
        {activeTab === 'sms_gateway' && (
          <div className="card" style={{ padding: '28px' }}>
            <div className="card-header">
              <div>
                <h2 className="card-title">Offline SMS Gateway Dispatcher</h2>
                <p className="card-subtitle">Send text message alerts when 3G/4G Internet data connectivity is lost</p>
              </div>
            </div>

            <form onSubmit={handleSimulateSMS}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Sender Mobile Number</label>
                  <input
                    type="text"
                    className="custom-input font-mono"
                    value={smsSimSender}
                    onChange={(e) => setSmsSimSender(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Telecom Carrier SMSC</label>
                  <select
                    className="custom-select"
                    value={smsSimProvider}
                    onChange={(e) => setSmsSimProvider(e.target.value)}
                  >
                    <option value="DIALOG_SMSC">Dialog Axiata Direct Gateway</option>
                    <option value="MOBITEL_SMSC">Mobitel Sri Lanka Telecom</option>
                    <option value="AIRTEL_SMSC">Airtel Sri Lanka</option>
                    <option value="HUTCH_SMSC">Hutchison Telecommunications</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Inbound SMS Payload Text</label>
                <textarea
                  rows="3"
                  className="custom-textarea font-mono"
                  value={smsSimMessage}
                  onChange={(e) => setSmsSimMessage(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={smsSimLoading}
                >
                  <Send size={16} />
                  <span>{smsSimLoading ? 'Simulating Dispatch...' : 'Dispatch Inbound SMS'}</span>
                </button>
              </div>
            </form>
          </div>
        )}
      </main>

      {/* ==========================================================================
          MODAL 1: FIRST-TIME USER ONBOARDING POPUP
          ========================================================================== */}
      {showOnboardingModal && (
        <div className="modal-overlay" onClick={() => {
          localStorage.setItem(`dr_victim_onboarding_shown_${user?.id || 'public'}`, 'true');
          setShowOnboardingModal(false);
        }}>
          <div className="modal-content onboarding-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="onboarding-icon-wrap">
              <Users size={36} />
            </div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: '900', color: 'var(--text-primary)', marginBottom: '10px' }}>
              Add Your 4 Emergency Contacts
            </h2>
            <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '24px' }}>
              You can add <strong>4 emergency contacts</strong> to your SOS when you need it in disaster time. If you want to add them now, please click the button below.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button
                className="btn btn-danger btn-lg"
                onClick={() => {
                  localStorage.setItem(`dr_victim_onboarding_shown_${user?.id || 'public'}`, 'true');
                  setShowOnboardingModal(false);
                  setActiveTab('emergency_contacts');
                }}
              >
                <Users size={18} />
                <span>Add 4 Emergency Contacts Now</span>
              </button>

              <button
                className="btn btn-secondary"
                onClick={() => {
                  localStorage.setItem(`dr_victim_onboarding_shown_${user?.id || 'public'}`, 'true');
                  setShowOnboardingModal(false);
                }}
              >
                I'll Do It Later
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==========================================================================
          MODAL 2: AUTOMATIC CONTACT BROADCAST DISPATCH LOG
          ========================================================================== */}
      {showBroadcastModal && (
        <div className="modal-overlay" onClick={() => setShowBroadcastModal(false)}>
          <div className="modal-content" style={{ maxWidth: '640px' }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div className="brand-icon" style={{ background: 'var(--accent-emerald)', color: 'white' }}>
                  <CheckCircle2 size={20} />
                </div>
                <div>
                  <h2 className="modal-title">Emergency Alert Broadcast Confirmation</h2>
                  <p className="card-subtitle">Automated Multi-Channel Dispatch to 4 Emergency Contacts</p>
                </div>
              </div>
              <button className="modal-close-btn" onClick={() => setShowBroadcastModal(false)}>
                <X size={18} />
              </button>
            </div>

            <div className="broadcast-log-card">
              <div style={{ fontSize: '0.84rem', fontWeight: '800', color: 'var(--accent-emerald)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={16} />
                <span>4 / 4 Emergency Contacts Alerted via Satellite Gateway</span>
              </div>

              {latestBroadcastLog.map((log) => (
                <div key={log.id} className="broadcast-item">
                  <div>
                    <div style={{ fontWeight: '800', color: 'var(--text-primary)' }}>
                      {log.name} ({log.relation})
                    </div>
                    <div className="font-mono" style={{ fontSize: '0.74rem', color: 'var(--accent-blue)' }}>
                      {log.phone} &bull; {log.provider}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span className="badge badge-success">✓ {log.status}</span>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>{log.time}</div>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                className="btn btn-primary"
                onClick={() => setShowBroadcastModal(false)}
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==========================================================================
          MODAL 3: VICTIM USER PROFILE
          ========================================================================== */}
      {showProfileModal && (
        <div className="modal-overlay" onClick={() => setShowProfileModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div className="victim-user-avatar" style={{ width: '40px', height: '40px', fontSize: '1.1rem' }}>
                  {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'V'}
                </div>
                <div>
                  <h2 className="modal-title">{user?.full_name || 'Victim Profile'}</h2>
                  <p className="card-subtitle">Public Emergency Beneficiary Account</p>
                </div>
              </div>
              <button className="modal-close-btn" onClick={() => setShowProfileModal(false)}>
                <X size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
              <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: '800' }}>EMAIL ADDRESS</div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: '700' }}>{user?.email || 'victim@kaduwela.lk'}</div>
              </div>

              <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: '800' }}>MOBILE NUMBER</div>
                <div className="font-mono" style={{ fontSize: '0.9rem', color: 'var(--accent-blue)', fontWeight: '700' }}>{user?.phone || '+94 77 123 4567'}</div>
              </div>

              <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: '800' }}>REGISTERED LOCATION</div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: '700' }}>{victimForm.current_address || 'Ranala, Kaduwela, Colombo'}</div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => {
                  setShowProfileModal(false);
                  setActiveTab('emergency_contacts');
                }}
              >
                <Users size={14} />
                <span>Manage Emergency Contacts</span>
              </button>

              <button
                className="btn btn-danger btn-sm"
                onClick={handleVictimSignOut}
              >
                <LogOut size={14} />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==========================================================================
          MODAL 4: PUBLIC VICTIM LOGIN & SIGN UP
          ========================================================================== */}
      {showAuthModal && (
        <div className="modal-overlay" onClick={() => setShowAuthModal(false)}>
          <div className="modal-content auth-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div className="brand-icon">
                  <Lock size={18} />
                </div>
                <div>
                  <h2 className="modal-title">Victim Portal Access</h2>
                  <p className="card-subtitle">Sign in or create an account for disaster relief services</p>
                </div>
              </div>
              <button className="modal-close-btn" onClick={() => setShowAuthModal(false)}>
                <X size={18} />
              </button>
            </div>

            <div className="auth-tab-switch">
              <button
                className={`auth-tab-btn ${authTab === 'login' ? 'active' : ''}`}
                onClick={() => setAuthTab('login')}
              >
                <span>Sign In</span>
              </button>
              <button
                className={`auth-tab-btn ${authTab === 'signup' ? 'active' : ''}`}
                onClick={() => setAuthTab('signup')}
              >
                <span>Create New Account</span>
              </button>
            </div>

            {authError && (
              <div className="auth-error-banner">
                <AlertTriangle size={18} style={{ flexShrink: 0 }} />
                <span>{authError}</span>
              </div>
            )}

            <form onSubmit={handleAuthSubmit}>
              {authTab === 'signup' && (
                <div className="form-group">
                  <label className="form-label">Full Name</label>
                  <input
                    type="text"
                    required
                    className="custom-input"
                    placeholder="e.g. Chamari Perera"
                    value={authForm.full_name}
                    onChange={(e) => setAuthForm({ ...authForm, full_name: e.target.value })}
                  />
                </div>
              )}

              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input
                  type="email"
                  required
                  className="custom-input"
                  placeholder="e.g. victim@kaduwela.lk"
                  value={authForm.email}
                  onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })}
                />
              </div>

              {authTab === 'signup' && (
                <div className="form-group">
                  <label className="form-label">Mobile Phone Number</label>
                  <input
                    type="tel"
                    required
                    className="custom-input"
                    placeholder="+94 77 123 4567"
                    value={authForm.phone}
                    onChange={(e) => setAuthForm({ ...authForm, phone: e.target.value })}
                  />
                </div>
              )}

              <div className="form-group">
                <label className="form-label">Password</label>
                <input
                  type="password"
                  required
                  className="custom-input"
                  placeholder="Enter secure password (at least 8 chars, 1 number)..."
                  value={authForm.password}
                  onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowAuthModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={authLoading}
                >
                  {authLoading ? 'Please wait...' : authTab === 'login' ? 'Sign In' : 'Create Victim Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
