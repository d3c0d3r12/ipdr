import { FormEvent, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPw, setShowPw] = useState(false)

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    const result = await login(username, password, rememberMe)
    setLoading(false)
    if (!result.success) { setError(result.message); return }
    const from = (location.state as { from?: string } | null)?.from || '/dashboard'
    navigate(from)
  }

  return (
    <div className="centered-page">
      <form className="card" onSubmit={onSubmit} style={{ position: 'relative', zIndex: 1 }}>
        {/* Logo / Brand */}
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          {/* Shield icon */}
          <div style={{
            width: 56, height: 56,
            margin: '0 auto 14px',
            borderRadius: 14,
            background: 'linear-gradient(135deg, rgba(37,99,235,0.08), rgba(124,58,237,0.06))',
            border: '1px solid rgba(37,99,235,0.2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5Z"
                stroke="var(--cyan)" strokeWidth="1.8" strokeLinejoin="round"
                fill="rgba(37,99,235,0.07)" />
              <path d="m9 12 2 2 4-4" stroke="var(--cyan)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div style={{
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: '2px',
            textTransform: 'uppercase',
            color: 'var(--cyan)',
            marginBottom: 8,
          }}>
            IFSO Delhi Police
          </div>
          <h1 style={{ marginBottom: 4 }}>IPDR COMMAND</h1>
          <p className="muted" style={{ fontSize: 11, letterSpacing: '2px', textTransform: 'uppercase', margin: 0 }}>
            Secure Access Portal
          </p>
        </div>

        {/* Divider */}
        <div style={{
          height: 1, marginBottom: 20,
          background: 'linear-gradient(90deg, transparent, var(--border-bright), transparent)',
        }} />

        {/* Username */}
        <div>
          <label htmlFor="username">Badge / Username</label>
          <div style={{ position: 'relative' }}>
            <span style={{
              position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)',
              color: 'var(--muted)', pointerEvents: 'none',
            }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </span>
            <input
              id="username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Enter username"
              required
              autoComplete="username"
              style={{ paddingLeft: 36 }}
            />
          </div>
        </div>

        {/* Password */}
        <div style={{ marginTop: 12 }}>
          <label htmlFor="password">Password</label>
          <div style={{ position: 'relative' }}>
            <span style={{
              position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)',
              color: 'var(--muted)', pointerEvents: 'none',
            }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" strokeWidth="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </span>
            <input
              id="password"
              type={showPw ? 'text' : 'password'}
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter password"
              required
              autoComplete="current-password"
              style={{ paddingLeft: 36, paddingRight: 42 }}
            />
            <button
              type="button"
              onClick={() => setShowPw(v => !v)}
              style={{
                position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                background: 'none', border: 'none', color: 'var(--muted)', cursor: 'pointer', padding: 4,
              }}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
                {showPw
                  ? <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24M1 1l22 22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  : <path d="M1 12S5 4 12 4s11 8 11 8-4 8-11 8S1 12 1 12Z M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                }
              </svg>
            </button>
          </div>
        </div>

        {/* Remember Me */}
        <div style={{ marginTop: 14, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <label style={{
            display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer',
            fontSize: 12, color: 'var(--muted)', userSelect: 'none',
          }}>
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={e => setRememberMe(e.target.checked)}
              style={{ width: 14, height: 14, accentColor: 'var(--cyan)', cursor: 'pointer' }}
            />
            Remember me
          </label>
          <span style={{ fontSize: 11, color: 'var(--muted)' }}>
            {rememberMe ? 'Session stays active' : 'Session ends on close'}
          </span>
        </div>

        {/* Error */}
        {error && (
          <div className="alert error" style={{ marginTop: 12 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
              <path d="M12 8v4M12 16h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            {error}
          </div>
        )}

        {/* Submit */}
        <button
          className="btn btn-primary"
          disabled={loading}
          style={{ width: '100%', marginTop: 18, padding: '11px 14px', fontSize: 13, letterSpacing: '1px' }}
        >
          {loading ? (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 1s linear infinite' }}>
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeDasharray="32" strokeDashoffset="10" />
              </svg>
              AUTHENTICATING...
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
              ACCESS SYSTEM
            </>
          )}
        </button>

        {/* Footer */}
        <p className="muted" style={{ fontSize: 12, textAlign: 'center', marginTop: 16, marginBottom: 0 }}>
          New officer?{' '}
          <Link to="/signup" style={{ fontWeight: 600 }}>Request Access</Link>
        </p>
      </form>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}
