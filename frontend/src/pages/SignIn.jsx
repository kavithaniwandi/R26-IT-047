import React, { useEffect, useState } from 'react'
import { Eye, EyeOff, LoaderCircle, LockKeyhole, Mail, Radio, ShieldAlert, Activity, HeartHandshake, Truck, ShieldCheck, UserCheck } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import { useAuth } from '../context/AuthContext'
import { getPortalForRole } from '../portalConfig'
import './SignIn.css'

function getDestination(user, requestedPortal) {
  const rolePortal = getPortalForRole(user?.role)
  const portal = requestedPortal === rolePortal ? requestedPortal : rolePortal
  return `/?portal=${encodeURIComponent(portal)}`
}

const PRESET_ACCOUNTS = [
  { label: 'Admin', email: 'admin@disaster.relief.lk', pass: 'Admin@2026!', icon: ShieldCheck, color: 'rose', role: 'admin' },
  { label: 'MOH Authority', email: 'authority@moh.gov.lk', pass: 'Authority@2026!', icon: Activity, color: 'blue', role: 'authority' },
  { label: 'Relief Donor', email: 'donor@redcross.lk', pass: 'Donor@2026!', icon: HeartHandshake, color: 'emerald', role: 'donor' },
  { label: 'Volunteer Dispatch', email: 'volunteer@relief.lk', pass: 'Volunteer@2026!', icon: Truck, color: 'amber', role: 'volunteer' },
  { label: 'Victim SOS', email: 'victim@kaduwela.lk', pass: 'Victim@2026!', icon: ShieldAlert, color: 'rose', role: 'victim' }
]

function SignIn() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, login, isLoading } = useAuth()
  const requestedPortal = location.state?.portal

  useEffect(() => {
    if (!isLoading && user) {
      navigate(getDestination(user, requestedPortal), { replace: true })
    }
  }, [isLoading, navigate, requestedPortal, user])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
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

  const handleSelectPreset = (preset) => {
    setEmail(preset.email)
    setPassword(preset.pass)
    setError('')
  }

  return (
    <div className="signin-page">
      <Navigation />
      <main className="signin-container">
        <section className="signin-card" aria-labelledby="signin-title">
          <div className="signin-mark" aria-hidden="true">
            <Radio size={28} />
          </div>

          <div className="signin-header">
            <span className="signin-eyebrow">NATIONAL DISASTER RELIEF SYSTEM</span>
            <h1 id="signin-title">Stakeholder Authentication</h1>
            <p>One secure login for every emergency response, MOH, donor & field portal.</p>
          </div>

          {/* Quick Demo Preset Account Fillers */}
          <div className="signin-presets-section">
            <span className="signin-presets-label">Quick 1-Click Demo Login:</span>
            <div className="signin-presets-grid">
              {PRESET_ACCOUNTS.map((acc) => {
                const Icon = acc.icon;
                const isSelected = email === acc.email;
                return (
                  <button
                    key={acc.role}
                    type="button"
                    className={`signin-preset-btn ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleSelectPreset(acc)}
                    title={`Fill ${acc.label} credentials`}
                  >
                    <Icon size={14} />
                    <span>{acc.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {requestedPortal && (
            <div className="signin-notice">
              Sign in with an account authorized for the requested workspace portal.
            </div>
          )}

          {error && <div className="error-message" role="alert">{error}</div>}

          <form className="signin-form" onSubmit={handleSubmit}>
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
              <span>{submitting ? 'Authenticating…' : 'Sign In to Workspace'}</span>
            </button>
          </form>

          <p className="signin-help">
            Claims-based RBAC automatically opens your designated portal. Need system access? Contact DMC National Directorate.
          </p>
          <Link to="/" className="signin-back-link">Return to Command Center Dashboard</Link>
        </section>
      </main>
      <Footer />
    </div>
  )
}

export default SignIn
