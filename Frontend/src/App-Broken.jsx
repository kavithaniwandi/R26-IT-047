import { useEffect, useState, useRef } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

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
      background: scrolled ? 'rgba(255, 255, 255, 0.98)' : 'rgba(255, 255, 255, 0.95)',
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
            width: '45px',
            height: '45px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 15px rgba(59, 130, 246, 0.3)'
          }}>
            <img src="/assets/logo.png" alt="Jeevadhara" style={{width: '45px', height: '45px', objectFit: 'contain'}} />
          </div>
          <span style={{
            fontSize: '1.6rem',
            fontWeight: '700',
            background: 'linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
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

// Beautiful Home Component with Parallax
const SimpleHome = () => {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div style={{ 
      width: '100vw',
      height: '100vh',
      background: 'linear-gradient(180deg, #FFFFFF 0%, #F0F9FF 50%, #E0F2FE 100%)',
      position: 'relative',
      overflow: 'hidden',
      margin: 0,
      padding: 0
    }}>
      {/* Hero Section with Parallax - Full Viewport */}
      <section style={{
        width: '100vw',
        height: '100vh',
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        margin: 0,
        padding: 0
      }}>
        {/* Parallax Background Elements */}
        <div style={{
          position: 'absolute',
          top: '10%',
          left: '10%',
          width: '400px',
          height: '400px',
          background: 'radial-gradient(circle, rgba(59, 130, 246, 0.08) 0%, transparent 70%)',
          borderRadius: '50%',
          transform: `translateY(${scrollY * 0.3}px)`
        }} />
        <div style={{
          position: 'absolute',
          bottom: '20%',
          right: '10%',
          width: '300px',
          height: '300px',
          background: 'radial-gradient(circle, rgba(96, 165, 250, 0.08) 0%, transparent 70%)',
          borderRadius: '50%',
          transform: `translateY(${scrollY * 0.5}px)`
        }} />
        <div style={{
          position: 'absolute',
          top: '60%',
          left: '20%',
          width: '200px',
          height: '200px',
          background: 'radial-gradient(circle, rgba(147, 197, 253, 0.08) 0%, transparent 70%)',
          borderRadius: '50%',
          transform: `translateY(${scrollY * 0.4}px)`
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
            width: '140px',
            height: '140px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 40px',
            boxShadow: '0 20px 40px rgba(59, 130, 246, 0.3)',
            animation: 'pulse 3s ease-in-out infinite'
          }}>
            <img src="/assets/logo.png" alt="Jeevadhara" style={{width: '140px', height: '140px', objectFit: 'contain'}} />
          </div>

          {/* Main Title */}
          <h1 style={{
            fontSize: '5rem',
            fontWeight: '900',
            background: 'linear-gradient(135deg, #3B82F6 0%, #60A5FA 50%, #93C5FD 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            marginBottom: '24px',
            animation: 'fadeInUp 1s ease-out'
          }}>
            Jeevadhara
          </h1>
          
          {/* Subtitle */}
          <p style={{
            fontSize: '1.6rem',
            color: '#64748B',
            marginBottom: '50px',
            maxWidth: '700px',
            lineHeight: '1.7',
            margin: '0 auto 50px',
            animation: 'fadeInUp 1s ease-out 0.2s',
            animationFillMode: 'both'
          }}>
            Connecting communities, providing relief, and saving lives when disaster strikes. 
            Every second counts, every donation matters.
          </p>

          {/* Dashboard Cards */}
          <div style={{
            display: 'flex',
            gap: '40px',
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
                padding: '40px 50px',
                background: 'linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%)',
                color: '#1E40AF',
                textDecoration: 'none',
                borderRadius: '24px',
                boxShadow: '0 10px 30px rgba(59, 130, 246, 0.2)',
                transition: 'all 0.3s ease',
                transform: 'translateY(0)',
                minWidth: '280px',
                border: '1px solid rgba(59, 130, 246, 0.1)'
              }}
              onMouseOver={(e) => {
                e.target.style.transform = 'translateY(-10px)';
                e.target.style.boxShadow = '0 20px 40px rgba(59, 130, 246, 0.3)';
              }}
              onMouseOut={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 10px 30px rgba(59, 130, 246, 0.2)';
              }}
            >
              <div style={{ fontSize: '3.5rem', marginBottom: '20px' }}>🩸</div>
              <h3 style={{ fontSize: '1.7rem', fontWeight: '700', marginBottom: '12px' }}>
                Medical Donations
              </h3>
              <p style={{ fontSize: '1.1rem', opacity: 0.8, marginBottom: '20px', lineHeight: '1.5' }}>
                Blood donations, medical supplies, healthcare support
              </p>
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '12px 20px',
                background: 'rgba(255, 255, 255, 0.6)',
                borderRadius: '20px',
                fontSize: '1rem',
                fontWeight: '600'
              }}>
                Explore Dashboard →
              </div>
            </a>

            {/* Disaster Rescue Card */}
            <a 
              href="/disaster-donations" 
              style={{
                display: 'block',
                padding: '40px 50px',
                background: 'linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%)',
                color: '#DC2626',
                textDecoration: 'none',
                borderRadius: '24px',
                boxShadow: '0 10px 30px rgba(239, 68, 68, 0.2)',
                transition: 'all 0.3s ease',
                transform: 'translateY(0)',
                minWidth: '280px',
                border: '1px solid rgba(239, 68, 68, 0.1)'
              }}
              onMouseOver={(e) => {
                e.target.style.transform = 'translateY(-10px)';
                e.target.style.boxShadow = '0 20px 40px rgba(239, 68, 68, 0.3)';
              }}
              onMouseOut={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 10px 30px rgba(239, 68, 68, 0.2)';
              }}
            >
              <div style={{ fontSize: '3.5rem', marginBottom: '20px' }}>🚨</div>
              <h3 style={{ fontSize: '1.7rem', fontWeight: '700', marginBottom: '12px' }}>
                Disaster Rescue
              </h3>
              <p style={{ fontSize: '1.1rem', opacity: 0.8, marginBottom: '20px', lineHeight: '1.5' }}>
                Emergency response, relief efforts, crisis management
              </p>
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '12px 20px',
                background: 'rgba(255, 255, 255, 0.6)',
                borderRadius: '20px',
                fontSize: '1rem',
                fontWeight: '600'
              }}>
                Explore Dashboard →
              </div>
            </a>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div style={{
          position: 'absolute',
          bottom: '30px',
          left: '50%',
          transform: 'translateX(-50%)',
          animation: 'bounce 2s infinite'
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
    console.log("ReliefHub app with blue theme and parallax mounted");
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
