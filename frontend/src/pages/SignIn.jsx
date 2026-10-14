import React, { useEffect, useState } from 'react'
import { Eye, EyeOff, LoaderCircle, LockKeyhole, Mail, Radio, UserCheck, User, Phone, ShieldAlert, LogIn } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import { useAuth } from '../context/AuthContext'
import { getPortalForRole } from '../portalConfig'
import { api } from '../api'
import './SignIn.css'

function getDestination(user, requestedPortal) {
  const rolePortal = getPortalForRole(user?.role)
  const portal = requestedPortal === rolePortal ? requestedPortal : rolePortal
  return `/?portal=${encodeURIComponent(portal)}`
}

function SignIn() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, login, isLoading } = useAuth()
  const requestedPortal = location.state?.portal

  const [activeTab, setActiveTab] = useState(() => {
    if (location.state?.tab === 'victim_signup' || requestedPortal === 'victim_signup') return 'victim_signup'
    return 'signin'
  })

  // Sign In fields
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  // Victim Sign Up fields
  const [fullName, setFullName] = useState('')
  const [victimEmail, setVictimEmail] = useState('')
  const [victimPhone, setVictimPhone] = useState('')
  const [victimPassword, setVictimPassword] = useState('')

  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!isLoading && user) {
      navigate(getDestination(user, requestedPortal), { replace: true })
    }
  }, [isLoading, navigate, requestedPortal, user])

  const handleSignInSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')
    setSubmitting(true)

    try {
      const loggedInUser = await login(email.trim(), password)
      navigate(getDestination(loggedInUser, requestedPortal), { replace: true })
    } catch (err) {
      setError(err.message || 'Sign in failed. Check your email and password.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleVictimSignUpSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')
    setSubmitting(true)

    try {
      await api.register({
        full_name: fullName.trim(),
        email: victimEmail.trim(),
        password: victimPassword,
        phone: victimPhone.trim() || '+94 77 123 4567'
      })

      setSuccess('Victim account registered successfully! Logging you in...')
      // Auto login
      const loggedInUser = await login(victimEmail.trim(), victimPassword)
      navigate('/?portal=victim', { replace: true })
    } catch (err) {
      setError(err.message || 'Victim registration failed. Please check the details provided.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="signin-page">
      <Navigation />
      <main className="signin-container">
        <section className="signin-card" aria-labelledby="signin-title">
          <div className="signin-mark" aria-hidden="true">
            <Radio size={28} />
          </div>

          {/* Mode Switch Tabs */}
          <div className="signin-tab-group" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'signin'}
              className={`signin-tab-btn ${activeTab === 'signin' ? 'active' : ''}`}
              onClick={() => { setActiveTab('signin'); setError(''); setSuccess(''); }}
            >
              <LogIn size={14} />
              <span>Sign In</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'victim_signup'}
              className={`signin-tab-btn ${activeTab === 'victim_signup' ? 'active' : ''}`}
              onClick={() => { setActiveTab('victim_signup'); setError(''); setSuccess(''); }}
            >
              <ShieldAlert size={14} style={{ color: '#ef4444' }} />
              <span>Victim Sign Up</span>
            </button>
          </div>

          {activeTab === 'signin' ? (
            <>
              <div className="signin-header">
                <span className="signin-eyebrow">SRI LANKA DISASTER RELIEF SYSTEM</span>
                <h1 id="signin-title">Stakeholder Authentication</h1>
                <p>Secure login for Ministry of Health (MOH), relief donors, field volunteers, disaster officers & victims.</p>
              </div>

              {requestedPortal && requestedPortal !== 'victim_signup' && (
                <div className="signin-notice">
                  Please sign in with credentials authorized for the requested portal workspace.
                </div>
              )}

              {error && <div className="error-message" role="alert">{error}</div>}
              {success && <div className="signin-notice" role="status">{success}</div>}

              <form className="signin-form" onSubmit={handleSignInSubmit}>
                <div className="signin-field">
                  <label htmlFor="signin-email">Stakeholder Email Address</label>
                  <div className="signin-input-wrap">
                    <Mail size={18} aria-hidden="true" />
                    <input
                      type="email"
                      id="signin-email"
                      name="email"
                      autoComplete="username"
                      placeholder="e.g. admin@disaster.relief.lk"
                      required
                      autoFocus
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      disabled={submitting}
                    />
                  </div>
                </div>

                <div className="signin-field">
                  <label htmlFor="signin-password">Password</label>
                  <div className="signin-input-wrap">
                    <LockKeyhole size={18} aria-hidden="true" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      id="signin-password"
                      name="password"
                      autoComplete="current-password"
                      placeholder="Enter account password"
                      required
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      disabled={submitting}
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowPassword((visible) => !visible)}
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                <button type="submit" className="signin-button" disabled={submitting || isLoading}>
                  {submitting ? <LoaderCircle className="signin-spinner" size={19} /> : <UserCheck size={18} />}
                  <span>{submitting ? 'Authenticating…' : 'Sign In'}</span>
                </button>
              </form>

              <p className="signin-help">
                Are you a disaster-affected civilian?{' '}
                <button
                  type="button"
                  style={{ background: 'none', border: 'none', color: '#2563eb', fontWeight: '700', cursor: 'pointer', padding: 0 }}
                  onClick={() => { setActiveTab('victim_signup'); setError(''); }}
                >
                  Register for Victim Relief Services &rarr;
                </button>
              </p>
            </>
          ) : (
            <>
              <div className="signin-header">
                <span className="signin-eyebrow" style={{ color: '#ef4444' }}>PUBLIC EMERGENCY RELIEF SERVICES</span>
                <h1 id="signin-title">Victim Sign Up</h1>
                <p>Register as a disaster-affected citizen for 24/7 SOS rescue, medical intake, and camp allocation.</p>
              </div>

              <div className="victim-register-notice">
                <strong>Public Victim Registration:</strong> This account gives you immediate access to the <strong>Victim Emergency SOS Portal</strong> with GPS distress broadcasting and registered family safe-zone tracking.
              </div>

              {error && <div className="error-message" role="alert">{error}</div>}
              {success && <div className="signin-notice" role="status">{success}</div>}

              <form className="signin-form" onSubmit={handleVictimSignUpSubmit}>
                <div className="signin-field">
                  <label htmlFor="victim-fullname">Full Name</label>
                  <div className="signin-input-wrap">
                    <User size={18} aria-hidden="true" />
                    <input
                      type="text"
                      id="victim-fullname"
                      name="fullName"
                      placeholder="e.g. Chamari Perera"
                      required
                      autoFocus
                      value={fullName}
                      onChange={(event) => setFullName(event.target.value)}
                      disabled={submitting}
                    />
                  </div>
                </div>

                <div className="signin-field">
                  <label htmlFor="victim-email">Email Address</label>
                  <div className="signin-input-wrap">
                    <Mail size={18} aria-hidden="true" />
                    <input
                      type="email"
                      id="victim-email"
                      name="victimEmail"
                      placeholder="e.g. victim@kaduwela.lk"
                      required
                      value={victimEmail}
                      onChange={(event) => setVictimEmail(event.target.value)}
                      disabled={submitting}
                    />
                  </div>
                </div>

                <div className="signin-field">
                  <label htmlFor="victim-phone">Mobile Phone Number</label>
                  <div className="signin-input-wrap">
                    <Phone size={18} aria-hidden="true" />
                    <input
                      type="tel"
                      id="victim-phone"
                      name="victimPhone"
                      placeholder="e.g. +94 77 123 4567"
                      required
                      value={victimPhone}
                      onChange={(event) => setVictimPhone(event.target.value)}
                      disabled={submitting}
                    />
                  </div>
                </div>

                <div className="signin-field">
                  <label htmlFor="victim-password">Create Secure Password</label>
                  <div className="signin-input-wrap">
                    <LockKeyhole size={18} aria-hidden="true" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      id="victim-password"
                      name="victimPassword"
                      placeholder="At least 8 chars (1 letter, 1 number)"
                      required
                      value={victimPassword}
                      onChange={(event) => setVictimPassword(event.target.value)}
                      disabled={submitting}
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowPassword((visible) => !visible)}
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                <button type="submit" className="signin-button" disabled={submitting || isLoading}>
                  {submitting ? <LoaderCircle className="signin-spinner" size={19} /> : <ShieldAlert size={18} />}
                  <span>{submitting ? 'Creating Victim Account…' : 'Register Victim Account'}</span>
                </button>
              </form>

              <p className="signin-help">
                Already registered?{' '}
                <button
                  type="button"
                  style={{ background: 'none', border: 'none', color: '#2563eb', fontWeight: '700', cursor: 'pointer', padding: 0 }}
                  onClick={() => { setActiveTab('signin'); setError(''); }}
                >
                  Sign in with your email & password &rarr;
                </button>
              </p>
            </>
          )}

          <Link to="/" className="signin-back-link">← Return to Home Page</Link>
        </section>
      </main>
      <Footer />
    </div>
  )
}

export default SignIn
