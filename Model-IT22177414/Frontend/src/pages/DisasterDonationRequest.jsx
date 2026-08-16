import React, { useState } from 'react'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import './DisasterDonationRequest.css'

const DEFAULT_POPULATIONS = [420, 310, 540, 260, 390]

const KADUWELA_GN_DIVISIONS = [
  '469 Ranala',
  '470 Nawagamuwa',
  '470 A Nawagamuwa South',
  '471 Ihala Bomiriya',
  '471 A Wakewatta',
  '472 A Pahala Bomiriya',
  '472 B Pahala Bomiriya',
  '473 Kothalawala',
  '473 A Kaduwela',
  '474 Hewagama',
  '474 A Rangahawatta',
  '475 Welivita',
  '475 A Mahadeniya',
  '476 Malabe East',
  '476 A Malabe West',
  '476 B Malabe North',
  '477 Thalangama North',
  '477 North Thalangama B',
  '477 B Mumnethotugoda',
  '477 C Pothuarawa',
  '478 Thalanghena North',
  '478 A Thalanghena South',
  '479 Jayawadanagama',
  '479 A Pahalawela',
  '479 B Asiri Uyana',
  '479 C Wickramasinghepura',
  '479 D Kumaragewatta',
  '479 E Batapotha',
  '479 F Aruppitiya',
  '480 Welipillawa',
  '480 A Dadigamuwa',
  '480 B Ambilladeniya',
  '480 C Bawathewela',
  '487 Oruwala',
  '487 A Shanthalokagama',
  '488 Korathota',
  '488 A Welihinda',
  '488 B Thunandhena',
  '489 Pore',
  '489 A Boralugoda',
  '490 Athurugiriya',
  '490 A Athurugiriya South',
  '490 B Thaldiyawala',
  '491 Kalapaluwawa',
  '491 A Walpola',
  '491 B Kotuwegoda',
  '492 Sri Subhuthipura',
  '492 A Battaramulla South',
  '492 B Battaramulla North',
  '492 C Udumulla',
  '492 D Rajamalwatta',
  '494 Hokandara North',
  '494 A Hokandara East',
  '494 B Arangala',
  '494 C Hokandara South',
  '495 Wellangiriya',
  '495 A Awarihena',
]

const NAWALAPITIYA_GN_DIVISIONS = [
  '314 Ambagamuwa South',
  '314 A Ambagamuwa East',
  '314 C Sellipigama',
  '314 D Homagama',
  '314 E Kalaweldeniya',
  '314 F Dehigasthenna',
  '314 G Habbakanda',
  '315 A Ginigathhena',
  '315 B Samansirigama',
  '315 C Vidulipura South',
  '315 D Vidulipura North',
  '316 Bulathgama',
  '316 A Rampadeniya',
  '316 B Gonawala',
  '316 C Kalugala',
  '316 D Pitawala',
  '316 E Millagahamula',
  '316 F Dagampitiya',
  '316 G Kehelwarawa',
  '317 Kirivan Eliya',
  '317 A Lakshapana',
  '317 B Waggama',
  '317 C Morahenagama',
  '318 Polpitiya',
  '318 A Hitigegama',
  '318 B Hagarapitiya',
  '318 C Minuwandeniya',
  '318 D Jambuthenna',
  '318 E Koththallena',
]

const DISASTER_TYPES = ['Flood', 'Landslide']

function DisasterDonationRequest() {
  const [locationCount, setLocationCount] = useState(1)
  const [step, setStep] = useState('intro')
  const [disasterType, setDisasterType] = useState('Flood')
  const [affectedArea, setAffectedArea] = useState(KADUWELA_GN_DIVISIONS[0])
  const [gnSearch, setGnSearch] = useState('')
  const [images, setImages] = useState(Array(5).fill(null))
  const [analysisData, setAnalysisData] = useState([])
  const [draggingIndex, setDraggingIndex] = useState(null)

  const totalPopulation = analysisData.reduce((sum, item) => sum + (item?.population ?? 0), 0)
  const reliefItems = [
    { label: 'Drinking Water', quantity: Math.round(totalPopulation * 3), unit: 'L' },
    { label: 'Food Packs', quantity: Math.round(totalPopulation * 1.4), unit: 'packs' },
    { label: 'OTC Medicines', quantity: Math.round(totalPopulation * 0.7), unit: 'boxes' },
    { label: 'Hygiene Kits', quantity: Math.round(totalPopulation * 0.8), unit: 'kits' },
  ]

  const donorRecommendations = [
    { name: 'LankaCare Foundation', score: '94%', distance: '12 km' },
    { name: 'Green Relief Network', score: '89%', distance: '18 km' },
    { name: 'CareConnect Sri Lanka', score: '86%', distance: '21 km' },
  ]

  const handleImageSelect = (event, index) => {
    const file = event.target.files?.[0]
    if (!file) return

    const previewUrl = URL.createObjectURL(file)
    const updatedImages = [...images]
    updatedImages[index] = previewUrl
    setImages(updatedImages)
  }

  const handleDrop = (event, index) => {
    event.preventDefault()
    setDraggingIndex(null)
    const file = event.dataTransfer.files?.[0]
    if (!file) return

    const previewUrl = URL.createObjectURL(file)
    const updatedImages = [...images]
    updatedImages[index] = previewUrl
    setImages(updatedImages)
  }

  const handleAnalyze = () => {
    const totalLocations = Number(locationCount)
    const results = Array.from({ length: totalLocations }, (_, index) => {
      const uploadedImage = images[index]
      const population = uploadedImage ? DEFAULT_POPULATIONS[index] : 0

      return {
        image: uploadedImage,
        population,
      }
    })

    setAnalysisData(results)
  }

  const handleBackToUpload = () => {
    setAnalysisData([])
    setStep('setup')
  }

  const renderIntroStep = () => (
    <div className="request-step intro-step">
      <div className="intro-card">
        <div className="intro-badge">Integrated Disaster Relief Prediction System</div>
        <h1>Smart disaster response planning for flood and landslide emergencies</h1>
        <p>
          The system estimates affected population from images, calculates essential relief
          requirements, and helps coordinate donation requests for medical and emergency support.
        </p>
        <div className="intro-points">
          <span>AI population estimation</span>
          <span>Relief prediction</span>
          <span>Donation coordination</span>
        </div>
        <div className="request-footer intro-footer">
          <button type="button" className="primary-button" onClick={() => setStep('setup')}>
            Get Started
          </button>
        </div>
      </div>
    </div>
  )

  const renderSetupStep = () => {
    const availableAreas = disasterType === 'Flood' ? KADUWELA_GN_DIVISIONS : NAWALAPITIYA_GN_DIVISIONS
    const filteredAreas = availableAreas.filter((area) =>
      area.toLowerCase().includes(gnSearch.toLowerCase()),
    )

    return (
      <div className="request-step">
        <div className="request-hero">
          <span className="request-badge">Disaster Donation Request</span>
          <h1>How many disaster locations need support?</h1>
          <p>
            Select the number of affected areas you want to review before starting the
            image analysis.
          </p>
        </div>

        <div className="location-selector-card">
          <div className="selector-group">
            <label htmlFor="disaster-type" className="selector-label">
              Disaster type
            </label>
            <select
              id="disaster-type"
              value={disasterType}
              onChange={(event) => {
                const nextType = event.target.value
                setDisasterType(nextType)
                setGnSearch('')
                setAffectedArea(
                  nextType === 'Flood' ? KADUWELA_GN_DIVISIONS[0] : NAWALAPITIYA_GN_DIVISIONS[0],
                )
              }}
            >
              {DISASTER_TYPES.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <div className="selector-group">
            <label htmlFor="gn-search" className="selector-label">
              Search GN division
            </label>
            <input
              id="gn-search"
              type="text"
              className="gn-search-input"
              placeholder="Search affected area or GN division"
              value={gnSearch}
              onChange={(event) => setGnSearch(event.target.value)}
            />
          </div>

          <div className="selector-group">
            <label htmlFor="affected-area" className="selector-label">
              Affected area / GN division
            </label>
            <select
              id="affected-area"
              value={affectedArea}
              onChange={(event) => setAffectedArea(event.target.value)}
            >
              {filteredAreas.length > 0 ? (
                filteredAreas.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))
              ) : (
                <option value="">No matching GN division found</option>
              )}
            </select>
          </div>

          <div className="selector-group">
            <label htmlFor="location-count" className="selector-label">
              Number of locations
            </label>
            <select
              id="location-count"
              value={locationCount}
              onChange={(event) => setLocationCount(Number(event.target.value))}
            >
              {[1, 2, 3, 4, 5].map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="request-footer">
          <button type="button" className="primary-button" onClick={() => setStep('upload')}>
            Next
          </button>
        </div>
      </div>
    )
  }

  const renderUploadStep = () => {
    const isAnalyzed = analysisData.length > 0

    return (
      <div className="request-step">
        <div className="request-hero compact">
          <div className="request-header-row">
            <div className="brand-mark-wrap">
              <div className="brand-mark">V</div>
            </div>
            <span className="request-badge">Upload Image References</span>
            <button type="button" className="sos-mini-button">Emergency SOS</button>
          </div>
          <h1>Upload images for each affected location</h1>
          <p>
            Add up to {locationCount} location images. The system will analyze each image for
            need estimation and population density.
          </p>
        </div>

        <div className="upload-grid">
          {Array.from({ length: Number(locationCount) }, (_, index) => {
            const previewImage = images[index]
            const result = analysisData[index]

            return (
              <div
                key={`slot-${index}`}
                className={`upload-box ${draggingIndex === index ? 'dragging' : ''}`}
                onDragOver={(event) => {
                  event.preventDefault()
                  setDraggingIndex(index)
                }}
                onDragLeave={() => setDraggingIndex(null)}
                onDrop={(event) => handleDrop(event, index)}
              >
                {previewImage ? (
                  <img src={previewImage} alt={`Location ${index + 1}`} className="upload-preview" />
                ) : (
                  <>
                    <div className="upload-icon">⬆️</div>
                  </>
                )}

                <p className="location-title">Location {index + 1}</p>

                {result && result.image && (
                  <div className="result-inline">
                    <div className="result-population">Population: {result.population}</div>
                  </div>
                )}

                {!isAnalyzed && (
                  <label className="upload-button" htmlFor={`upload-${index}`}>
                    Upload Image
                  </label>
                )}

                {!isAnalyzed && (
                  <input
                    id={`upload-${index}`}
                    type="file"
                    accept="image/*"
                    onChange={(event) => handleImageSelect(event, index)}
                  />
                )}
              </div>
            )
          })}
        </div>

        {isAnalyzed && (
          <div className="total-population-box">
            Total Population: {totalPopulation}
          </div>
        )}

        <div className="request-footer">
          {isAnalyzed ? (
            <>
              <button type="button" className="secondary-button" onClick={handleBackToUpload}>
                Back
              </button>
              <button type="button" className="primary-button" onClick={() => setStep('dashboard')}>
                Next
              </button>
            </>
          ) : (
            <button type="button" className="primary-button" onClick={handleAnalyze}>
              Analyze
            </button>
          )}
        </div>
      </div>
    )
  }

  const renderDashboardStep = () => (
    <div className="dashboard-step">
      <div className="dashboard-header-row">
        <div className="dashboard-brand-wrap">
          <div className="dashboard-brand">V</div>
        </div>
        <div className="dashboard-title-group">
          <span className="dashboard-badge">Integrated Disaster Relief Prediction System</span>
          <h1>Disaster Relief Dashboard</h1>
        </div>
        <button type="button" className="sos-mini-button">Emergency SOS</button>
      </div>

      <div className="dashboard-metrics">
        <div className="metric-card">
          <span className="metric-label">Affected Population</span>
          <strong>{totalPopulation}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Active Requests</span>
          <strong>{locationCount}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Disaster Severity</span>
          <strong>High</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Est. Relief Need</span>
          <strong>{Math.round(totalPopulation * 1.5)} items</strong>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="dashboard-panel">
          <h3>Predicted Relief Requirements</h3>
          <div className="requirement-list">
            {reliefItems.map((item) => (
              <div className="requirement-item" key={item.label}>
                <div>
                  <span className="requirement-name">{item.label}</span>
                </div>
                <strong>
                  {item.quantity} {item.unit}
                </strong>
              </div>
            ))}
          </div>
        </div>

        <div className="dashboard-panel">
          <h3>AI Model Insights</h3>
          <ul className="insight-list">
            <li>Estimated affected population derived from crowd counting model.</li>
            <li>Disaster severity is classified as high due to dense gathering patterns.</li>
            <li>Recommended emergency period is 7 days based on humanitarian standards.</li>
            <li>Relief calculations align with Sphere-based per-person requirements.</li>
          </ul>
        </div>
      </div>

      <div className="dashboard-content lower">
        <div className="dashboard-panel">
          <h3>Recommended Donors</h3>
          <div className="donor-list">
            {donorRecommendations.map((donor) => (
              <div className="donor-row" key={donor.name}>
                <div>
                  <strong>{donor.name}</strong>
                  <span>{donor.distance} away</span>
                </div>
                <span className="donor-score">{donor.score}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="dashboard-panel">
          <h3>Donation Summary</h3>
          <div className="summary-box">
            <div className="summary-row">
              <span>Need met</span>
              <strong>38%</strong>
            </div>
            <div className="summary-row">
              <span>Remaining critical items</span>
              <strong>{Math.round(totalPopulation * 0.9)}</strong>
            </div>
            <div className="summary-row">
              <span>Urgency status</span>
              <strong>Critical</strong>
            </div>
          </div>
        </div>
      </div>

      <div className="request-footer dashboard-footer">
        <button type="button" className="secondary-button" onClick={() => setStep('upload')}>
          Back
        </button>
        <button type="button" className="primary-button" onClick={() => setStep('upload')}>
          Submit Request
        </button>
      </div>
    </div>
  )

  return (
    <div className="disaster-request-page">
      <Navigation />
      <main className="disaster-request-wrapper">
        <div className="disaster-request-card">
          {step === 'intro' && renderIntroStep()}
          {step === 'setup' && renderSetupStep()}
          {step === 'upload' && renderUploadStep()}
          {step === 'dashboard' && renderDashboardStep()}
        </div>
      </main>
      <Footer />
    </div>
  )
}

export default DisasterDonationRequest
