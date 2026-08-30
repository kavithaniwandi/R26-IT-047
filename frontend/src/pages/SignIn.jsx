import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import { useAuth } from '../context/AuthContext'
import './SignIn.css'

function SignIn() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { login } = useAuth()

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')

    if (!email || !password) {
      setError('Please fill in all fields')
      return
    }

    const userData = {
      name: email.split('@')[0],
      email: email,
      id: Date.now()
    }

    login(userData)
    navigate('/')
  }

  return (
    <div className="signin-page">
      <Navigation />
      <div className="signin-container">
        <div className="signin-card">
          <div className="signin-header">
            <h1>Sign In</h1>
            <p>Access your MediDonate account</p>
          </div>
          {error && <div className="error-message">{error}</div>}
          <form className="signin-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input 
                type="email" 
                id="email" 
                placeholder="Enter your email" 
                required 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input 
                type="password" 
                id="password" 
                placeholder="Enter your password" 
                required 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="form-options">
              <label className="remember-me">
                <input type="checkbox" />
                <span>Remember me</span>
              </label>
              <a href="#" className="forgot-password">Forgot password?</a>
            </div>
            <button type="submit" className="signin-button">Sign In</button>
          </form>
          <div className="signin-divider">
            <span>or</span>
          </div>
          <div className="social-signin">
            <button className="social-button google">
              <span>🔵</span> Sign in with Google
            </button>
            <button className="social-button facebook">
              <span>📘</span> Sign in with Facebook
            </button>
          </div>
          <div className="signup-link">
            <p>Don't have an account? <a href="#">Sign Up</a></p>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default SignIn
