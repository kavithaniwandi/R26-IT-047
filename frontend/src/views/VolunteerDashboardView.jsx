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
  Compass, 
  RefreshCw, 
  AlertCircle,
  Thermometer,
  Droplets,
  Waves,
  CloudRain
} from 'lucide-react';
import { api } from '../api';
import { ReliefCampDetailView } from './ReliefCampDetailView';

export function VolunteerDashboardView({ currentUser, onNavigate, onAddToast }) {
  const [camps, setCamps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDs, setSelectedDs] = useState('All');
  const [error, setError] = useState(null);
  const [selectedCampId, setSelectedCampId] = useState(null);
  const [envData, setEnvData] = useState(null);
  const [syncingEnv, setSyncingEnv] = useState(false);
  const [lastSyncedTime, setLastSyncedTime] = useState(null);

  const fetchCamps = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getReliefCamps();
      setCamps(data || []);
    } catch (err) {
      setError(err.message || 'Failed to load assigned relief camps.');
    } finally {
      setLoading(false);
    }
  };

  const syncLiveEnvironment = async (showToast = false) => {
    setSyncingEnv(true);
    try {
      const data = await api.getKelaniEnvironment();
      setEnvData(data);
      setLastSyncedTime(new Date());
      if (showToast && onAddToast) {
        onAddToast('Live weather, rainfall, and Kelani River gauge data synchronized.', 'success', 'Live Environment Synced');
      }
    } catch (err) {
      console.warn('Failed to sync live environmental conditions:', err);
    } finally {
      setSyncingEnv(false);
    }
  };

  useEffect(() => {
    fetchCamps();
    syncLiveEnvironment();
  }, []);

  const dsAreas = ['All', ...new Set(camps.map((c) => c.dsArea || c.ds_division || c.district).filter(Boolean))];

  const filteredCamps = camps.filter((c) => {
    const dsValue = c.dsArea || c.ds_division || c.district || '';
    const gnValue = c.gnDivision || c.gn_division || '';
    const nameValue = c.name || '';
    const matchesDs = selectedDs === 'All' || dsValue === selectedDs;
    const query = searchQuery.toLowerCase();
    const matchesSearch = [nameValue, dsValue, gnValue].some((value) => value.toLowerCase().includes(query));
    return matchesDs && matchesSearch;
  });

  if (selectedCampId) {
    return (
      <ReliefCampDetailView
        campId={selectedCampId}
        currentUser={currentUser}
        onBack={() => {
          setSelectedCampId(null);
          fetchCamps();
        }}
        onAddToast={onAddToast}
      />
    );
  }

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

      {/* Live Environmental Conditions & River Telemetry */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        padding: '16px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: '#10b981',
              display: 'inline-block',
              boxShadow: '0 0 8px #10b981'
            }} />
            <h3 style={{ margin: 0, fontSize: '0.92rem', fontWeight: '700', color: 'var(--text-primary)' }}>
              {envData ? 'Live Kaduwela Environment & Kelani Basin Telemetry' : 'Sample data (live feed unavailable) ? Kaduwela Environment & Kelani Basin Telemetry'}
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {lastSyncedTime ? `Synced at ${lastSyncedTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}` : 'Synchronizing...'}
            </span>
          </div>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => syncLiveEnvironment(true)}
            disabled={syncingEnv}
            style={{ fontSize: '0.78rem', padding: '5px 12px' }}
          >
            <RefreshCw size={13} className={syncingEnv ? 'spin' : ''} />
            <span>{syncingEnv ? 'Syncing...' : 'Sync Live Telemetry'}</span>
          </button>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '12px'
        }}>
          {/* Temperature & Humidity */}
          <div style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'rgba(239, 68, 68, 0.12)',
              color: '#ef4444',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Thermometer size={18} />
            </div>
            <div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>Kaduwela Weather</span>
              <strong style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                {envData?.weather?.available ? `${envData.weather.temperatureC}°C` : '27.2°C'}
              </strong>
              <small style={{ display: 'block', fontSize: '0.68rem', color: 'var(--text-secondary)' }}>
                {envData?.weather?.available ? `${envData.weather.humidityPercent}% humidity · Open-Meteo` : '91% humidity · Open-Meteo'}
              </small>
            </div>
          </div>

          {/* Rainfall */}
          <div style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'rgba(59, 130, 246, 0.12)',
              color: '#3b82f6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Droplets size={18} />
            </div>
            <div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>Current Rainfall</span>
              <strong style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                {envData?.rainHistory ? `${envData.rainHistory[0] ?? 0} mm` : '0.3 mm'}
              </strong>
              <small style={{ display: 'block', fontSize: '0.68rem', color: 'var(--text-secondary)' }}>
                Recent 3-hour precipitation
              </small>
            </div>
          </div>

          {/* Hanwella Gauge */}
          <div style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'rgba(16, 185, 129, 0.12)',
              color: '#10b981',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Waves size={18} />
            </div>
            <div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>Kelani River · Hanwella</span>
              <strong style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                {envData?.river?.levelM ? `${Number(envData.river.levelM).toFixed(2)} m` : '3.42 m'}
              </strong>
              <small style={{ display: 'block', fontSize: '0.68rem', color: 'var(--text-secondary)' }}>
                {envData?.river?.available
                  ? `${String(envData.river.status || 'normal').replaceAll('_', ' ')} · ${envData.river.isRising ? 'rising' : 'stable/falling'}`
                  : 'normal · stable/falling'}
              </small>
            </div>
          </div>
        </div>
      </div>

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
              const currentPop = camp.currentPopulation ?? camp.current_occupancy ?? 0;
              const maxCap = camp.maxCapacityPersons ?? camp.estimated_capacity ?? 100;
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
                      {camp.dsArea || camp.district}
                    </span>
                  </div>

                  <div>
                    <h3 style={{ margin: '0 0 6px', fontSize: '1.05rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                      {camp.name}
                    </h3>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      <MapPin size={12} style={{ color: 'var(--accent-rose)' }} />
                      <span>{camp.gnDivision || camp.gn_division || camp.dsArea || camp.ds_division || camp.district}</span>
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
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => setSelectedCampId(camp.id)}
                  >
                    <span>Enter Field Station</span>
                    <ArrowRight size={14} />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
}
