import React from 'react'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import './Donations.css'

function Donations() {
  return (
    <div className="donations-page">
      <Navigation />
      <div className="donations-container">
        <div className="donations-header">
          <h1>Make a Donation</h1>
          <p>Choose how you want to contribute to saving lives</p>
        </div>
        <div className="donations-grid">
          <div className="donation-card">
            <span className="donation-icon">💉</span>
            <h2>Blood Donation</h2>
            <p>Donate blood and help save lives during emergencies and medical procedures</p>
            <button className="donate-button">Donate Blood</button>
          </div>
          <div className="donation-card">
            <span className="donation-icon">🏥</span>
            <h2>Medical Supplies</h2>
            <p>Contribute medical equipment, first aid kits, and healthcare supplies</p>
            <button className="donate-button">Donate Supplies</button>
          </div>
          <div className="donation-card">
            <span className="donation-icon">💰</span>
            <h2>Financial Support</h2>
            <p>Provide monetary support to help purchase critical medical resources</p>
            <button className="donate-button">Donate Money</button>
          </div>
          <div className="donation-card">
            <span className="donation-icon">👤</span>
            <h2>Volunteer</h2>
            <p>Offer your time and skills to help with logistics and coordination</p>
            <button className="donate-button">Become Volunteer</button>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default Donations
