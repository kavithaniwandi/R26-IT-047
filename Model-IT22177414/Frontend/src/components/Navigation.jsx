import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logo from "../assets/logo.png";
import "./Navigation.css";

function Navigation() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const closeMenu = () => {
    setMobileMenuOpen(false);
  };

  const handleLogout = () => {
    logout();
    navigate("/");
    closeMenu();
  };

  return (
    <nav className="navigation">
      <div className="nav-container">
        {/* LOGO */}
        <Link to="/" className="nav-logo" onClick={closeMenu}>
          <img src={logo} alt="MediDonate Logo" className="logo-image" />
        </Link>

        {/* NAVIGATION LINKS */}
        <div className={`nav-links ${mobileMenuOpen ? "open" : ""}`}>
          <Link to="/" className="nav-link" onClick={closeMenu}>
            Home
          </Link>
          <Link to="/map" className="nav-link" onClick={closeMenu}>
            Disaster Map
          </Link>
          <Link to="/donations" className="nav-link" onClick={closeMenu}>
            Donations
          </Link>
          <Link to="/contacts" className="nav-link" onClick={closeMenu}>
            Contacts
          </Link>
          <Link to="/donor-details" className="nav-link" onClick={closeMenu}>
            Donor Details
          </Link>

          {user ? (
            <>
              <Link
                to="/profile"
                className="nav-link profile-link"
                onClick={closeMenu}
              >
                {user.name || user.firstName || "Profile"}
              </Link>
              <button
                type="button"
                className="nav-action-btn logout-button"
                onClick={handleLogout}
              >
                Logout
              </button>
            </>
          ) : (
            <Link to="/signin" className="nav-link" onClick={closeMenu}>
              Sign In
            </Link>
          )}

          <Link to="/sos" className="nav-action-btn sos-button" onClick={closeMenu}>
            Emergency SOS
          </Link>
        </div>

        {/* MOBILE TOGGLE */}
        <button
          type="button"
          className="mobile-menu-button"
          aria-label="Toggle menu"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          <span className={`hamburger ${mobileMenuOpen ? "active" : ""}`}>
            <span></span>
            <span></span>
            <span></span>
          </span>
        </button>
      </div>
    </nav>
  );
}

export default Navigation;