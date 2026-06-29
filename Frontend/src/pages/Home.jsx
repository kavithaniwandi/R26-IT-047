import React from 'react'
import { Link } from 'react-router-dom'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import './Home.css'

function Home() {
  return (
    <div className="home">
      <Navigation />
      
      {/* Hero Section with Parallax */}
      <section className="hero-section parallax">
        <div className="hero-content">
          <h1 className="hero-title">Smart Medical Donation System</h1>
          <p className="hero-subtitle">Disaster Response & Emergency Medical Supplies</p>
          <div className="hero-buttons">
            <Link to="/donations" className="hero-button primary">Donate Now</Link>
            <Link to="/map" className="hero-button secondary">View Map</Link>
          </div>
        </div>
        <div className="hero-overlay"></div>
      </section>

      {/* About Section */}
      <section className="about-section">
        <div className="section-container">
          <h2 className="section-title">About Our Mission</h2>
          <p className="section-description">
            MediDonate is a revolutionary platform connecting medical donors with healthcare facilities 
            and disaster response teams. Our smart system ensures timely delivery of critical medical 
            supplies during emergencies, saving lives when it matters most.
          </p>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-number">10K+</div>
              <div className="stat-label">Donors Registered</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">500+</div>
              <div className="stat-label">Healthcare Partners</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">50K+</div>
              <div className="stat-label">Lives Impacted</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">24/7</div>
              <div className="stat-label">Emergency Response</div>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section 1 - Medical Supplies */}
      <section className="services-section parallax" data-speed="0.5">
        <div className="services-overlay"></div>
        <div className="section-container">
          <div className="service-content">
            <h2 className="section-title">Medical Supplies Distribution</h2>
            <p className="section-description">
              Our intelligent routing system ensures medical supplies reach the right locations at the right time. 
              From basic first aid kits to specialized equipment, we coordinate with healthcare providers to 
              meet urgent needs during disasters and medical emergencies.
            </p>
            <div className="service-features">
              <div className="feature-item">
                <span className="feature-icon">🏥</span>
                <h3>Hospital Partnerships</h3>
                <p>Direct coordination with healthcare facilities</p>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🚚</span>
                <h3>Smart Logistics</h3>
                <p>AI-powered route optimization for delivery</p>
              </div>
              <div className="feature-item">
                <span className="feature-icon">📦</span>
                <h3>Inventory Management</h3>
                <p>Real-time tracking of medical supplies</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section 2 - Blood Donation */}
      <section className="blood-section">
        <div className="section-container">
          <div className="blood-content">
            <h2 className="section-title">Blood Donation Network</h2>
            <p className="section-description">
              Connect with blood donors across the region. Our platform matches blood types with urgent 
              requirements, ensuring critical blood supplies are available for surgeries, trauma cases, 
              and disaster response operations.
            </p>
            <div className="blood-types">
              <div className="blood-type">A+</div>
              <div className="blood-type">A-</div>
              <div className="blood-type">B+</div>
              <div className="blood-type">B-</div>
              <div className="blood-type">AB+</div>
              <div className="blood-type">AB-</div>
              <div className="blood-type">O+</div>
              <div className="blood-type">O-</div>
            </div>
            <Link to="/donations" className="cta-button">Become a Donor</Link>
          </div>
        </div>
      </section>

      {/* Services Section 3 - Disaster Response */}
      <section className="disaster-section parallax" data-speed="0.3">
        <div className="disaster-overlay"></div>
        <div className="section-container">
          <div className="disaster-content">
            <h2 className="section-title">Disaster Response System</h2>
            <p className="section-description">
              When disaster strikes, every second counts. Our SOS alert system and real-time mapping 
              enable rapid deployment of medical resources to affected areas. Coordinate with emergency 
              responders and volunteers to provide immediate medical assistance.
            </p>
            <div className="disaster-features">
              <div className="disaster-feature">
                <span className="disaster-icon">🚨</span>
                <h3>SOS Alerts</h3>
                <p>Instant emergency notification system</p>
              </div>
              <div className="disaster-feature">
                <span className="disaster-icon">🗺️</span>
                <h3>Real-time Mapping</h3>
                <p>Live tracking of affected areas and resources</p>
              </div>
              <div className="disaster-feature">
                <span className="disaster-icon">👥</span>
                <h3>Volunteer Network</h3>
                <p>Mobilize community support quickly</p>
              </div>
              <div className="disaster-feature">
                <span className="disaster-icon">📡</span>
                <h3>Communication Hub</h3>
                <p>Seamless coordination between teams</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section 4 - Volunteer Network */}
      <section className="volunteer-section">
        <div className="section-container">
          <h2 className="section-title">Join Our Volunteer Network</h2>
          <p className="section-description">
            Make a difference in your community. Join thousands of volunteers who help coordinate 
            donations, assist with logistics, and provide support during medical emergencies. 
            Your time and skills can save lives.
          </p>
          <div className="volunteer-roles">
            <div className="role-card">
              <span className="role-icon">🚗</span>
              <h3>Transport Volunteers</h3>
              <p>Help deliver medical supplies to healthcare facilities</p>
            </div>
            <div className="role-card">
              <span className="role-icon">📞</span>
              <h3>Call Center Support</h3>
              <p>Assist with donor coordination and emergency calls</p>
            </div>
            <div className="role-card">
              <span className="role-icon">💉</span>
              <h3>Medical Professionals</h3>
              <p>Provide expertise and support during emergencies</p>
            </div>
            <div className="role-card">
              <span className="role-icon">📋</span>
              <h3>Administrative Support</h3>
              <p>Help with documentation and logistics planning</p>
            </div>
          </div>
          <Link to="/contacts" className="cta-button secondary">Sign Up as Volunteer</Link>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section parallax">
        <div className="cta-overlay"></div>
        <div className="section-container">
          <div className="cta-content">
            <h2 className="cta-title">Ready to Make a Difference?</h2>
            <p className="cta-description">
              Join our community of donors and volunteers. Together, we can save lives and 
              provide critical medical support during emergencies.
            </p>
            <div className="cta-buttons">
              <Link to="/donations" className="cta-button primary">Start Donating</Link>
              <Link to="/sos" className="cta-button emergency">SOS Emergency</Link>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}

export default Home
