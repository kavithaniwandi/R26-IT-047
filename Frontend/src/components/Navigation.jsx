import React, { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Navigation.css'

function Navigation() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/')
    setMobileMenuOpen(false)
  }

  return (
    <nav className={`navigation ${scrolled ? 'scrolled' : ''}`}>
      <div className="nav-container">
        <Link to="/" className="nav-logo">
          <span className="logo-icon">❤️</span>
          <span className="logo-text">MediDonate</span>
        </Link>

        <div className={`nav-links ${mobileMenuOpen ? 'open' : ''}`}>
          <Link to="/" className="nav-link">Home</Link>
          <Link to="/map" className="nav-link">Map</Link>
          <Link to="/donations" className="nav-link">Donations</Link>
          <Link to="/contacts" className="nav-link">Contacts</Link>
          {user ? (
            <>
              <Link to="/profile" className="nav-link profile-link">
                <span className="profile-icon">👤</span>
                <span className="profile-name">{user.name || 'Profile'}</span>
              </Link>
              <button onClick={handleLogout} className="nav-link logout-button">Logout</button>
            </>
          ) : (
            <Link to="/signin" className="nav-link">Sign In</Link>
          )}
          <Link to="/sos" className="nav-link sos-button">SOS</Link>
        </div>

        <button 
          className="mobile-menu-button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle menu"
        >
          <span className={`hamburger ${mobileMenuOpen ? 'open' : ''}`}>
            <span></span>
            <span></span>
            <span></span>
          </span>
        </button>
      </div>
    </nav>
  )
}

export default Navigation
