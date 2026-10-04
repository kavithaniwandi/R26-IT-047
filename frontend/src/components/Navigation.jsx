import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import CreditStatusBar from "./CreditStatusBar";
import { Radio, ShieldAlert } from "lucide-react";
import "./Navigation.css";

function Navigation() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 30);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const closeMenu = () => setMobileMenuOpen(false);

  const handleLogout = () => {
    logout();
    navigate("/signin");
    closeMenu();
  };

  return (
    <nav className={`navigation ${scrolled ? "scrolled" : ""}`}>
      <div className="nav-container">
        {/* LOGO */}
        <Link to="/" className="nav-logo">
          <div style={{ width: '36px', height: '36px', borderRadius: '10px', backgroundColor: '#2563eb', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <Radio size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.94rem', fontWeight: '800', letterSpacing: '-0.02em', color: '#0f172a', lineHeight: '1.2' }}>
              DISASTER RELIEF
            </div>
            <div style={{ fontSize: '0.62rem', color: '#2563eb', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Smart Medical Telemetry
            </div>
          </div>
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

          {user ? (
            <>
              <Link to="/profile" className="nav-link profile-link" onClick={closeMenu}>
                {user.full_name || user.email || "Profile"}
              </Link>
              <button className="logout-button" onClick={handleLogout}>
                Logout
              </button>
            </>
          ) : (
            <Link to="/signin" className="nav-link" onClick={closeMenu}>
              Sign In
            </Link>
          )}

          <CreditStatusBar />

          <Link to="/sos-public" className="sos-button" onClick={closeMenu}>
            <ShieldAlert size={15} />
            <span>Emergency SOS</span>
          </Link>
        </div>

        {/* MOBILE MENU */}
        <button
          className="mobile-menu-button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle menu"
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
