import React, { useState, useEffect } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('riq_token') || '')
  const [email, setEmail] = useState('admin@rhythmiq.io')
  const [password, setPassword] = useState('admin123')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [name, setName] = useState('')
  const [contacts, setContacts] = useState([])
  const [insights, setInsights] = useState(null)
  const [leaderboard, setLeaderboard] = useState([])
  const [error, setError] = useState('')

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

  const addContact = async () => {
    if (!phoneNumber) return
    try {
      setError('')
      const headers = { Authorization: `Bearer ${token}` }
      await axios.post(`${API}/contacts/`, {
        phone_number: phoneNumber,
        name: name || phoneNumber,
        status: 'unknown'
      }, { headers })

      setPhoneNumber('')
      setName('')
      loadContacts()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not add contact')
    }
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

  useEffect(() => {
    if (token) {
      loadContacts()
      loadInsights()
    }
  }, [token])

  if (!token) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <div style={{ width: 360, background: '#111827', padding: 24, borderRadius: 12 }}>
          <h2 style={{ marginBottom: 16 }}>RhythmIQ Admin Monitor</h2>
          <input value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" style={inputStyle} />
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" style={inputStyle} />
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
        <input value={phoneNumber} onChange={e => setPhoneNumber(e.target.value)} placeholder="+1234567890" style={inputStyle} />
        <input value={name} onChange={e => setName(e.target.value)} placeholder="Display name" style={inputStyle} />
        <button onClick={addContact} style={buttonStyle}>Add Contact</button>
      </div>

      <div style={{ background: '#111827', padding: 20, borderRadius: 12, marginBottom: 20 }}>
        <h3>Team list</h3>
        {contacts.length === 0 ? <p>No contacts yet</p> : contacts.map(c => (
          <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', padding: '10px 0' }}>
            <div>
              <strong>{c.name || c.phone_number}</strong>
              <div style={{ color: '#94a3b8' }}>{c.phone_number}</div>
            </div>
            <div>
              <span style={{ color: '#38bdf8' }}>{c.status}</span>
            </div>
          </div>
        ))}
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
        {leaderboard.map(item => (
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
  color: '#e2e8f0'
}

const buttonStyle = {
  background: '#38bdf8',
  color: '#0f172a',
  border: 'none',
  borderRadius: 8,
  padding: '10px 16px',
  cursor: 'pointer',
  fontWeight: 700
}
