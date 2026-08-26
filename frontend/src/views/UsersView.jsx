import React, { useState, useEffect } from 'react';
import { 
  Users, 
  UserPlus, 
  ShieldCheck, 
  Search, 
  Filter, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Edit3, 
  Tent, 
  Building, 
  RefreshCw, 
  Heart, 
  MapPin, 
  BadgeCheck,
  X 
} from 'lucide-react';
import { api } from '../api';

export function UsersView({ currentUser }) {
  const [users, setUsers] = useState([]);
  const [victims, setVictims] = useState([]);
  const [camps, setCamps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('users'); // 'users' | 'victims'
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAssignCampModal, setShowAssignCampModal] = useState(false);
  const [selectedVictim, setSelectedVictim] = useState(null);
  const [selectedCampId, setSelectedCampId] = useState('');
  const [newRole, setNewRole] = useState('victim');
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // New user form state
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    phone: '',
    address: '',
    role: 'victim',
  });

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [uData, vData, cData] = await Promise.all([
        api.getUsers({ search: activeTab === 'users' ? search : '', role_filter: roleFilter }),
        api.getVictims({ search: activeTab === 'victims' ? search : '' }).catch(() => []),
        api.getCamps({ status_filter: 'approved' }).catch(() => []),
      ]);
      setUsers(uData || []);
      setVictims(vData || []);
      setCamps(cData || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [search, roleFilter, activeTab]);

  const handleRoleChangeSubmit = async (e) => {
    e.preventDefault();
    if (!selectedUser) return;
    try {
      await api.changeUserRole(selectedUser.id, newRole);
      setSuccessMsg(`Role updated to '${newRole}' for ${selectedUser.full_name}.`);
      setShowRoleModal(false);
      loadData();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleToggleStatus = async (user) => {
    try {
      await api.toggleUserStatus(user.id, !user.is_active);
      setSuccessMsg(`User status changed to ${!user.is_active ? 'Active' : 'Deactivated'}.`);
      loadData();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCreateUserSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.createUser(formData);
      setSuccessMsg(`User '${formData.full_name}' created successfully.`);
      setShowCreateModal(false);
      setFormData({ full_name: '', email: '', password: '', phone: '', address: '', role: 'victim' });
      loadData();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleAssignCampSubmit = async (e) => {
    e.preventDefault();
    if (!selectedVictim || !selectedCampId) return;
    try {
      await api.assignVictimToCamp(selectedVictim.id, parseInt(selectedCampId));
      setSuccessMsg(`Victim household ${selectedVictim.full_name} assigned to camp successfully.`);
      setShowAssignCampModal(false);
      loadData();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleToggleVictimVerify = async (victim) => {
    try {
      await api.updateVictim(victim.id, { is_verified: !victim.is_verified });
      setSuccessMsg(`Victim verification status updated for ${victim.full_name}.`);
      loadData();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err.message);
    }
  };

  const getRoleBadge = (role) => {
    switch (role) {
      case 'admin': return <span className="badge badge-critical">Admin</span>;
      case 'authority': return <span className="badge badge-triaged">Authority</span>;
      case 'donor': return <span className="badge badge-low">Donor</span>;
      case 'volunteer': return <span className="badge badge-medium">Volunteer</span>;
      default: return <span className="badge badge-low" style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}>Victim</span>;
    }
  };

  return (
    <div>
      {/* Alert Notifications */}
      {successMsg && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: 'var(--accent-emerald-subtle)',
          border: '1px solid hsla(150, 84%, 42%, 0.3)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--accent-emerald)',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <CheckCircle size={16} />
          <span>{successMsg}</span>
        </div>
      )}

      {error && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: 'var(--accent-rose-subtle)',
          border: '1px solid hsla(350, 89%, 60%, 0.3)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--accent-rose)',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Header controls & Tab Switcher */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h2 className="card-title">Stakeholder Access Control & Victim Intake Management</h2>
            <p className="card-subtitle">
              Manage system stakeholder RBAC roles and registered disaster victim households with camp assignments
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            {activeTab === 'users' && (
              <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
                <UserPlus size={16} />
                <span>Create New User Account</span>
              </button>
            )}
            <button className="btn btn-secondary" onClick={loadData} disabled={loading}>
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Sub-tab navigation */}
        <div style={{ display: 'flex', gap: '8px', marginTop: '16px', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
          <button
            className={`btn ${activeTab === 'users' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('users')}
          >
            <ShieldCheck size={16} />
            <span>Stakeholder User Accounts ({users.length})</span>
          </button>
          <button
            className={`btn ${activeTab === 'victims' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('victims')}
          >
            <Users size={16} />
            <span>Registered Disaster Victims Database ({victims.length})</span>
          </button>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="card" style={{ marginBottom: '20px', padding: '16px' }}>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
          <div className="search-box" style={{ flex: '1', minWidth: '240px' }}>
            <Search className="search-icon" size={16} />
            <input
              type="text"
              className="form-input search-input"
              placeholder={activeTab === 'users' ? "Search users by name, email, phone..." : "Search victims by name, NIC, phone, address..."}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {activeTab === 'users' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Filter size={16} style={{ color: 'var(--text-muted)' }} />
              <select
                className="form-input"
                style={{ width: '180px' }}
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
              >
                <option value="">All Stakeholder Roles</option>
                <option value="admin">System Admin</option>
                <option value="authority">Medical Authority</option>
                <option value="donor">Relief Donor</option>
                <option value="volunteer">Field Volunteer</option>
                <option value="victim">Disaster Victim</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* TAB 1: USERS RBAC TABLE */}
      {activeTab === 'users' && (
        <div className="card">
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>User ID</th>
                  <th>Full Name</th>
                  <th>Email & Phone</th>
                  <th>Role Claim</th>
                  <th>Status</th>
                  <th>Registered</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                      Loading stakeholder directory...
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                      No users match the search criteria.
                    </td>
                  </tr>
                ) : (
                  users.map((u) => (
                    <tr key={u.id}>
                      <td style={{ fontWeight: '700' }}>#{u.id}</td>
                      <td>
                        <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{u.full_name}</div>
                        {u.address && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{u.address}</div>}
                      </td>
                      <td>
                        <div>{u.email}</div>
                        {u.phone && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{u.phone}</div>}
                      </td>
                      <td>{getRoleBadge(u.role)}</td>
                      <td>
                        <button
                          className="btn btn-sm"
                          style={{
                            padding: '3px 8px',
                            fontSize: '0.75rem',
                            backgroundColor: u.is_active ? 'var(--accent-emerald-subtle)' : 'var(--accent-rose-subtle)',
                            color: u.is_active ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                            border: 'none',
                          }}
                          onClick={() => handleToggleStatus(u)}
                        >
                          {u.is_active ? 'Active' : 'Disabled'}
                        </button>
                      </td>
                      <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => {
                            setSelectedUser(u);
                            setNewRole(u.role);
                            setShowRoleModal(true);
                          }}
                        >
                          <Edit3 size={14} />
                          <span>Change Role</span>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: VICTIMS DATABASE TABLE */}
      {activeTab === 'victims' && (
        <div className="card">
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Victim ID</th>
                  <th>Full Name & NIC</th>
                  <th>Contact</th>
                  <th>District & Division</th>
                  <th>Household</th>
                  <th>Evacuation Status</th>
                  <th>Vulnerability</th>
                  <th>Medical Needs</th>
                  <th>Camp & Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="9" style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                      Loading victims registry...
                    </td>
                  </tr>
                ) : victims.length === 0 ? (
                  <tr>
                    <td colSpan="9" style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                      No registered victims found.
                    </td>
                  </tr>
                ) : (
                  victims.map((v) => (
                    <tr key={v.id}>
                      <td style={{ fontWeight: '700' }}>#{v.id}</td>
                      <td>
                        <div style={{ fontWeight: '700', color: 'var(--text-primary)' }}>{v.full_name}</div>
                        {v.nic && <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>NIC: {v.nic}</div>}
                      </td>
                      <td>
                        <a href={`tel:${v.phone}`} style={{ color: 'var(--accent-blue)', fontWeight: '600', textDecoration: 'none' }}>
                          {v.phone}
                        </a>
                      </td>
                      <td>
                        <div style={{ fontWeight: '600' }}>{v.district}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{v.gn_division || v.ds_division}</div>
                      </td>
                      <td>
                        <div style={{ fontSize: '0.8rem' }}><strong>{v.family_members_count}</strong> persons</div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                          {v.children_count > 0 && `${v.children_count} children `}
                          {v.elderly_count > 0 && `${v.elderly_count} elderly `}
                          {v.disabled_count > 0 && `${v.disabled_count} special needs`}
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${v.evacuation_status === 'trapped_in_house' || v.evacuation_status === 'isolated_roof_level' ? 'badge-critical' : 'badge-low'}`} style={{ fontSize: '0.72rem' }}>
                          {v.evacuation_status.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${v.vulnerability_score >= 75 ? 'badge-critical' : 'badge-medium'}`} style={{ fontWeight: '800' }}>
                          {v.vulnerability_score}%
                        </span>
                      </td>
                      <td style={{ maxWidth: '200px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                        {v.immediate_medical_needs || v.chronic_diseases || 'Standard relief'}
                      </td>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          {v.assigned_camp_name ? (
                            <span className="badge badge-low" style={{ fontSize: '0.7rem', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                              <Tent size={11} />
                              <span>{v.assigned_camp_name}</span>
                            </span>
                          ) : (
                            <button
                              className="btn btn-secondary btn-sm"
                              style={{ padding: '3px 8px', fontSize: '0.72rem' }}
                              onClick={() => {
                                setSelectedVictim(v);
                                setSelectedCampId(camps[0]?.id || '');
                                setShowAssignCampModal(true);
                              }}
                            >
                              <Tent size={12} />
                              <span>Assign Camp</span>
                            </button>
                          )}
                          <button
                            className="btn btn-sm"
                            style={{
                              padding: '2px 6px',
                              fontSize: '0.68rem',
                              backgroundColor: v.is_verified ? 'var(--accent-emerald-subtle)' : 'var(--bg-secondary)',
                              color: v.is_verified ? 'var(--accent-emerald)' : 'var(--text-muted)'
                            }}
                            onClick={() => handleToggleVictimVerify(v)}
                          >
                            {v.is_verified ? 'Verified' : 'Verify'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ASSIGN CAMP MODAL */}
      {showAssignCampModal && selectedVictim && (
        <div className="modal-overlay" onClick={() => setShowAssignCampModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Assign Victim Household to Medical Camp</h2>
              <button className="modal-close-btn" onClick={() => setShowAssignCampModal(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleAssignCampSubmit}>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
                Assigning <strong>{selectedVictim.full_name}</strong> ({selectedVictim.family_members_count} family members) from {selectedVictim.district}.
              </p>
              <div className="form-group">
                <label className="form-label">Select Approved Medical Camp</label>
                <select
                  className="form-input"
                  value={selectedCampId}
                  onChange={(e) => setSelectedCampId(e.target.value)}
                  required
                >
                  <option value="">Select a Camp...</option>
                  {camps.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.district} - Cap: {c.estimated_capacity}, Occ: {c.current_occupancy})
                    </option>
                  ))}
                </select>
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '10px' }}>
                Confirm Camp Admission
              </button>
            </form>
          </div>
        </div>
      )}

      {/* CHANGE ROLE MODAL */}
      {showRoleModal && selectedUser && (
        <div className="modal-overlay" onClick={() => setShowRoleModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Update Stakeholder Role Claim</h2>
              <button className="modal-close-btn" onClick={() => setShowRoleModal(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleRoleChangeSubmit}>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
                Modify RBAC role claim for <strong>{selectedUser.full_name}</strong> ({selectedUser.email}):
              </p>
              <div className="form-group">
                <label className="form-label">Target Role</label>
                <select
                  className="form-input"
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                >
                  <option value="admin">System Admin</option>
                  <option value="authority">Medical Authority (MOH)</option>
                  <option value="donor">Relief Donor</option>
                  <option value="volunteer">Field Volunteer</option>
                  <option value="victim">Disaster Victim</option>
                </select>
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '10px' }}>
                Save Role Claim
              </button>
            </form>
          </div>
        </div>
      )}

      {/* CREATE USER MODAL */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Create New Stakeholder Account</h2>
              <button className="modal-close-btn" onClick={() => setShowCreateModal(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCreateUserSubmit}>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input
                  type="email"
                  className="form-input"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Temporary Password</label>
                <input
                  type="password"
                  className="form-input"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Assigned Role</label>
                <select
                  className="form-input"
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                >
                  <option value="victim">Disaster Victim</option>
                  <option value="donor">Relief Donor</option>
                  <option value="volunteer">Field Volunteer</option>
                  <option value="authority">Medical Authority</option>
                  <option value="admin">System Admin</option>
                </select>
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '10px' }}>
                Create Account
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
