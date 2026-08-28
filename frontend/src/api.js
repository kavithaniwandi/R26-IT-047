/**
 * src/api.js
 * Centralized API client for Disaster Relief Module Backend.
 */

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export const getAuthToken = () => localStorage.getItem('dr_token');
export const setAuthToken = (token) => localStorage.setItem('dr_token', token);
export const removeAuthToken = () => {
  localStorage.removeItem('dr_token');
  localStorage.removeItem('dr_user');
};

export const getStoredUser = () => {
  try {
    const raw = localStorage.getItem('dr_user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

export const setStoredUser = (user) => {
  localStorage.setItem('dr_user', JSON.stringify(user));
};

async function apiRequest(endpoint, options = {}) {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // If unauthorized and endpoint is not login/register, clear token
    if (!endpoint.includes('/auth/login') && !endpoint.includes('/auth/register')) {
      removeAuthToken();
    }
  }

  let data = null;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    data = await response.json();
  }

  if (!response.ok) {
    const errorMsg = data?.detail || `HTTP Error ${response.status}: ${response.statusText}`;
    throw new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
  }

  return data;
}

export const api = {
  // Auth
  login: (email, password) => apiRequest('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (payload) => apiRequest('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  getMe: () => apiRequest('/auth/me'),

  // Admin Stats
  getAdminStats: () => apiRequest('/admin/stats'),

  // Users
  getUsers: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/users${qs ? `?${qs}` : ''}`);
  },
  createUser: (payload) => apiRequest('/users', { method: 'POST', body: JSON.stringify(payload) }),
  changeUserRole: (userId, role) => apiRequest(`/users/${userId}/role`, { method: 'PATCH', body: JSON.stringify({ role }) }),
  toggleUserStatus: (userId, is_active) => apiRequest(`/users/${userId}/status`, { method: 'PATCH', body: JSON.stringify({ is_active }) }),

  // SOS
  getSOSRequests: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/sos${qs ? `?${qs}` : ''}`);
  },
  createSOS: (payload) => apiRequest('/sos', { method: 'POST', body: JSON.stringify(payload) }),
  updateSOSStatus: (sosId, status) => apiRequest(`/sos/${sosId}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),

  // Camps
  getCamps: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/camps${qs ? `?${qs}` : ''}`);
  },
  createCamp: (payload) => apiRequest('/camps', { method: 'POST', body: JSON.stringify(payload) }),
  approveCamp: (campId) => apiRequest(`/camps/${campId}/approve`, { method: 'PATCH' }),

  // Heatmap & ML Inference
  getHeatmap: () => apiRequest('/heatmap'),
  predictFlood: (payload) => apiRequest('/predict/flood', { method: 'POST', body: JSON.stringify(payload) }),
  predictLandslide: (payload) => apiRequest('/predict/landslide', { method: 'POST', body: JSON.stringify(payload) }),
  predictCampSuitability: (payload) => apiRequest('/predict/camp', { method: 'POST', body: JSON.stringify(payload) }),
  predictPriorityScore: (payload) => apiRequest('/predict/priority', { method: 'POST', body: JSON.stringify(payload) }),

  // Donations
  getDonationNeeds: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/donations/needs${qs ? `?${qs}` : ''}`);
  },
  pledgeDonation: (payload) => apiRequest('/donations', { method: 'POST', body: JSON.stringify(payload) }),
  createDonationItem: (payload) => apiRequest('/donations/items', { method: 'POST', body: JSON.stringify(payload) }),
  getAllPledges: () => apiRequest('/donations'),

  // Notifications
  getNotifications: (limit = 50) => apiRequest(`/notifications?limit=${limit}`),

  // Victims Registry & Intake
  registerVictim: (payload) => apiRequest('/victims/register', { method: 'POST', body: JSON.stringify(payload) }),
  getVictims: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/victims${qs ? `?${qs}` : ''}`);
  },
  getVictimStats: () => apiRequest('/victims/stats/summary'),
  getVictimById: (victimId) => apiRequest(`/victims/${victimId}`),
  updateVictim: (victimId, payload) => apiRequest(`/victims/${victimId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  assignVictimToCamp: (victimId, campId) => apiRequest(`/victims/${victimId}/assign-camp`, { method: 'POST', body: JSON.stringify({ camp_id: campId }) }),

  // SMS Gateway & Telecom Simulator
  simulateInboundSMS: (payload) => apiRequest('/sms/simulate-inbound', { method: 'POST', body: JSON.stringify(payload) }),
  sendDirectSMS: (payload) => apiRequest('/sms/send', { method: 'POST', body: JSON.stringify(payload) }),
  broadcastSMS: (payload) => apiRequest('/sms/broadcast', { method: 'POST', body: JSON.stringify(payload) }),
  getSMSLogs: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/sms/logs${qs ? `?${qs}` : ''}`);
  },
  getSMSGatewayStatus: () => apiRequest('/sms/gateway-status'),
};
