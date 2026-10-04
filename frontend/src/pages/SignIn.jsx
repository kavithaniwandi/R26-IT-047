import React, { useEffect, useState } from 'react'
import { Eye, EyeOff, LoaderCircle, LockKeyhole, Mail, ShieldCheck } from 'lucide-react'
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

  return (
    <div className="signin-page">
      <Navigation />
      <main className="signin-container">
        <section className="signin-card" aria-labelledby="signin-title">
          <div className="signin-mark" aria-hidden="true">
            <ShieldCheck size={28} />
          </div>
          <div className="signin-header">
            <span className="signin-eyebrow">Unified access</span>
            <h1 id="signin-title">Sign in to MediDonate</h1>
            <p>One secure login for every disaster relief stakeholder portal.</p>
          </div>

          {requestedPortal && (
            <div className="signin-notice">
              Sign in with an account authorized for the requested portal.
            </div>
          )}

          {error && <div className="error-message" role="alert">{error}</div>}

          <form className="signin-form" onSubmit={handleSubmit}>
            <div className="signin-field">
              <label htmlFor="signin-email">Email address</label>
              <div className="signin-input-wrap">
                <Mail size={18} aria-hidden="true" />
                <input
                  type="email"
                  id="signin-email"
                  name="email"
                  autoComplete="username"
                  placeholder="name@organisation.lk"
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
                  placeholder="Enter your password"
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
              {submitting ? <LoaderCircle className="signin-spinner" size={19} /> : <LockKeyhole size={18} />}
              <span>{submitting ? 'Signing in…' : 'Sign in securely'}</span>
            </button>
          </form>

          <p className="signin-help">
            Your account role automatically opens the correct workspace. Need access? Contact your system administrator.
          </p>
          <Link to="/home" className="signin-back-link">Return to public site</Link>
        </section>
      </main>
      <Footer />
    </div>
  )
}

export default SignIn
