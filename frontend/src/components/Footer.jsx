import React from 'react'
import { Radio, PhoneCall, HeartHandshake } from 'lucide-react'
import './Footer.css'

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-content">
          <div className="footer-section brand-col">
            <div className="footer-brand">
              <div className="footer-brand-icon">
                <Radio size={20} />
              </div>
              <div>
                <h3 className="footer-title">SRI LANKA DISASTER RELIEF</h3>
                <span className="footer-subtitle">Smart Medical Telemetry Cloud</span>
              </div>
            </div>
            <p className="footer-description">
              National emergency crisis orchestration platform bridging disaster victims with Ministry of Health (MOH) clinical teams, verified relief donors, and field rescue responders across Sri Lanka.
            </p>
          </div>

          <div className="footer-section">
            <h4 className="footer-heading">Response Portals</h4>
            <ul className="footer-links">
              <li><a href="/signin">Stakeholder Authentication</a></li>
              <li><a href="/sos-public">Victim Emergency SOS Beacon</a></li>
              <li><a href="/map">Geospatial Hazard Heatmap</a></li>
              <li><a href="/donations">Relief Donor Marketplace</a></li>
              <li><a href="/donation-appeal">Medical Donation Appeals</a></li>
            </ul>
          </div>

          <div className="footer-section">
            <h4 className="footer-heading">Emergency Hotlines</h4>
            <ul className="footer-contact">
              <li>
                <PhoneCall size={14} className="contact-icon-svg" />
                <span>Disaster Management (DMC): <strong>117</strong></span>
              </li>
              <li>
                <PhoneCall size={14} className="contact-icon-svg" />
                <span>Suwa Seriya Ambulance: <strong>1990</strong></span>
              </li>
              <li>
                <PhoneCall size={14} className="contact-icon-svg" />
                <span>Police Emergency Rescue: <strong>119</strong></span>
              </li>
              <li>
                <HeartHandshake size={14} className="contact-icon-svg" />
                <span>Red Cross Hotline: <strong>011 267 2727</strong></span>
              </li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <div className="footer-bottom-content">
            <p className="copyright">
              © 2026 Sri Lanka National Disaster Relief Directorate &bull; Ministry of Health & DMC
            </p>
            <div className="footer-legal">
              <a href="#">Privacy Policy</a>
              <a href="#">Security Protocol</a>
              <a href="#">OpenAPI Specification</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer
