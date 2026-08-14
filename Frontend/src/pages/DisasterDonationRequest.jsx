import React, { useState } from 'react'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import './DisasterDonationRequest.css'

const DEFAULT_POPULATIONS = [420, 310, 540, 260, 390]

function DisasterDonationRequest() {
  const [locationCount, setLocationCount] = useState(1)
  const [step, setStep] = useState('setup')
  const [images, setImages] = useState(Array(5).fill(null))
  const [analysisData, setAnalysisData] = useState([])
  const [draggingIndex, setDraggingIndex] = useState(null)

  const totalPopulation = analysisData.reduce((sum, item) => sum + (item?.population ?? 0), 0)

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

  const renderSetupStep = () => (
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

      <div className="request-footer">
        <button type="button" className="primary-button" onClick={() => setStep('upload')}>
          Next
        </button>
      </div>
    </div>
  )

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
              <button type="button" className="primary-button" onClick={() => setStep('setup')}>
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

  return (
    <div className="disaster-request-page">
      <Navigation />
      <main className="disaster-request-wrapper">
        <div className="disaster-request-card">
          {step === 'setup' && renderSetupStep()}
          {step === 'upload' && renderUploadStep()}
        </div>
      </main>
      <Footer />
    </div>
  )
}

export default DisasterDonationRequest
