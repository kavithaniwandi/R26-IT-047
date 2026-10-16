import React, { useState, useEffect } from 'react';
import { 
  Tent, 
  Users, 
  MapPin, 
  ArrowLeft, 
  Zap, 
  Plus, 
  Upload, 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  CloudRain, 
  TrendingUp, 
  FileText, 
  RefreshCw,
  X,
  Layers,
  ChevronDown,
  ChevronUp,
  CalendarDays,
  Clock,
  Droplets,
  Waves,
  Thermometer
} from 'lucide-react';
import { api, API_BASE_URL, getAuthToken } from '../api';

const DISASTER_TYPES = ['Flood', 'Landslide'];
const SEVERITY_LEVELS = ['Low', 'Moderate', 'High', 'Critical'];

const getLatestHourlyEntries = (history, limit = 5) => {
  const entriesByHour = new Map();
  [...(history || [])]
    .filter((entry) =>
      entry?.timestamp
      && Number.isFinite(Number(entry.population))
      && ['manual', 'image_analysis'].includes(entry.source)
    )
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    .forEach((entry) => {
      const hourKey = Math.floor(new Date(entry.timestamp).getTime() / 3600000);
      if (!entriesByHour.has(hourKey)) entriesByHour.set(hourKey, entry);
    });
  return [...entriesByHour.values()].slice(0, limit);
};

export function ReliefCampDetailView({ campId, onBack, currentUser, onAddToast }) {
  const token = getAuthToken() || '';

  // Relief Camp & Requests State
  const [camp, setCamp] = useState(null);
  const [campRequests, setCampRequests] = useState([]);
  const [catalogItems, setCatalogItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  // Collapsible Population Tools Accordion State
  const [isToolsExpanded, setIsToolsExpanded] = useState(false);

  // 1. Manual Entry State
  const [manualCount, setManualCount] = useState(0);
  const [savingManual, setSavingManual] = useState(false);

  // 2. Multi-Photo Crowd AI State
  const [crowdFiles, setCrowdFiles] = useState([]);
  const [isBatchAnalyzing, setIsBatchAnalyzing] = useState(false);
  const [analyzingFileId, setAnalyzingFileId] = useState(null);

  // 3. Influx Predictor AI State
  const [popHistory, setPopHistory] = useState([0, 0, 0, 0, 0, 0, 0]);
  const [rainHistory, setRainHistory] = useState([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]);
  const [riverLevel, setRiverLevel] = useState(5.2);
  const [hourOfDay, setHourOfDay] = useState(new Date().getHours());
  const [predSeverity, setPredSeverity] = useState('High');
  const [predictionResult, setPredictionResult] = useState(null);
  const [predicting, setPredicting] = useState(false);
  const [applyingPrediction, setApplyingPrediction] = useState(false);
  const [syncingEnvironment, setSyncingEnvironment] = useState(false);
  const [environmentData, setEnvironmentData] = useState(null);
  const [weatherStatus, setWeatherStatus] = useState('');

  // Create Donation Request Modal State
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false);
  const [populationBasis, setPopulationBasis] = useState('current');
  const [reqDisasterType, setReqDisasterType] = useState('Flood');
  const [reqSeverity, setReqSeverity] = useState('High');
  const [selectedCatalogItemKeys, setSelectedCatalogItemKeys] = useState([]);
  const [submittingRequest, setSubmittingRequest] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const authHeaders = { Authorization: `Bearer ${token}` };

      const [campRes, reqsRes, itemsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/relief-camps/${campId}`, { headers: authHeaders }),
        fetch(`${API_BASE_URL}/disaster-donation-requests`, { headers: authHeaders }),
        fetch(`${API_BASE_URL}/donation-items`, { headers: authHeaders }),
      ]);

      if (!campRes.ok) {
        const errData = await campRes.json();
        throw new Error(errData.detail || 'Relief Camp not found or access denied');
      }

      const campData = await campRes.json();
      setCamp(campData);
      setManualCount(campData.currentPopulation || 0);

      if (campData.hourlyHistory && campData.hourlyHistory.length > 0) {
        const historyPops = getLatestHourlyEntries(campData.hourlyHistory, 7)
          .map((entry) => entry.population);
        setPopHistory(historyPops);
      } else {
        setPopHistory([]);
      }

      if (reqsRes.ok) {
        const allReqs = await reqsRes.json();
        const filtered = allReqs.filter(
          (r) => r.reliefCamp?.trim().toLowerCase() === campData.name?.trim().toLowerCase()
        );
        setCampRequests(filtered);
      }

      if (itemsRes.ok) {
        const items = await itemsRes.json();
        setCatalogItems(items);
      }
    } catch (err) {
      console.error('Error loading camp detail:', err);
      setErrorMsg(err.message || 'Error loading relief camp');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [campId]);

  // --- MANUAL UPDATE ---
  const handleSaveManual = async () => {
    if (!camp) return;
    setSavingManual(true);
    try {
      const updated = await api.updateReliefCampPopulation(camp.id, {
        currentPopulation: Number(manualCount),
        observationSource: 'manual',
      });
      setCamp(updated);
      setManualCount(updated.currentPopulation);
      setPopHistory(getLatestHourlyEntries(updated.hourlyHistory, 7).map((entry) => entry.population));
      if (onAddToast) onAddToast(`Manual population updated to ${updated.currentPopulation} people.`, 'success', 'Population Saved');
    } catch (err) {
      if (onAddToast) onAddToast(err.message || 'Failed to update population', 'error', 'Update Failed');
    } finally {
      setSavingManual(false);
    }
  };

  // --- MULTI-PHOTO CROWD AI ---
  const handleImageFileAdd = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    const newEntries = files.map((file) => ({
      id: Math.random().toString(36).substring(2, 9),
      file: file,
      preview: URL.createObjectURL(file),
      detectedCount: null,
      annotatedUrl: null,
      isVerified: false,
    }));

    setCrowdFiles((prev) => [...prev, ...newEntries]);
  };

  const handleAnalyzeAllPhotosSequential = async () => {
    if (crowdFiles.length === 0) return;
    setIsBatchAnalyzing(true);

    for (let i = 0; i < crowdFiles.length; i++) {
      const current = crowdFiles[i];
      setAnalyzingFileId(current.id);

      try {
        const formData = new FormData();
        formData.append('file', current.file);

        const res = await fetch(`${API_BASE_URL}/population/count`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });

        if (!res.ok) throw new Error('Analysis failed');
        const data = await res.json();

        setCrowdFiles((prev) =>
          prev.map((item) =>
            item.id === current.id
              ? {
                  ...item,
                  detectedCount: data.person_count || 0,
                  annotatedUrl: data.annotated_image_url || item.preview,
                  isVerified: true,
                }
              : item
          )
        );
      } catch (err) {
        console.error(`Error analyzing photo ${i + 1}:`, err);
      }
    }

    setAnalyzingFileId(null);
    setIsBatchAnalyzing(false);
  };

  const handleRemoveCrowdFile = (id) => {
    setCrowdFiles((prev) => prev.filter((item) => item.id !== id));
  };

  const totalVerifiedCrowd = crowdFiles.reduce(
    (sum, item) => sum + (item.detectedCount !== null ? item.detectedCount : 0),
    0
  );

  const handleApplyCrowdTotal = async () => {
    if (totalVerifiedCrowd <= 0 && crowdFiles.length > 0) {
      if (onAddToast) onAddToast('Please run analysis before applying total count.', 'error', 'Action Blocked');
      return;
    }

    try {
      const updated = await api.updateReliefCampPopulation(camp.id, {
        currentPopulation: totalVerifiedCrowd,
        observationSource: 'image_analysis',
      });
      setCamp(updated);
      setManualCount(updated.currentPopulation);
      setPopHistory(getLatestHourlyEntries(updated.hourlyHistory, 7).map((entry) => entry.population));
      if (onAddToast) onAddToast(`Verified AI crowd count of ${totalVerifiedCrowd} applied!`, 'success', 'AI Count Applied');
    } catch (err) {
      if (onAddToast) onAddToast(err.message || 'Failed to apply detected crowd count', 'error', 'Action Failed');
    }
  };

  // --- INFLUX PREDICTOR AI ---
  const handleEnvironmentSync = async (silent = false) => {
    setSyncingEnvironment(true);
    if (!silent) setWeatherStatus('Syncing Kaduwela weather and Kelani River conditions...');
    try {
      const res = await fetch(`${API_BASE_URL}/relief-camps/environment/kelani`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed to retrieve live environmental data');
      const data = await res.json();
      const newRains = [...(data.rainHistory || [])].slice(0, 7);
      while (newRains.length < 7) newRains.push(0);
      const liveRiverLevel = Number(data.river?.levelM);

      setRainHistory(newRains);
      if (data.river?.available && Number.isFinite(liveRiverLevel)) {
        setRiverLevel(liveRiverLevel);
      }
      setHourOfDay(new Date().getHours());
      setEnvironmentData(data);
      setWeatherStatus(
        data.river?.available
          ? 'Live weather, rainfall, and Hanwella gauge data synchronized.'
          : 'Weather and rainfall synchronized; live river gauge is temporarily unavailable.'
      );
      return {
        rainHistory: newRains,
        riverLevel: data.river?.available && Number.isFinite(liveRiverLevel)
          ? liveRiverLevel
          : riverLevel,
        temperatureC: data.weather?.temperatureC,
        humidityPercent: data.weather?.humidityPercent,
        weatherCode: data.weather?.weatherCode,
      };
    } catch (err) {
      setWeatherStatus('Live conditions unavailable. The forecast will use the last synchronized values.');
      return null;
    } finally {
      setSyncingEnvironment(false);
    }
  };

  const handlePredictProgression = async () => {
    if (!camp) return;
    if (popHistory.length < 5) {
      if (onAddToast) {
        onAddToast(
          `Collect ${5 - popHistory.length} more hourly population observation${5 - popHistory.length === 1 ? '' : 's'} before forecasting.`,
          'warning',
          'More Observations Required'
        );
      }
      return;
    }
    setPredicting(true);
    try {
      const liveInputs = await handleEnvironmentSync(true);
      const res = await fetch(`${API_BASE_URL}/relief-camps/predict-population`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          currentPopulation: Number(popHistory[0] || camp.currentPopulation),
          maxCapacity: Number(camp.maxCapacityPersons),
          popHistory: popHistory.slice(0, 5),
          rainHistory: liveInputs?.rainHistory || rainHistory,
          riverLevel: Number(liveInputs?.riverLevel ?? riverLevel),
          temperatureC: liveInputs?.temperatureC ?? environmentData?.weather?.temperatureC,
          humidityPercent: liveInputs?.humidityPercent ?? environmentData?.weather?.humidityPercent,
          weatherCode: liveInputs?.weatherCode ?? environmentData?.weather?.weatherCode,
          hourOfDay: Number(hourOfDay),
          severity: predSeverity,
        }),
      });

      if (!res.ok) throw new Error('Forecast service rejected the request');
      const data = await res.json();
      setPredictionResult(data);
    } catch (err) {
      if (onAddToast) onAddToast('Error running next-hour prediction', 'error', 'Prediction Failed');
    } finally {
      setPredicting(false);
    }
  };

  const handleSavePredictedToCamp = async () => {
    if (!predictionResult || !camp) return;
    setApplyingPrediction(true);
    try {
      const updated = await api.updateReliefCampPopulation(camp.id, {
        predictedPopulation: predictionResult.predictedPopulation,
      });
      setCamp(updated);
      if (onAddToast) onAddToast(`Predicted population updated to ${updated.predictedPopulation} people.`, 'success', 'Prediction Applied');
    } catch (err) {
      if (onAddToast) onAddToast(err.message || 'Failed to save predicted population', 'error', 'Update Failed');
    } finally {
      setApplyingPrediction(false);
    }
  };

  // --- CREATE DONATION REQUEST ---
  const toggleCatalogItem = (itemKey) => {
    setSelectedCatalogItemKeys((prev) =>
      prev.includes(itemKey) ? prev.filter((k) => k !== itemKey) : [...prev, itemKey]
    );
  };

  const chosenPopulationForRequest =
    populationBasis === 'predicted'
      ? Math.max(camp?.predictedPopulation || camp?.currentPopulation || 1, 1)
      : Math.max(camp?.currentPopulation || 1, 1);

  const handleCreateRequestSubmit = async (e) => {
    e.preventDefault();
    if (!camp) return;

    const selectedItems = catalogItems.filter((i) =>
      selectedCatalogItemKeys.includes(i.itemId || i.item)
    );

    if (selectedItems.length === 0) {
      if (onAddToast) onAddToast('Please select at least one relief item.', 'error', 'Selection Required');
      return;
    }

    const payload = {
      disasterType: reqDisasterType,
      severity: reqSeverity,
      dsArea: camp.dsArea,
      gnDivision: camp.gnDivision,
      reliefCamp: camp.name,
      people_count: chosenPopulationForRequest,
      items: selectedItems.map((i) => ({
        itemId: i.itemId,
        itemName: i.item,
        unit: i.unit,
        // Supplies are requested as whole units. Rounding up also prevents
        // floating-point artifacts such as 0.1 * 34 = 3.4000000000000004.
        neededQuantity: Math.ceil(
          (Number(i.quantityPerPerson) || 1) * chosenPopulationForRequest
        ),
      })),
    };

    setSubmittingRequest(true);
    try {
      const res = await fetch(`${API_BASE_URL}/disaster-donation-requests`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to submit request');
      }

      if (onAddToast) onAddToast('Disaster Donation Request published successfully!', 'success', 'Request Published');
      setIsRequestModalOpen(false);
      setSelectedCatalogItemKeys([]);
      loadData();
    } catch (err) {
      if (onAddToast) onAddToast(err.message || 'Error publishing request', 'error', 'Publish Failed');
    } finally {
      setSubmittingRequest(false);
    }
  };

  const latestFiveObservations = getLatestHourlyEntries(camp?.hourlyHistory, 5).reverse();
  const hasForecastHistory = latestFiveObservations.length === 5;
  const observationSlots = [
    ...Array(Math.max(0, 5 - latestFiveObservations.length)).fill(null),
    ...latestFiveObservations,
  ];
  const predictedFor = new Date(
    predictionResult?.forecastFor
      || new Date(camp?.lastUpdated || 0).getTime() + 60 * 60 * 1000
  );

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
        Loading Relief Camp Details...
      </div>
    );
  }

  if (errorMsg || !camp) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '40px 20px' }}>
        <AlertTriangle size={40} style={{ color: 'var(--accent-rose)', marginBottom: '12px' }} />
        <h3 style={{ color: 'var(--accent-rose)', margin: '0 0 8px' }}>{errorMsg || 'Relief Camp Not Found'}</h3>
        <button className="btn btn-secondary btn-sm" onClick={onBack} style={{ marginTop: '14px' }}>
          <ArrowLeft size={14} />
          <span>Back to Assigned Camps</span>
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button className="btn btn-secondary btn-sm" onClick={onBack}>
          <ArrowLeft size={14} />
          <span>Back to Assigned Camps</span>
        </button>
        <span className="font-mono" style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          Last Synced: {new Date(camp.lastUpdated || Date.now()).toLocaleTimeString()}
        </span>
      </div>

      {/* Hero Banner */}
      <div style={{
        background: 'linear-gradient(135deg, hsla(217, 91%, 60%, 0.15), hsla(220, 20%, 14%, 1))',
        border: '1px solid hsla(217, 91%, 60%, 0.35)',
        borderRadius: 'var(--radius-xl)',
        padding: '24px 28px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '20px'
      }}>
        <div>
          <span style={{ fontSize: '0.72rem', color: 'var(--accent-blue)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Relief Shelter Station
          </span>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '800', margin: '4px 0 6px', color: 'var(--text-primary)' }}>{camp.name}</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            <MapPin size={14} style={{ color: 'var(--accent-rose)' }} />
            <span>{camp.gnDivision} • {camp.dsArea} DS Office</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '12px 18px', textAlign: 'center', minWidth: '110px' }}>
            <span style={{ display: 'block', fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: '700', textTransform: 'uppercase' }}>Sheltered</span>
            <strong style={{ fontSize: '1.6rem', color: 'var(--text-primary)' }}>{camp.currentPopulation}</strong>
          </div>
          <div style={{ background: 'var(--accent-blue-subtle)', border: '1px solid hsla(217, 91%, 60%, 0.35)', borderRadius: 'var(--radius-lg)', padding: '12px 18px', textAlign: 'center', minWidth: '110px' }}>
            <span style={{ display: 'block', fontSize: '0.68rem', color: 'var(--accent-blue)', fontWeight: '700', textTransform: 'uppercase' }}>Predicted</span>
            <strong style={{ fontSize: '1.6rem', color: 'var(--accent-blue)' }}>{camp.predictedPopulation || camp.currentPopulation}</strong>
          </div>
          <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '12px 18px', textAlign: 'center', minWidth: '110px' }}>
            <span style={{ display: 'block', fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: '700', textTransform: 'uppercase' }}>Max Capacity</span>
            <strong style={{ fontSize: '1.6rem', color: 'var(--text-primary)' }}>{camp.maxCapacityPersons}</strong>
          </div>
        </div>
      </div>

      {/* Collapsible Population Tools Accordion */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div
          onClick={() => setIsToolsExpanded(!isToolsExpanded)}
          style={{
            padding: '16px 20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            cursor: 'pointer',
            backgroundColor: isToolsExpanded ? 'var(--bg-secondary)' : 'transparent',
            borderBottom: isToolsExpanded ? '1px solid var(--border-subtle)' : 'none',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Zap size={18} style={{ color: 'var(--accent-amber)' }} />
            <div>
              <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                Population Management & AI Tools
              </h3>
              <p style={{ margin: '2px 0 0', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Manual head count, photo crowd estimation, or influx forecasting
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-blue)', fontWeight: '700', fontSize: '0.82rem' }}>
            <span>{isToolsExpanded ? 'Collapse Tools' : 'Open Tools'}</span>
            {isToolsExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </div>
        </div>

        {isToolsExpanded && (
          <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* 1. Manual Entry */}
            <div style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '16px' }}>
              <h4 style={{ margin: '0 0 6px', fontSize: '0.95rem', fontWeight: '700' }}>Add Population Manually</h4>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '0 0 12px' }}>
                Set verified headcount (can exceed max capacity for overflow shelters).
              </p>
              <div style={{ display: 'flex', gap: '10px', maxWidth: '380px' }}>
                <input
                  type="number"
                  min="0"
                  className="form-input"
                  value={manualCount}
                  onChange={(e) => setManualCount(e.target.value)}
                />
                <button className="btn btn-primary btn-sm" onClick={handleSaveManual} disabled={savingManual}>
                  {savingManual ? 'Saving...' : 'Update Count'}
                </button>
              </div>
            </div>

            {/* 2. Photo Crowd AI */}
            <div style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '14px' }}>
                <div>
                  <h4 style={{ margin: '0 0 4px', fontSize: '0.95rem', fontWeight: '700' }}>Detect Crowd Using Images</h4>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
                    Upload crowd images and run the YOLO model for automated headcounts.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <label className="btn btn-secondary btn-sm" style={{ cursor: 'pointer' }}>
                    <Plus size={14} />
                    <span>Add Photos</span>
                    <input type="file" multiple accept="image/*" style={{ display: 'none' }} onChange={handleImageFileAdd} />
                  </label>
                  {crowdFiles.length > 0 && (
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={handleAnalyzeAllPhotosSequential}
                      disabled={isBatchAnalyzing}
                    >
                      <Sparkles size={14} />
                      <span>{isBatchAnalyzing ? 'Analyzing...' : 'Analyze All Photos'}</span>
                    </button>
                  )}
                </div>
              </div>

              {crowdFiles.length > 0 && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px', marginBottom: '14px' }}>
                  {crowdFiles.map((item, idx) => (
                    <div key={item.id} style={{ border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', overflow: 'hidden', backgroundColor: 'var(--bg-card)' }}>
                      <div style={{ position: 'relative', height: '240px', backgroundColor: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <img
                          src={item.annotatedUrl || item.preview}
                          alt={`Zone ${idx + 1}`}
                          style={{ width: '100%', height: '100%', objectFit: 'contain', objectPosition: 'center' }}
                        />
                        <button
                          onClick={() => handleRemoveCrowdFile(item.id)}
                          style={{ position: 'absolute', top: '8px', right: '8px', background: 'rgba(0,0,0,0.6)', color: 'white', border: 'none', borderRadius: '50%', width: '24px', height: '24px', cursor: 'pointer' }}
                        >
                          ✕
                        </button>
                      </div>
                      <div style={{ padding: '10px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.8rem', fontWeight: '600' }}>Zone #{idx + 1}</span>
                        {item.detectedCount !== null ? (
                          <span className="badge badge-low">✓ {item.detectedCount} Detected</span>
                        ) : (
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Queued</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {crowdFiles.length > 0 && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--accent-blue)', fontWeight: '700' }}>
                    Total Verified Detections: {totalVerifiedCrowd}
                  </span>
                  <button className="btn btn-success btn-sm" onClick={handleApplyCrowdTotal}>
                    <CheckCircle2 size={14} />
                    <span>Apply Count ({totalVerifiedCrowd})</span>
                  </button>
                </div>
              )}
            </div>

            {/* 3. Influx Predictor AI */}
            <div className="population-forecast-panel">
              <div className="population-forecast-header">
                <div>
                  <h4>Next-Hour Population Forecast</h4>
                  <p>Five latest hourly headcounts followed by the next-hour forecast.</p>
                </div>
                <button className="btn btn-secondary btn-sm" onClick={() => handleEnvironmentSync(false)} disabled={syncingEnvironment}>
                  <CloudRain size={13} />
                  <span>{syncingEnvironment ? 'Syncing...' : 'Sync Live Conditions'}</span>
                </button>
              </div>

              {weatherStatus && (
                <div className="population-forecast-status">{weatherStatus}</div>
              )}

              <div className="population-hour-grid">
                {observationSlots.map((entry, index) => (
                  <div className={`population-hour-card ${entry ? '' : 'empty'}`} key={entry?.timestamp || `empty-${index}`}>
                    <span className="population-hour-card__step">Hour {index + 1}</span>
                    {entry ? (
                      <>
                        <div className="population-hour-card__date">
                          <CalendarDays size={13} />
                          {new Date(entry.timestamp).toLocaleDateString('en-GB', {
                            timeZone: 'Asia/Colombo', day: '2-digit', month: 'short', year: 'numeric'
                          })}
                        </div>
                        <div className="population-hour-card__time">
                          <Clock size={13} />
                          {new Date(entry.timestamp).toLocaleTimeString('en-US', {
                            timeZone: 'Asia/Colombo', hour: '2-digit', minute: '2-digit'
                          })}
                        </div>
                        <strong>{entry.population}</strong>
                        <small>{entry.source === 'image_analysis' ? 'Image analysis' : entry.source === 'manual' ? 'Manual count' : 'Verified count'}</small>
                      </>
                    ) : (
                      <div className="population-hour-card__empty">Awaiting hourly observation</div>
                    )}
                  </div>
                ))}

                <div className="population-hour-card population-hour-card--prediction">
                  <span className="population-hour-card__step">Next Hour</span>
                  <div className="population-hour-card__date">
                    <CalendarDays size={13} />
                    {predictedFor.toLocaleDateString('en-GB', {
                      timeZone: 'Asia/Colombo', day: '2-digit', month: 'short', year: 'numeric'
                    })}
                  </div>
                  <div className="population-hour-card__time">
                    <Clock size={13} />
                    {predictedFor.toLocaleTimeString('en-US', {
                      timeZone: 'Asia/Colombo', hour: '2-digit', minute: '2-digit'
                    })}
                  </div>
                  <strong>{predictionResult?.predictedPopulation ?? '—'}</strong>
                  <small>{predictionResult ? `${predictionResult.delta >= 0 ? '+' : ''}${predictionResult.delta} expected` : 'Run forecast'}</small>
                </div>
              </div>

              <div className="population-environment-grid">
                <div className="population-environment-card">
                  <Thermometer size={18} />
                  <span>Kaduwela weather</span>
                  <strong>{environmentData?.weather?.available ? `${environmentData.weather.temperatureC}°C` : 'Not synced'}</strong>
                  <small>{environmentData?.weather?.available ? `${environmentData.weather.humidityPercent}% humidity · Open-Meteo` : 'Sync to load current weather'}</small>
                </div>
                <div className="population-environment-card">
                  <Droplets size={18} />
                  <span>Latest rainfall</span>
                  <strong>{rainHistory[0] || 0} mm</strong>
                  <small>Recent 3-hour average is used by the forecast</small>
                </div>
                <div className="population-environment-card">
                  <Waves size={18} />
                  <span>Kelani River · Hanwella</span>
                  <strong>{Number(riverLevel).toFixed(2)} m</strong>
                  <small>
                    {environmentData?.river?.available
                      ? `${String(environmentData.river.status || 'normal').replaceAll('_', ' ')} · ${environmentData.river.isRising ? 'rising' : 'stable/falling'}`
                      : 'Last/default value; live gauge unavailable'}
                  </small>
                </div>
              </div>

              <div className="population-forecast-actions">
                <button className="btn btn-primary btn-sm" onClick={handlePredictProgression} disabled={predicting || syncingEnvironment || !hasForecastHistory}>
                  <TrendingUp size={14} />
                  <span>{predicting ? 'Computing...' : 'Predict Next-Hour Population'}</span>
                </button>
                {predictionResult && (
                  <button className="btn btn-secondary btn-sm" onClick={handleSavePredictedToCamp} disabled={applyingPrediction}>
                    <span>{applyingPrediction ? 'Applying...' : 'Apply Prediction'}</span>
                  </button>
                )}
              </div>

              {!hasForecastHistory && (
                <div className="population-forecast-history-warning">
                  {latestFiveObservations.length}/5 real hourly observations collected. Add a verified manual or image-analysis count during each hour to enable forecasting.
                </div>
              )}

              {predictionResult && (
                <div className="population-forecast-explanation">
                  <strong>Forecast inputs</strong>
                  <span>Hourly growth: {predictionResult.factors?.averageHourlyGrowth ?? 0} people/hour</span>
                  <span>Recent rain: {predictionResult.factors?.recentRainfallMm ?? 0} mm</span>
                  <span>River level: {predictionResult.factors?.riverLevelM ?? riverLevel} m</span>
                  <p>{predictionResult.note}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Donation Requests Section */}
      <div className="card">
        <div className="card-header" style={{ flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h2 className="card-title">Donation Requests</h2>
            <p className="card-subtitle">Relief item requests scaled by camp population</p>
          </div>
          <button className="btn btn-primary btn-sm" onClick={() => setIsRequestModalOpen(true)}>
            <Plus size={14} />
            <span>Add Donation Request</span>
          </button>
        </div>

        {campRequests.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
            No donation requests published for this camp yet.
          </div>
        ) : (
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Request ID</th>
                  <th>Disaster</th>
                  <th>Severity</th>
                  <th>Population</th>
                  <th>Items Requested</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {campRequests.map((req) => (
                  <tr key={req.id}>
                    <td style={{ fontWeight: '700' }}>#{req.id.slice(-6).toUpperCase()}</td>
                    <td>{req.disasterType}</td>
                    <td><span className="badge badge-medium">{req.severity}</span></td>
                    <td>{req.people_count} people</td>
                    <td style={{ fontSize: '0.8rem' }}>
                      {req.items?.map((i, idx) => (
                        <div key={idx}>• {i.itemName}: <strong>{i.neededQuantity}</strong> {i.unit}</div>
                      ))}
                    </td>
                    <td>
                      <span className={`badge ${req.status === 'fulfilled' ? 'badge-low' : 'badge-medium'}`}>
                        {req.status === 'fulfilled' ? 'Fulfilled' : 'Pending'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Publish Request */}
      {isRequestModalOpen && (
        <div className="modal-overlay" onClick={() => setIsRequestModalOpen(false)}>
          <div className="modal-content relief-request-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header relief-request-modal__header">
              <div className="relief-request-modal__heading">
                <span className="relief-request-modal__icon"><CloudRain size={22} /></span>
                <div>
                  <span className="relief-request-modal__eyebrow">CAMP SUPPLY REQUEST</span>
                  <h2 className="modal-title">Publish Relief Request</h2>
                  <p>Choose the population basis, disaster details, and required supplies.</p>
                </div>
              </div>
              <button type="button" className="modal-close-btn" onClick={() => setIsRequestModalOpen(false)} aria-label="Close request form">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCreateRequestSubmit} className="relief-request-form">
              <section className="relief-request-section relief-request-section--population">
                <div className="relief-request-section__heading">
                  <div>
                    <h3>Population basis</h3>
                    <p>Quantities will be calculated using this headcount.</p>
                  </div>
                </div>
                <div className="relief-request-population-grid">
                <button
                  type="button"
                  onClick={() => setPopulationBasis('current')}
                  className={`relief-request-population-card ${populationBasis === 'current' ? 'active' : ''}`}
                  aria-pressed={populationBasis === 'current'}
                >
                  <span>CURRENT POPULATION</span>
                  <strong>{camp.currentPopulation} <small>people</small></strong>
                  {populationBasis === 'current' && <CheckCircle2 size={18} />}
                </button>
                <button
                  type="button"
                  onClick={() => setPopulationBasis('predicted')}
                  className={`relief-request-population-card ${populationBasis === 'predicted' ? 'active' : ''}`}
                  aria-pressed={populationBasis === 'predicted'}
                >
                  <span>PREDICTED POPULATION</span>
                  <strong>{camp.predictedPopulation || camp.currentPopulation} <small>people</small></strong>
                  {populationBasis === 'predicted' && <CheckCircle2 size={18} />}
                </button>
                </div>
              </section>

              <section className="relief-request-section relief-request-section--details">
                <div className="relief-request-section__heading">
                  <div>
                    <h3>Request details</h3>
                    <p>This project accepts flood and landslide relief requests.</p>
                  </div>
                </div>
                <div className="relief-request-field-grid">
                  <div className="relief-request-field relief-request-field--disaster">
                    <label className="form-label">Disaster Type</label>
                    <div className="relief-request-select-wrap">
                      <select className="form-input" value={reqDisasterType} onChange={(e) => setReqDisasterType(e.target.value)}>
                        {DISASTER_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                      </select>
                    </div>
                  </div>
                  <div className={`relief-request-field relief-request-field--severity severity-${reqSeverity.toLowerCase()}`}>
                    <label className="form-label">Severity Level</label>
                    <div className="relief-request-select-wrap">
                      <select className="form-input" value={reqSeverity} onChange={(e) => setReqSeverity(e.target.value)}>
                        {SEVERITY_LEVELS.map((s) => <option key={s} value={s}>{s}</option>)}
                      </select>
                    </div>
                  </div>
                </div>
              </section>

              <section className="relief-request-section relief-request-section--catalog relief-request-catalog">
                <div className="relief-request-section__heading">
                  <div>
                    <h3>Required relief items</h3>
                    <p>Select every supply category needed by this camp.</p>
                  </div>
                  <span className="relief-request-selected-count">
                    <Layers size={14} /> {selectedCatalogItemKeys.length} selected
                  </span>
                </div>
                <div className="relief-request-item-grid">
                  {catalogItems.map((item) => {
                    const key = item.itemId || item.item;
                    const isChecked = selectedCatalogItemKeys.includes(key);
                    return (
                      <label key={key} className={`relief-request-item ${isChecked ? 'selected' : ''}`}>
                        <input type="checkbox" checked={isChecked} onChange={() => toggleCatalogItem(key)} />
                        <span>{item.item}</span>
                        {isChecked && <CheckCircle2 size={16} />}
                      </label>
                    );
                  })}
                </div>
              </section>

              <div className="relief-request-actions">
                <span>Request for <strong>{chosenPopulationForRequest} people</strong></span>
                <div>
                  <button type="button" className="btn btn-secondary btn-sm" onClick={() => setIsRequestModalOpen(false)}>Cancel</button>
                  <button type="submit" className="btn btn-primary btn-sm" disabled={submittingRequest}>
                  {submittingRequest ? 'Publishing...' : 'Publish Request'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
