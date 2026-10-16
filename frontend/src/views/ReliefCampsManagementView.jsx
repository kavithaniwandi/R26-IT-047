import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  Check,
  CheckCircle2,
  MapPin,
  Plus,
  RefreshCw,
  Search,
  Tent,
  UserCheck,
  Users,
  X,
} from 'lucide-react';
import { api } from '../api';

const initialForm = () => ({
  dsArea: '',
  gnDivision: '',
  name: '',
  maxCapacityPersons: 100,
  maxFamilies: 25,
  currentPopulation: 0,
  predictedPopulation: 0,
  assignedVolunteerIds: [],
});

const volunteerName = (volunteer) => {
  const name = volunteer.full_name
    || `${volunteer.firstName || ''} ${volunteer.lastName || ''}`.trim();
  return name || volunteer.email || 'Unnamed volunteer';
};

const normalizeSqlVolunteers = (users) => {
  const uniqueVolunteers = new Map();

  (users || [])
    .filter((user) => user.role === 'volunteer' && user.is_active !== false)
    .forEach((user) => {
      const key = user.email?.trim().toLowerCase() || `id:${user.id}`;
      const existing = uniqueVolunteers.get(key);
      if (!existing) {
        uniqueVolunteers.set(key, { ...user, aliasIds: [String(user.id)] });
      } else {
        const canonical = Number(user.id) > Number(existing.id) ? user : existing;
        uniqueVolunteers.set(key, {
          ...canonical,
          aliasIds: [...new Set([...existing.aliasIds, String(user.id)])],
        });
      }
    });

  return [...uniqueVolunteers.values()].map((user) => ({
    ...user,
    userId: String(user.id),
    source: 'sql',
  }));
};

export function ReliefCampsManagementView({ onAddToast }) {
  const [camps, setCamps] = useState([]);
  const [volunteers, setVolunteers] = useState([]);
  const [divisions, setDivisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [savingAssignments, setSavingAssignments] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [dsFilter, setDsFilter] = useState('All');
  const [gnFilter, setGnFilter] = useState('All');
  const [selectedCampId, setSelectedCampId] = useState(null);
  const [selectedVolunteerIds, setSelectedVolunteerIds] = useState(new Set());
  const [volunteerSearch, setVolunteerSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState(initialForm);

  const loadWorkspace = async ({ showLoader = true } = {}) => {
    if (showLoader) setLoading(true);
    setError(null);
    try {
      const [campData, volunteerData, divisionData] = await Promise.all([
        api.getReliefCamps(),
        api.getUsers({ role_filter: 'volunteer' }),
        api.getDivisions(),
      ]);
      setCamps(campData || []);
      setVolunteers(normalizeSqlVolunteers(volunteerData));
      setDivisions(divisionData || []);
    } catch (err) {
      setError(err.message || 'Failed to load the relief-camp workspace.');
    } finally {
      if (showLoader) setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      api.getReliefCamps(),
      api.getUsers({ role_filter: 'volunteer' }),
      api.getDivisions(),
    ])
      .then(([campData, volunteerData, divisionData]) => {
        if (cancelled) return;
        setCamps(campData || []);
        setVolunteers(normalizeSqlVolunteers(volunteerData));
        setDivisions(divisionData || []);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Failed to load the relief-camp workspace.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const dsAreas = useMemo(() => {
    const values = new Set([
      ...divisions.map((division) => division.dsArea),
      ...camps.map((camp) => camp.dsArea),
    ].filter(Boolean));
    return [...values].sort();
  }, [camps, divisions]);

  const gnDivisions = useMemo(() => {
    const values = new Set();
    divisions
      .filter((division) => dsFilter === 'All' || division.dsArea === dsFilter)
      .forEach((division) => (division.gnDivisions || []).forEach((gn) => values.add(gn)));
    camps
      .filter((camp) => dsFilter === 'All' || camp.dsArea === dsFilter)
      .forEach((camp) => camp.gnDivision && values.add(camp.gnDivision));
    return [...values].sort();
  }, [camps, divisions, dsFilter]);

  const createGnDivisions = useMemo(() => {
    const division = divisions.find((item) => item.dsArea === formData.dsArea);
    return [...new Set([
      ...(division?.gnDivisions || []),
      ...camps.filter((camp) => camp.dsArea === formData.dsArea).map((camp) => camp.gnDivision),
    ].filter(Boolean))].sort();
  }, [camps, divisions, formData.dsArea]);

  const filteredCamps = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return camps.filter((camp) => {
      const matchesDs = dsFilter === 'All' || camp.dsArea === dsFilter;
      const matchesGn = gnFilter === 'All' || camp.gnDivision === gnFilter;
      const matchesSearch = !query || [camp.name, camp.dsArea, camp.gnDivision]
        .some((value) => String(value || '').toLowerCase().includes(query));
      return matchesDs && matchesGn && matchesSearch;
    });
  }, [camps, dsFilter, gnFilter, searchQuery]);

  const selectedCamp = camps.find((camp) => camp.id === selectedCampId) || null;

  const filteredVolunteers = useMemo(() => {
    const query = volunteerSearch.trim().toLowerCase();
    return volunteers.filter((volunteer) => !query || [
      volunteerName(volunteer),
      volunteer.email,
      volunteer.phone,
      volunteer.address,
    ].some((value) => String(value || '').toLowerCase().includes(query)));
  }, [volunteerSearch, volunteers]);

  const selectCamp = (camp) => {
    const assignedIds = new Set((camp.assignedVolunteerIds || []).map(String));
    const canonicalAssignments = volunteers
      .filter((volunteer) => volunteer.aliasIds.some((id) => assignedIds.has(id)))
      .map((volunteer) => volunteer.userId);
    setSelectedCampId(camp.id);
    setSelectedVolunteerIds(new Set(canonicalAssignments));
    setVolunteerSearch('');
  };

  const toggleVolunteer = (volunteerId) => {
    setSelectedVolunteerIds((current) => {
      const next = new Set(current);
      if (next.has(volunteerId)) next.delete(volunteerId);
      else next.add(volunteerId);
      return next;
    });
  };

  const saveVolunteerAssignments = async () => {
    if (!selectedCamp) return;
    setSavingAssignments(true);
    setError(null);
    try {
      const updated = await api.assignReliefCampVolunteers(selectedCamp.id, [...selectedVolunteerIds]);
      setCamps((current) => current.map((camp) => camp.id === updated.id ? updated : camp));
      onAddToast?.(`${selectedVolunteerIds.size} volunteer(s) assigned to ${updated.name}.`, 'success', 'Assignments Saved');
    } catch (err) {
      const message = err.message || 'Failed to save volunteer assignments.';
      setError(message);
      onAddToast?.(message, 'error', 'Assignment Failed');
    } finally {
      setSavingAssignments(false);
    }
  };

  const updateForm = (field, value) => {
    setFormData((current) => ({ ...current, [field]: value }));
  };

  const handleCreate = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const created = await api.createReliefCamp({
        ...formData,
        predictedPopulation: formData.currentPopulation,
      });
      setCamps((current) => [...current, created].sort((a, b) => a.name.localeCompare(b.name)));
      selectCamp(created);
      setFormData(initialForm());
      setShowCreateModal(false);
      onAddToast?.(`${created.name} was created and added to the registry.`, 'success', 'Relief Camp Created');
    } catch (err) {
      const message = err.message || 'Failed to create relief camp.';
      setError(message);
      onAddToast?.(message, 'error', 'Creation Failed');
    } finally {
      setSubmitting(false);
    }
  };

  const openCreateModal = () => {
    const defaultDs = dsFilter !== 'All' ? dsFilter : (dsAreas[0] || '');
    const division = divisions.find((item) => item.dsArea === defaultDs);
    const defaultGn = gnFilter !== 'All' ? gnFilter : (division?.gnDivisions?.[0] || '');
    setFormData({ ...initialForm(), dsArea: defaultDs, gnDivision: defaultGn });
    setShowCreateModal(true);
  };

  const handleDsFilterChange = (value) => {
    setDsFilter(value);
    setGnFilter('All');
  };

  const totalPopulation = camps.reduce((sum, camp) => sum + (camp.currentPopulation || 0), 0);
  const totalCapacity = camps.reduce((sum, camp) => sum + (camp.maxCapacityPersons || 0), 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="card" style={{ padding: '22px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ width: 48, height: 48, borderRadius: 'var(--radius-lg)', background: 'var(--accent-blue-subtle)', color: 'var(--accent-blue)', display: 'grid', placeItems: 'center' }}>
            <Tent size={26} />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.35rem' }}>Disaster Relief Camp Management</h1>
            <p className="card-subtitle">Create camps by GN division and assign field volunteers.</p>
          </div>
        </div>
        <button className="btn btn-primary" onClick={openCreateModal}>
          <Plus size={16} />
          <span>Add Relief Camp</span>
        </button>
      </div>

      {error && (
        <div style={{ padding: '13px 16px', borderRadius: 'var(--radius-md)', color: 'var(--accent-rose)', background: 'var(--accent-rose-subtle)', border: '1px solid hsla(350, 89%, 60%, 0.35)', display: 'flex', gap: 10, alignItems: 'center' }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 14 }}>
        {[
          ['Registered Camps', camps.length, Tent],
          ['Current Population', totalPopulation.toLocaleString(), Users],
          ['Total Capacity', totalCapacity.toLocaleString(), CheckCircle2],
          ['Available Volunteers', volunteers.length, UserCheck],
        ].map(([label, value, Icon]) => (
          <div className="card" key={label} style={{ padding: 18, display: 'flex', alignItems: 'center', gap: 13 }}>
            <Icon size={23} style={{ color: 'var(--accent-blue)' }} />
            <div>
              <div style={{ fontSize: '1.35rem', fontWeight: 800 }}>{value}</div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>{label}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(360px, 1.15fr) minmax(340px, 0.85fr)', gap: 18, alignItems: 'start' }}>
        <section className="card">
          <div className="card-header" style={{ flexWrap: 'wrap', gap: 10 }}>
            <div>
              <h2 className="card-title">Relief Camps ({filteredCamps.length})</h2>
              <p className="card-subtitle">Select a camp to manage its volunteers</p>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => loadWorkspace({ showLoader: false })} title="Refresh workspace">
              <RefreshCw size={14} />
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(180px, 1fr) 150px 150px', gap: 8, marginBottom: 16 }}>
            <div className="search-box">
              <Search className="search-icon" size={15} />
              <input className="form-input search-input" placeholder="Search camps..." value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} />
            </div>
            <select className="form-select" value={dsFilter} onChange={(event) => handleDsFilterChange(event.target.value)} aria-label="Filter by DS area">
              <option value="All">All DS Areas</option>
              {dsAreas.map((area) => <option key={area} value={area}>{area}</option>)}
            </select>
            <select className="form-select" value={gnFilter} onChange={(event) => setGnFilter(event.target.value)} aria-label="Filter by GN division">
              <option value="All">All GN Divisions</option>
              {gnDivisions.map((division) => <option key={division} value={division}>{division}</option>)}
            </select>
          </div>

          {loading ? (
            <div style={{ padding: 44, textAlign: 'center', color: 'var(--text-muted)' }}>Loading relief camps...</div>
          ) : filteredCamps.length === 0 ? (
            <div style={{ padding: 44, textAlign: 'center', color: 'var(--text-muted)', border: '1px dashed var(--border-subtle)', borderRadius: 'var(--radius-lg)' }}>
              <Tent size={38} style={{ marginBottom: 10 }} />
              <div>No relief camps match the selected area.</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 9, maxHeight: 560, overflowY: 'auto', paddingRight: 4 }}>
              {filteredCamps.map((camp) => {
                const capacity = camp.maxCapacityPersons || 1;
                const population = camp.currentPopulation || 0;
                const occupancy = Math.min(100, Math.round((population / capacity) * 100));
                const selected = camp.id === selectedCampId;
                return (
                  <button
                    type="button"
                    key={camp.id}
                    onClick={() => selectCamp(camp)}
                    style={{ textAlign: 'left', padding: 15, color: 'inherit', background: selected ? 'var(--accent-blue-subtle)' : 'var(--bg-secondary)', border: selected ? '1px solid var(--accent-blue)' : '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', cursor: 'pointer' }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, marginBottom: 8 }}>
                      <strong>{camp.name}</strong>
                      <span className={`badge ${occupancy >= 90 ? 'badge-critical' : occupancy >= 70 ? 'badge-medium' : 'badge-low'}`}>{occupancy}% full</span>
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 9 }}>
                      <MapPin size={14} /> {camp.gnDivision}, {camp.dsArea}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                      <span>{population} / {capacity} people</span>
                      <span>{(camp.assignedVolunteerIds || []).length} volunteer(s)</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </section>

        <aside className="card" style={{ position: 'sticky', top: 16 }}>
          <div className="card-header">
            <div>
              <h2 className="card-title">Volunteer Assignment</h2>
              <p className="card-subtitle">Assign registered volunteers to the selected camp</p>
            </div>
          </div>

          {!selectedCamp ? (
            <div style={{ padding: '54px 20px', textAlign: 'center', color: 'var(--text-muted)', border: '1px dashed var(--border-subtle)', borderRadius: 'var(--radius-lg)' }}>
              <UserCheck size={40} style={{ marginBottom: 12, color: 'var(--accent-blue)' }} />
              <strong style={{ display: 'block', color: 'var(--text-primary)', marginBottom: 6 }}>Select a relief camp</strong>
              Choose a camp from the left side to view and update its volunteer team.
            </div>
          ) : (
            <>
              <div style={{ padding: 14, background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', marginBottom: 14 }}>
                <strong style={{ display: 'block', marginBottom: 5 }}>{selectedCamp.name}</strong>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{selectedCamp.gnDivision}, {selectedCamp.dsArea}</span>
              </div>

              <div className="search-box" style={{ marginBottom: 12 }}>
                <Search className="search-icon" size={15} />
                <input className="form-input search-input" placeholder="Search volunteers..." value={volunteerSearch} onChange={(event) => setVolunteerSearch(event.target.value)} />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                <span>{selectedVolunteerIds.size} selected</span>
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setSelectedVolunteerIds(new Set())}>Clear</button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 365, overflowY: 'auto', paddingRight: 4 }}>
                {filteredVolunteers.length === 0 ? (
                  <div style={{ padding: 28, textAlign: 'center', color: 'var(--text-muted)' }}>No registered volunteers found.</div>
                ) : filteredVolunteers.map((volunteer) => {
                  const id = String(volunteer.userId);
                  const checked = selectedVolunteerIds.has(id);
                  return (
                    <label key={id} style={{ padding: 11, borderRadius: 'var(--radius-md)', border: checked ? '1px solid var(--accent-blue)' : '1px solid var(--border-subtle)', background: checked ? 'var(--accent-blue-subtle)' : 'var(--bg-secondary)', display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
                      <input type="checkbox" checked={checked} onChange={() => toggleVolunteer(id)} />
                      <div style={{ minWidth: 0, flex: 1 }}>
                        <strong style={{ fontSize: '0.83rem', display: 'block' }}>{volunteerName(volunteer)}</strong>
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem', overflow: 'hidden', textOverflow: 'ellipsis', display: 'block' }}>{volunteer.email || volunteer.phone || 'No contact details'}</span>
                      </div>
                      {checked && <Check size={16} style={{ color: 'var(--accent-blue)' }} />}
                    </label>
                  );
                })}
              </div>

              <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: 16 }} onClick={saveVolunteerAssignments} disabled={savingAssignments}>
                <UserCheck size={16} />
                <span>{savingAssignments ? 'Saving...' : 'Save Volunteer Assignments'}</span>
              </button>
            </>
          )}
        </aside>
      </div>

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => !submitting && setShowCreateModal(false)}>
          <div className="modal-content" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title">Add Disaster Relief Camp</h3>
                <p className="card-subtitle">Select the administrative division and register its capacity.</p>
              </div>
              <button className="modal-close-btn" onClick={() => setShowCreateModal(false)} disabled={submitting}><X size={20} /></button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label className="form-label">Camp Name</label>
                <input className="form-input" required minLength={2} value={formData.name} onChange={(event) => updateForm('name', event.target.value)} placeholder="e.g. Sri Maha Viharaya Relief Camp" />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="form-group">
                  <label className="form-label">DS Area</label>
                  <select
                    className="form-select"
                    required
                    value={formData.dsArea}
                    onChange={(event) => {
                      const dsArea = event.target.value;
                      const division = divisions.find((item) => item.dsArea === dsArea);
                      setFormData((current) => ({ ...current, dsArea, gnDivision: division?.gnDivisions?.[0] || '' }));
                    }}
                  >
                    <option value="">Select DS Area</option>
                    {dsAreas.map((area) => <option key={area} value={area}>{area}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">GN Division</label>
                  <select className="form-select" required value={formData.gnDivision} onChange={(event) => updateForm('gnDivision', event.target.value)} disabled={!formData.dsArea}>
                    <option value="">Select GN Division</option>
                    {createGnDivisions.map((division) => <option key={division} value={division}>{division}</option>)}
                  </select>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                <div className="form-group">
                  <label className="form-label">Person Capacity</label>
                  <input type="number" className="form-input" required min="1" value={formData.maxCapacityPersons} onChange={(event) => updateForm('maxCapacityPersons', Number(event.target.value))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Family Capacity</label>
                  <input type="number" className="form-input" min="0" value={formData.maxFamilies} onChange={(event) => updateForm('maxFamilies', Number(event.target.value))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Current Population</label>
                  <input type="number" className="form-input" min="0" max={formData.maxCapacityPersons} value={formData.currentPopulation} onChange={(event) => updateForm('currentPopulation', Number(event.target.value))} />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)} disabled={submitting}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={submitting || !formData.gnDivision}>
                  {submitting ? 'Creating...' : 'Create Relief Camp'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
