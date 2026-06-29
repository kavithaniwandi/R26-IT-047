import React from 'react'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import './Contacts.css'

function Contacts() {
  return (
    <div className="contacts-page">
      <Navigation />
      <div className="contacts-container">
        <div className="contacts-header">
          <h1>Contact Us</h1>
          <p>Get in touch with our team for support and inquiries</p>
        </div>
        <div className="contacts-content">
          <div className="contact-form-section">
            <form className="contact-form">
              <div className="form-group">
                <label htmlFor="name">Full Name</label>
                <input type="text" id="name" placeholder="Enter your name" required />
              </div>
              <div className="form-group">
                <label htmlFor="email">Email Address</label>
                <input type="email" id="email" placeholder="Enter your email" required />
              </div>
              <div className="form-group">
                <label htmlFor="subject">Subject</label>
                <input type="text" id="subject" placeholder="Enter subject" required />
              </div>
              <div className="form-group">
                <label htmlFor="message">Message</label>
                <textarea id="message" rows="5" placeholder="Enter your message" required></textarea>
              </div>
              <button type="submit" className="submit-button">Send Message</button>
            </form>
          </div>
          <div className="contact-info-section">
            <div className="contact-info-card">
              <span className="contact-info-icon">📍</span>
              <h3>Address</h3>
              <p>123 Medical Center Drive<br />Healthcare City, HC 12345</p>
            </div>
            <div className="contact-info-card">
              <span className="contact-info-icon">📞</span>
              <h3>Phone</h3>
              <p>+1 (555) 123-4567<br />+1 (555) 987-6543</p>
            </div>
            <div className="contact-info-card">
              <span className="contact-info-icon">✉️</span>
              <h3>Email</h3>
              <p>info@medidonate.org<br />support@medidonate.org</p>
            </div>
            <div className="contact-info-card emergency">
              <span className="contact-info-icon">🚨</span>
              <h3>Emergency</h3>
              <p>24/7 Emergency Line<br />911</p>
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default Contacts
