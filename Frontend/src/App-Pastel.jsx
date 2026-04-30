import { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

// Navigation Bar Component
const NavigationBar = () => {
  return (
    <nav style={{
      position: 'fixed',
      top: '0',
      left: '0',
      right: '0',
      background: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(10px)',
      boxShadow: '0 2px 20px rgba(0,0,0,0.1)',
      zIndex: 1000,
      padding: '0 20px'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        maxWidth: '1200px',
        margin: '0 auto',
        height: '70px'
      }}>
        {/* Logo */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            background: 'linear-gradient(135deg, #FFB6C1 0%, #E6E6FA 100%)',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '16px',
            fontWeight: 'bold',
            color: '#8B7AB8'
          }}>
            RH
          </div>
          <span style={{
            fontSize: '1.5rem',
            fontWeight: '700',
            background: 'linear-gradient(135deg, #FFB6C1 0%, #8B7AB8 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
            ReliefHub
          </span>
        </div>

        {/* Navigation Links */}
        <div style={{
          display: 'flex',
          gap: '30px',
          alignItems: 'center'
        }}>
          <a 
            href="/" 
            style={{
              textDecoration: 'none',
              color: '#8B7AB8',
              fontWeight: '500',
              fontSize: '1rem',
              transition: 'all 0.3s ease',
              padding: '8px 16px',
              borderRadius: '20px',
              background: 'rgba(255, 182, 193, 0.1)'
            }}
            onMouseOver={(e) => {
              e.target.style.background = 'rgba(255, 182, 193, 0.2)';
              e.target.style.color = '#FF69B4';
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'rgba(255, 182, 193, 0.1)';
              e.target.style.color = '#8B7AB8';
            }}
          >
            Home
          </a>
          <a 
            href="/contacts" 
            style={{
              textDecoration: 'none',
              color: '#8B7AB8',
              fontWeight: '500',
              fontSize: '1rem',
              transition: 'all 0.3s ease',
              padding: '8px 16px',
              borderRadius: '20px'
            }}
            onMouseOver={(e) => {
              e.target.style.background = 'rgba(230, 230, 250, 0.3)';
              e.target.style.color = '#6B5B95';
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'transparent';
              e.target.style.color = '#8B7AB8';
            }}
          >
            Contacts
          </a>
          <a 
            href="/volunteers" 
            style={{
              textDecoration: 'none',
              color: '#8B7AB8',
              fontWeight: '500',
              fontSize: '1rem',
              transition: 'all 0.3s ease',
              padding: '8px 16px',
              borderRadius: '20px'
            }}
            onMouseOver={(e) => {
              e.target.style.background = 'rgba(255, 218, 185, 0.3)';
              e.target.style.color = '#FF8C00';
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'transparent';
              e.target.style.color = '#8B7AB8';
            }}
          >
            Volunteers
          </a>
          <a 
            href="/login" 
            style={{
              textDecoration: 'none',
              color: '#8B7AB8',
              fontWeight: '500',
              fontSize: '1rem',
              transition: 'all 0.3s ease',
              padding: '8px 16px',
              borderRadius: '20px',
              border: '2px solid #E6E6FA'
            }}
            onMouseOver={(e) => {
              e.target.style.background = '#E6E6FA';
              e.target.style.color = '#6B5B95';
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'transparent';
              e.target.style.color = '#8B7AB8';
            }}
          >
            Login
          </a>
          <a 
            href="/signup" 
            style={{
              textDecoration: 'none',
              color: 'white',
              fontWeight: '600',
              fontSize: '1rem',
              transition: 'all 0.3s ease',
              padding: '10px 20px',
              borderRadius: '25px',
              background: 'linear-gradient(135deg, #FFB6C1 0%, #FFA07A 100%)',
              boxShadow: '0 4px 15px rgba(255, 182, 193, 0.3)'
            }}
            onMouseOver={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 6px 20px rgba(255, 182, 193, 0.4)';
            }}
            onMouseOut={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 4px 15px rgba(255, 182, 193, 0.3)';
            }}
          >
            Signup
          </a>
        </div>
      </div>
    </nav>
  );
};

// Beautiful Home component
const SimpleHome = () => {
  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #FFF5F5 0%, #F0F8FF 25%, #F5FFFA 50%, #FFF0F5 75%, #F8F4FF 100%)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Animated Background Elements */}
      <div style={{
        position: 'absolute',
        top: '10%',
        left: '10%',
        width: '300px',
        height: '300px',
        background: 'radial-gradient(circle, rgba(255, 182, 193, 0.15) 0%, transparent 70%)',
        borderRadius: '50%',
        animation: 'float 6s ease-in-out infinite'
      }} />
      <div style={{
        position: 'absolute',
        bottom: '20%',
        right: '10%',
        width: '200px',
        height: '200px',
        background: 'radial-gradient(circle, rgba(230, 230, 250, 0.15) 0%, transparent 70%)',
        borderRadius: '50%',
        animation: 'float 8s ease-in-out infinite reverse'
      }} />
      <div style={{
        position: 'absolute',
        top: '60%',
        left: '20%',
        width: '150px',
        height: '150px',
        background: 'radial-gradient(circle, rgba(255, 218, 185, 0.1) 0%, transparent 70%)',
        borderRadius: '50%',
        animation: 'float 7s ease-in-out infinite'
      }} />
      
      {/* Navigation Bar */}
      <NavigationBar />
      
      {/* Main Content */}
      <div style={{
        position: 'relative',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: '120px 20px 40px',
        textAlign: 'center'
      }}>
        {/* Logo/Icon */}
        <div style={{
          width: '100px',
          height: '100px',
          background: 'linear-gradient(135deg, #FFB6C1 0%, #E6E6FA 100%)',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '30px',
          boxShadow: '0 20px 40px rgba(255, 182, 193, 0.3)',
          animation: 'pulse 2s ease-in-out infinite'
        }}>
          <div style={{
            width: '60px',
            height: '60px',
            background: 'white',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '24px',
            fontWeight: 'bold',
            color: '#FFB6C1'
          }}>
            RH
          </div>
        </div>

        {/* Main Title */}
        <h1 style={{
          fontSize: '4rem',
          fontWeight: '800',
          background: 'linear-gradient(135deg, #FFB6C1 0%, #8B7AB8 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          marginBottom: '20px',
          animation: 'fadeInUp 1s ease-out'
        }}>
          ReliefHub
        </h1>
        
        {/* Subtitle */}
        <p style={{
          fontSize: '1.5rem',
          color: '#8B7AB8',
          marginBottom: '40px',
          maxWidth: '600px',
          lineHeight: '1.6',
          animation: 'fadeInUp 1s ease-out 0.2s',
          animationFillMode: 'both'
        }}>
          Connecting communities, providing relief, and saving lives when disaster strikes
        </p>

        {/* Dashboard Cards */}
        <div style={{
          display: 'flex',
          gap: '30px',
          flexWrap: 'wrap',
          justifyContent: 'center',
          animation: 'fadeInUp 1s ease-out 0.4s',
          animationFillMode: 'both'
        }}>
          {/* Medical Donations Card */}
          <a 
            href="/medical-donations" 
            style={{
              display: 'block',
              padding: '30px 40px',
              background: 'linear-gradient(135deg, #B5EAD7 0%, #C7F9CC 100%)',
              color: '#2D6A4F',
              textDecoration: 'none',
              borderRadius: '20px',
              boxShadow: '0 10px 30px rgba(181, 234, 215, 0.3)',
              transition: 'all 0.3s ease',
              transform: 'translateY(0)',
              minWidth: '250px'
            }}
            onMouseOver={(e) => {
              e.target.style.transform = 'translateY(-10px)';
              e.target.style.boxShadow = '0 20px 40px rgba(181, 234, 215, 0.4)';
            }}
            onMouseOut={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 10px 30px rgba(181, 234, 215, 0.3)';
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '15px' }}>🩸</div>
            <h3 style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '10px' }}>
              Medical Donations
            </h3>
            <p style={{ fontSize: '1rem', opacity: 0.9, marginBottom: '15px' }}>
              Blood donations, medical supplies, healthcare support
            </p>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '8px 16px',
              background: 'rgba(255, 255, 255, 0.5)',
              borderRadius: '20px',
              fontSize: '0.9rem'
            }}>
              Explore Dashboard →
            </div>
          </a>

          {/* Disaster Rescue Card */}
          <a 
            href="/disaster-donations" 
            style={{
              display: 'block',
              padding: '30px 40px',
              background: 'linear-gradient(135deg, #FFDAB9 0%, #FFE4E1 100%)',
              color: '#D2691E',
              textDecoration: 'none',
              borderRadius: '20px',
              boxShadow: '0 10px 30px rgba(255, 218, 185, 0.3)',
              transition: 'all 0.3s ease',
              transform: 'translateY(0)',
              minWidth: '250px'
            }}
            onMouseOver={(e) => {
              e.target.style.transform = 'translateY(-10px)';
              e.target.style.boxShadow = '0 20px 40px rgba(255, 218, 185, 0.4)';
            }}
            onMouseOut={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 10px 30px rgba(255, 218, 185, 0.3)';
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '15px' }}>🚨</div>
            <h3 style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '10px' }}>
              Disaster Rescue
            </h3>
            <p style={{ fontSize: '1rem', opacity: 0.9, marginBottom: '15px' }}>
              Emergency response, relief efforts, crisis management
            </p>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '8px 16px',
              background: 'rgba(255, 255, 255, 0.5)',
              borderRadius: '20px',
              fontSize: '0.9rem'
            }}>
              Explore Dashboard →
            </div>
          </a>
        </div>

        {/* Quick Stats */}
        <div style={{
          display: 'flex',
          gap: '40px',
          marginTop: '60px',
          animation: 'fadeInUp 1s ease-out 0.6s',
          animationFillMode: 'both'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2.5rem', fontWeight: '800', color: '#8B7AB8', marginBottom: '5px' }}>
              50K+
            </div>
            <div style={{ fontSize: '1rem', color: '#B8B8D1' }}>
              Lives Saved
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2.5rem', fontWeight: '800', color: '#8B7AB8', marginBottom: '5px' }}>
              2K+
            </div>
            <div style={{ fontSize: '1rem', color: '#B8B8D1' }}>
              Volunteers
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2.5rem', fontWeight: '800', color: '#8B7AB8', marginBottom: '5px' }}>
              150+
            </div>
            <div style={{ fontSize: '1rem', color: '#B8B8D1' }}>
              Partners
            </div>
          </div>
        </div>
      </div>

      {/* Add CSS animations */}
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

// Simple Medical Dashboard
const SimpleMedical = () => (
  <div style={{ padding: '40px', backgroundColor: '#f0fdf4', minHeight: '100vh' }}>
    <h1 style={{ color: '#059669', fontSize: '48px', marginBottom: '20px' }}>
      Medical Donations Dashboard
    </h1>
    <p style={{ fontSize: '18px', color: '#374151' }}>
      ✅ Medical dashboard is working!
    </p>
    <div style={{ marginTop: '30px', padding: '20px', backgroundColor: 'white', borderRadius: '8px' }}>
      <h2 style={{ color: '#059669', marginBottom: '10px' }}>🩸 Features:</h2>
      <ul style={{ color: '#6b7280' }}>
        <li>Blood Donation Requests</li>
        <li>Medical Supplies</li>
        <li>Donation Form</li>
        <li>24/7 Medical Hotline</li>
      </ul>
    </div>
    <a href="/" style={{ 
      display: 'inline-block', 
      marginTop: '20px',
      padding: '10px 20px', 
      backgroundColor: '#6b7280', 
      color: 'white', 
      textDecoration: 'none', 
      borderRadius: '8px' 
    }}>
      ← Back to Home
    </a>
  </div>
);

// Simple Disaster Dashboard
const SimpleDisaster = () => (
  <div style={{ padding: '40px', backgroundColor: '#fef2f2', minHeight: '100vh' }}>
    <h1 style={{ color: '#dc2626', fontSize: '48px', marginBottom: '20px' }}>
      Disaster Rescue Dashboard
    </h1>
    <p style={{ fontSize: '18px', color: '#374151' }}>
      ✅ Disaster dashboard is working!
    </p>
    <div style={{ marginTop: '30px', padding: '20px', backgroundColor: 'white', borderRadius: '8px' }}>
      <h2 style={{ color: '#dc2626', marginBottom: '10px' }}>🚨 Features:</h2>
      <ul style={{ color: '#6b7280' }}>
        <li>Emergency Request Form</li>
        <li>Active Disasters</li>
        <li>Relief Requests</li>
        <li>24/7 Emergency Hotline</li>
      </ul>
    </div>
    <a href="/" style={{ 
      display: 'inline-block', 
      marginTop: '20px',
      padding: '10px 20px', 
      backgroundColor: '#6b7280', 
      color: 'white', 
      textDecoration: 'none', 
      borderRadius: '8px' 
    }}>
      ← Back to Home
    </a>
  </div>
);

function App() {
  useEffect(() => {
    console.log("ReliefHub app with pastel theme mounted");
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/" element={<SimpleHome />} />
        <Route path="/medical-donations" element={<SimpleMedical />} />
        <Route path="/disaster-donations" element={<SimpleDisaster />} />
      </Routes>
    </Router>
  );
}

export default App;
