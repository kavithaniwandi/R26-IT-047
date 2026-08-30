import React from 'react'
import { useNavigate } from 'react-router-dom'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import { useAuth } from '../context/AuthContext'
import './Profile.css'

function Profile() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  if (!user) {
    navigate('/signin')
    return null
  }

  return (
    <div className="profile-page">
      <Navigation />
      <div className="profile-container">
        <div className="profile-header">
          <div className="profile-avatar">
            <span className="avatar-icon">👤</span>
          </div>
          <h1 className="profile-name">{user.name}</h1>
          <p className="profile-email">{user.email}</p>
        </div>

        <div className="profile-content">
          <div className="profile-section">
            <h2 className="section-title">Account Information</h2>
            <div className="info-grid">
              <div className="info-item">
                <label>Name</label>
                <p>{user.name}</p>
              </div>
              <div className="info-item">
                <label>Email</label>
                <p>{user.email}</p>
              </div>
              <div className="info-item">
                <label>Member Since</label>
                <p>{new Date(user.id).toLocaleDateString()}</p>
              </div>
              <div className="info-item">
                <label>Account Type</label>
                <p>Donor</p>
              </div>
            </div>
          </div>

          <div className="profile-section">
            <h2 className="section-title">Donation Statistics</h2>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-number">0</div>
                <div className="stat-label">Donations Made</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">0</div>
                <div className="stat-label">Volunteer Hours</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">0</div>
                <div className="stat-label">Lives Impacted</div>
              </div>
            </div>
          </div>

          <div className="profile-section">
            <h2 className="section-title">Quick Actions</h2>
            <div className="actions-grid">
              <button className="action-button">
                <span className="action-icon">📝</span>
                <span>Edit Profile</span>
              </button>
              <button className="action-button">
                <span className="action-icon">🔒</span>
                <span>Change Password</span>
              </button>
              <button className="action-button">
                <span className="action-icon">📋</span>
                <span>Donation History</span>
              </button>
              <button className="action-button">
                <span className="action-icon">⚙️</span>
                <span>Settings</span>
              </button>
            </div>
          </div>

          <div className="profile-section">
            <h2 className="section-title">Account Actions</h2>
            <button onClick={handleLogout} className="logout-button">
              <span className="logout-icon">🚪</span>
              <span>Logout</span>
            </button>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default Profile
