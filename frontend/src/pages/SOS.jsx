import React from 'react'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import './SOS.css'

function SOS() {
  return (
    <div className="sos-page">
      <Navigation />
      <div className="sos-container">
        <div className="sos-header">
          <div className="sos-icon">🚨</div>
          <h1>Emergency SOS</h1>
          <p>Immediate emergency assistance and disaster response</p>
        </div>
        <div className="sos-content">
          <div className="sos-alert-section">
            <div className="sos-alert-card">
              <h2>Report Emergency</h2>
              <p>Use this form to report a medical emergency or disaster situation</p>
              <form className="sos-form">
                <div className="form-group">
                  <label htmlFor="emergency-type">Emergency Type</label>
                  <select id="emergency-type" required>
                    <option value="">Select emergency type</option>
                    <option value="medical">Medical Emergency</option>
                    <option value="disaster">Natural Disaster</option>
                    <option value="accident">Accident</option>
                    <option value="fire">Fire</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="location">Location</label>
                  <input type="text" id="location" placeholder="Enter location or use GPS" required />
                </div>
                <div className="form-group">
                  <label htmlFor="description">Description</label>
                  <textarea id="description" rows="4" placeholder="Describe the emergency situation" required></textarea>
                </div>
                <div className="form-group">
                  <label htmlFor="contact">Contact Number</label>
                  <input type="tel" id="contact" placeholder="Your phone number" required />
                </div>
                <button type="submit" className="sos-button">SEND SOS ALERT</button>
              </form>
            </div>
          </div>
          <div className="sos-info-section">
            <div className="sos-info-card urgent">
              <span className="info-icon">📞</span>
              <h3>Call Emergency Services</h3>
              <p className="emergency-number">911</p>
              <p>For immediate life-threatening emergencies</p>
            </div>
            <div className="sos-info-card">
              <span className="info-icon">📍</span>
              <h3>Share Location</h3>
              <p>Enable GPS to share your exact location with emergency responders</p>
            </div>
            <div className="sos-info-card">
              <span className="info-icon">👥</span>
              <h3>Alert Contacts</h3>
              <p>Notify your emergency contacts automatically</p>
            </div>
            <div className="sos-info-card">
              <span className="info-icon">🏥</span>
              <h3>Nearby Hospitals</h3>
              <p>Find the nearest healthcare facilities</p>
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default SOS
