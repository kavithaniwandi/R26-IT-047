import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Tent, 
  MapPin, 
  Search, 
  Filter, 
  ArrowRight, 
  HeartHandshake, 
  ShieldAlert, 
  PhoneCall, 
  Compass, 
  RefreshCw, 
  AlertCircle 
} from 'lucide-react';
import { api } from '../api';

export function VolunteerDashboardView({ currentUser, onNavigate, onAddToast }) {
  const [camps, setCamps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDs, setSelectedDs] = useState('All');
  const [error, setError] = useState(null);

  const fetchCamps = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getCamps({ status_filter: 'approved' });
      setCamps(data || []);
    } catch (err) {
      setError(err.message || 'Failed to load assigned relief camps.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCamps();
  }, []);

  const dsAreas = ['All', ...new Set(camps.map((c) => c.ds_division || c.district).filter(Boolean))];

  const filteredCamps = camps.filter((c) => {
    const dsValue = c.ds_division || c.district || '';
    const nameValue = c.name || '';
    const matchesDs = selectedDs === 'All' || dsValue === selectedDs;
    const matchesSearch = nameValue.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesDs && matchesSearch;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Volunteer Dashboard Banner */}
      <div style={{
        background: 'linear-gradient(135deg, hsla(38, 92%, 50%, 0.15), hsla(220, 20%, 14%, 1))',
        border: '1px solid hsla(38, 92%, 50%, 0.35)',
        borderRadius: 'var(--radius-xl)',
        padding: '24px 28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '54px',
            height: '54px',
            borderRadius: 'var(--radius-lg)',
            backgroundColor: 'var(--accent-amber)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'black',
            boxShadow: '0 0 24px hsla(38, 92%, 50%, 0.5)'
          }}>
            <LayoutDashboard size={28} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.45rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--text-primary)', margin: 0 }}>
              Volunteer Field Command Dashboard
            </h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '4px 0 0' }}>
              Manage shelter population, coordinate field tasks, and publish relief requests.
            </p>
          </div>
        </div>

        <div style={{
          padding: '8px 16px',
          backgroundColor: 'var(--bg-secondary)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)'
        }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase' }}>DISPATCH COMMANDER</span>
          <strong style={{ fontSize: '1.1rem', color: 'var(--accent-amber)' }}>{currentUser?.full_name || 'Volunteer Unit'}</strong>
        </div>
      </div>

      {error && (
        <div style={{
          padding: '14px 18px',
          backgroundColor: 'var(--accent-rose-subtle)',
          border: '1px solid hsla(350, 89%, 60%, 0.4)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--accent-rose)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Directory Section */}
      <div className="card">
        <div className="card-header" style={{ flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 className="card-title">Assigned Camps & Stations ({filteredCamps.length})</h2>
            <p className="card-subtitle">Active shelters allocated under your operational supervision</p>
          </div>

          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
            <div className="search-box" style={{ width: '220px' }}>
              <Search className="search-icon" size={15} />
              <input
                type="text"
                className="form-input search-input"
                placeholder="Search camp..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ padding: '6px 12px 6px 34px', fontSize: '0.82rem' }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Filter size={14} style={{ color: 'var(--text-muted)' }} />
              <select
                className="form-input"
                value={selectedDs}
                onChange={(e) => setSelectedDs(e.target.value)}
                style={{ padding: '6px 12px', fontSize: '0.82rem', width: '140px' }}
              >
                {dsAreas.map((ds) => (
                  <option key={ds} value={ds}>{ds}</option>
                ))}
              </select>
            </div>

            <button className="btn btn-secondary btn-sm" onClick={fetchCamps} disabled={loading}>
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
            </button>
          </div>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
            Loading assigned relief camps...
          </div>
        ) : filteredCamps.length === 0 ? (
          <div style={{
            backgroundColor: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-lg)',
            padding: '48px 20px',
            textAlign: 'center',
            border: '1px dashed var(--border-subtle)',
            margin: '10px 0'
          }}>
            <Tent size={40} style={{ color: 'var(--accent-amber)', marginBottom: '12px', opacity: 0.8 }} />
            <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)', margin: '0 0 6px' }}>No Relief Camps Assigned</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '480px', margin: '0 auto' }}>
              You have not been allocated to any relief camp yet. Please contact your system administrator to assign a shelter station.
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '18px' }}>
            {filteredCamps.map((camp) => {
              const currentPop = camp.current_occupancy ?? 0;
              const maxCap = camp.estimated_capacity ?? 100;
              const fillPct = Math.min(100, Math.round((currentPop / (maxCap || 1)) * 100));

              return (
                <div
                  key={camp.id}
                  style={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '14px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className={`badge ${fillPct >= 90 ? 'badge-critical' : 'badge-low'}`}>
                      {fillPct}% Occupied
                    </span>
                    <span className="font-mono" style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {camp.district}
                    </span>
                  </div>

                  <div>
                    <h3 style={{ margin: '0 0 6px', fontSize: '1.05rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                      {camp.name}
                    </h3>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      <MapPin size={12} style={{ color: 'var(--accent-rose)' }} />
                      <span>{camp.gn_division || camp.ds_division || camp.district}</span>
                    </div>
                  </div>

                  <div style={{ backgroundColor: 'var(--bg-card)', padding: '10px 12px', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '6px' }}>
                      <span>Occupancy: <strong>{currentPop} / {maxCap}</strong></span>
                      <strong>{fillPct}%</strong>
                    </div>
                    <div className="progress-bar-bg">
                      <div className="progress-bar-fill" style={{ width: `${fillPct}%`, backgroundColor: 'var(--accent-amber)' }} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Action Shortcuts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '18px' }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--accent-emerald-subtle)', color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <HeartHandshake size={20} />
          </div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: '700', margin: 0 }}>Disaster Appeals Overview</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0, flex: 1 }}>
            View active disaster supply requests and match donor pledges.
          </p>
          <button className="btn btn-secondary btn-sm" onClick={() => onNavigate && onNavigate('donations')}>
            <span>All Requests</span>
            <ArrowRight size={14} />
          </button>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--accent-rose-subtle)', color: 'var(--accent-rose)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShieldAlert size={20} />
          </div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: '700', margin: 0 }}>SOS Emergency Queue</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0, flex: 1 }}>
            Respond to active emergency distress beacons and dispatch rescue tasks.
          </p>
          <button className="btn btn-danger btn-sm" onClick={() => onNavigate && onNavigate('sos')}>
            <span>View SOS Tasks</span>
            <ArrowRight size={14} />
          </button>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--accent-blue-subtle)', color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Compass size={20} />
          </div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: '700', margin: 0 }}>Disaster Heatmap</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0, flex: 1 }}>
            Examine GIS active danger zones and affected Grama Niladhari divisions.
          </p>
          <button className="btn btn-secondary btn-sm" onClick={() => onNavigate && onNavigate('heatmap')}>
            <span>Open Map</span>
            <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}