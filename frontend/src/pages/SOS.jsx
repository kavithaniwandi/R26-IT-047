import React, { useState, useEffect, useRef } from 'react'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import { api } from '../api'
import './SOS.css'

/* ── Emergency type → human label ── */
const EMERGENCY_TYPES = [
  { value: '',        label: 'Select emergency type' },
  { value: 'medical', label: 'Medical Emergency' },
  { value: 'disaster',label: 'Natural Disaster' },
  { value: 'accident',label: 'Accident' },
  { value: 'fire',    label: 'Fire' },
  { value: 'other',   label: 'Other' },
]

/* urgency map: emergency type → default urgency level (1-5) */
const TYPE_URGENCY = { medical: 5, disaster: 5, accident: 4, fire: 5, other: 3 }

/**
 * SOS page — real end-to-end emergency SOS flow:
 *
 *   1. Victim fills form (emergency type, GPS location, description, contact count)
 *   2. On submit:
 *        a. POST /sos           → creates SOS record + ML priority score
 *        b. POST /sos/alert-contacts → dispatches SMS to saved emergency contacts
 *   3. Displays real-time dispatch log with per-contact delivery status
 *
 * SMS is dispatched via the backend Text.lk / SMSGo gateway.
 * When TEXTLK_ENABLED=false the status will show "simulated" — set the env
 * var to activate real SMS sending.
 */
function SOS() {
  /* ── form state ── */
  const [emergencyType, setEmergencyType] = useState('')
  const [location, setLocation]           = useState('')
  const [lat, setLat]                     = useState(null)
  const [lng, setLng]                     = useState(null)
  const [description, setDescription]     = useState('')
  const [affectedPeople, setAffectedPeople] = useState(1)
  const [hasElderly, setHasElderly]       = useState(false)
  const [hasChildren, setHasChildren]     = useState(false)
  const [hasDisabled, setHasDisabled]     = useState(false)

  /* ── contacts saved on server ── */
  const [savedContacts, setSavedContacts] = useState([])
  const [contactsLoaded, setContactsLoaded] = useState(false)

  /* ── UI state ── */
  const [gpsLoading, setGpsLoading]       = useState(false)
  const [gpsError, setGpsError]           = useState(null)
  const [submitting, setSubmitting]       = useState(false)
  const [result, setResult]               = useState(null)   // { sos, dispatch }
  const [error, setError]                 = useState(null)
  const [phase, setPhase]                 = useState('idle') // idle | locating | submitting | alerting | done

  const submitRef = useRef(null)

  /* ── Load saved emergency contacts on mount ── */
  useEffect(() => {
    api.getEmergencyContacts()
      .then(contacts => {
        setSavedContacts(contacts || [])
        setContactsLoaded(true)
      })
      .catch(() => {
        setContactsLoaded(true) // fail silently — contacts section will show "none saved"
      })
  }, [])

  /* ── GPS capture ── */
  const handleGetGPS = () => {
    if (!navigator.geolocation) {
      setGpsError('Geolocation is not supported by your browser.')
      return
    }
    setGpsLoading(true)
    setGpsError(null)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords
        setLat(latitude)
        setLng(longitude)
        setLocation(`GPS: ${latitude.toFixed(5)}, ${longitude.toFixed(5)}`)
        setGpsLoading(false)
      },
      (err) => {
        setGpsError(`GPS error: ${err.message}. Enter location manually.`)
        setGpsLoading(false)
      },
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }

  /* ── Main submit handler ── */
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setResult(null)
    setSubmitting(true)
    setPhase('submitting')

    /* ── Step 1: Resolve coordinates ── */
    let resolvedLat = lat
    let resolvedLng = lng

    if (!resolvedLat || !resolvedLng) {
      // Attempt a last-resort GPS lookup
      setPhase('locating')
      try {
        await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(
            (pos) => {
              resolvedLat = pos.coords.latitude
              resolvedLng = pos.coords.longitude
              setLat(resolvedLat)
              setLng(resolvedLng)
              resolve()
            },
            reject,
            { enableHighAccuracy: true, timeout: 8000 }
          )
        })
      } catch {
        // Fall back to Colombo central if GPS is unavailable
        resolvedLat = 6.9271
        resolvedLng = 79.8612
      }
      setPhase('submitting')
    }

    const urgencyLevel = TYPE_URGENCY[emergencyType] ?? 4

    /* ── Step 2: Create SOS record via API ── */
    let sosRecord = null
    try {
      sosRecord = await api.createSOS({
        latitude:              resolvedLat,
        longitude:             resolvedLng,
        district:              'Colombo',          // geocoding enrichment handled server-side
        ds_division:           'Kaduwela',
        gn_division:           location || undefined,
        address_text:          location || undefined,
        urgency_level:         urgencyLevel,
        affected_people:       Number(affectedPeople),
        affected_families:     Math.max(1, Math.ceil(Number(affectedPeople) / 4)),
        has_elderly:           hasElderly,
        has_children:          hasChildren,
        has_disabled:          hasDisabled,
        medical_needs_summary: description || emergencyType,
      })
    } catch (err) {
      setError(`SOS submission failed: ${err.message}`)
      setSubmitting(false)
      setPhase('idle')
      return
    }

    /* ── Step 3: Alert emergency contacts via SMS ── */
    setPhase('alerting')
    let dispatchResult = null
    try {
      dispatchResult = await api.sendSOSAlertToContacts({
        sos_id:        sosRecord.id,
        priority_score: sosRecord.priority_score,
        victim_name:   undefined,           // backend fills from auth token
        location_text: location || `${resolvedLat.toFixed(4)}, ${resolvedLng.toFixed(4)}`,
        latitude:      resolvedLat,
        longitude:     resolvedLng,
        contacts:      savedContacts.length > 0 ? savedContacts : undefined,
      })
    } catch (err) {
      // SMS dispatch failure is non-fatal — SOS was still created successfully
      dispatchResult = {
        contacts_alerted: 0,
        total_contacts: 0,
        dispatch_log: [],
        message: `SOS created but SMS dispatch failed: ${err.message}`,
      }
    }

    setResult({ sos: sosRecord, dispatch: dispatchResult })
    setPhase('done')
    setSubmitting(false)

    // Scroll to result card
    setTimeout(() => submitRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
  }

  /* ── Phase badge ── */
  const PhaseIndicator = () => {
    const PHASES = {
      locating:   { label: '📡 Acquiring GPS location…',             color: '#f39c12' },
      submitting: { label: '🚨 Registering SOS with relief system…', color: '#e74c3c' },
      alerting:   { label: '📲 Dispatching SMS to emergency contacts…', color: '#8e44ad' },
    }
    const cfg = PHASES[phase]
    if (!cfg) return null
    return (
      <div className="sos-phase-indicator" style={{ borderLeft: `4px solid ${cfg.color}` }}>
        <span className="sos-spinner" />
        <span style={{ color: cfg.color, fontWeight: 700 }}>{cfg.label}</span>
      </div>
    )
  }

  return (
    <div className="sos-page">
      <Navigation />
      <div className="sos-container">

        {/* ── Header ── */}
        <div className="sos-header">
          <div className="sos-icon">🚨</div>
          <h1>Emergency SOS</h1>
          <p>Immediate emergency assistance and disaster response</p>
        </div>

        <div className="sos-content">

          {/* ── LEFT: Form ── */}
          <div className="sos-alert-section">
            <div className="sos-alert-card">
              <h2>Report Emergency</h2>
              <p>Fill the form below. Your SOS is registered and an SMS alert is instantly dispatched to your saved emergency contacts.</p>

              {/* ── Result / success card ── */}
              {result && phase === 'done' && (
                <div className="sos-result-card" ref={submitRef}>
                  <div className="sos-result-header">
                    <span className="sos-result-icon">✅</span>
                    <div>
                      <strong>SOS #{result.sos.id} REGISTERED</strong>
                      <span className="sos-priority-tag">
                        Priority Score: {result.sos.priority_score}/100
                      </span>
                    </div>
                  </div>

                  {/* SMS dispatch log */}
                  <div className="sos-dispatch-log">
                    <p className="sos-dispatch-title">📲 SMS Dispatch Report</p>
                    <p className="sos-dispatch-summary">{result.dispatch.message}</p>

                    {result.dispatch.dispatch_log?.length > 0 ? (
                      <ul className="sos-dispatch-list">
                        {result.dispatch.dispatch_log.map((entry, idx) => {
                          const isOk = entry.status === 'sent' || entry.status === 'simulated'
                          return (
                            <li key={idx} className={`sos-dispatch-item ${isOk ? 'ok' : 'fail'}`}>
                              <span className="dispatch-status-dot">{isOk ? '✓' : '✗'}</span>
                              <span className="dispatch-name">{entry.name}</span>
                              <span className="dispatch-phone">{entry.phone}</span>
                              <span className={`dispatch-status-label ${entry.status}`}>
                                {entry.status.toUpperCase()}
                              </span>
                            </li>
                          )
                        })}
                      </ul>
                    ) : (
                      <p className="sos-no-contacts-warn">
                        ⚠️ No emergency contacts saved. Go to your profile to add contacts so they can be alerted next time.
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* ── Error banner ── */}
              {error && (
                <div className="sos-error-banner">
                  <span>⛔ {error}</span>
                </div>
              )}

              {/* ── Phase progress indicator ── */}
              <PhaseIndicator />

              {/* ── Form ── */}
              {phase !== 'done' && (
                <form className="sos-form" onSubmit={handleSubmit}>
                  {/* Emergency Type */}
                  <div className="form-group">
                    <label htmlFor="emergency-type">Emergency Type</label>
                    <select
                      id="emergency-type"
                      required
                      value={emergencyType}
                      onChange={e => setEmergencyType(e.target.value)}
                    >
                      {EMERGENCY_TYPES.map(t => (
                        <option key={t.value} value={t.value} disabled={!t.value}>{t.label}</option>
                      ))}
                    </select>
                  </div>

                  {/* Location with GPS button */}
                  <div className="form-group">
                    <label htmlFor="location">Location</label>
                    <div className="sos-location-row">
                      <input
                        type="text"
                        id="location"
                        placeholder="Enter address or use GPS button →"
                        value={location}
                        onChange={e => setLocation(e.target.value)}
                        required
                      />
                      <button
                        type="button"
                        className="sos-gps-btn"
                        onClick={handleGetGPS}
                        disabled={gpsLoading}
                        title="Get GPS location"
                      >
                        {gpsLoading ? '⏳' : '📍 GPS'}
                      </button>
                    </div>
                    {lat && lng && (
                      <span className="sos-gps-coords">
                        ✅ GPS fixed: {lat.toFixed(5)}, {lng.toFixed(5)}
                      </span>
                    )}
                    {gpsError && (
                      <span className="sos-gps-error">{gpsError}</span>
                    )}
                  </div>

                  {/* Description */}
                  <div className="form-group">
                    <label htmlFor="description">Situation Description</label>
                    <textarea
                      id="description"
                      rows="4"
                      placeholder="Describe the emergency situation, injuries, medical needs…"
                      required
                      value={description}
                      onChange={e => setDescription(e.target.value)}
                    />
                  </div>

                  {/* Affected people */}
                  <div className="form-group">
                    <label htmlFor="affected-people">Number of People Affected</label>
                    <input
                      type="number"
                      id="affected-people"
                      min="1"
                      max="999"
                      value={affectedPeople}
                      onChange={e => setAffectedPeople(e.target.value)}
                      required
                    />
                  </div>

                  {/* Vulnerability checkboxes */}
                  <div className="form-group">
                    <label>Vulnerable Groups Present</label>
                    <div className="sos-checkbox-row">
                      <label className="sos-checkbox-label">
                        <input type="checkbox" checked={hasElderly} onChange={e => setHasElderly(e.target.checked)} />
                        👴 Elderly
                      </label>
                      <label className="sos-checkbox-label">
                        <input type="checkbox" checked={hasChildren} onChange={e => setHasChildren(e.target.checked)} />
                        👶 Children
                      </label>
                      <label className="sos-checkbox-label">
                        <input type="checkbox" checked={hasDisabled} onChange={e => setHasDisabled(e.target.checked)} />
                        ♿ Disabled
                      </label>
                    </div>
                  </div>

                  {/* Saved contacts preview */}
                  {contactsLoaded && (
                    <div className="sos-contacts-preview">
                      <span className="sos-contacts-label">
                        {savedContacts.length > 0
                          ? `📲 SMS will be sent to ${savedContacts.length} saved contact(s): ${savedContacts.map(c => c.name).join(', ')}`
                          : '⚠️ No emergency contacts saved. Add contacts in your Profile to enable SMS alerts.'}
                      </span>
                    </div>
                  )}

                  <button
                    type="submit"
                    className="sos-button"
                    disabled={submitting}
                  >
                    {submitting ? '⏳ Sending SOS…' : '🚨 SEND SOS ALERT'}
                  </button>
                </form>
              )}

              {/* Reset button after done */}
              {phase === 'done' && (
                <button
                  className="sos-reset-btn"
                  onClick={() => {
                    setPhase('idle')
                    setResult(null)
                    setError(null)
                    setEmergencyType('')
                    setLocation('')
                    setLat(null)
                    setLng(null)
                    setDescription('')
                    setAffectedPeople(1)
                    setHasElderly(false)
                    setHasChildren(false)
                    setHasDisabled(false)
                  }}
                >
                  🔁 Send Another SOS
                </button>
              )}
            </div>
          </div>

          {/* ── RIGHT: Info cards ── */}
          <div className="sos-info-section">
            <div className="sos-info-card urgent">
              <span className="info-icon">📞</span>
              <div>
                <h3>Call Emergency Services</h3>
                <p className="emergency-number">119 / 1990</p>
                <p>For immediate life-threatening emergencies in Sri Lanka</p>
              </div>
            </div>
            <div className="sos-info-card">
              <span className="info-icon">📍</span>
              <div>
                <h3>Share Location</h3>
                <p>Use the GPS button to share your exact coordinates with emergency responders</p>
              </div>
            </div>
            <div className="sos-info-card">
              <span className="info-icon">👥</span>
              <div>
                <h3>Alert Contacts</h3>
                <p>An SMS is automatically sent to your saved emergency contacts when you trigger SOS</p>
              </div>
            </div>
            <div className="sos-info-card">
              <span className="info-icon">🏥</span>
              <div>
                <h3>ML Priority Scoring</h3>
                <p>Your SOS is scored by our AI model (Model 4) and routed to the nearest responders first</p>
              </div>
            </div>

            {/* How it works box */}
            <div className="sos-how-it-works">
              <h4>⚙️ How Real SMS Sending Works</h4>
              <ol>
                <li>You fill & submit the SOS form</li>
                <li>Backend creates an SOS record and scores urgency (ML Model 4)</li>
                <li>Backend calls <code>POST /sos/alert-contacts</code></li>
                <li>Gateway dispatches SMS via <strong>Text.lk</strong> or SMSGo to each contact</li>
                <li>Each SMS is logged with status: <em>sent / simulated / failed</em></li>
                <li>You see the per-contact dispatch report instantly</li>
              </ol>
              <p className="sos-note">
                🔴 <strong>LIVE mode:</strong> Set <code>TEXTLK_ENABLED=true</code> + API token in <code>backend/.env</code><br />
                🟡 <strong>Simulation mode:</strong> SMS logged but not sent (default for development)
              </p>
            </div>
          </div>

        </div>
      </div>
      <Footer />
    </div>
  )
}

export default SOS
