/**
 * src/portalConfig.js
 * Multi-Portal Routing & Dedicated IP/Port Mapping Architecture
 */

export const PORTAL_CONFIG = {
  home: {
    id: 'home',
    name: 'National Disaster Relief Portal',
    subtitle: 'Sri Lanka Emergency Command & Medical Response Cloud',
    port: 5173,
    path: '/',
    defaultRole: null,
    color: 'blue',
    badge: 'Public Landing',
  },
  admin: {
    id: 'admin',
    name: 'Admin Command Center',
    subtitle: 'National Triage & System Orchestration',
    port: 5173,
    path: '/admin',
    defaultRole: 'admin',
    defaultEmail: 'admin@disaster.relief.lk',
    defaultPassword: 'Admin@2026!',
    color: 'rose',
    badge: 'Port :5173',
  },
  victim: {
    id: 'victim',
    name: 'Victim SOS & Public Portal',
    subtitle: 'Emergency Satellite GPS & Multi-Channel SOS',
    port: 5174,
    path: '/victim',
    defaultRole: 'victim',
    defaultEmail: 'victim@kaduwela.lk',
    defaultPassword: 'Victim@2026!',
    color: 'rose',
    badge: 'Port :5174',
  },
  authority: {
    id: 'authority',
    name: 'Medical Authority Console',
    subtitle: 'Ministry of Health: Triage, Camps & ML Analytics',
    port: 5175,
    path: '/authority',
    defaultRole: 'authority',
    defaultEmail: 'authority@moh.gov.lk',
    defaultPassword: 'Authority@2026!',
    color: 'blue',
    badge: 'Port :5175',
  },
  donor: {
    id: 'donor',
    name: 'Donor Donation Portal',
    subtitle: 'Personalized Requests, Pledges & Donation History',
    port: 5176,
    path: '/donor',
    defaultRole: 'donor',
    defaultEmail: 'donor@redcross.lk',
    defaultPassword: 'Donor@2026!',
    color: 'emerald',
    badge: 'Port :5176',
  },
  volunteer: {
    id: 'volunteer',
    name: 'Field Volunteer Dispatch',
    subtitle: 'On-Ground Rescue Missions & Rapid Delivery',
    port: 5177,
    path: '/volunteer',
    defaultRole: 'volunteer',
    defaultEmail: 'volunteer@relief.lk',
    defaultPassword: 'Volunteer@2026!',
    color: 'amber',
    badge: 'Port :5177',
  },
  volunteer_dash: {
    id: 'volunteer_dash',
    name: 'Volunteer Field Command',
    port: 5178,
    path: '/volunteer-dash',
    defaultRole: 'volunteer',
    defaultEmail: 'volunteer@relief.lk',
    defaultPassword: 'Volunteer@2026!',
    badge: 'Port :5178',
    color: 'amber',
  },
  disaster_officer: {
    id: 'disaster_officer',
    name: 'Disaster Officer Portal',
    port: 5179,
    path: '/disaster-officer',
    defaultRole: 'disaster_officer',
    defaultEmail: 'officer@disaster.relief.lk',
    defaultPassword: 'Officer@2026!',
    badge: 'Port :5179',
    color: 'blue',
  },
  disaster_donation: {
    id: 'disaster_donation',
    name: 'Disaster Donation Portal',
    port: 5180,
    path: '/disaster-donation',
    defaultRole: 'volunteer',
    defaultEmail: 'volunteer@relief.lk',
    defaultPassword: 'Volunteer@2026!',
    badge: 'Port :5180',
    color: 'emerald',
  },
  donor_matching: {
    id: 'donor_matching',
    name: 'Personalized Donor Matching',
    subtitle: 'GN-Based Donor Ranking & Targeted Relief Outreach',
    port: 5181,
    path: '/donor-matching',
    defaultRole: 'disaster_officer',
    defaultEmail: 'officer@disaster.relief.lk',
    defaultPassword: 'Officer@2026!',
    badge: 'Port :5181',
    color: 'violet',
  },
};

/**
 * Detect current portal from port, URL path, query params, or environment variable.
 */
export function detectCurrentPortal() {
  // 1. Explicit query parameter has highest precedence (e.g. ?portal=admin, ?portal=victim)
  const params = new URLSearchParams(window.location.search);
  const portalParam = params.get('portal');
  if (portalParam && PORTAL_CONFIG[portalParam]) {
    return portalParam;
  }

  // 2. Public Root URL on primary port 5173 is always the public 'home' landing page
  const pathname = window.location.pathname.toLowerCase();
  const currentPort = parseInt(window.location.port, 10);
  if (pathname === '/' && (!currentPort || currentPort === 5173)) {
    return 'home';
  }

  // 3. Window pathname detection for specific subpaths (e.g. /admin, /victim)
  for (const [key, cfg] of Object.entries(PORTAL_CONFIG)) {
    if (cfg.path !== '/' && pathname.startsWith(cfg.path)) {
      return key;
    }
  }

  // 4. Dedicated port detection for other micro-portals (ports 5174-5181)
  for (const [key, cfg] of Object.entries(PORTAL_CONFIG)) {
    if (cfg.port === currentPort && key !== 'home' && key !== 'admin') {
      return key;
    }
  }

  // 5. Environment variable fallback (if not admin on root)
  const envPortal = import.meta.env.VITE_PORTAL_TYPE;
  if (envPortal && PORTAL_CONFIG[envPortal] && envPortal !== 'admin') {
    return envPortal;
  }

  // Default to home public portal
  return 'home';
}

export function getPortalForRole(role) {
  return {
    admin: 'admin',
    victim: 'victim',
    authority: 'authority',
    donor: 'donor',
    volunteer: 'volunteer',
    disaster_officer: 'disaster_officer',
  }[role] || 'home';
}

/**
 * Generate the direct URL for a specific portal on its dedicated IP / Port.
 */
export function getPortalUrl(portalId) {
  const cfg = PORTAL_CONFIG[portalId];
  if (!cfg) return window.location.origin;

  const hostname = window.location.hostname || 'localhost';
  const protocol = window.location.protocol || 'http:';

  // If running in dev mode or distinct ports
  return `${protocol}//${hostname}:${cfg.port}${cfg.path}`;
}
