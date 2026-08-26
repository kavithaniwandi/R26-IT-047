import React, { useState, useEffect } from 'react';
import { 
  MapPin, 
  Activity, 
  Layers, 
  Droplets, 
  Mountain, 
  ShieldAlert, 
  Tent, 
  Play, 
  CheckCircle2, 
  AlertCircle,
  Zap,
  Navigation
} from 'lucide-react';
import { api } from '../api';
import { RealTimeMap } from '../components/RealTimeMap';

export function HeatmapView() {
  const [heatmapData, setHeatmapData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Model 1 (Flood) Simulator state
  const [floodInput, setFloodInput] = useState({
    latitude: 6.936,
    longitude: 79.957,
    dist_to_kelani_km: 3.5,
    boggy_frac: 0.09,
    water_frac: 0.08,
    river_level_m: 4.2,
    rainfall_mm: 240.0,
    is_kelani_zone: 1,
  });
  const [floodResult, setFloodResult] = useState(null);
  const [floodLoading, setFloodLoading] = useState(false);

  // Model 2 (Landslide) Simulator state
  const [landslideInput, setLandslideInput] = useState({
    gn_name: 'Lakshapana',
    incident_count: 5,
    total_families: 12,
    total_people: 48,
    mean_families: 2.4,
    mean_people: 9.6,
    max_people: 22,
    std_people: 4.1,
    people_per_family: 4.0,
  });
  const [landslideResult, setLandslideResult] = useState(null);
  const [landslideLoading, setLandslideLoading] = useState(false);

  // Model 3 (Camp Suitability) Simulator state
  const [campInput, setCampInput] = useState({
    latitude: 6.947,
    longitude: 80.012,
    dist_to_road_km: 1.2,
    dist_to_hospital_km: 4.5,
    population_5km: 12000,
    elevation_m: 145,
  });
  const [campResult, setCampResult] = useState(null);
  const [campLoading, setCampLoading] = useState(false);

  // Model 4 (Priority Score) Simulator state
  const [priorityInput, setPriorityInput] = useState({
    urgency_level: 4,
    affected_people: 25,
    has_vulnerable: 1,
    hours_since_alert: 3,
    has_medical_emergency: 1,
    district_risk_tier: 3,
  });
  const [priorityResult, setPriorityResult] = useState(null);
  const [priorityLoading, setPriorityLoading] = useState(false);

  useEffect(() => {
    loadHeatmap();
  }, []);

  const loadHeatmap = async () => {
    setLoading(true);
    try {
      const data = await api.getHeatmap();
      setHeatmapData(data);
    } catch (err) {
      console.error('Heatmap load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunFloodModel = async (e) => {
    e.preventDefault();
    setFloodLoading(true);
    setFloodResult(null);
    try {
      const res = await api.predictFlood(floodInput);
      setFloodResult(res);
    } catch (err) {
      alert('Flood inference error: ' + err.message);
    } finally {
      setFloodLoading(false);
    }
  };

  const handleRunLandslideModel = async (e) => {
    e.preventDefault();
    setLandslideLoading(true);
    setLandslideResult(null);
    try {
      const res = await api.predictLandslide(landslideInput);
      setLandslideResult(res);
    } catch (err) {
      alert('Landslide inference error: ' + err.message);
    } finally {
      setLandslideLoading(false);
    }
  };

  const handleRunCampModel = async (e) => {
    e.preventDefault();
    setCampLoading(true);
    setCampResult(null);
    try {
      const res = await api.predictCampSuitability(campInput);
      setCampResult(res);
    } catch (err) {
      alert('Camp suitability inference error: ' + err.message);
    } finally {
      setCampLoading(false);
    }
  };

  const handleRunPriorityModel = async (e) => {
    e.preventDefault();
    setPriorityLoading(true);
    setPriorityResult(null);
    try {
      const res = await api.predictPriorityScore(priorityInput);
      setPriorityResult(res);
    } catch (err) {
      alert('Priority score inference error: ' + err.message);
    } finally {
      setPriorityLoading(false);
    }
  };

  return (
    <div>
      {/* Header Info */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 className="card-title">Live Geospatial Hazard Map & ML Inference Center</h2>
            <p className="card-subtitle">
              Real-Time Leaflet Map rendering OpenStreetMap tiles, Kelani Flood inundation buffer, NBRO Landslide zones & active SOS clusters
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn btn-secondary btn-sm" onClick={loadHeatmap}>
              <Activity size={14} />
              <span>Poll Sensors & Telemetry</span>
            </button>
          </div>
        </div>
      </div>

      {/* REAL-TIME INTERACTIVE MAP */}
      <div style={{ marginBottom: '24px' }}>
        <RealTimeMap
          sosPoints={heatmapData?.sos_clusters || []}
          hazardZones={heatmapData?.hazard_zones || []}
          camps={heatmapData?.medical_camps || []}
          height="540px"
          onRefresh={loadHeatmap}
          autoRefreshInterval={8000}
        />
      </div>

      {/* Spatial Clusters & ML Simulators */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Model 1: Flood Predictor */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="kpi-icon-wrap" style={{ backgroundColor: 'var(--accent-blue-subtle)', color: 'var(--accent-blue)' }}>
                <Droplets size={18} />
              </div>
              <div>
                <h3 className="card-title">Model 1: Flood Risk RF Predictor</h3>
                <p className="card-subtitle">Random Forest Classifier (Kelani River Basin Hydro Data)</p>
              </div>
            </div>
          </div>

          <form onSubmit={handleRunFloodModel}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div className="form-group">
                <label className="form-label">Rainfall (mm)</label>
                <input
                  type="number"
                  className="form-input"
                  value={floodInput.rainfall_mm}
                  onChange={(e) => setFloodInput({ ...floodInput, rainfall_mm: parseFloat(e.target.value) })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">River Level Stage (m)</label>
                <input
                  type="number"
                  step="0.1"
                  className="form-input"
                  value={floodInput.river_level_m}
                  onChange={(e) => setFloodInput({ ...floodInput, river_level_m: parseFloat(e.target.value) })}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div className="form-group">
                <label className="form-label">Dist to River Centroid (km)</label>
                <input
                  type="number"
                  step="0.1"
                  className="form-input"
                  value={floodInput.dist_to_kelani_km}
                  onChange={(e) => setFloodInput({ ...floodInput, dist_to_kelani_km: parseFloat(e.target.value) })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">In Kelani Basin Polygon?</label>
                <select
                  className="form-select"
                  value={floodInput.is_kelani_zone}
                  onChange={(e) => setFloodInput({ ...floodInput, is_kelani_zone: parseInt(e.target.value) })}
                >
                  <option value={1}>Yes (Inside Flood Perimeter)</option>
                  <option value={0}>No (Perimeter Zone)</option>
                </select>
              </div>
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '6px' }} disabled={floodLoading}>
              <Play size={14} />
              <span>{floodLoading ? 'Running Model 1 Inference...' : 'Execute Model 1 Inference'}</span>
            </button>
          </form>

          {floodResult && (
            <div style={{
              marginTop: '16px',
              padding: '14px',
              backgroundColor: 'var(--bg-secondary)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-accent)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: '700' }}>Predicted Risk Classification:</span>
                <span className={`badge ${floodResult.predicted_risk_tier === 'High' ? 'badge-critical' : floodResult.predicted_risk_tier === 'Medium' ? 'badge-medium' : 'badge-low'}`}>
                  {floodResult.predicted_risk_tier} RISK
                </span>
              </div>
              <div style={{ display: 'flex', gap: '8px', fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                <span>Probabilities: </span>
                <span>Low: {(floodResult.probabilities.Low * 100).toFixed(1)}%</span> · 
                <span>Med: {(floodResult.probabilities.Medium * 100).toFixed(1)}%</span> · 
                <span>High: {(floodResult.probabilities.High * 100).toFixed(1)}%</span>
              </div>
            </div>
          )}
        </div>

        {/* Model 2: Landslide Predictor */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="kpi-icon-wrap" style={{ backgroundColor: 'var(--accent-rose-subtle)', color: 'var(--accent-rose)' }}>
                <Mountain size={18} />
              </div>
              <div>
                <h3 className="card-title">Model 2: Landslide Risk RF Predictor</h3>
                <p className="card-subtitle">Trained on Verified NBRO Historical Records (Nuwara Eliya)</p>
              </div>
            </div>
          </div>

          <form onSubmit={handleRunLandslideModel}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div className="form-group">
                <label className="form-label">GN Division</label>
                <select
                  className="form-select"
                  value={landslideInput.gn_name}
                  onChange={(e) => setLandslideInput({ ...landslideInput, gn_name: e.target.value })}
                >
                  <option value="Lakshapana">Lakshapana (317A)</option>
                  <option value="Ginigathhena">Ginigathhena (315A)</option>
                  <option value="Kalugala">Kalugala (316C)</option>
                  <option value="Pitawala">Pitawala (316D)</option>
                  <option value="Millagahamula">Millagahamula (316E)</option>
                  <option value="Norton Bridge">Norton Bridge (318)</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Displaced People</label>
                <input
                  type="number"
                  className="form-input"
                  value={landslideInput.total_people}
                  onChange={(e) => setLandslideInput({ ...landslideInput, total_people: parseInt(e.target.value) })}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div className="form-group">
                <label className="form-label">Affected Families</label>
                <input
                  type="number"
                  className="form-input"
                  value={landslideInput.total_families}
                  onChange={(e) => setLandslideInput({ ...landslideInput, total_families: parseInt(e.target.value) })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Incident Recurrence Count</label>
                <input
                  type="number"
                  className="form-input"
                  value={landslideInput.incident_count}
                  onChange={(e) => setLandslideInput({ ...landslideInput, incident_count: parseInt(e.target.value) })}
                  required
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '6px' }} disabled={landslideLoading}>
              <Play size={14} />
              <span>{landslideLoading ? 'Running Model 2 Inference...' : 'Execute Model 2 Inference'}</span>
            </button>
          </form>

          {landslideResult && (
            <div style={{
              marginTop: '16px',
              padding: '14px',
              backgroundColor: 'var(--bg-secondary)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-accent)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: '700' }}>Landslide Severity Classification:</span>
                <span className={`badge ${landslideResult.predicted_risk_tier === 'High' ? 'badge-critical' : landslideResult.predicted_risk_tier === 'Medium' ? 'badge-medium' : 'badge-low'}`}>
                  {landslideResult.predicted_risk_tier} SEVERITY
                </span>
              </div>
              <div style={{ display: 'flex', gap: '8px', fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                <span>Probabilities: </span>
                <span>Low: {(landslideResult.probabilities.Low * 100).toFixed(1)}%</span> · 
                <span>Med: {(landslideResult.probabilities.Medium * 100).toFixed(1)}%</span> · 
                <span>High: {(landslideResult.probabilities.High * 100).toFixed(1)}%</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Model 3 & 4: Camp Suitability + Priority Scorer ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '4px' }}>

        {/* Model 3: Camp Suitability Scorer */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="kpi-icon-wrap" style={{ backgroundColor: 'var(--accent-emerald-subtle)', color: 'var(--accent-emerald)' }}>
                <Tent size={18} />
              </div>
              <div>
                <h3 className="card-title">Model 3: Camp Suitability Scorer</h3>
                <p className="card-subtitle">RF Regressor — Spatial Accessibility &amp; Infrastructure Score</p>
              </div>
            </div>
          </div>
          <form onSubmit={handleRunCampModel}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div className="form-group">
                <label className="form-label">Candidate Latitude</label>
                <input type="number" step="0.001" className="form-input" value={campInput.latitude}
                  onChange={(e) => setCampInput({ ...campInput, latitude: parseFloat(e.target.value) })} required />
              </div>
              <div className="form-group">
                <label className="form-label">Candidate Longitude</label>
                <input type="number" step="0.001" className="form-input" value={campInput.longitude}
                  onChange={(e) => setCampInput({ ...campInput, longitude: parseFloat(e.target.value) })} required />
              </div>
              <div className="form-group">
                <label className="form-label">Dist. to Main Road (km)</label>
                <input type="number" step="0.1" className="form-input" value={campInput.dist_to_road_km}
                  onChange={(e) => setCampInput({ ...campInput, dist_to_road_km: parseFloat(e.target.value) })} required />
              </div>
              <div className="form-group">
                <label className="form-label">Nearest Hospital (km)</label>
                <input type="number" step="0.1" className="form-input" value={campInput.dist_to_hospital_km}
                  onChange={(e) => setCampInput({ ...campInput, dist_to_hospital_km: parseFloat(e.target.value) })} required />
              </div>
              <div className="form-group">
                <label className="form-label">Population Within 5 km</label>
                <input type="number" className="form-input" value={campInput.population_5km}
                  onChange={(e) => setCampInput({ ...campInput, population_5km: parseInt(e.target.value) })} required />
              </div>
              <div className="form-group">
                <label className="form-label">Elevation (m)</label>
                <input type="number" className="form-input" value={campInput.elevation_m}
                  onChange={(e) => setCampInput({ ...campInput, elevation_m: parseInt(e.target.value) })} required />
              </div>
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '6px' }} disabled={campLoading}>
              <Play size={14} />
              <span>{campLoading ? 'Running Model 3 Inference...' : 'Execute Model 3 Inference'}</span>
            </button>
          </form>
          {campResult && (() => {
            const score = campResult.suitability_score ?? campResult.score ?? 0;
            const tier  = score >= 75 ? { label: 'High Suitability', cls: 'badge-low' }
                        : score >= 50 ? { label: 'Moderate',         cls: 'badge-medium' }
                        :               { label: 'Poor Location',    cls: 'badge-critical' };
            return (
              <div style={{ marginTop: '16px', padding: '14px', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-accent)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: '700' }}>Suitability Score:</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '1.4rem', fontWeight: '900', color: 'var(--accent-emerald)' }}>{score.toFixed(1)}</span>
                    <span className={`badge ${tier.cls}`}>{tier.label}</span>
                  </div>
                </div>
                <div className="progress-bar-bg">
                  <div className="progress-bar-fill" style={{ width: `${score}%`, backgroundColor: score >= 75 ? 'var(--accent-emerald)' : score >= 50 ? 'var(--accent-amber)' : 'var(--accent-rose)' }} />
                </div>
              </div>
            );
          })()}
        </div>

        {/* Model 4: SOS Priority Scorer */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="kpi-icon-wrap" style={{ backgroundColor: 'var(--accent-amber-subtle)', color: 'var(--accent-amber)' }}>
                <Zap size={18} />
              </div>
              <div>
                <h3 className="card-title">Model 4: SOS Priority Scorer</h3>
                <p className="card-subtitle">RF Regressor — Urgency × Vulnerability × Temporal Decay</p>
              </div>
            </div>
          </div>
          <form onSubmit={handleRunPriorityModel}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div className="form-group">
                <label className="form-label">Urgency Level (1–5)</label>
                <input type="number" min="1" max="5" className="form-input" value={priorityInput.urgency_level}
                  onChange={(e) => setPriorityInput({ ...priorityInput, urgency_level: parseInt(e.target.value) })} required />
              </div>
              <div className="form-group">
                <label className="form-label">Affected People</label>
                <input type="number" className="form-input" value={priorityInput.affected_people}
                  onChange={(e) => setPriorityInput({ ...priorityInput, affected_people: parseInt(e.target.value) })} required />
              </div>
              <div className="form-group">
                <label className="form-label">Vulnerable Present?</label>
                <select className="form-select" value={priorityInput.has_vulnerable}
                  onChange={(e) => setPriorityInput({ ...priorityInput, has_vulnerable: parseInt(e.target.value) })}>
                  <option value={1}>Yes — Elderly / Children / Disabled</option>
                  <option value={0}>No</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Hours Since Alert</label>
                <input type="number" step="0.5" className="form-input" value={priorityInput.hours_since_alert}
                  onChange={(e) => setPriorityInput({ ...priorityInput, hours_since_alert: parseFloat(e.target.value) })} required />
              </div>
              <div className="form-group">
                <label className="form-label">Medical Emergency?</label>
                <select className="form-select" value={priorityInput.has_medical_emergency}
                  onChange={(e) => setPriorityInput({ ...priorityInput, has_medical_emergency: parseInt(e.target.value) })}>
                  <option value={1}>Yes — Immediate Care Required</option>
                  <option value={0}>No</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">District Risk Tier</label>
                <select className="form-select" value={priorityInput.district_risk_tier}
                  onChange={(e) => setPriorityInput({ ...priorityInput, district_risk_tier: parseInt(e.target.value) })}>
                  <option value={3}>High Risk Zone</option>
                  <option value={2}>Medium Risk Zone</option>
                  <option value={1}>Low Risk Zone</option>
                </select>
              </div>
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '6px' }} disabled={priorityLoading}>
              <Play size={14} />
              <span>{priorityLoading ? 'Running Model 4 Scoring...' : 'Execute Model 4 Priority Scoring'}</span>
            </button>
          </form>
          {priorityResult && (() => {
            const score = priorityResult.priority_score ?? priorityResult.score ?? 0;
            const tier  = score >= 85 ? { label: 'CRITICAL PRIORITY', cls: 'badge-critical' }
                        : score >= 70 ? { label: 'HIGH PRIORITY',     cls: 'badge-medium' }
                        : score >= 50 ? { label: 'MODERATE',          cls: 'badge-low' }
                        :               { label: 'STANDARD',          cls: 'badge-low' };
            return (
              <div style={{ marginTop: '16px', padding: '14px', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-accent)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: '700' }}>Priority Score:</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '1.4rem', fontWeight: '900', color: 'var(--accent-amber)' }}>
                      {score.toFixed(1)} <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>/ 100</span>
                    </span>
                    <span className={`badge ${tier.cls}`}>{tier.label}</span>
                  </div>
                </div>
                <div className="progress-bar-bg">
                  <div className="progress-bar-fill" style={{ width: `${score}%`, backgroundColor: score >= 85 ? 'var(--accent-rose)' : score >= 70 ? 'var(--accent-amber)' : 'var(--accent-emerald)' }} />
                </div>
              </div>
            );
          })()}
        </div>

      </div>
    </div>
  );
}
