import React from 'react'
import { useNavigate } from 'react-router-dom'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import './Donations.css'

function AdminDashboard() {
  const navigate = useNavigate()

  return (
    <div className="donations-page">
      <Navigation />
      <div className="donations-container">
        <div className="donations-header">
          <h1>Admin Control Panel</h1>
          <p>Coordinate disaster responses, manage relief inventory, and oversee users</p>
        </div>
        <div className="donations-grid">
          <div className="donation-card">
            <span className="donation-icon">🚨</span>
            <h2>Disaster Donation Requests</h2>
            <p>Create donation requests for disaster relief efforts</p>
            <button
              className="donate-button"
              onClick={() => navigate('/disaster-donation-request')}
            >
              Manage Requests
            </button>
          </div>

          <div className="donation-card">
            <span className="donation-icon">👥</span>
            <h2>User Management</h2>
            <p>Oversee registered donors, coordinators and roles</p>
            <button
              className="donate-button"
              onClick={() => navigate('/contacts')}
            >
              Manage Users
            </button>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default AdminDashboard