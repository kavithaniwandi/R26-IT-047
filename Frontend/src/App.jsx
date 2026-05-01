import { useEffect, useState, useRef } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import logo from './assets/logo.png';
import medIcon from './assets/med.png';
import disIcon from './assets/dis.png';
import heroImage from './assets/i4.jpg';
import heroVideo1 from './assets/1.mp4';
import heroVideo2 from './assets/2.mp4';
import heroVideo3 from './assets/3.mp4';
import heroVideo4 from './assets/4.mp4';
import heroVideo5 from './assets/5.mp4';
import emergencyIcon from './assets/emergency.png';
import activeIcon from './assets/active.png';
import reliefIcon from './assets/relief.png';
import hotlineIcon from './assets/hotline.png';
import RequestForm from './components/RequestForm.jsx';
import History from './pages/History';
import OfflineBanner from './components/OfflineBanner';

// Navigation Bar Component
const NavigationBar = () => {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav style={{
      position: 'fixed',
      top: '0',
      left: '0',
      right: '0',
      background: scrolled ? 'rgba(255, 255, 255, 0.1)' : 'rgba(255, 255, 255, 0.05)',
      backdropFilter: 'blur(10px)',
      boxShadow: scrolled ? '0 4px 30px rgba(59, 130, 246, 0.1)' : '0 2px 20px rgba(0,0,0,0.05)',
      zIndex: 1000,
      padding: '0 20px',
      transition: 'all 0.3s ease'
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
          gap: '12px'
        }}>
          <div style={{
            width: '60px',
            height: '60px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 15px rgba(59, 130, 246, 0.3)'
          }}>
            {/* Logo fallback - will show if image doesn't load */}
            <span style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '100%',
              height: '100%'
            }}>
              <img 
                src={logo} 
                alt="Jeevadhara" 
                style={{width: '50px', height: '50px', objectFit: 'contain'}} 
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.parentElement.innerHTML = '<span style="color: white; font-weight: bold;">JD</span>';
                }}
              />
            </span>
          </div>
          <span style={{
            fontSize: '1.6rem',
            fontWeight: '700',
            color: '#3B82F6'
          }}>
            Jeevadhara
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
              color: '#3B82F6',
              fontWeight: '500',
              fontSize: '1rem',
              transition: 'all 0.3s ease',
              padding: '8px 16px',
              borderRadius: '20px',
              background: 'rgba(59, 130, 246, 0.08)'
            }}
            onMouseOver={(e) => {
              e.target.style.background = 'rgba(59, 130, 246, 0.15)';
              e.target.style.color = '#2563EB';
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'rgba(59, 130, 246, 0.08)';
              e.target.style.color = '#3B82F6';
            }}
          >
            Home
          </a>
          <a 
            href="/contacts" 
            style={{
              textDecoration: 'none',
              color: '#64748B',
              fontWeight: '500',
              fontSize: '1rem',
              transition: 'all 0.3s ease',
              padding: '8px 16px',
              borderRadius: '20px'
            }}
            onMouseOver={(e) => {
              e.target.style.background = 'rgba(59, 130, 246, 0.1)';
              e.target.style.color = '#3B82F6';
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'transparent';
              e.target.style.color = '#64748B';
            }}
          >
            Contacts
          </a>
          <a 
            href="/volunteers" 
            style={{
              textDecoration: 'none',
              color: '#64748B',
              fontWeight: '500',
              fontSize: '1rem',
              transition: 'all 0.3s ease',
              padding: '8px 16px',
              borderRadius: '20px'
            }}
            onMouseOver={(e) => {
              e.target.style.background = 'rgba(59, 130, 246, 0.1)';
              e.target.style.color = '#3B82F6';
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'transparent';
              e.target.style.color = '#64748B';
            }}
          >
            Volunteers
          </a>
          <a 
            href="/login" 
            style={{
              textDecoration: 'none',
              color: '#3B82F6',
              fontWeight: '500',
              fontSize: '1rem',
              transition: 'all 0.3s ease',
              padding: '8px 16px',
              borderRadius: '20px',
              border: '2px solid #3B82F6'
            }}
            onMouseOver={(e) => {
              e.target.style.background = '#3B82F6';
              e.target.style.color = 'white';
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'transparent';
              e.target.style.color = '#3B82F6';
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
              padding: '12px 24px',
              borderRadius: '25px',
              background: 'linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%)',
              boxShadow: '0 4px 15px rgba(59, 130, 246, 0.3)'
            }}
            onMouseOver={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 6px 20px rgba(59, 130, 246, 0.4)';
            }}
            onMouseOut={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 4px 15px rgba(59, 130, 246, 0.3)';
            }}
          >
            Signup
          </a>
        </div>
      </div>
    </nav>
  );
};

// Animated Counter Component
const AnimatedCounter = ({ target, duration = 2000, suffix = '' }) => {
  const [count, setCount] = useState(0);
  const [hasAnimated, setHasAnimated] = useState(false);
  const ref = useRef();

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true);
          let start = 0;
          const increment = target / (duration / 16);
          
          const timer = setInterval(() => {
            start += increment;
            if (start >= target) {
              setCount(target);
              clearInterval(timer);
            } else {
              setCount(Math.floor(start));
            }
          }, 16);
        }
      },
      { threshold: 0.5 }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [target, duration, hasAnimated]);

  return <span ref={ref}>{count.toLocaleString()}{suffix}</span>;
};

// Beautiful Home Component with Proper Scrolling
const SimpleHome = () => {
  const [scrollY, setScrollY] = useState(0);
  const [currentVideo, setCurrentVideo] = useState(1);
  const videoRef = useRef(null);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleVideoEnd = () => {
    // Switch to the next video (1 -> 2 -> 3 -> 4 -> 5 -> 1...)
    setCurrentVideo(prev => prev === 5 ? 1 : prev + 1);
  };

  // Create video array for easy access
  const videos = [heroVideo1, heroVideo2, heroVideo3, heroVideo4, heroVideo5];

  useEffect(() => {
    // When currentVideo changes, update the video source
    if (videoRef.current) {
      videoRef.current.load();
      videoRef.current.play().catch(err => console.log('Video play error:', err));
    }
  }, [currentVideo]);

  return (
    <div style={{ 
      width: '100vw',
      minWidth: '100vw',
      maxWidth: '100vw',
      background: 'linear-gradient(180deg, #FFFFFF 0%, #F0F9FF 50%, #E0F2FE 100%)',
      position: 'relative',
      overflowX: 'hidden',
      margin: 0,
      padding: 0,
      boxSizing: 'border-box'
    }}>
      {/* Hero Section with Video Background */}
      <section style={{
        height: '100vh',
        width: '100vw',
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        margin: 0,
        padding: 0,
        minHeight: '100vh'
      }}>
        {/* Video Background Only */}
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          preload="auto"
          onEnded={handleVideoEnd}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            zIndex: 1
          }}
          onError={(e) => {
            console.log('Video error:', e);
            // Fallback to gradient background if video fails
            e.target.style.display = 'none';
          }}
        >
          <source src={videos[currentVideo - 1]} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
        
        {/* Overlay for better text visibility */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(255, 255, 255, 0.3)',
          zIndex: 2
        }} />
        
        {/* Navigation Bar */}
        <NavigationBar />
        
        {/* Hero Content */}
        <div style={{
          position: 'relative',
          zIndex: 10,
          textAlign: 'center',
          padding: '0 20px',
          transform: `translateY(${scrollY * 0.2}px)`
        }}>
          {/* Logo/Icon */}
          <div style={{
            width: '200px',
            height: '200px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 40px',
            boxShadow: '0 20px 40px rgba(59, 130, 246, 0.3)',
            animation: 'pulse 3s ease-in-out infinite',
            background: 'linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%)',
            borderRadius: '50%'
          }}>
            <div style={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'white',
              borderRadius: '50%',
              margin: '5px'
            }}>
              <img 
                src={logo} 
                alt="Jeevadhara" 
                style={{width: '160px', height: '160px', objectFit: 'contain'}} 
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.parentElement.innerHTML = '<span style="color: #3B82F6; font-size: 60px; font-weight: bold;">JD</span>';
                }}
              />
            </div>
          </div>

          {/* Main Title */}
          <h1 style={{
            fontSize: '5rem',
            fontWeight: '900',
            color: '#3B82F6',
            marginBottom: '24px',
            animation: 'fadeInUp 1s ease-out',
            textShadow: '2px 2px 4px rgba(0,0,0,0.1)'
          }}>
            Jeevadhara
          </h1>
          
          {/* Subtitle */}
          <p style={{
            fontSize: '1.6rem',
            color: '#1e293b',
            marginBottom: '50px',
            maxWidth: '700px',
            lineHeight: '1.7',
            margin: '0 auto 50px',
            animation: 'fadeInUp 1s ease-out 0.2s',
            animationFillMode: 'both',
            textShadow: '2px 2px 4px rgba(0,0,0,0.3)'
          }}>
            Connecting communities, providing relief, and saving lives when disaster strikes. 
            Every second counts, every donation matters.
          </p>
        </div>

        {/* Scroll Indicator */}
        <div style={{
          position: 'absolute',
          bottom: '30px',
          left: '50%',
          transform: 'translateX(-50%)',
          animation: 'bounce 2s infinite',
          zIndex: 10
        }}>
          <div style={{
            width: '6px',
            height: '10px',
            border: '2px solid #3B82F6',
            borderRadius: '10px',
            display: 'flex',
            justifyContent: 'center'
          }}>
            <div style={{
              width: '1px',
              height: '3px',
              background: '#3B82F6',
              borderRadius: '1px',
              marginTop: '2px'
            }} />
          </div>
        </div>
      </section>

      {/* Services Section - Medical Donations */}
      <section style={{
        padding: '100px 20px',
        background: 'linear-gradient(180deg, #f8fafc 0%, #e0f2fe 100%)',
        position: 'relative'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          textAlign: 'center'
        }}>
          <h2 style={{
            fontSize: '3rem',
            fontWeight: '800',
            color: '#1e40af',
            marginBottom: '20px',
            animation: 'fadeInUp 1s ease-out'
          }}>
            Medical Donations
          </h2>
          <p style={{
            fontSize: '1.2rem',
            color: '#64748b',
            marginBottom: '50px',
            maxWidth: '600px',
            margin: '0 auto 50px',
            lineHeight: '1.6'
          }}>
            Save lives through blood donations, medical supplies, and healthcare support
          </p>
          
          {/* Medical Donations Card */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            animation: 'fadeInUp 1s ease-out 0.2s',
            animationFillMode: 'both'
          }}>
            <a 
              href="/medical-donations" 
              style={{
                display: 'block',
                padding: '50px 60px',
                background: 'linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%)',
                color: '#1E40AF',
                textDecoration: 'none',
                borderRadius: '24px',
                boxShadow: '0 20px 40px rgba(59, 130, 246, 0.2)',
                transition: 'all 0.3s ease',
                transform: 'translateY(0)',
                maxWidth: '500px',
                width: '100%',
                border: '1px solid rgba(59, 130, 246, 0.1)',
                textAlign: 'center'
              }}
              onMouseOver={(e) => {
                e.target.style.transform = 'translateY(-10px)';
                e.target.style.boxShadow = '0 30px 60px rgba(59, 130, 246, 0.3)';
              }}
              onMouseOut={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 20px 40px rgba(59, 130, 246, 0.2)';
              }}
            >
              <div style={{ marginBottom: '30px', display: 'flex', justifyContent: 'center' }}>
                <img 
                  src={medIcon} 
                  alt="Medical Donations" 
                  style={{width: '100px', height: '100px', objectFit: 'contain'}} 
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.parentElement.innerHTML = '<div style="font-size: 4rem;">🩸</div>';
                  }}
                />
              </div>
              <h3 style={{ fontSize: '2.2rem', fontWeight: '700', marginBottom: '16px' }}>
                Medical Donations
              </h3>
              <p style={{ fontSize: '1.2rem', opacity: 0.8, marginBottom: '30px', lineHeight: '1.6' }}>
                Blood donations, medical supplies, healthcare support
              </p>
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '16px 24px',
                background: 'rgba(255, 255, 255, 0.8)',
                borderRadius: '20px',
                fontSize: '1.1rem',
                fontWeight: '600',
                boxShadow: '0 4px 15px rgba(59, 130, 246, 0.2)'
              }}>
                Explore Dashboard →
              </div>
            </a>
          </div>
        </div>
      </section>

      {/* Services Section - Disaster Rescue */}
      <section style={{
        padding: '100px 20px',
        background: 'linear-gradient(180deg, #fef2f2 0%, #fee2e2 100%)',
        position: 'relative'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          textAlign: 'center'
        }}>
          <h2 style={{
            fontSize: '3rem',
            fontWeight: '800',
            color: '#dc2626',
            marginBottom: '20px',
            animation: 'fadeInUp 1s ease-out'
          }}>
            Disaster Rescue
          </h2>
          <p style={{
            fontSize: '1.2rem',
            color: '#7f1d1d',
            marginBottom: '50px',
            maxWidth: '600px',
            margin: '0 auto 50px',
            lineHeight: '1.6'
          }}>
            Emergency response coordination, relief efforts, and crisis management
          </p>
          
          {/* Disaster Rescue Card */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            animation: 'fadeInUp 1s ease-out 0.2s',
            animationFillMode: 'both'
          }}>
            <a 
              href="/disaster-donations" 
              style={{
                display: 'block',
                padding: '50px 60px',
                background: 'linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%)',
                color: '#DC2626',
                textDecoration: 'none',
                borderRadius: '24px',
                boxShadow: '0 20px 40px rgba(239, 68, 68, 0.2)',
                transition: 'all 0.3s ease',
                transform: 'translateY(0)',
                maxWidth: '500px',
                width: '100%',
                border: '1px solid rgba(239, 68, 68, 0.1)',
                textAlign: 'center'
              }}
              onMouseOver={(e) => {
                e.target.style.transform = 'translateY(-10px)';
                e.target.style.boxShadow = '0 30px 60px rgba(239, 68, 68, 0.3)';
              }}
              onMouseOut={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 20px 40px rgba(239, 68, 68, 0.2)';
              }}
            >
              <div style={{ marginBottom: '30px', display: 'flex', justifyContent: 'center' }}>
                <img 
                  src={disIcon} 
                  alt="Disaster Rescue" 
                  style={{width: '100px', height: '100px', objectFit: 'contain'}} 
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.parentElement.innerHTML = '<div style="font-size: 4rem;">🚨</div>';
                  }}
                />
              </div>
              <h3 style={{ fontSize: '2.2rem', fontWeight: '700', marginBottom: '16px' }}>
                Disaster Rescue
              </h3>
              <p style={{ fontSize: '1.2rem', opacity: 0.8, marginBottom: '30px', lineHeight: '1.6' }}>
                Emergency response, relief efforts, crisis management
              </p>
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '16px 24px',
                background: 'rgba(255, 255, 255, 0.8)',
                borderRadius: '20px',
                fontSize: '1.1rem',
                fontWeight: '600',
                boxShadow: '0 4px 15px rgba(239, 68, 68, 0.2)'
              }}>
                Explore Dashboard →
              </div>
            </a>
          </div>
        </div>
      </section>

      {/* Stats Section with Animated Counters */}
      <section style={{
        padding: '100px 20px',
        background: 'white',
        position: 'relative'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          textAlign: 'center'
        }}>
          <h2 style={{
            fontSize: '3rem',
            fontWeight: '800',
            color: '#1E293B',
            marginBottom: '20px'
          }}>
            Making a Real Impact
          </h2>
          <p style={{
            fontSize: '1.3rem',
            color: '#64748B',
            marginBottom: '60px',
            maxWidth: '600px',
            margin: '0 auto 60px'
          }}>
            Together we're creating hope and saving lives every day
          </p>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '40px'
          }}>
            <div style={{
              textAlign: 'center',
              padding: '40px 20px',
              background: 'linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%)',
              borderRadius: '20px',
              border: '1px solid rgba(59, 130, 246, 0.1)'
            }}>
              <div style={{
                fontSize: '3.5rem',
                fontWeight: '900',
                color: '#3B82F6',
                marginBottom: '10px'
              }}>
                <AnimatedCounter target={50000} suffix="+" />
              </div>
              <div style={{ fontSize: '1.2rem', color: '#64748B', fontWeight: '600' }}>
                Lives Saved
              </div>
            </div>
            
            <div style={{
              textAlign: 'center',
              padding: '40px 20px',
              background: 'linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%)',
              borderRadius: '20px',
              border: '1px solid rgba(34, 197, 94, 0.1)'
            }}>
              <div style={{
                fontSize: '3.5rem',
                fontWeight: '900',
                color: '#22C55E',
                marginBottom: '10px'
              }}>
                <AnimatedCounter target={2500} suffix="+" />
              </div>
              <div style={{ fontSize: '1.2rem', color: '#64748B', fontWeight: '600' }}>
                Volunteers
              </div>
            </div>
            
            <div style={{
              textAlign: 'center',
              padding: '40px 20px',
              background: 'linear-gradient(135deg, #FEF3C7 0%, #FEF9C3 100%)',
              borderRadius: '20px',
              border: '1px solid rgba(245, 158, 11, 0.1)'
            }}>
              <div style={{
                fontSize: '3.5rem',
                fontWeight: '900',
                color: '#F59E0B',
                marginBottom: '10px'
              }}>
                <AnimatedCounter target={180} suffix="+" />
              </div>
              <div style={{ fontSize: '1.2rem', color: '#64748B', fontWeight: '600' }}>
                Partner Organizations
              </div>
            </div>
            
            <div style={{
              textAlign: 'center',
              padding: '40px 20px',
              background: 'linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%)',
              borderRadius: '20px',
              border: '1px solid rgba(239, 68, 68, 0.1)'
            }}>
              <div style={{
                fontSize: '3.5rem',
                fontWeight: '900',
                color: '#EF4444',
                marginBottom: '10px'
              }}>
                24/7
              </div>
              <div style={{ fontSize: '1.2rem', color: '#64748B', fontWeight: '600' }}>
                Emergency Support
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section style={{
        padding: '100px 20px',
        background: 'linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto'
        }}>
          <h2 style={{
            fontSize: '3rem',
            fontWeight: '800',
            color: '#1E293B',
            textAlign: 'center',
            marginBottom: '60px'
          }}>
            How We Help
          </h2>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
            gap: '40px'
          }}>
            <div style={{
              background: 'white',
              padding: '40px',
              borderRadius: '20px',
              boxShadow: '0 10px 30px rgba(0,0,0,0.05)',
              border: '1px solid rgba(59, 130, 246, 0.1)',
              transition: 'all 0.3s ease'
            }}>
              <div style={{
                width: '60px',
                height: '60px',
                background: 'linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%)',
                borderRadius: '15px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.5rem',
                marginBottom: '20px'
              }}>
                🏥
              </div>
              <h3 style={{ fontSize: '1.5rem', fontWeight: '700', color: '#1E293B', marginBottom: '15px' }}>
                Medical Support
              </h3>
              <p style={{ color: '#64748B', lineHeight: '1.6' }}>
                Connecting patients with medical resources, volunteers, and emergency healthcare services.
              </p>
            </div>
            
            <div style={{
              background: 'white',
              padding: '40px',
              borderRadius: '20px',
              boxShadow: '0 10px 30px rgba(0,0,0,0.05)',
              border: '1px solid rgba(34, 197, 94, 0.1)',
              transition: 'all 0.3s ease'
            }}>
              <div style={{
                width: '60px',
                height: '60px',
                background: 'linear-gradient(135deg, #22C55E 0%, #4ADE80 100%)',
                borderRadius: '15px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.5rem',
                marginBottom: '20px'
              }}>
                🚑
              </div>
              <h3 style={{ fontSize: '1.5rem', fontWeight: '700', color: '#1E293B', marginBottom: '15px' }}>
                Emergency Response
              </h3>
              <p style={{ color: '#64748B', lineHeight: '1.6' }}>
                Immediate response to natural disasters, providing shelter, food, and essential supplies.
              </p>
            </div>
            
            <div style={{
              background: 'white',
              padding: '40px',
              borderRadius: '20px',
              boxShadow: '0 10px 30px rgba(0,0,0,0.05)',
              border: '1px solid rgba(245, 158, 11, 0.1)',
              transition: 'all 0.3s ease'
            }}>
              <div style={{
                width: '60px',
                height: '60px',
                background: 'linear-gradient(135deg, #F59E0B 0%, #FCD34D 100%)',
                borderRadius: '15px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.5rem',
                marginBottom: '20px'
              }}>
                👥
              </div>
              <h3 style={{ fontSize: '1.5rem', fontWeight: '700', color: '#1E293B', marginBottom: '15px' }}>
                Volunteer Network
              </h3>
              <p style={{ color: '#64748B', lineHeight: '1.6' }}>
                Join thousands of volunteers making a difference in their communities during crises.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Call to Action Section */}
      <section style={{
        padding: '100px 20px',
        background: 'linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%)',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)'
        }} />
        
        <div style={{ position: 'relative', zIndex: 1, maxWidth: '800px', margin: '0 auto' }}>
          <h2 style={{
            fontSize: '3.5rem',
            fontWeight: '900',
            color: 'white',
            marginBottom: '30px'
          }}>
            Be the Hope Someone Needs
          </h2>
          <p style={{
            fontSize: '1.4rem',
            color: 'rgba(255,255,255,0.9)',
            marginBottom: '50px',
            lineHeight: '1.6'
          }}>
            Join thousands of volunteers and donors making a real difference in crisis situations.
          </p>
          <div style={{
            display: 'flex',
            gap: '20px',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}>
            <a
              href="/signup"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '16px 32px',
                background: 'white',
                color: '#3B82F6',
                textDecoration: 'none',
                borderRadius: '30px',
                fontWeight: '700',
                fontSize: '1.1rem',
                boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
                transition: 'all 0.3s ease'
              }}
              onMouseOver={(e) => {
                e.target.style.transform = 'translateY(-3px)';
                e.target.style.boxShadow = '0 15px 40px rgba(0,0,0,0.3)';
              }}
              onMouseOut={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 10px 30px rgba(0,0,0,0.2)';
              }}
            >
              Become a Volunteer
            </a>
            <a
              href="/disaster-donations"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '16px 32px',
                background: 'rgba(255,255,255,0.2)',
                color: 'white',
                textDecoration: 'none',
                borderRadius: '30px',
                fontWeight: '700',
                fontSize: '1.1rem',
                border: '2px solid white',
                backdropFilter: 'blur(10px)',
                transition: 'all 0.3s ease'
              }}
              onMouseOver={(e) => {
                e.target.style.background = 'rgba(255,255,255,0.3)';
                e.target.style.transform = 'translateY(-3px)';
              }}
              onMouseOut={(e) => {
                e.target.style.background = 'rgba(255,255,255,0.2)';
                e.target.style.transform = 'translateY(0)';
              }}
            >
              Make a Donation
            </a>
          </div>
        </div>
      </section>

      {/* Add CSS animations and reset */}
      <style>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        
        html, body {
          width: 100%;
          height: 100%;
          overflow-x: hidden;
          margin: 0;
          padding: 0;
        }
        
        #root {
          width: 100%;
          height: 100%;
          margin: 0;
          padding: 0;
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
        @keyframes bounce {
          0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
          40% { transform: translateY(-10px); }
          60% { transform: translateY(-5px); }
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

// Comprehensive Disaster Rescue Dashboard
const SimpleDisaster = () => {
  const [activeSection, setActiveSection] = useState('emergency-form');
  
  // Emergency Request Form State
  const [formData, setFormData] = useState({
    patientName: '',
    age: '',
    medicalNeed: '',
    urgency: 'normal',
    medicines: [{ name: '', grams: '' }],
    location: null,
    notes: ''
  });

  // Handle form input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle medicine changes
  const handleMedicineChange = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      medicines: prev.medicines.map((med, i) => 
        i === index ? { ...med, [field]: value } : med
      )
    }));
  };

  // Add new medicine field
  const addMedicine = () => {
    setFormData(prev => ({
      ...prev,
      medicines: [...prev.medicines, { name: '', grams: '' }]
    }));
  };

  // Remove medicine field
  const removeMedicine = (index) => {
    setFormData(prev => ({
      ...prev,
      medicines: prev.medicines.filter((_, i) => i !== index)
    }));
  };

  // Handle form submission
  const handleSubmit = () => {
    // Validate required fields
    if (!formData.patientName || !formData.age || !formData.medicalNeed) {
      alert('Please fill in all required fields (Patient Name, Age, and Type of Emergency)');
      return;
    }

    // Create request object
    const request = {
      ...formData,
      timestamp: new Date().toISOString(),
      localId: Date.now(),
      syncStatus: 'pending'
    };

    // Save to localStorage for demo purposes
    const existingRequests = JSON.parse(localStorage.getItem('emergencyRequests') || '[]');
    existingRequests.push(request);
    localStorage.setItem('emergencyRequests', JSON.stringify(existingRequests));

    // Show success message
    alert('Emergency request submitted successfully! It has been saved locally and will sync when online.');

    // Reset form
    setFormData({
      patientName: '',
      age: '',
      medicalNeed: '',
      urgency: 'normal',
      medicines: [{ name: '', grams: '' }],
      location: null,
      notes: ''
    });

    // Redirect to history page
    window.location.href = '/history';
  };
  
  // Mock data for demonstration
  const activeDisasters = [
    {
      id: 1,
      type: 'Flood',
      location: 'Southern Province',
      severity: 'High',
      affected: 2500,
      status: 'Active',
      date: '2024-01-15',
      description: 'Heavy rainfall causing widespread flooding in coastal areas'
    },
    {
      id: 2,
      type: 'Landslide',
      location: 'Central Hills',
      severity: 'Medium',
      affected: 800,
      status: 'Monitoring',
      date: '2024-01-14',
      description: 'Landslide risk due to continuous rainfall'
    }
  ];

  const reliefRequests = [
    {
      id: 1,
      type: 'Food Supplies',
      quantity: '500 kg',
      urgency: 'High',
      location: 'Galle District',
      requestedBy: 'Local Relief Camp',
      status: 'Pending'
    },
    {
      id: 2,
      type: 'Medical Aid',
      quantity: '100 kits',
      urgency: 'Critical',
      location: 'Matara District',
      requestedBy: 'Regional Hospital',
      status: 'In Progress'
    },
    {
      id: 3,
      type: 'Shelter Materials',
      quantity: '200 units',
      urgency: 'Medium',
      location: 'Hambantota District',
      requestedBy: 'Disaster Management Unit',
      status: 'Approved'
    }
  ];

  const emergencyContacts = [
    { name: 'National Emergency Hotline', number: '119', type: 'Emergency' },
    { name: 'Disaster Management Center', number: '1170', type: 'Disaster' },
    { name: 'Medical Emergency', number: '110', type: 'Medical' },
    { name: 'Fire & Rescue', number: '110', type: 'Fire' },
    { name: 'Police Emergency', number: '119', type: 'Police' }
  ];

  const navigationItems = [
    { id: 'emergency-form', label: 'Emergency Request Form', icon: emergencyIcon, color: '#fca5a5' },
    { id: 'active-disasters', label: 'Active Disasters', icon: activeIcon, color: '#f87171' },
    { id: 'relief-requests', label: 'Relief Requests', icon: reliefIcon, color: '#ef4444' },
    { id: 'emergency-hotline', label: '24/7 Emergency Hotline', icon: hotlineIcon, color: '#dc2626' }
  ];

  return (
    <>
      <style>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        html, body {
          margin: 0;
          padding: 0;
          width: 100%;
          overflow-x: hidden;
          position: relative;
        }
        #root {
          margin: 0;
          padding: 0;
          width: 100%;
          overflow-x: hidden;
        }
      `}</style>
      <div style={{ 
        minHeight: '100vh', 
        width: '100vw',
        background: '#fef2f2',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        margin: 0,
        padding: 0,
        boxSizing: 'border-box',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        overflowX: 'hidden'
      }}>
      {/* Header */}
      <div style={{
        background: '#fca5a5',
        padding: '30px 20px',
        textAlign: 'center',
        color: 'black',
        position: 'relative',
        overflow: 'hidden',
        width: '100%'
      }}>
        <div style={{
          position: 'absolute',
          top: '-50px',
          right: '-50px',
          width: '200px',
          height: '200px',
          background: 'rgba(255,255,255,0.1)',
          borderRadius: '50%'
        }} />
        <h1 style={{ 
          fontSize: '3rem', 
          fontWeight: '800', 
          margin: '0 0 10px 0',
          position: 'relative',
          zIndex: 1
        }}>
          Disaster Rescue Dashboard
        </h1>
        <p style={{ 
          fontSize: '1.2rem', 
          margin: '0',
          opacity: 0.9,
          position: 'relative',
          zIndex: 1
        }}>
          Emergency response coordination and relief management
        </p>
      </div>

      {/* Navigation Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        padding: '30px 20px',
        width: '100%'
      }}>
        {navigationItems.map((item) => (
          <div
            key={item.id}
            onClick={() => setActiveSection(item.id)}
            style={{
              background: 'rgba(255, 255, 255, 0.8)',
              border: activeSection === item.id ? '2px solid ' + item.color : '1px solid ' + item.color,
              borderRadius: '12px',
              padding: '20px',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              textAlign: 'center',
              boxShadow: activeSection === item.id ? '0 4px 15px ' + item.color + '0.2' : '0 2px 8px rgba(0,0,0,0.05)',
              transform: activeSection === item.id ? 'translateY(-2px)' : 'translateY(0)'
            }}
            onMouseOver={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 4px 15px ' + item.color + '0.2';
            }}
            onMouseOut={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.05)';
            }}
          >
            <div style={{ 
              width: '40px', 
              height: '40px', 
              margin: '0 auto 10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <img 
                src={item.icon} 
                alt={item.label}
                style={{ 
                  width: '100%', 
                  height: '100%', 
                  objectFit: 'contain' 
                }}
                onError={(e) => {
                  // Fallback to emoji if icon fails to load
                  const fallbackIcons = {
                    'emergency-form': '🚨',
                    'active-disasters': '🌊',
                    'relief-requests': '📦',
                    'emergency-hotline': '📞'
                  };
                  e.target.style.display = 'none';
                  e.target.parentElement.innerHTML = '<span style="font-size: 1.5rem;">' + (fallbackIcons[item.id] || '📋') + '</span>';
                }}
              />
            </div>
            <h3 style={{ 
              fontSize: '1.1rem', 
              fontWeight: '500', 
              color: 'black',
              marginBottom: '5px' 
            }}>
              {item.label}
            </h3>
          </div>
        ))}
      </div>

      {/* Content Area */}
      <div style={{
        padding: '0 20px 40px',
        width: '100%'
      }}>
        {/* Emergency Request Form Section */}
        {activeSection === 'emergency-form' && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.9)',
            borderRadius: '12px',
            padding: '20px',
            boxShadow: '0 4px 15px rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.2)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              marginBottom: '16px'
            }}>
              <div style={{
                width: '30px',
                height: '30px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <img 
                  src={emergencyIcon} 
                  alt="Emergency Request Form"
                  style={{ 
                    width: '100%', 
                    height: '100%', 
                    objectFit: 'contain' 
                  }}
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.parentElement.innerHTML = '<span style="font-size: 1.2rem;">🚨</span>';
                  }}
                />
              </div>
              <h2 style={{ 
                fontSize: '1.4rem', 
                fontWeight: '600', 
                color: 'black',
                margin: 0
              }}>
                Emergency Request Form
              </h2>
            </div>
            <p style={{ 
              color: '#6b7280', 
              marginBottom: '30px',
              fontSize: '1rem'
            }}>
              Submit emergency requests for immediate assistance during disasters and crises.
            </p>
            
            {/* Direct Emergency Request Form */}
            <div style={{
              background: 'linear-gradient(135deg, #fefce8 0%, #fef3c7 100%)',
              border: '2px solid #f59e0b',
              borderRadius: '16px',
              padding: '0',
              overflow: 'hidden'
            }}>
              {/* Form Header */}
              <div style={{
                background: 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)',
                padding: '24px 30px',
                color: 'white',
                textAlign: 'center',
                position: 'relative'
              }}>
                <div style={{
                  position: 'absolute',
                  top: '-30px',
                  right: '-30px',
                  width: '120px',
                  height: '120px',
                  background: 'rgba(255,255,255,0.1)',
                  borderRadius: '50%'
                }} />
                <div style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: 'rgba(255,255,255,0.2)',
                  border: '1px solid rgba(255,255,255,0.3)',
                  borderRadius: '20px',
                  padding: '6px 16px',
                  fontSize: '12px',
                  fontWeight: '600',
                  marginBottom: '12px'
                }}>
                  <span>🏥</span>
                  <span>EMERGENCY REQUEST</span>
                </div>
                <h3 style={{ 
                  fontSize: '1.8rem', 
                  fontWeight: '700', 
                  margin: '0 0 8px 0',
                  position: 'relative',
                  zIndex: 1
                }}>
                  Medical Emergency Form
                </h3>
                <p style={{ 
                  margin: 0,
                  fontSize: '0.9rem',
                  opacity: 0.9,
                  position: 'relative',
                  zIndex: 1
                }}>
                  Works offline — your request is saved locally and synced when connected
                </p>
              </div>

              {/* Form Body */}
              <div style={{
                padding: '30px',
                background: 'white'
              }}>
                {/* Patient Information */}
                <div style={{ marginBottom: '32px' }}>
                  <div style={{
                    fontSize: '11px',
                    fontWeight: '600',
                    letterSpacing: '1.2px',
                    textTransform: 'uppercase',
                    color: '#f59e0b',
                    marginBottom: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    Patient Information
                    <div style={{
                      flex: 1,
                      height: '1px',
                      background: '#e5e7eb'
                    }} />
                  </div>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '16px'
                  }}>
                    <div>
                      <label style={{
                        display: 'block',
                        fontSize: '13px',
                        fontWeight: '500',
                        color: '#374151',
                        marginBottom: '6px'
                      }}>
                        Full Name *
                      </label>
                      <input
                        type="text"
                        name="patientName"
                        value={formData.patientName}
                        onChange={handleChange}
                        placeholder="e.g. Saman Perera"
                        style={{
                          width: '100%',
                          padding: '10px 14px',
                          border: '2px solid #e5e7eb',
                          borderRadius: '8px',
                          fontSize: '14px',
                          background: '#f9fafb',
                          color: '#000000',
                          transition: 'all 0.2s'
                        }}
                        onFocus={(e) => {
                          e.target.style.borderColor = '#f59e0b';
                          e.target.style.background = '#fff';
                          e.target.style.boxShadow = '0 0 0 3px rgba(245,158,11,0.1)';
                        }}
                        onBlur={(e) => {
                          e.target.style.borderColor = '#e5e7eb';
                          e.target.style.background = '#f9fafb';
                          e.target.style.boxShadow = 'none';
                        }}
                      />
                    </div>
                    <div>
                      <label style={{
                        display: 'block',
                        fontSize: '13px',
                        fontWeight: '500',
                        color: '#374151',
                        marginBottom: '6px'
                      }}>
                        Age *
                      </label>
                      <input
                        type="number"
                        name="age"
                        value={formData.age}
                        onChange={handleChange}
                        placeholder="e.g. 35"
                        min="1"
                        max="120"
                        style={{
                          width: '100%',
                          padding: '10px 14px',
                          border: '2px solid #e5e7eb',
                          borderRadius: '8px',
                          fontSize: '14px',
                          background: '#f9fafb',
                          color: '#000000',
                          transition: 'all 0.2s'
                        }}
                        onFocus={(e) => {
                          e.target.style.borderColor = '#f59e0b';
                          e.target.style.background = '#fff';
                          e.target.style.boxShadow = '0 0 0 3px rgba(245,158,11,0.1)';
                        }}
                        onBlur={(e) => {
                          e.target.style.borderColor = '#e5e7eb';
                          e.target.style.background = '#f9fafb';
                          e.target.style.boxShadow = 'none';
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* Urgency Level */}
                <div style={{ marginBottom: '32px' }}>
                  <div style={{
                    fontSize: '11px',
                    fontWeight: '600',
                    letterSpacing: '1.2px',
                    textTransform: 'uppercase',
                    color: '#f59e0b',
                    marginBottom: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    Urgency Level *
                    <div style={{
                      flex: 1,
                      height: '1px',
                      background: '#e5e7eb'
                    }} />
                  </div>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(3, 1fr)',
                    gap: '12px'
                  }}>
                    {[
                      { value: 'critical', label: 'Critical', color: '#dc2626', bg: '#fef2f2' },
                      { value: 'high', label: 'High', color: '#f59e0b', bg: '#fffbeb' },
                      { value: 'normal', label: 'Normal', color: '#10b981', bg: '#f0fdf4' }
                    ].map((level) => (
                      <div
                        key={level.value}
                        style={{
                          border: '2px solid #e5e7eb',
                          borderRadius: '10px',
                          padding: '16px 12px',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          background: '#f9fafb',
                          textAlign: 'center',
                          position: 'relative',
                          overflow: 'hidden'
                        }}
                        onMouseOver={(e) => {
                          e.target.style.transform = 'translateY(-2px)';
                          e.target.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                        }}
                        onMouseOut={(e) => {
                          e.target.style.transform = 'translateY(0)';
                          e.target.style.boxShadow = 'none';
                        }}
                        onClick={(e) => {
                          // Remove selected state from all cards
                          e.currentTarget.parentElement.querySelectorAll('div').forEach(card => {
                            card.style.borderColor = '#e5e7eb';
                            card.style.background = '#f9fafb';
                          });
                          // Add selected state to clicked card
                          e.currentTarget.style.borderColor = level.color;
                          e.currentTarget.style.background = level.bg;
                        }}
                      >
                        <div style={{
                          width: '10px',
                          height: '10px',
                          borderRadius: '50%',
                          margin: '0 auto 8px',
                          background: level.color
                        }} />
                        <div style={{
                          fontSize: '13px',
                          fontWeight: '600',
                          marginBottom: '4px',
                          color: '#374151'
                        }}>
                          {level.label}
                        </div>
                        <div style={{
                          fontSize: '10px',
                          lineHeight: '1.4',
                          opacity: '0.7',
                          color: '#6b7280'
                        }}>
                          {level.value === 'critical' && 'Life-threatening, immediate attention required'}
                          {level.value === 'high' && 'Serious condition, urgent care needed'}
                          {level.value === 'normal' && 'Stable, requires medical attention'}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Medical Need */}
                <div style={{ marginBottom: '32px' }}>
                  <div style={{
                    fontSize: '11px',
                    fontWeight: '600',
                    letterSpacing: '1.2px',
                    textTransform: 'uppercase',
                    color: '#f59e0b',
                    marginBottom: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    Medical Need
                    <div style={{
                      flex: 1,
                      height: '1px',
                      background: '#e5e7eb'
                    }} />
                  </div>
                  <div>
                    <label style={{
                      display: 'block',
                      fontSize: '13px',
                      fontWeight: '500',
                      color: '#374151',
                      marginBottom: '6px'
                    }}>
                      Type of Emergency *
                    </label>
                    <select
                      name="medicalNeed"
                      value={formData.medicalNeed}
                      onChange={handleChange}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        border: '2px solid #e5e7eb',
                        borderRadius: '8px',
                        fontSize: '14px',
                        background: '#f9fafb',
                        color: '#000000',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                      onFocus={(e) => {
                        e.target.style.borderColor = '#dc2626';
                        e.target.style.background = '#fff';
                        e.target.style.boxShadow = '0 0 0 3px rgba(220,38,38,0.1)';
                      }}
                      onBlur={(e) => {
                        e.target.style.borderColor = '#e5e7eb';
                        e.target.style.background = '#f9fafb';
                        e.target.style.boxShadow = 'none';
                      }}
                    >
                      <option value="">— Select type —</option>
                      <option value="injury">Injury / Trauma</option>
                      <option value="respiratory">Respiratory Distress</option>
                      <option value="cardiac">Cardiac Emergency</option>
                      <option value="infection">Infection / Fever</option>
                      <option value="diabetic">Diabetic Emergency</option>
                      <option value="maternity">Maternity / Obstetric</option>
                      <option value="mental">Mental Health Crisis</option>
                      <option value="chronic">Chronic Disease Flare</option>
                      <option value="pediatric">Pediatric Emergency</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>

                {/* Required Medicines */}
                <div style={{ marginBottom: '32px' }}>
                  <div style={{
                    fontSize: '11px',
                    fontWeight: '600',
                    letterSpacing: '1.2px',
                    textTransform: 'uppercase',
                    color: '#f59e0b',
                    marginBottom: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    Required Medicines
                    <div style={{
                      flex: 1,
                      height: '1px',
                      background: '#e5e7eb'
                    }} />
                  </div>
                  
                  {/* Column headers */}
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 120px 40px',
                    gap: '8px',
                    marginBottom: '8px'
                  }}>
                    <span style={{ fontSize: '12px', color: '#6b7280', fontWeight: '500' }}>Medicine Name</span>
                    <span style={{ fontSize: '12px', color: '#6b7280', fontWeight: '500' }}>Amount (g/mg)</span>
                    <span />
                  </div>

                  {/* Medicine row */}
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 120px 40px',
                    gap: '8px',
                    alignItems: 'start',
                    marginBottom: '8px'
                  }}>
                    <input
                      type="text"
                      value={formData.medicines[0]?.name || ''}
                      onChange={(e) => handleMedicineChange(0, 'name', e.target.value)}
                      placeholder="e.g. Paracetamol"
                      style={{
                        padding: '10px 14px',
                        border: '2px solid #e5e7eb',
                        borderRadius: '8px',
                        fontSize: '14px',
                        background: '#f9fafb',
                        color: '#000000',
                        transition: 'all 0.2s'
                      }}
                      onFocus={(e) => {
                        e.target.style.borderColor = '#dc2626';
                        e.target.style.background = '#fff';
                        e.target.style.boxShadow = '0 0 0 3px rgba(220,38,38,0.1)';
                      }}
                      onBlur={(e) => {
                        e.target.style.borderColor = '#e5e7eb';
                        e.target.style.background = '#f9fafb';
                        e.target.style.boxShadow = 'none';
                      }}
                    />
                    <input
                      type="text"
                      value={formData.medicines[0]?.grams || ''}
                      onChange={(e) => handleMedicineChange(0, 'grams', e.target.value)}
                      placeholder="500mg"
                      style={{
                        padding: '10px 14px',
                        border: '2px solid #e5e7eb',
                        borderRadius: '8px',
                        fontSize: '14px',
                        background: '#f9fafb',
                        color: '#000000',
                        transition: 'all 0.2s'
                      }}
                      onFocus={(e) => {
                        e.target.style.borderColor = '#dc2626';
                        e.target.style.background = '#fff';
                        e.target.style.boxShadow = '0 0 0 3px rgba(220,38,38,0.1)';
                      }}
                      onBlur={(e) => {
                        e.target.style.borderColor = '#e5e7eb';
                        e.target.style.background = '#f9fafb';
                        e.target.style.boxShadow = 'none';
                      }}
                    />
                    <button
                      type="button"
                      style={{
                        width: '40px',
                        height: '42px',
                        border: '2px solid #fca5a5',
                        background: '#fff5f5',
                        borderRadius: '8px',
                        color: '#dc2626',
                        cursor: 'pointer',
                        fontSize: '16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'all 0.15s'
                      }}
                      onMouseOver={(e) => {
                        e.target.style.background = '#fee2e2';
                        e.target.style.borderColor = '#dc2626';
                      }}
                      onMouseOut={(e) => {
                        e.target.style.background = '#fff5f5';
                        e.target.style.borderColor = '#fca5a5';
                      }}
                    >
                      ×
                    </button>
                  </div>

                  <button
                    type="button"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 16px',
                      border: '2px dashed #f59e0b',
                      background: 'transparent',
                      color: '#f59e0b',
                      fontSize: '13px',
                      fontWeight: '500',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      width: '100%',
                      justifyContent: 'center',
                      marginTop: '8px'
                    }}
                    onMouseOver={(e) => {
                      e.target.style.background = '#fefce8';
                    }}
                    onMouseOut={(e) => {
                      e.target.style.background = 'transparent';
                    }}
                  >
                    + Add Another Medicine
                  </button>
                </div>

                {/* GPS Location */}
                <div style={{ marginBottom: '32px' }}>
                  <div style={{
                    fontSize: '11px',
                    fontWeight: '600',
                    letterSpacing: '1.2px',
                    textTransform: 'uppercase',
                    color: '#f59e0b',
                    marginBottom: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    Location
                    <div style={{
                      flex: 1,
                      height: '1px',
                      background: '#e5e7eb'
                    }} />
                  </div>
                  <button
                    type="button"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '12px 20px',
                      borderRadius: '8px',
                      fontSize: '13px',
                      fontWeight: '500',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      border: '2px solid #f59e0b',
                      background: '#fefce8',
                      color: '#f59e0b',
                      width: '100%',
                      justifyContent: 'center'
                    }}
                    onMouseOver={(e) => {
                      e.target.style.background = '#fef3c7';
                    }}
                    onMouseOut={(e) => {
                      e.target.style.background = '#fefce8';
                    }}
                  >
                    <span>📍</span>
                    Capture GPS Location
                  </button>
                </div>

                {/* Additional Notes */}
                <div style={{ marginBottom: '32px' }}>
                  <div style={{
                    fontSize: '11px',
                    fontWeight: '600',
                    letterSpacing: '1.2px',
                    textTransform: 'uppercase',
                    color: '#f59e0b',
                    marginBottom: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    Additional Notes
                    <div style={{
                      flex: 1,
                      height: '1px',
                      background: '#e5e7eb'
                    }} />
                  </div>
                  <textarea
                    name="notes"
                    value={formData.notes}
                    onChange={handleChange}
                    placeholder="Any additional details about the patient's condition..."
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      border: '2px solid #e5e7eb',
                      borderRadius: '8px',
                      fontSize: '14px',
                      background: '#f9fafb',
                      color: '#000000',
                      resize: 'vertical',
                      minHeight: '80px',
                      fontFamily: 'inherit',
                      transition: 'all 0.2s'
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = '#dc2626';
                      e.target.style.background = '#fff';
                      e.target.style.boxShadow = '0 0 0 3px rgba(220,38,38,0.1)';
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = '#e5e7eb';
                      e.target.style.background = '#f9fafb';
                      e.target.style.boxShadow = 'none';
                    }}
                  />
                </div>

                {/* Submit Button */}
                <button
                  type="button"
                  onClick={handleSubmit}
                  style={{
                    width: '100%',
                    padding: '16px',
                    background: 'linear-gradient(135deg, #f59e0b, #fbbf24)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '12px',
                    fontSize: '16px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    letterSpacing: '0.3px'
                  }}
                  onMouseOver={(e) => {
                    e.target.style.transform = 'translateY(-2px)';
                    e.target.style.boxShadow = '0 8px 25px rgba(245,158,11,0.3)';
                  }}
                  onMouseOut={(e) => {
                    e.target.style.transform = 'translateY(0)';
                    e.target.style.boxShadow = 'none';
                  }}
                >
                  <span>🚨</span>
                  Submit Emergency Request
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Active Disasters Section */}
        {activeSection === 'active-disasters' && (
          <div style={{
            background: 'white',
            borderRadius: '16px',
            padding: '30px',
            boxShadow: '0 10px 30px rgba(0,0,0,0.1)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              marginBottom: '24px'
            }}>
              <span style={{ fontSize: '2rem' }}>🌊</span>
              <h2 style={{ 
                fontSize: '1.8rem', 
                fontWeight: '700', 
                color: '#f59e0b',
                margin: 0
              }}>
                Active Disasters
              </h2>
            </div>
            <p style={{ 
              color: '#6b7280', 
              marginBottom: '30px',
              fontSize: '1rem'
            }}>
              Real-time monitoring of ongoing disaster situations and response efforts.
            </p>
            
            <div style={{ display: 'grid', gap: '20px' }}>
              {activeDisasters.map((disaster) => (
                <div key={disaster.id} style={{
                  background: '#fef3c7',
                  border: '1px solid #fbbf24',
                  borderRadius: '12px',
                  padding: '20px',
                  display: 'grid',
                  gridTemplateColumns: 'auto 1fr auto',
                  gap: '20px',
                  alignItems: 'center'
                }}>
                  <div style={{
                    width: '60px',
                    height: '60px',
                    background: '#f59e0b',
                    borderRadius: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.5rem'
                  }}>
                    {disaster.type === 'Flood' ? '🌊' : '⛰️'}
                  </div>
                  <div>
                    <h3 style={{ 
                      fontSize: '1.2rem', 
                      fontWeight: '600', 
                      color: '#92400e',
                      margin: '0 0 8px 0'
                    }}>
                      {disaster.type} - {disaster.location}
                    </h3>
                    <p style={{ 
                      color: '#78350f', 
                      margin: '0 0 12px 0',
                      fontSize: '0.9rem'
                    }}>
                      {disaster.description}
                    </p>
                    <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                      <span style={{
                        background: '#fbbf24',
                        color: '#78350f',
                        padding: '4px 12px',
                        borderRadius: '20px',
                        fontSize: '0.8rem',
                        fontWeight: '500'
                      }}>
                        {disaster.severity} Severity
                      </span>
                      <span style={{
                        background: '#dc2626',
                        color: 'white',
                        padding: '4px 12px',
                        borderRadius: '20px',
                        fontSize: '0.8rem',
                        fontWeight: '500'
                      }}>
                        {disaster.affected} Affected
                      </span>
                      <span style={{
                        background: '#10b981',
                        color: 'white',
                        padding: '4px 12px',
                        borderRadius: '20px',
                        fontSize: '0.8rem',
                        fontWeight: '500'
                      }}>
                        {disaster.status}
                      </span>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ 
                      color: '#78350f', 
                      fontSize: '0.8rem',
                      marginBottom: '8px'
                    }}>
                      {disaster.date}
                    </div>
                    <button style={{
                      background: '#f59e0b',
                      color: 'white',
                      border: 'none',
                      padding: '8px 16px',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontSize: '0.9rem',
                      fontWeight: '500'
                    }}>
                      View Details
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Relief Requests Section */}
        {activeSection === 'relief-requests' && (
          <div style={{
            background: 'white',
            borderRadius: '16px',
            padding: '30px',
            boxShadow: '0 10px 30px rgba(0,0,0,0.1)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              marginBottom: '24px'
            }}>
              <span style={{ fontSize: '2rem' }}>📦</span>
              <h2 style={{ 
                fontSize: '1.8rem', 
                fontWeight: '700', 
                color: '#10b981',
                margin: 0
              }}>
                Relief Requests
              </h2>
            </div>
            <p style={{ 
              color: '#6b7280', 
              marginBottom: '30px',
              fontSize: '1rem'
            }}>
              Track and manage relief supply requests from affected areas.
            </p>
            
            <div style={{ display: 'grid', gap: '16px' }}>
              {reliefRequests.map((request) => (
                <div key={request.id} style={{
                  background: '#d1fae5',
                  border: '1px solid #10b981',
                  borderRadius: '12px',
                  padding: '20px',
                  display: 'grid',
                  gridTemplateColumns: 'auto 1fr auto auto',
                  gap: '20px',
                  alignItems: 'center'
                }}>
                  <div style={{
                    width: '50px',
                    height: '50px',
                    background: '#10b981',
                    borderRadius: '10px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.2rem'
                  }}>
                    📦
                  </div>
                  <div>
                    <h3 style={{ 
                      fontSize: '1.1rem', 
                      fontWeight: '600', 
                      color: '#065f46',
                      margin: '0 0 6px 0'
                    }}>
                      {request.type}
                    </h3>
                    <p style={{ 
                      color: '#047857', 
                      margin: '0 0 8px 0',
                      fontSize: '0.9rem'
                    }}>
                      {request.location} • {request.requestedBy}
                    </p>
                    <div style={{ fontSize: '0.9rem', color: '#065f46' }}>
                      Quantity: {request.quantity}
                    </div>
                  </div>
                  <div>
                    <span style={{
                      background: request.urgency === 'Critical' ? '#dc2626' : 
                                 request.urgency === 'High' ? '#f59e0b' : '#10b981',
                      color: 'white',
                      padding: '6px 12px',
                      borderRadius: '20px',
                      fontSize: '0.8rem',
                      fontWeight: '500',
                      display: 'block',
                      textAlign: 'center',
                      marginBottom: '8px'
                    }}>
                      {request.urgency}
                    </span>
                  </div>
                  <div>
                    <span style={{
                      background: request.status === 'Approved' ? '#10b981' :
                                 request.status === 'In Progress' ? '#f59e0b' : '#6b7280',
                      color: 'white',
                      padding: '6px 12px',
                      borderRadius: '20px',
                      fontSize: '0.8rem',
                      fontWeight: '500',
                      display: 'block',
                      textAlign: 'center'
                    }}>
                      {request.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Emergency Hotline Section */}
        {activeSection === 'emergency-hotline' && (
          <div style={{
            background: 'white',
            borderRadius: '16px',
            padding: '30px',
            boxShadow: '0 10px 30px rgba(0,0,0,0.1)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              marginBottom: '24px'
            }}>
              <span style={{ fontSize: '2rem' }}>📞</span>
              <h2 style={{ 
                fontSize: '1.8rem', 
                fontWeight: '700', 
                color: '#3b82f6',
                margin: 0
              }}>
                24/7 Emergency Hotline
              </h2>
            </div>
            <p style={{ 
              color: '#6b7280', 
              marginBottom: '30px',
              fontSize: '1rem'
            }}>
              Emergency contact numbers for immediate assistance during disasters.
            </p>
            
            <div style={{ display: 'grid', gap: '16px' }}>
              {emergencyContacts.map((contact, index) => (
                <div key={index} style={{
                  background: '#dbeafe',
                  border: '1px solid #3b82f6',
                  borderRadius: '12px',
                  padding: '20px',
                  display: 'grid',
                  gridTemplateColumns: 'auto 1fr auto',
                  gap: '20px',
                  alignItems: 'center'
                }}>
                  <div style={{
                    width: '50px',
                    height: '50px',
                    background: '#3b82f6',
                    borderRadius: '10px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.2rem'
                  }}>
                    📞
                  </div>
                  <div>
                    <h3 style={{ 
                      fontSize: '1.1rem', 
                      fontWeight: '600', 
                      color: '#1e40af',
                      margin: '0 0 6px 0'
                    }}>
                      {contact.name}
                    </h3>
                    <div style={{ fontSize: '0.9rem', color: '#3730a3' }}>
                      {contact.type} Emergency
                    </div>
                  </div>
                  <div>
                    <div style={{
                      background: '#1e40af',
                      color: 'white',
                      padding: '12px 20px',
                      borderRadius: '8px',
                      fontSize: '1.1rem',
                      fontWeight: '600',
                      textAlign: 'center'
                    }}>
                      {contact.number}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div style={{
              background: '#fef3c7',
              border: '1px solid #fbbf24',
              borderRadius: '12px',
              padding: '20px',
              marginTop: '30px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '1.5rem', marginBottom: '10px' }}>⚠️</div>
              <h3 style={{ 
                fontSize: '1.2rem', 
                fontWeight: '600', 
                color: '#92400e',
                margin: '0 0 10px 0'
              }}>
                Important Notice
              </h3>
              <p style={{ 
                color: '#78350f', 
                margin: '0',
                fontSize: '0.9rem',
                lineHeight: '1.5'
              }}>
                These emergency numbers are available 24/7. Only use them for genuine emergencies. 
                For non-emergency inquiries, please contact your local disaster management office.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Back to Home Link */}
      <div style={{ textAlign: 'center', padding: '20px' }}>
        <a href="/" style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '12px 24px',
          background: '#6b7280',
          color: 'white',
          textDecoration: 'none',
          borderRadius: '8px',
          fontSize: '1rem',
          fontWeight: '500',
          transition: 'all 0.3s ease'
        }}>
          ← Back to Home
        </a>
      </div>
    </div>
    </>
  );
};

function App() {
  // Register Service Worker
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      window.addEventListener("load", () => {
        navigator.serviceWorker
          .register("/sw.js")
          .then((reg) => {
            console.log("✅ Service Worker registered:", reg.scope);

            // Listen for SW updates
            reg.addEventListener("updatefound", () => {
              const newWorker = reg.installing;
              newWorker?.addEventListener("statechange", () => {
                if (
                  newWorker.state === "installed" &&
                  navigator.serviceWorker.controller
                ) {
                  console.log("🔄 New Service Worker available — refresh to update");
                }
              });
            });
          })
          .catch((err) => console.error("❌ Service Worker failed:", err));
      });
    }
  }, []);

  useEffect(() => {
    console.log("Jeevadhara app with blue theme and parallax mounted");
  }, []);

  return (
    <Router>
      {/* OfflineBanner sits outside Routes — visible on every page */}
      <OfflineBanner />

      <Routes>
        <Route path="/" element={<SimpleHome />} />
        <Route path="/medical-donations" element={<SimpleMedical />} />
        <Route path="/disaster-donations" element={<SimpleDisaster />} />
        <Route path="/emergency-request" element={<History />} />
        <Route path="/history"           element={<History />} />

        {/* ── Future routes (add as you build them) ──────────
        <Route path="/dashboard"   element={<Dashboard />} />
        <Route path="/donations"   element={<Donations />} />
        ─────────────────────────────────────────────────── */}
      </Routes>
    </Router>
  );
}

export default App;
