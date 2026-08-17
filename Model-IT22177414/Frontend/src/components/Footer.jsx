import React from 'react'
import { Link } from 'react-router-dom'
import './Footer.css'

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-content">
          <div className="footer-section">
            <h3 className="footer-title">About MediDonate</h3>
            <p className="footer-description">
              A smart medical donation system with disaster response capabilities. 
              Connecting donors with those in need during emergencies.
            </p>
            <div className="footer-social">
              <a href="#" className="social-link">Facebook</a>
              <a href="#" className="social-link">Twitter</a>
              <a href="#" className="social-link">Instagram</a>
              <a href="#" className="social-link">LinkedIn</a>
            </div>
          </div>

          <div className="footer-section">
            <h3 className="footer-title">Quick Links</h3>
            <ul className="footer-links">
              <li><Link to="/">Home</Link></li>
              <li><Link to="/map">Disaster Map</Link></li>
              <li><Link to="/donations">Donations</Link></li>
              <li><Link to="/contacts">Contacts</Link></li>
              <li><Link to="/sos">Emergency SOS</Link></li>
            </ul>
          </div>

          <div className="footer-section">
            <h3 className="footer-title">Services</h3>
            <ul className="footer-links">
              <li><Link to="/donations">Medical Supplies</Link></li>
              <li><Link to="/donations">Blood Donation</Link></li>
              <li><Link to="/sos">Emergency Response</Link></li>
              <li><Link to="/disaster-donation-request">Disaster Relief</Link></li>
              <li><Link to="/contacts">Volunteer Network</Link></li>
            </ul>
          </div>

          <div className="footer-section">
            <h3 className="footer-title">Contact Us</h3>
            <ul className="footer-contact">
              <li>
                <span className="contact-icon">📍</span>
                <span>123 Medical Center Drive, Healthcare City</span>
              </li>
              <li>
                <span className="contact-icon">📞</span>
                <span>+1 (555) 123-4567</span>
              </li>
              <li>
                <span className="contact-icon">✉️</span>
                <span>info@medidonate.org</span>
              </li>
              <li>
                <span className="contact-icon">🚨</span>
                <span>Emergency: 911</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <div className="footer-bottom-content">
            <p className="copyright">
              © 2026 MediDonate. All rights reserved.
            </p>
            <div className="footer-legal">
              <a href="#">Privacy Policy</a>
              <a href="#">Terms of Service</a>
              <a href="#">Cookie Policy</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer