import React, { useEffect, useState } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('riq_token') || '')
  const [email, setEmail] = useState('admin@rhythmiq.io')
  const [password, setPassword] = useState('admin123')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [name, setName] = useState('')
  const [trackPhone, setTrackPhone] = useState('')
  const [trackPlatform, setTrackPlatform] = useState('whatsapp')
  const [contacts, setContacts] = useState([])
  const [trackerJobs, setTrackerJobs] = useState([])
  const [insights, setInsights] = useState(null)
  const [leaderboard, setLeaderboard] = useState([])
  const [serviceStatus, setServiceStatus] = useState({ enabled: false, connected: false, url: '', jobs: 0 })
  const [error, setError] = useState('')
  const [verification, setVerification] = useState(null)

  const login = async () => {
    try {
      setError('')
      const form = new URLSearchParams()
      form.append('username', email)
      form.append('password', password)
      const res = await axios.post(`${API}/auth/login`, form)
      setToken(res.data.access_token)
      localStorage.setItem('riq_token', res.data.access_token)
    } catch {
      setError('Invalid credentials')
    }
  }

  const loadContacts = async () => {
    if (!token) return
    const headers = { Authorization: `Bearer ${token}` }
    const res = await axios.get(`${API}/contacts/`, { headers })
    setContacts(res.data)
  }

  const loadTrackerJobs = async () => {
    if (!token) return
    const headers = { Authorization: `Bearer ${token}` }
    const res = await axios.get(`${API}/tracker/jobs`, { headers })
    setTrackerJobs(res.data)
  }

  const loadServiceStatus = async () => {
    if (!token) return
    const headers = { Authorization: `Bearer ${token}` }
    const res = await axios.get(`${API}/tracker/service-status`, { headers })
    setServiceStatus(res.data)
  }

  const loadInsights = async () => {
    if (!token) return
    const headers = { Authorization: `Bearer ${token}` }
    const [insRes, lbRes] = await Promise.all([
      axios.get(`${API}/insights/`, { headers }),
      axios.get(`${API}/leaderboard/`, { headers }),
    ])
    setInsights(insRes.data)
    setLeaderboard(lbRes.data)
  }

  const addContact = async () => {
    if (!phoneNumber) return
    try {
      setError('')
      const headers = { Authorization: `Bearer ${token}` }
      await axios.post(`${API}/contacts/`, {
        phone_number: phoneNumber,
        name: name || phoneNumber,
        status: 'unknown',
      }, { headers })
      setPhoneNumber('')
      setName('')
      await loadContacts()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not add contact')
    }
  }

  const verifyNumber = async () => {
    if (!trackPhone) return
    try {
      setError('')
      const headers = { Authorization: `Bearer ${token}` }
      const res = await axios.post(`${API}/tracker/verify`, { phone_number: trackPhone, platform: trackPlatform }, { headers })
      setVerification(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Verification failed')
    }
  }

  const startTracker = async (contactId, phoneValue, platform = trackPlatform) => {
    if (!contactId || !phoneValue) return
    try {
      setError('')
      const headers = { Authorization: `Bearer ${token}` }
      await axios.post(`${API}/tracker/jobs/start`, {
        contact_id: contactId,
        phone_number: phoneValue,
        platform,
      }, { headers })
      await loadContacts()
      await loadTrackerJobs()
      await loadServiceStatus()
      await loadInsights()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not start tracker job')
    }
  }

  const stopTracker = async (contactId, phoneValue, platform = trackPlatform) => {
    if (!contactId || !phoneValue) return
    try {
      setError('')
      const headers = { Authorization: `Bearer ${token}` }
      await axios.post(`${API}/tracker/jobs/stop`, {
        contact_id: contactId,
        phone_number: phoneValue,
        platform,
      }, { headers })
      await loadContacts()
      await loadTrackerJobs()
      await loadServiceStatus()
      await loadInsights()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not stop tracker job')
    }
  }

  useEffect(() => {
    if (token) {
      loadContacts()
      loadTrackerJobs()
      loadServiceStatus()
      loadInsights()
    }
  }, [token])

  const getStatusColor = (status) => {
    switch ((status || '').toLowerCase()) {
      case 'online':
        return '#4ade80'
      case 'standby':
        return '#fbbf24'
      case 'offline':
        return '#f87171'
      case 'tracking':
        return '#38bdf8'
      default:
        return '#94a3b8'
    }
  }

  if (!token) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <div style={{ width: 360, background: '#111827', padding: 24, borderRadius: 12 }}>
          <h2 style={{ marginBottom: 16 }}>RhythmIQ Admin Monitor</h2>
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" style={inputStyle} />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" style={inputStyle} />
          <button onClick={login} style={buttonStyle}>Login</button>
          {error && <div style={{ color: '#fca5a5', marginTop: 12 }}>{error}</div>}
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: 30 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2>My Team</h2>
        <button onClick={() => { setToken(''); localStorage.removeItem('riq_token') }} style={{ ...buttonStyle, background: '#334155' }}>Logout</button>
      </div>

      <div style={{ background: '#111827', padding: 20, borderRadius: 12, marginBottom: 20 }}>
        <h3>Add phone number</h3>
        <input value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} placeholder="+1234567890" style={inputStyle} />
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Display name" style={inputStyle} />
        <button onClick={addContact} style={buttonStyle}>Add Contact</button>
      </div>

      <div style={{ background: '#111827', padding: 20, borderRadius: 12, marginBottom: 20 }}>
        <h3>Live tracker service</h3>
        <div style={{ marginBottom: 12, color: serviceStatus.connected ? '#4ade80' : '#fca5a5' }}>
          {serviceStatus.connected ? 'Connected' : 'Disconnected'} · {serviceStatus.url || 'tracker unavailable'}
        </div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <input value={trackPhone} onChange={(e) => setTrackPhone(e.target.value)} placeholder="+15551234567" style={{ ...inputStyle, width: 260, marginBottom: 0 }} />
          <select value={trackPlatform} onChange={(e) => setTrackPlatform(e.target.value)} style={{ ...inputStyle, width: 180, marginBottom: 0 }}>
            <option value="whatsapp">WhatsApp</option>
            <option value="signal">Signal</option>
          </select>
          <button onClick={verifyNumber} style={{ ...buttonStyle, background: '#38bdf8' }}>Verify</button>
        </div>
        {verification && (
          <div style={{ marginTop: 12, color: verification.verified ? '#4ade80' : '#fca5a5' }}>
            {verification.verified ? `Verified: ${verification.platform} / ${verification.number}` : verification.message}
          </div>
        )}
      </div>

      <div style={{ background: '#111827', padding: 20, borderRadius: 12, marginBottom: 20 }}>
        <h3>Active tracker jobs</h3>
        {trackerJobs.length === 0 ? <p>No active tracker jobs</p> : trackerJobs.map((job) => (
          <div key={job.contact_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1f2937', padding: '12px 0' }}>
            <div>
              <div style={{ fontWeight: 700 }}>{job.name || job.phone_number}</div>
              <div style={{ color: '#94a3b8', fontSize: 12 }}>{job.phone_number} • {job.platform}</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ color: getStatusColor(job.state || job.status), fontWeight: 700, textTransform: 'capitalize' }}>{job.state || job.status}</span>
              <button onClick={() => stopTracker(job.contact_id, job.phone_number, job.platform)} style={{ ...buttonStyle, background: '#ef4444', padding: '8px 10px' }}>Stop</button>
            </div>
          </div>
        ))}
      </div>

      <div style={{ background: '#111827', padding: 20, borderRadius: 12, marginBottom: 20 }}>
        <h3>Team list</h3>
        {contacts.length === 0 ? <p>No contacts yet</p> : contacts.map((c) => {
          const tracked = trackerJobs.find((job) => job.contact_id === c.id)
          const state = tracked ? (tracked.state || tracked.status || c.status || 'unknown') : (c.status || 'unknown')
          const rttLabel = tracked && tracked.rtt_ms != null ? `${Number(tracked.rtt_ms).toFixed(0)} ms` : 'No RTT yet'
          return (
            <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', padding: '12px 0', gap: 16, alignItems: 'center' }}>
              <div>
                <strong>{c.name || c.phone_number}</strong>
                <div style={{ color: '#94a3b8' }}>{c.phone_number}</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                <span style={{ color: getStatusColor(state), fontWeight: 700, textTransform: 'capitalize' }}>{state}</span>
                <span style={{ color: '#cbd5e1', fontSize: 12 }}>{rttLabel}</span>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                  <button onClick={() => startTracker(c.id, c.phone_number, trackPlatform)} style={{ ...buttonStyle, padding: '6px 10px', fontSize: 11, background: '#14532d' }}>Start</button>
                  <button onClick={() => stopTracker(c.id, c.phone_number, trackPlatform)} style={{ ...buttonStyle, padding: '6px 10px', fontSize: 11, background: '#7f1d1d' }}>Stop</button>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {insights && (
        <div style={{ background: '#111827', padding: 20, borderRadius: 12 }}>
          <h3>Current state: {insights.state}</h3>
          <p>{insights.explanation}</p>
          <pre style={{ overflow: 'auto', whiteSpace: 'pre-wrap' }}>{JSON.stringify(insights.features, null, 2)}</pre>
        </div>
      )}

      <div style={{ background: '#111827', padding: 20, borderRadius: 12, marginTop: 20 }}>
        <h3>Leaderboard</h3>
        {leaderboard.map((item) => (
          <div key={item.rank} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #1f2937' }}>
            <span>{item.rank}. {item.name}</span>
            <span>{item.score}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

const inputStyle = {
  display: 'block',
  width: '100%',
  marginBottom: 12,
  padding: '10px 12px',
  borderRadius: 8,
  border: '1px solid #334155',
  background: '#0f172a',
  color: '#e2e8f0',
}

const buttonStyle = {
  background: '#38bdf8',
  color: '#0f172a',
  border: 'none',
  borderRadius: 8,
  padding: '10px 16px',
  cursor: 'pointer',
  fontWeight: 700,
}
