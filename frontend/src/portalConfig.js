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
    name: 'Relief Donor Marketplace',
    subtitle: 'Demand-Driven Medical Supplies & Verified Pledges',
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
    port: 5178,
    name: 'Volunteer Field Command',
    badge: 'Field Station',
    color: 'amber',
    defaultRole: 'volunteer',
  },
  officer_dash: {
    port: 5179,
    name: 'Disaster Officer Console',
    badge: 'DS Command',
    color: 'blue',
    defaultRole: 'disaster_officer',
  },
  donation_req_dash: {
    port: 5180,
    name: 'Disaster Donation Requests',
    badge: 'Appeals',
    color: 'rose',
    defaultRole: 'volunteer',
  }
};

/**
 * Detect current portal from port, URL path, query params, or environment variable.
 */
export function detectCurrentPortal() {
  // 1. Environment Variable
  const envPortal = import.meta.env.VITE_PORTAL_TYPE;
  if (envPortal && PORTAL_CONFIG[envPortal]) {
    return envPortal;
  }

  // 2. Window location port detection
  const currentPort = parseInt(window.location.port, 10);
  for (const [key, cfg] of Object.entries(PORTAL_CONFIG)) {
    if (cfg.port === currentPort) {
      return key;
    }
  }

  // 3. Window pathname detection
  const pathname = window.location.pathname.toLowerCase();
  for (const [key, cfg] of Object.entries(PORTAL_CONFIG)) {
    if (pathname.startsWith(cfg.path)) {
      return key;
    }
  }

  // 4. Query param (?portal=victim)
  const params = new URLSearchParams(window.location.search);
  const portalParam = params.get('portal');
  if (portalParam && PORTAL_CONFIG[portalParam]) {
    return portalParam;
  }

  // Default to admin
  return 'admin';
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
