import { FormEvent, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'

export default function SignupPage() {
  const { signup } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    badge_number: '',
    department: 'Cyber Cell',
  })
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const strength = useMemo(() => {
    const p = form.password
    let score = 0
    if (p.length >= 8)  score++
    if (/[A-Z]/.test(p)) score++
    if (/[a-z]/.test(p)) score++
    if (/[0-9]/.test(p)) score++
    if (/[^A-Za-z0-9]/.test(p)) score++
    return score
  }, [form.password])

  const strengthLabel = ['', 'Very Weak', 'Weak', 'Fair', 'Strong', 'Very Strong'][strength] ?? ''
  const strengthColor = ['', '#dc2626', '#ea580c', '#ca8a04', '#16a34a', '#2563eb'][strength] ?? ''

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')

    if (strength < 3) { setError('Password too weak — needs uppercase, lowercase, number'); return }
    if (form.password !== confirmPassword) { setError('Passwords do not match'); return }

    setLoading(true)
    const result = await signup(form)
    setLoading(false)

    if (!result.success) { setError(result.message); return }
    setMessage(result.message)
    setTimeout(() => navigate('/login'), 1500)
  }

  const field = (id: keyof typeof form, label: string, type = 'text', placeholder = '') => (
    <div>
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        type={type}
        value={form[id]}
        onChange={e => setForm({ ...form, [id]: e.target.value })}
        placeholder={placeholder}
        required={['username', 'email', 'password', 'full_name'].includes(id)}
      />
    </div>
  )

  return (
    <div className="centered-page">
      <form className="card" onSubmit={onSubmit} style={{
        width: 440, maxWidth: '96vw', position: 'relative', zIndex: 1,
        padding: '28px 24px',
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 22 }}>
          <div style={{
            width: 50, height: 50, margin: '0 auto 12px',
            borderRadius: 12,
            background: 'linear-gradient(135deg, rgba(124,58,237,0.08), rgba(37,99,235,0.06))',
            border: '1px solid rgba(124,58,237,0.2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0M19 8v6M22 11h-6" stroke="var(--purple)" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          </div>
          <h1 style={{ color: 'var(--purple)', marginBottom: 4 }}>
            REQUEST ACCESS
          </h1>
          <p className="muted" style={{ fontSize: 11, letterSpacing: '2px', textTransform: 'uppercase', margin: 0 }}>
            Officer Registration
          </p>
        </div>

        <div style={{ height: 1, marginBottom: 20, background: 'linear-gradient(90deg, transparent, var(--border-bright), transparent)' }} />

        <div style={{ display: 'grid', gap: 12 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {field('full_name',    'Full Name',     'text',  'Officer Full Name')}
            {field('badge_number', 'Badge Number',  'text',  'e.g. DL-2024-001')}
          </div>
          {field('username',   'Username',    'text',     'Choose a username')}
          {field('email',      'Email',       'email',    'official@delhi.gov.in')}
          {field('department', 'Department',  'text',     'Cyber Cell')}

          {/* Password */}
          <div>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              placeholder="Create strong password"
              required
            />
            {form.password && (
              <div style={{ marginTop: 6 }}>
                <div style={{ display: 'flex', gap: 4, marginBottom: 4 }}>
                  {[1,2,3,4,5].map(i => (
                    <div key={i} style={{
                      flex: 1, height: 3, borderRadius: 999,
                      background: i <= strength ? strengthColor : '#e5e7eb',
                      transition: 'background 200ms',
                    }} />
                  ))}
                </div>
                <span style={{ fontSize: 10, color: strengthColor, letterSpacing: '0.5px' }}>
                  {strengthLabel}
                </span>
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <div>
            <label htmlFor="confirm">Confirm Password</label>
            <input
              id="confirm"
              type="password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              placeholder="Repeat password"
              required
            />
          </div>
        </div>

        {/* Alerts */}
        {error   && <div className="alert error"   style={{ marginTop: 14 }}>{error}</div>}
        {message && <div className="alert success" style={{ marginTop: 14 }}>{message}</div>}

        <button
          className="btn btn-primary"
          disabled={loading}
          style={{ width: '100%', marginTop: 18, padding: '11px', fontSize: 13, letterSpacing: '1px' }}
        >
          {loading ? 'SUBMITTING...' : 'SUBMIT REQUEST'}
        </button>

        <p className="muted" style={{ fontSize: 12, textAlign: 'center', marginTop: 14, marginBottom: 0 }}>
          Already registered? <Link to="/login" style={{ fontWeight: 600 }}>Sign In</Link>
        </p>
      </form>
    </div>
  )
}
