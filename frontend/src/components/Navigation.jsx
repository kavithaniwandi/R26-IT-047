import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Radio, ShieldAlert, LogIn, UserCheck } from 'lucide-react';
import './Navigation.css';

export function Navigation() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const isSignInPage = location.pathname === '/signin';

  return (
    <header className="site-public-navbar">
      <div className="site-public-navbar-container">
        {/* Brand Logo */}
        <Link to="/" className="site-public-brand">
          <div className="site-public-brand-icon">
            <Radio size={20} />
          </div>
          <div>
            <div className="site-public-brand-title">
              SRI LANKA DISASTER RELIEF
            </div>
            <div className="site-public-brand-subtitle">
              Smart Medical & Emergency Telemetry Cloud
            </div>
          </div>
        </Link>

        {/* Center Nav Links */}
        <nav className="site-public-nav-links">
          <Link to="/" className="site-public-nav-link">
            Stakeholder Portals
          </Link>
          <Link to="/map" className="site-public-nav-link">
            Live GIS Map
          </Link>
          <a href="/#ai-models" className="site-public-nav-link">
            ML Intelligence
          </a>
          <a href="/#helplines" className="site-public-nav-link">
            Emergency Helplines
          </a>
          <Link to="/donation-appeal" className="site-public-nav-link">
            Donation Appeals
          </Link>
        </nav>

        {/* Right CTA buttons */}
        <div className="site-public-nav-actions">
          <Link
            to="/sos-public"
            className="btn btn-danger btn-sm site-public-sos-btn"
          >
            <ShieldAlert size={15} />
            <span>Emergency SOS</span>
          </Link>

          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Link
                to={`/?portal=${encodeURIComponent(user.role || 'admin')}`}
                className="btn btn-secondary btn-sm"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontWeight: '600',
                  padding: '7px 14px'
                }}
              >
                <UserCheck size={14} style={{ color: 'var(--blue-600, #2563eb)' }} />
                <span>{user.full_name || user.email || 'Dashboard'}</span>
              </Link>
              <button
                className="btn btn-outline btn-sm"
                style={{ fontWeight: '600', padding: '7px 12px' }}
                onClick={logout}
                title="Sign out"
              >
                Logout
              </button>
            </div>
          ) : isSignInPage ? (
            <Link
              to="/"
              className="btn btn-secondary btn-sm"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontWeight: '600',
                padding: '7px 14px',
                textDecoration: 'none'
              }}
            >
              <span>Back to Home</span>
            </Link>
          ) : (
            <Link
              to="/signin"
              className="btn btn-primary btn-sm"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontWeight: '700',
                padding: '7px 18px',
                backgroundColor: 'var(--color-primary, #2563eb)',
                color: '#ffffff',
                borderRadius: 'var(--radius-md, 8px)',
                boxShadow: '0 2px 6px rgba(37, 99, 235, 0.25)',
                textDecoration: 'none'
              }}
              title="Sign in to your Stakeholder Portal"
            >
              <LogIn size={15} />
              <span>Signin</span>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

export default Navigation;
