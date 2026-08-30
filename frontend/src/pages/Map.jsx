import React from 'react'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import './Map.css'

function Map() {
  return (
    <div className="map-page">
      <Navigation />
      <div className="map-container">
        <div className="map-header">
          <h1>Interactive Donation Map</h1>
          <p>View donation centers, healthcare facilities, and emergency response locations</p>
        </div>
        <div className="map-placeholder">
          <div className="map-content">
            <span className="map-icon">🗺️</span>
            <h2>Map Coming Soon</h2>
            <p>Interactive map with real-time donation locations and emergency response zones</p>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default Map
