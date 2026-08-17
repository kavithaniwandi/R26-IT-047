import React from 'react'
import { useNavigate } from 'react-router-dom'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import './Donations.css'

function DonorDashboard() {
  const navigate = useNavigate()

  return (
    <div className="donations-page">
      <Navigation />
      <div className="donations-container">
        <div className="donations-header">
          <h1>Donor Dashboard</h1>
          <p>Manage your contributions and help those in need</p>
        </div>
        <div className="donations-grid">
          <div className="donation-card">
            <span className="donation-icon">📦</span>
            <h2>Donate Items</h2>
            <p>Contribute medical supplies, food packs, and critical relief items</p>
            <button
              className="donate-button"
              onClick={() => navigate('/donations')}
            >
              Donate Now
            </button>
          </div>

          <div className="story-card">
            <span className="story-icon">📋</span>
            <h2>Disaster Requests</h2>
            <p>Browse active disaster areas and view urgent relief requirements</p>
            <button
              className="donate-button"
              onClick={() => navigate('/disaster-donation-request')}
            >
              View Requests
            </button>
          </div>

          <div className="donation-card">
            <span className="donation-icon">📜</span>
            <h2>Donation History</h2>
            <p>View your past donations, impact summary, and fulfillment receipts</p>
            <button
              className="donate-button"
              onClick={() => navigate('/donor-details')}
            >
              View History
            </button>
          </div>

          <div className="donation-card">
            <span className="donation-icon">👤</span>
            <h2>My Profile</h2>
            <p>Update your contact information, emergency alerts, and preferences</p>
            <button
              className="donate-button"
              onClick={() => navigate('/profile')}
            >
              Edit Profile
            </button>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default DonorDashboard