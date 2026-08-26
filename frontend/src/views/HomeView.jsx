import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Activity, 
  HeartHandshake, 
  Truck, 
  ShieldCheck, 
  PhoneCall, 
  Layers, 
  Sparkles, 
  ArrowRight, 
  MapPin, 
  Tent, 
  Users, 
  Radio, 
  Zap, 
  Clock, 
  CheckCircle2, 
  ExternalLink,
  ChevronRight,
  UserCheck,
  Shield,
  FileText,
  AlertTriangle,
  Send,
  Lock,
  Globe
} from 'lucide-react';
import { RealTimeMap } from '../components/RealTimeMap';
import { api } from '../api';
import { PORTAL_CONFIG } from '../portalConfig';
import { playNotificationPing } from '../utils/audioAlert';

export function HomeView({ onSelectPortal, onOpenLoginModal, onAddToast }) {
  const [stats, setStats] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const statsData = await api.getAdminStats();
        setStats(statsData);
      } catch (e) {
        console.warn('Stats load in home', e);
      }
      try {
        const mapData = await api.getHeatmap();
        setHeatmapData(mapData);
      } catch (e) {
        console.warn('Map load in home', e);
      }
    };
    fetchData();
  }, []);

  const portalCards = [
    {
      id: 'victim',
      title: 'Victim & Public Emergency SOS Portal',
      subtitle: 'Port :5174',
      badge: 'Public Emergency',
      desc: '1-Click satellite GPS distress beacons, 4 emergency contacts auto-SMS notification, evacuee intake registration, and nearby shelter locator.',
      icon: ShieldAlert,
      color: 'rose',
      actionText: 'Open Victim SOS Portal',
      features: ['Satellite GPS Fix', '4 Emergency Contacts Alert', 'Safe Shelters & Evacuee Intake', 'Offline SMS Dispatch']
    },
    {
      id: 'authority',
      title: 'Medical Authority Console (MOH)',
      subtitle: 'Port :5175',
      badge: 'Ministry of Health',
      desc: 'National health triage orchestration, spatial camp location authorization, epidemic outbreak surveillance, and emergency medical supply requisitions.',
      icon: Activity,
      color: 'blue',
      actionText: 'Open Medical Authority Console',
      features: ['Camp Spatial Approvals', 'Epidemic Outbreak Risk', 'Hospital Bed & Supply Requisitions', 'Clinical Triage Queue']
    },
    {
      id: 'donor',
      title: 'Relief Donor & Supply Marketplace',
      subtitle: 'Port :5176',
      badge: 'Red Cross & Pledges',
      desc: 'Demand-driven medical supply fulfillment, priority shortage matching, certified donation shipments, and verifiable tracking codes.',
      icon: HeartHandshake,
      color: 'emerald',
      actionText: 'Open Donor Marketplace',
      features: ['Live Shortage Matchmaking', 'Verified Pledges Tracking', 'Certified Medical Goods', 'Transparent Fulfillment']
    },
    {
      id: 'volunteer',
      title: 'Field Volunteer & Responder Dispatch',
      subtitle: 'Port :5177',
      badge: 'Ground Rescue Teams',
      desc: 'Real-time rescue mission routing, on-ground victim status verification, rapid medical delivery dispatch, and offline SMS responder sync.',
      icon: Truck,
      color: 'amber',
      actionText: 'Open Volunteer Dispatch',
      features: ['On-Ground Rescue Routing', 'Victim Verification', 'Supply Delivery Tasks', 'Live Status Synchronization']
    },
    {
      id: 'admin',
      title: 'National Executive Command Center',
      subtitle: 'Port :5173',
      badge: 'National Directorate',
      desc: 'Complete national triage orchestration, 4 active machine learning predictive intelligence engines, and 5-role claims authorization directory.',
      icon: ShieldCheck,
      color: 'blue',
      actionText: 'Open Command Center',
      features: ['4 ML Predictive Engines', 'National Triage Queue', '5-Role RBAC Directory', 'Audit Trail & Telemetry']
    }
  ];

  const mlModels = [
    {
      name: 'Model 1: Epidemic Outbreak Predictor',
      tag: 'Disease Surveillance',
      desc: 'Forecasts probability of post-flood waterborne outbreaks (Leptospirosis, Dengue, Diarrheal diseases) using rainfall, humidity, and standing water data.',
      accuracy: '94.2% ROC-AUC',
      badgeClass: 'badge-critical'
    },
    {
      name: 'Model 2: Medical Demand Estimator',
      tag: 'Supply Chain AI',
      desc: 'Computes exact unit demands for IV Saline, clean water, insulin, and trauma kits based on demographic age breakdown and flood displacement severity.',
      accuracy: '91.8% R² Score',
      badgeClass: 'badge-low'
    },
    {
      name: 'Model 3: Camp Spatial Placement Optimizer',
      tag: 'Spatial Suitability',
      desc: 'Ranks geographical candidate sites by elevation safety (>+25m), distance from river banks, road accessibility, and drinking water availability.',
      accuracy: '96.5% Precision',
      badgeClass: 'badge-medium'
    },
    {
      name: 'Model 4: Triage Urgency Priority Engine',
      tag: 'Life-Threatening Triage',
      desc: 'Automatically ranks incoming SOS distress beacons from 0 to 100 based on water level rise, trapped status, infants, elderly, and chronic illnesses.',
      accuracy: '< 2.2ms Latency',
      badgeClass: 'badge-high'
    }
  ];

  return (
    <div className="home-container" style={{ minHeight: '100vh', backgroundColor: 'var(--bg-app)', color: 'var(--text-primary)' }}>
      
      {/* Top Public Header */}
      <header style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        backgroundColor: '#ffffff',
        borderBottom: '1px solid var(--border-subtle)',
        padding: '12px 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: 'var(--shadow-xs)',
        gap: '20px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div className="brand-icon" style={{ width: '38px', height: '38px', borderRadius: 'var(--radius-md)' }}>
            <Radio size={20} />
          </div>
          <div>
            <div style={{ fontSize: '1.02rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
              SRI LANKA DISASTER RELIEF
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--blue-600)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Smart Medical & Emergency Telemetry Cloud
            </div>
          </div>
        </div>

        {/* Center Nav Links */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <a href="#portals" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.84rem', fontWeight: '600', transition: 'color 0.15s' }}>
            Stakeholder Portals
          </a>
          <a href="#map" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.84rem', fontWeight: '600', transition: 'color 0.15s' }}>
            Live GIS Map
          </a>
          <a href="#ai-models" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.84rem', fontWeight: '600', transition: 'color 0.15s' }}>
            ML Intelligence
          </a>
          <a href="#helplines" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.84rem', fontWeight: '600', transition: 'color 0.15s' }}>
            Emergency Helplines
          </a>
        </div>

        {/* Right CTA buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            className="btn btn-danger btn-sm"
            style={{ fontWeight: '700', padding: '7px 14px' }}
            onClick={() => {
              playNotificationPing();
              onSelectPortal('victim');
            }}
          >
            <ShieldAlert size={15} />
            <span>Emergency SOS</span>
          </button>

          <button
            className="btn btn-secondary btn-sm"
            onClick={onOpenLoginModal}
          >
            <UserCheck size={14} style={{ color: 'var(--blue-600)' }} />
            <span>Stakeholder Login</span>
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section style={{
        padding: '60px 32px 40px',
        maxWidth: '1380px',
        margin: '0 auto',
        position: 'relative'
      }}>
        <div style={{ textAlign: 'center', maxWidth: '920px', margin: '0 auto' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            background: 'var(--blue-50)',
            color: 'var(--blue-700)',
            border: '1px solid var(--blue-200)',
            padding: '4px 14px',
            borderRadius: 'var(--radius-full)',
            fontSize: '0.76rem',
            fontWeight: '700',
            letterSpacing: '0.04em',
            marginBottom: '18px'
          }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-success)', display: 'inline-block' }} />
            <span>NATIONAL DISASTER RESPONSE INFRASTRUCTURE · 24/7 LIVE</span>
          </div>

          <h1 style={{
            fontSize: 'clamp(2rem, 4.5vw, 3.1rem)',
            fontWeight: '800',
            letterSpacing: '-0.03em',
            lineHeight: '1.2',
            color: 'var(--text-primary)',
            marginBottom: '18px'
          }}>
            Smart Medical Response, Emergency Triage & Real-Time Disaster Relief
          </h1>

          <p style={{
            fontSize: '1.05rem',
            color: 'var(--text-muted)',
            lineHeight: '1.6',
            maxWidth: '780px',
            margin: '0 auto 32px'
          }}>
            A unified crisis orchestration platform bridging flood and landslide victims with Ministry of Health (MOH) clinical teams, verified relief donors, and rapid field rescue responders across Sri Lanka.
          </p>

          {/* Action Button Group */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '14px', flexWrap: 'wrap', marginBottom: '40px' }}>
            <button
              className="btn btn-danger btn-lg"
              style={{ padding: '12px 28px', fontSize: '1rem', fontWeight: '800' }}
              onClick={() => {
                playNotificationPing();
                onSelectPortal('victim');
              }}
            >
              <ShieldAlert size={20} />
              <span>I Need Help · Trigger Emergency SOS</span>
            </button>

            <button
              className="btn btn-secondary btn-lg"
              style={{ padding: '12px 24px', fontSize: '0.95rem', fontWeight: '600' }}
              onClick={() => {
                const el = document.getElementById('portals');
                el?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              <span>Explore 5 Stakeholder Portals</span>
              <ArrowRight size={17} />
            </button>
          </div>

          {/* Telemetry Metric KPI Strip */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '14px',
            background: '#ffffff',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-xl)',
            padding: '20px 24px',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Active SOS Alerts
              </div>
              <div style={{ fontSize: '1.9rem', fontWeight: '800', color: 'var(--color-danger)', marginTop: '2px' }}>
                {stats?.sos?.active ?? 12}
              </div>
              <div style={{ fontSize: '0.73rem', color: 'var(--text-faint)' }}>Live satellite beacons</div>
            </div>

            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Operational Camps
              </div>
              <div style={{ fontSize: '1.9rem', fontWeight: '800', color: 'var(--blue-600)', marginTop: '2px' }}>
                {(stats?.camps?.approved ?? 0) + (stats?.camps?.operational ?? 14)}
              </div>
              <div style={{ fontSize: '0.73rem', color: 'var(--text-faint)' }}>MOH verified shelters</div>
            </div>

            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Relief Pledges
              </div>
              <div style={{ fontSize: '1.9rem', fontWeight: '800', color: 'var(--color-success)', marginTop: '2px' }}>
                {stats?.donations?.total_pledges ?? 48}
              </div>
              <div style={{ fontSize: '0.73rem', color: 'var(--text-faint)' }}>Verified medical supplies</div>
            </div>

            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                ML Predictors
              </div>
              <div style={{ fontSize: '1.9rem', fontWeight: '800', color: 'var(--color-violet)', marginTop: '2px' }}>
                4 Models
              </div>
              <div style={{ fontSize: '0.73rem', color: 'var(--text-faint)' }}>In-memory AI inference</div>
            </div>
          </div>
        </div>
      </section>

      {/* Emergency Helplines Bar */}
      <section id="helplines" style={{ padding: '0 32px 40px', maxWidth: '1380px', margin: '0 auto' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))',
          gap: '12px'
        }}>
          <a href="tel:117" style={{ textDecoration: 'none' }}>
            <div className="card" style={{ padding: '14px 18px', background: '#fff', border: '1px solid var(--color-danger-border)', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: 'var(--radius-md)', background: 'var(--color-danger-light)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <PhoneCall size={20} style={{ color: 'var(--color-danger-text)' }} />
              </div>
              <div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: '700' }}>DISASTER MANAGEMENT (DMC)</div>
                <div style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--color-danger-text)' }}>DIAL 117</div>
              </div>
            </div>
          </a>

          <a href="tel:1990" style={{ textDecoration: 'none' }}>
            <div className="card" style={{ padding: '14px 18px', background: '#fff', border: '1px solid var(--blue-200)', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: 'var(--radius-md)', background: 'var(--blue-50)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Activity size={20} style={{ color: 'var(--blue-600)' }} />
              </div>
              <div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: '700' }}>SUWA SERIYA AMBULANCE</div>
                <div style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--blue-600)' }}>DIAL 1990</div>
              </div>
            </div>
          </a>

          <a href="tel:119" style={{ textDecoration: 'none' }}>
            <div className="card" style={{ padding: '14px 18px', background: '#fff', border: '1px solid var(--color-warning-border)', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: 'var(--radius-md)', background: 'var(--color-warning-light)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <ShieldAlert size={20} style={{ color: 'var(--color-warning-text)' }} />
              </div>
              <div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: '700' }}>POLICE EMERGENCY RESCUE</div>
                <div style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--color-warning-text)' }}>DIAL 119</div>
              </div>
            </div>
          </a>

          <a href="tel:0112672727" style={{ textDecoration: 'none' }}>
            <div className="card" style={{ padding: '14px 18px', background: '#fff', border: '1px solid var(--color-success-border)', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: 'var(--radius-md)', background: 'var(--color-success-light)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <HeartHandshake size={20} style={{ color: 'var(--color-success-text)' }} />
              </div>
              <div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: '700' }}>SRI LANKA RED CROSS</div>
                <div style={{ fontSize: '1.15rem', fontWeight: '800', color: 'var(--color-success-text)' }}>011 267 2727</div>
              </div>
            </div>
          </a>
        </div>
      </section>

      {/* 5 Dedicated Stakeholder Portals Showcase */}
      <section id="portals" style={{ padding: '24px 32px 50px', maxWidth: '1380px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--blue-600)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '6px' }}>
            Multi-Stakeholder Architecture
          </div>
          <h2 style={{ fontSize: '1.9rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            5 Dedicated Portals Tailored for Every Response Unit
          </h2>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', maxWidth: '640px', margin: '6px auto 0' }}>
            Role-based interfaces optimized specifically for victims under distress, Ministry of Health commanders, donors, field responders, and national administrators.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
          gap: '20px'
        }}>
          {portalCards.map((p) => {
            const Icon = p.icon;
            return (
              <div
                key={p.id}
                className="card"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  padding: '24px',
                  borderTop: `3px solid var(--blue-600)`
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                    <div style={{
                      width: '38px',
                      height: '38px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--blue-50)',
                      color: 'var(--blue-600)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <Icon size={20} />
                    </div>
                    <span className="badge badge-blue font-mono">
                      {p.subtitle}
                    </span>
                  </div>

                  <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '8px' }}>
                    {p.title}
                  </h3>

                  <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: '1.5', marginBottom: '16px' }}>
                    {p.desc}
                  </p>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '20px' }}>
                    {p.features.map((feat, idx) => (
                      <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                        <CheckCircle2 size={13} style={{ color: 'var(--blue-600)' }} />
                        <span>{feat}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  className={`btn ${p.id === 'victim' ? 'btn-danger' : 'btn-primary'}`}
                  style={{ width: '100%', justifyContent: 'space-between', padding: '9px 16px', fontWeight: '700' }}
                  onClick={() => {
                    playNotificationPing();
                    onSelectPortal(p.id);
                  }}
                >
                  <span>{p.actionText}</span>
                  <ArrowRight size={15} />
                </button>
              </div>
            );
          })}
        </div>
      </section>

      {/* Live Situational GIS Map Preview */}
      <section id="map" style={{ padding: '0 32px 50px', maxWidth: '1380px', margin: '0 auto' }}>
        <div className="card" style={{ padding: '24px' }}>
          <div className="card-header">
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={18} style={{ color: 'var(--blue-600)' }} />
                <h2 className="card-title" style={{ fontSize: '1.2rem' }}>National Real-Time Situational Awareness Map</h2>
              </div>
              <p className="card-subtitle">
                OpenStreetMap GIS telemetry rendering Kelani river flood basin, Nuwara Eliya landslide zones, and active relief camps
              </p>
            </div>

            <button
              className="btn btn-secondary btn-sm"
              onClick={() => onSelectPortal('admin')}
            >
              <span>Launch Full GIS Console</span>
              <ExternalLink size={13} />
            </button>
          </div>

          <RealTimeMap
            sosPoints={heatmapData?.sos_clusters || []}
            hazardZones={heatmapData?.hazard_zones || []}
            camps={heatmapData?.medical_camps || []}
            height="440px"
          />
        </div>
      </section>

      {/* 4 Machine Learning Predictive Models Showcase */}
      <section id="ai-models" style={{ padding: '0 32px 50px', maxWidth: '1380px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--blue-600)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '6px' }}>
            Machine Learning Pipeline
          </div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            4 Predictive AI Engines Driving Resource Triage
          </h2>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', maxWidth: '640px', margin: '6px auto 0' }}>
            Trained on multi-decade Sri Lanka Department of Meteorology & Disaster Management Centre datasets.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '16px'
        }}>
          {mlModels.map((m, idx) => (
            <div key={idx} className="card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span className={`badge ${m.badgeClass}`}>{m.tag}</span>
                <span className="font-mono" style={{ fontSize: '0.72rem', color: 'var(--blue-600)', fontWeight: '700' }}>
                  {m.accuracy}
                </span>
              </div>
              <h3 style={{ fontSize: '0.96rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '6px' }}>
                {m.name}
              </h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                {m.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border-subtle)',
        backgroundColor: '#ffffff',
        padding: '32px 32px 28px'
      }}>
        <div style={{
          maxWidth: '1380px',
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '20px'
        }}>
          <div>
            <div style={{ fontSize: '0.92rem', fontWeight: '800', color: 'var(--text-primary)' }}>
              SRI LANKA NATIONAL DISASTER RELIEF SYSTEM
            </div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '3px' }}>
              Ministry of Health & Disaster Management Directorate &bull; Fast-Track Emergency Response Cloud
            </div>
          </div>

          <div style={{ display: 'flex', gap: '16px', fontSize: '0.8rem' }}>
            <button
              onClick={() => onSelectPortal('victim')}
              style={{ background: 'transparent', border: 'none', color: 'var(--color-danger-text)', cursor: 'pointer', fontWeight: '600' }}
            >
              Public SOS
            </button>
            <button
              onClick={() => onSelectPortal('authority')}
              style={{ background: 'transparent', border: 'none', color: 'var(--blue-600)', cursor: 'pointer', fontWeight: '600' }}
            >
              MOH Console
            </button>
            <button
              onClick={() => onSelectPortal('donor')}
              style={{ background: 'transparent', border: 'none', color: 'var(--color-success-text)', cursor: 'pointer', fontWeight: '600' }}
            >
              Donor Hub
            </button>
            <button
              onClick={() => onSelectPortal('volunteer')}
              style={{ background: 'transparent', border: 'none', color: 'var(--color-warning-text)', cursor: 'pointer', fontWeight: '600' }}
            >
              Volunteer Dispatch
            </button>
            <button
              onClick={() => onSelectPortal('admin')}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontWeight: '600' }}
            >
              Admin Command
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
