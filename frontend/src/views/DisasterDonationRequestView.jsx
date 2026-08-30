import React, { useState, useEffect } from 'react';
import './DisasterDonationRequest.css';

const DISASTER_TYPES = ['Flood', 'Landslide', 'Tsunami', 'Drought', 'Fire', 'Other'];
const SEVERITY_LEVELS = ['Low', 'Moderate', 'High', 'Critical'];

export function DisasterDonationRequestView({ currentUser, onAddToast }) {
  const [step, setStep] = useState('dashboard');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [viewRequestModal, setViewRequestModal] = useState(null);

  // Dynamic Division Data from Database
  const [divisionsData, setDivisionsData] = useState([]);
  const [dsAreas, setDsAreas] = useState([]);
  const [gnDivisionsList, setGnDivisionsList] = useState([]);
  const [divisionsLoading, setDivisionsLoading] = useState(false);

  // Form State
  const [disasterType, setDisasterType] = useState('Flood');
  const [dsArea, setDsArea] = useState('');
  const [gnDivision, setGnDivision] = useState('');
  const [reliefCamp, setReliefCamp] = useState('');
  const [gnSearch, setGnSearch] = useState('');
  const [locationCount, setLocationCount] = useState(1);
  const [severity, setSeverity] = useState('High');

  // Upload & Estimation State
  const [rawFiles, setRawFiles] = useState(Array(5).fill(null));
  const [images, setImages] = useState(Array(5).fill(null));
  const [analysisData, setAnalysisData] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [draggingIndex, setDraggingIndex] = useState(null);
  const [donationItems, setDonationItems] = useState([]);
  const [selectedDonationItems, setSelectedDonationItems] = useState([]);
  const [donationItemsLoading, setDonationItemsLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Requests Table State
  const [donationRequests, setDonationRequests] = useState([]);
  const [requestsLoading, setRequestsLoading] = useState(false);
  const [searchTableQuery, setSearchTableQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const totalPopulation = analysisData.reduce((sum, item) => sum + (item?.population ?? 0), 0);

  // Fetch All Administrative Divisions
  const fetchDivisions = async () => {
    setDivisionsLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/divisions');
      if (response.ok) {
        const data = await response.json();
        setDivisionsData(data);
        if (Array.isArray(data) && data.length > 0) {
          const areaNames = data.map((d) => d.dsArea);
          setDsAreas(areaNames);
          setDsArea(areaNames[0]);
          setGnDivisionsList(data[0].gnDivisions || []);
          setGnDivision(data[0].gnDivisions?.[0] || '');
        }
      }
    } catch (err) {
      console.error('Error loading administrative divisions:', err);
    } finally {
      setDivisionsLoading(false);
    }
  };

  // Fetch Disaster Requests
  const fetchAllRequests = async () => {
    setRequestsLoading(true);
    const token = localStorage.getItem('token') || localStorage.getItem('access_token') || '';
    try {
      const response = await fetch('http://127.0.0.1:8000/disaster-donation-requests', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        if (Array.isArray(data)) {
          setDonationRequests(data);
        }
      }
    } catch (err) {
      console.error('Error fetching disaster donation requests:', err);
    } finally {
      setRequestsLoading(false);
    }
  };

  // Fetch Catalog Donation Items
  const loadDonationItems = async () => {
    setDonationItemsLoading(true);
    const token = localStorage.getItem('token') || localStorage.getItem('access_token') || '';
    try {
      const response = await fetch('http://127.0.0.1:8000/donation-items', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const items = await response.json();
        setDonationItems(items);
      }
    } catch (error) {
      console.error('Unable to fetch donation items:', error);
    } finally {
      setDonationItemsLoading(false);
    }
  };

  useEffect(() => {
    fetchDivisions();
    fetchAllRequests();
    loadDonationItems();
  }, []);

  const handleDsAreaChange = (e) => {
    const selectedArea = e.target.value;
    setDsArea(selectedArea);
    setGnSearch('');

    const matched = divisionsData.find((d) => d.dsArea === selectedArea);
    const gnList = matched ? matched.gnDivisions || [] : [];
    setGnDivisionsList(gnList);
    setGnDivision(gnList[0] || '');
  };

  const filteredGnList = gnDivisionsList.filter((gn) =>
    gn.toLowerCase().includes(gnSearch.toLowerCase())
  );

  const handleOpenCreateModal = () => setIsModalOpen(true);
  const handleCloseModal = () => setIsModalOpen(false);

  const handleProceedToUpload = (e) => {
    e.preventDefault();
    if (!reliefCamp.trim()) {
      onAddToast?.('Please specify the Relief Camp name', 'warning', 'Missing Name');
      return;
    }
    setIsModalOpen(false);
    setRawFiles(Array(5).fill(null));
    setImages(Array(5).fill(null));
    setAnalysisData([]);
    setStep('upload');
  };

  const handleImageSelect = (event, index) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const previewUrl = URL.createObjectURL(file);
    const updatedImages = [...images];
    const updatedFiles = [...rawFiles];

    updatedImages[index] = previewUrl;
    updatedFiles[index] = file;

    setImages(updatedImages);
    setRawFiles(updatedFiles);
  };

  const handleRemoveImage = (index) => {
    const updatedImages = [...images];
    const updatedFiles = [...rawFiles];
    updatedImages[index] = null;
    updatedFiles[index] = null;
    setImages(updatedImages);
    setRawFiles(updatedFiles);

    if (analysisData.length > 0) {
      const updatedAnalysis = [...analysisData];
      updatedAnalysis[index] = null;
      setAnalysisData(updatedAnalysis);
    }
  };

  const handleDrop = (event, index) => {
    event.preventDefault();
    setDraggingIndex(null);
    const file = event.dataTransfer.files?.[0];
    if (!file) return;

    const previewUrl = URL.createObjectURL(file);
    const updatedImages = [...images];
    const updatedFiles = [...rawFiles];

    updatedImages[index] = previewUrl;
    updatedFiles[index] = file;

    setImages(updatedImages);
    setRawFiles(updatedFiles);
  };

  const handleAnalyze = async () => {
    const count = Number(locationCount);
    const activeFiles = rawFiles.slice(0, count);
    const hasAnyImage = activeFiles.some((f) => f !== null);

    if (!hasAnyImage) {
      onAddToast?.('Please upload at least one image before running the analysis.', 'warning', 'Verification Error');
      return;
    }

    setAnalyzing(true);

    try {
      const results = [];
      const updatedAnnotatedImages = [...images];

      for (let i = 0; i < count; i++) {
        const file = rawFiles[i];
        if (!file) {
          results.push({ image: null, population: 0 });
          continue;
        }

        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('http://127.0.0.1:8000/population/count', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Failed to analyze image for Location #${i + 1}`);
        }

        const data = await response.json();
        const detectedCount = data.person_count || 0;
        const annotatedImgUrl = data.annotated_image_url || images[i];

        updatedAnnotatedImages[i] = annotatedImgUrl;
        results.push({
          image: annotatedImgUrl,
          population: detectedCount,
        });
      }

      setImages(updatedAnnotatedImages);
      setAnalysisData(results);
      onAddToast?.('AI crowd estimation analysis complete.', 'success', 'Analysis Succeeded');
    } catch (err) {
      onAddToast?.(err.message || 'Error processing images with AI Model', 'error', 'AI Model Failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const selectedDonationDetails = donationItems.filter((item) => {
    const itemKey = item.itemId || item.item;
    return selectedDonationItems.includes(itemKey);
  });

  const toggleDonationItemSelection = (item) => {
    const itemKey = item.itemId || item.item;
    setSelectedDonationItems((current) =>
      current.includes(itemKey)
        ? current.filter((value) => value !== itemKey)
        : [...current, itemKey]
    );
  };

  const handleCreateRequestSubmit = async () => {
    if (selectedDonationDetails.length === 0) {
      onAddToast?.('Please select at least one donation item.', 'warning', 'No Items Selected');
      return;
    }

    const payload = {
      disasterType: disasterType,
      severity: severity,
      dsArea: dsArea,
      gnDivision: gnDivision,
      reliefCamp: reliefCamp,
      people_count: totalPopulation,
      items: selectedDonationDetails.map((item) => {
        const requiredQty = (Number(item.quantityPerPerson) || 1) * Math.max(totalPopulation, 1);
        return {
          itemId: item.itemId,
          itemName: item.item,
          unit: item.unit,
          neededQuantity: requiredQty,
        };
      }),
    };

    const token = localStorage.getItem('token') || localStorage.getItem('access_token') || '';
    setSubmitting(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/disaster-donation-requests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to submit request');
      }

      onAddToast?.('Disaster donation request published successfully!', 'success', 'Request Published');
      await fetchAllRequests();
      setStep('dashboard');
    } catch (err) {
      onAddToast?.(err.message || 'Error submitting request', 'error', 'Submission Failed');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredRequests = donationRequests.filter((req) => {
    const matchesStatus = statusFilter === 'all' || req.status === statusFilter;
    const matchesSearch =
      (req.gnDivision || '').toLowerCase().includes(searchTableQuery.toLowerCase()) ||
      (req.dsArea || '').toLowerCase().includes(searchTableQuery.toLowerCase()) ||
      (req.reliefCamp || '').toLowerCase().includes(searchTableQuery.toLowerCase()) ||
      (req.disasterType || '').toLowerCase().includes(searchTableQuery.toLowerCase()) ||
      (req.severity || '').toLowerCase().includes(searchTableQuery.toLowerCase()) ||
      (req.id || '').toLowerCase().includes(searchTableQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const totalCount = donationRequests.length;
  const fulfilledCount = donationRequests.filter((r) => r.status === 'fulfilled').length;
  const remainingCount = donationRequests.filter((r) => r.status === 'remaining').length;

  const renderUploadStep = () => {
    const isAnalyzed = analysisData.length > 0;

    return (
      <div className="upload-flow-card">
        <div className="upload-flow-header">
          <div className="flow-badge">Crowd Estimation Model</div>
          <h2>Upload Disaster Location Images</h2>
          <div className="flow-location-pill">
            <span className="location-pin">📍</span>
            <strong>{dsArea}</strong> — <span>{gnDivision}</span> ({reliefCamp})
          </div>
          <p className="flow-description">
            Upload images for {locationCount} location slot{locationCount > 1 ? 's' : ''}. The crowd estimation model will estimate the affected population.
          </p>
        </div>

        <div className={`upload-cards-grid grid-count-${locationCount}`}>
          {Array.from({ length: Number(locationCount) }, (_, index) => {
            const previewImage = images[index];
            const result = analysisData[index];

            return (
              <div
                key={`slot-${index}`}
                className={`upload-dropzone-card ${previewImage ? 'has-preview' : ''} ${draggingIndex === index ? 'is-dragging' : ''}`}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDraggingIndex(index);
                }}
                onDragLeave={() => setDraggingIndex(null)}
                onDrop={(e) => handleDrop(e, index)}
              >
                <div className="dropzone-top-bar">
                  <span className="location-badge">Location #{index + 1}</span>
                  {previewImage && !isAnalyzed && (
                    <button
                      type="button"
                      className="btn-remove-preview"
                      onClick={() => handleRemoveImage(index)}
                      title="Remove image"
                    >
                      ✕
                    </button>
                  )}
                </div>

                {previewImage ? (
                  <div className="preview-container">
                    <img src={previewImage} alt={`Location ${index + 1}`} className="preview-img" />
                    {isAnalyzed && (
                      <div className="ai-verified-tag">
                        <span>✓ Density Analyzed</span>
                      </div>
                    )}
                    {!isAnalyzed && (
                      <div className="preview-overlay">
                        <label className="btn-change-image" htmlFor={`upload-${index}`}>
                          🔄 Change Photo
                        </label>
                      </div>
                    )}
                  </div>
                ) : (
                  <label className="dropzone-placeholder" htmlFor={`upload-${index}`}>
                    <div className="upload-cloud-icon">📸</div>
                    <span className="upload-prompt-text">Click or Drag Photo Here</span>
                    <span className="upload-hint-text">Supports JPG, PNG or WEBP</span>
                    <span className="btn-browse-file">Browse File</span>
                  </label>
                )}

                {result && result.image && (
                  <div className="slot-result-badge">
                    <span className="result-icon">👥</span>
                    <div className="result-text">
                      <small>AI Estimated Count</small>
                      <strong>{result.population} Individuals</strong>
                    </div>
                  </div>
                )}

                <input
                  id={`upload-${index}`}
                  type="file"
                  accept="image/*"
                  className="hidden-file-input"
                  onChange={(e) => handleImageSelect(e, index)}
                />
              </div>
            );
          })}
        </div>

        {isAnalyzed && (
          <div className="population-result-hero">
            <div className="hero-icon-wrap">⚡</div>
            <div className="hero-data">
              <span className="hero-label">Total AI Estimated Impact</span>
              <h3 className="hero-count">{totalPopulation} Individuals</h3>
              <p className="hero-subtext">Verified crowd analysis for {reliefCamp} in {gnDivision}</p>
            </div>
          </div>
        )}

        <div className="upload-action-footer">
          <button type="button" className="btn-flow-cancel" onClick={() => setStep('dashboard')}>
            Cancel
          </button>

          <div className="footer-right-actions">
            {isAnalyzed ? (
              <>
                <button
                  type="button"
                  className="btn-flow-secondary"
                  onClick={() => {
                    setAnalysisData([]);
                    setImages(rawFiles.map((f) => (f ? URL.createObjectURL(f) : null)));
                  }}
                >
                  ↺ Re-Upload
                </button>
                <button
                  type="button"
                  className="btn-flow-primary"
                  onClick={() => setStep('donationRequest')}
                >
                  Create Donation Request →
                </button>
              </>
            ) : (
              <button
                type="button"
                className="btn-flow-primary"
                disabled={analyzing}
                onClick={handleAnalyze}
              >
                {analyzing ? '⏳ Estimating Crowd Count...' : '⚡ Analyze Images'}
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderDonationRequestStep = () => (
    <div className="request-step">
      <div className="step-header">
        <h2>Confirm Disaster Donation Needs</h2>
        <p>Review the predicted requirements for {reliefCamp} ({gnDivision}, {dsArea})</p>
      </div>

      <div className="metrics-summary-bar">
        <div className="metric-pill">
          <span>Disaster:</span>
          <strong>{disasterType}</strong>
        </div>
        <div className="metric-pill">
          <span>Severity:</span>
          <strong>{severity}</strong>
        </div>
        <div className="metric-pill">
          <span>Relief Camp:</span>
          <strong>{reliefCamp}</strong>
        </div>
        <div className="metric-pill">
          <span>Affected Population:</span>
          <strong>{totalPopulation}</strong>
        </div>
      </div>

      <div className="panel-box">
        <h3>Required Donation Items</h3>
        {donationItemsLoading ? (
          <p>Loading items from database...</p>
        ) : donationItems.length === 0 ? (
          <p style={{ color: '#64748b' }}>No catalog items found. Please add donation items to the catalog.</p>
        ) : (
          <div className="donation-item-selector">
            {donationItems.map((item) => {
              const itemKey = item.itemId || item.item;
              const isChecked = selectedDonationItems.includes(itemKey);
              const estimatedUnits = (Number(item.quantityPerPerson) || 1) * Math.max(totalPopulation, 1);

              return (
                <label className={`item-option-card ${isChecked ? 'selected' : ''}`} key={itemKey}>
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggleDonationItemSelection(item)}
                  />
                  <div className="item-info">
                    <strong>{item.item}</strong>
                    <small>{item.quantityPerPerson} {item.unit} / person</small>
                    <span className="unit-calc">Total: {estimatedUnits} {item.unit}</span>
                  </div>
                </label>
              );
            })}
          </div>
        )}
      </div>

      <div className="request-footer">
        <button type="button" className="btn-secondary" onClick={() => setStep('upload')}>
          ← Back
        </button>
        <button
          type="button"
          className="btn-primary"
          disabled={submitting || selectedDonationDetails.length === 0}
          onClick={handleCreateRequestSubmit}
        >
          {submitting ? 'Submitting to Database...' : 'Confirm & Publish Request'}
        </button>
      </div>
    </div>
  );

  return (
    <div className="dashboard-container" style={{ padding: '24px 0' }}>
      {step === 'dashboard' && (
        <div className="dashboard-container" style={{ padding: 0 }}>
          <div className="dashboard-topbar">
            <div className="title-area">
              <h1 style={{ fontSize: '1.75rem', fontWeight: 800 }}>Disaster Relief & Donation Requests</h1>
              <p style={{ margin: '4px 0 0', fontSize: '0.9rem' }}>Track, manage, and coordinate real-time disaster supply requests</p>
            </div>
            <div className="topbar-actions">
              <button type="button" className="btn btn-primary btn-sm" onClick={handleOpenCreateModal}>
                + Create New Request
              </button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            <div className="stat-card" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)' }}>
              <div className="stat-icon icon-blue">📋</div>
              <div className="stat-text">
                <span>Total Requests</span>
                <h2>{totalCount}</h2>
              </div>
            </div>
            <div className="stat-card" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)' }}>
              <div className="stat-icon icon-amber">⏳</div>
              <div className="stat-text">
                <span>Pending Action</span>
                <h2>{remainingCount}</h2>
              </div>
            </div>
            <div className="stat-card" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)' }}>
              <div className="stat-icon icon-green">✅</div>
              <div className="stat-text">
                <span>Fulfilled</span>
                <h2>{fulfilledCount}</h2>
              </div>
            </div>
          </div>

          <div className="table-card" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)' }}>
            <div className="table-controls" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
              <div className="search-box" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)' }}>
                <span className="search-icon">🔍</span>
                <input
                  type="text"
                  placeholder="Search by camp, GN, DS, severity..."
                  value={searchTableQuery}
                  onChange={(e) => setSearchTableQuery(e.target.value)}
                  style={{ color: 'var(--text-primary)' }}
                />
              </div>
              <div className="filter-buttons">
                <button
                  type="button"
                  className={`filter-btn ${statusFilter === 'all' ? 'active' : ''}`}
                  onClick={() => setStatusFilter('all')}
                  style={statusFilter === 'all' ? { background: 'var(--accent-blue)', color: 'white' } : {}}
                >
                  All ({totalCount})
                </button>
                <button
                  type="button"
                  className={`filter-btn ${statusFilter === 'remaining' ? 'active' : ''}`}
                  onClick={() => setStatusFilter('remaining')}
                  style={statusFilter === 'remaining' ? { background: 'var(--accent-blue)', color: 'white' } : {}}
                >
                  Pending ({remainingCount})
                </button>
                <button
                  type="button"
                  className={`filter-btn ${statusFilter === 'fulfilled' ? 'active' : ''}`}
                  onClick={() => setStatusFilter('fulfilled')}
                  style={statusFilter === 'fulfilled' ? { background: 'var(--accent-blue)', color: 'white' } : {}}
                >
                  Fulfilled ({fulfilledCount})
                </button>
              </div>
            </div>

            <div className="table-responsive">
              <table className="custom-table" style={{ width: '100%' }}>
                <thead>
                  <tr style={{ color: 'var(--text-muted)' }}>
                    <th>Request ID</th>
                    <th>Disaster</th>
                    <th>Severity</th>
                    <th>DS Area</th>
                    <th>Relief Camp / GN</th>
                    <th>Affected Pop.</th>
                    <th>Requested Items</th>
                    <th>Status</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {requestsLoading ? (
                    <tr>
                      <td colSpan="9" className="empty-table-cell">
                        Loading disaster requests from server...
                      </td>
                    </tr>
                  ) : filteredRequests.length === 0 ? (
                    <tr>
                      <td colSpan="9" className="empty-table-cell">
                        No disaster requests found matching your filters.
                      </td>
                    </tr>
                  ) : (
                    filteredRequests.map((req) => (
                      <tr key={req.id}>
                        <td className="font-semibold text-primary">#{req.id.slice(-6).toUpperCase()}</td>
                        <td>
                          <span className={`disaster-badge ${(req.disasterType || 'flood').toLowerCase()}`}>
                            {req.disasterType}
                          </span>
                        </td>
                        <td>
                          <span className={`badge ${req.severity === 'Critical' ? 'badge-high' : req.severity === 'High' ? 'badge-medium' : 'badge-low'}`}>
                            {req.severity}
                          </span>
                        </td>
                        <td><strong>{req.dsArea}</strong></td>
                        <td>
                          <strong>{req.reliefCamp}</strong>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{req.gnDivision}</div>
                        </td>
                        <td>{req.people_count || '—'}</td>
                        <td className="items-cell">
                          <div className="items-tags">
                            {req.items?.slice(0, 2).map((itm, i) => (
                              <span className="item-tag" key={i} style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)' }}>
                                {itm.itemName} ({itm.neededQuantity} {itm.unit})
                              </span>
                            ))}
                            {req.items?.length > 2 && (
                              <span className="item-tag-more">+{req.items.length - 2} more</span>
                            )}
                          </div>
                        </td>
                        <td>
                          <span className={`badge ${req.status === 'fulfilled' ? 'badge-low' : 'badge-medium'}`}>
                            {req.status === 'fulfilled' ? 'Fulfilled' : 'Pending'}
                          </span>
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => setViewRequestModal(req)}
                          >
                            View Progress
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {step === 'upload' && renderUploadStep()}
      {step === 'donationRequest' && renderDonationRequestStep()}

      {/* POPUP MODAL: CREATE NEW REQUEST */}
      {isModalOpen && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)' }}>
            <div className="modal-header">
              <div>
                <h2>Create Disaster Donation Request</h2>
                <p>Select location specifications and disaster classification</p>
              </div>
              <button type="button" className="btn-close-modal" onClick={handleCloseModal}>✕</button>
            </div>

            <form onSubmit={handleProceedToUpload} className="modal-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="modal-disaster-type">Disaster Type</label>
                  <select
                    id="modal-disaster-type"
                    className="form-input"
                    value={disasterType}
                    onChange={(e) => setDisasterType(e.target.value)}
                    required
                  >
                    {DISASTER_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="modal-severity">Severity Level</label>
                  <select
                    id="modal-severity"
                    className="form-input"
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    required
                  >
                    {SEVERITY_LEVELS.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="modal-ds-area">Divisional Secretariat Area</label>
                <select
                  id="modal-ds-area"
                  className="form-input"
                  value={dsArea}
                  onChange={handleDsAreaChange}
                  required
                  disabled={divisionsLoading}
                >
                  {dsAreas.length === 0 ? (
                    <option value="">{divisionsLoading ? 'Loading areas...' : 'No DS Areas available'}</option>
                  ) : (
                    dsAreas.map((area) => (
                      <option key={area} value={area}>{area}</option>
                    ))
                  )}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="modal-gn-division">Grama Niladhari Division</label>
                <select
                  id="modal-gn-division"
                  className="form-input"
                  value={gnDivision}
                  onChange={(e) => setGnDivision(e.target.value)}
                  required
                >
                  {filteredGnList.length > 0 ? (
                    filteredGnList.map((gn) => (
                      <option key={gn} value={gn}>{gn}</option>
                    ))
                  ) : (
                    <option value="">No GN division matches</option>
                  )}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="modal-relief-camp">Relief Camp / Shelter Name</label>
                <input
                  id="modal-relief-camp"
                  type="text"
                  placeholder="e.g. Nawagamuwa Primary School Hall"
                  className="form-input"
                  value={reliefCamp}
                  onChange={(e) => setReliefCamp(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="modal-location-count">Number of Image Locations</label>
                <select
                  id="modal-location-count"
                  className="form-input"
                  value={locationCount}
                  onChange={(e) => setLocationCount(Number(e.target.value))}
                  required
                >
                  {[1, 2, 3, 4, 5].map((n) => (
                    <option key={n} value={n}>{n} Location{n > 1 ? 's' : ''}</option>
                  ))}
                </select>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary btn-sm" onClick={handleCloseModal}>Cancel</button>
                <button type="submit" className="btn btn-primary btn-sm">Upload Images</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* POPUP MODAL: VIEW REQUEST PROGRESS */}
      {viewRequestModal && (
        <div className="modal-overlay" onClick={() => setViewRequestModal(null)}>
          <div className="modal-content modal-detail" onClick={(e) => e.stopPropagation()} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', maxWidth: '640px' }}>
            <div className="modal-header">
              <div>
                <h2>{viewRequestModal.reliefCamp}</h2>
                <p style={{ margin: '4px 0 0' }}>{viewRequestModal.gnDivision} • {viewRequestModal.dsArea} DS Office</p>
              </div>
              <button type="button" className="btn-close-modal" onClick={() => setViewRequestModal(null)}>✕</button>
            </div>

            <div className="detail-modal-body">
              <div className="detail-grid" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)' }}>
                <div>
                  <span className="label-dim">Status:</span>
                  <span className={`status-pill ${viewRequestModal.status}`}>{viewRequestModal.status}</span>
                </div>
                <div>
                  <span className="label-dim">Severity:</span>
                  <span className={`badge ${viewRequestModal.severity === 'Critical' ? 'badge-high' : viewRequestModal.severity === 'High' ? 'badge-medium' : 'badge-low'}`}>
                    {viewRequestModal.severity}
                  </span>
                </div>
                <div>
                  <span className="label-dim">Affected Population:</span>
                  <strong>{viewRequestModal.people_count || '0'} People</strong>
                </div>
                <div>
                  <span className="label-dim">Date:</span>
                  <strong>{new Date(viewRequestModal.createdAt).toLocaleDateString()}</strong>
                </div>
              </div>

              <h4 style={{ marginTop: '20px', marginBottom: '10px' }}>Requested Items Progress</h4>
              <div className="detail-items-list">
                {viewRequestModal.items?.map((item, idx) => (
                  <div className="detail-item-card" key={idx} style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)' }}>
                    <div>
                      <strong>{item.itemName}</strong>
                      <p style={{ margin: '4px 0 0' }}>
                        Needed: <b>{item.neededQuantity}</b> {item.unit} | Pledged: <b>{item.pledgedQuantity}</b> | Received: <b>{item.donatedQuantity}</b>
                      </p>
                    </div>
                    <span className={`badge ${item.status === 'fulfilled' ? 'badge-low' : 'badge-medium'}`}>{item.status}</span>
                  </div>
                ))}
              </div>

              {viewRequestModal.donations?.length > 0 && (
                <>
                  <h4 style={{ marginTop: '20px', marginBottom: '10px' }}>Pledge Log</h4>
                  <div className="detail-items-list">
                    {viewRequestModal.donations.map((don, idx) => (
                      <div className="detail-item-card" key={idx} style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)' }}>
                        <div>
                          <strong>{don.donorName} ({don.quantity} {don.itemName})</strong>
                          <p style={{ margin: '4px 0 0' }}>Status: {don.status} • {new Date(don.donatedAt).toLocaleDateString()}</p>
                        </div>
                        <span className={`badge ${don.status === 'received' ? 'badge-low' : 'badge-medium'}`}>{don.status}</span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>

            <div className="modal-footer">
              <button type="button" className="btn btn-primary btn-sm" onClick={() => setViewRequestModal(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DisasterDonationRequestView;
