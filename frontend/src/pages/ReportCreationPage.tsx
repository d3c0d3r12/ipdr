import { FormEvent, useState } from 'react'
import { API_BASE, apiRequest } from '../lib/api'
import { useAuth } from '../lib/auth'

export default function ReportCreationPage() {
  const { token } = useAuth()
  const savedRunDir = localStorage.getItem('latest_run_dir') || ''
  const [runDir, setRunDir] = useState(savedRunDir)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const extractRunDirName = (value: string) => {
    const normalized = value.trim().replace(/\\/g, '/')
    const parts = normalized.split('/').filter(Boolean)
    return parts[parts.length - 1] || normalized
  }

  const run = async (endpoint: string, label: string) => {
    setLoading(true)
    setError('')
    setMessage('')
    const name = extractRunDirName(runDir)
    if (!name) { setError('Enter the run directory name first'); setLoading(false); return }
    localStorage.setItem('latest_run_dir', name)
    setRunDir(name)
    const fd = new FormData()
    fd.append('run_dir', name)
    const result = await apiRequest<any>(endpoint, { method: 'POST', body: fd }, token)
    setLoading(false)
    if (!result.success) { setError(result.error || `${label} failed`); return }
    setMessage(`${label} created successfully for: ${name}`)
  }

  const download = (filename: string) => {
    const name = extractRunDirName(runDir)
    if (!name) { setError('Enter the run directory name first'); return }
    window.open(`${API_BASE}/api/files/${encodeURIComponent(name)}/${encodeURIComponent(filename)}`, '_blank')
  }

  return (
    <section>
      <div style={{ marginBottom: 24 }}>
        <h1>Generate Reports</h1>
        <p className="muted" style={{ fontSize: 13, margin: 0 }}>
          After IP lookup is complete, generate master files and download reports for your case.
        </p>
      </div>

      {/* Workflow reminder */}
      <div style={{
        display: 'flex', gap: 0, marginBottom: 24, overflowX: 'auto',
      }}>
        {[
          { n: '1', label: 'Upload IPDR',  done: true,  link: '/upload' },
          { n: '2', label: 'IP Lookup',    done: true,  link: '/ip-lookup' },
          { n: '3', label: 'Generate Reports', done: false, link: null },
          { n: '4', label: 'ISP Letters',  done: false, link: '/isp-letters' },
        ].map((step, i) => (
          <div key={step.n} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '8px 14px',
              background: step.done ? 'rgba(0,229,255,0.06)' : !step.link ? 'rgba(0,229,255,0.12)' : 'transparent',
              border: `1px solid ${step.link === null ? 'rgba(0,229,255,0.4)' : step.done ? 'rgba(0,229,255,0.15)' : 'var(--border)'}`,
              borderRadius: 8,
              opacity: step.done ? 0.6 : 1,
            }}>
              <span style={{
                width: 20, height: 20, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: step.link === null ? 'var(--cyan)' : step.done ? 'rgba(0,229,255,0.2)' : 'rgba(255,255,255,0.05)',
                color: step.link === null ? '#000' : 'var(--cyan)',
                fontSize: 10, fontWeight: 700,
              }}>{step.n}</span>
              <span style={{ fontSize: 12, color: step.link === null ? 'var(--text-bright)' : 'var(--muted)', whiteSpace: 'nowrap' }}>
                {step.label}
              </span>
            </div>
            {i < 3 && <div style={{ width: 24, height: 1, background: 'var(--border)', flexShrink: 0 }} />}
          </div>
        ))}
      </div>

      <div className="card form-card">
        <div style={{ marginBottom: 16 }}>
          <label>Run Directory</label>
          <input
            value={runDir}
            onChange={e => setRunDir(e.target.value)}
            placeholder="e.g. 20260430_061822_FIR201"
            style={{ fontFamily: 'JetBrains Mono, monospace' }}
          />
          {savedRunDir && runDir !== savedRunDir && (
            <button
              type="button"
              className="btn btn-ghost"
              style={{ fontSize: 11, padding: '4px 10px', marginTop: 6 }}
              onClick={() => setRunDir(savedRunDir)}
            >
              ↩ Use last: {savedRunDir}
            </button>
          )}
          <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 6 }}>
            This is the folder name created after uploading your IPDR file. Check the Upload page if unsure.
          </div>
        </div>

        <div style={{ display: 'grid', gap: 10 }}>
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10,
            padding: '14px', background: 'rgba(0,229,255,0.03)', borderRadius: 8, border: '1px solid var(--border)',
          }}>
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-bright)', marginBottom: 4 }}>Master File</div>
              <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 10 }}>
                Combined CSV of all IP records with ISP and geo data.
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-primary" style={{ fontSize: 12 }} disabled={loading}
                  onClick={() => run('/api/merge-master-file', 'Master file')}>
                  {loading ? 'Working…' : 'Create'}
                </button>
                <button className="btn btn-ghost" style={{ fontSize: 12 }} disabled={loading}
                  onClick={() => download('Master file.csv')}>
                  Download
                </button>
              </div>
            </div>

            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-bright)', marginBottom: 4 }}>Fully Fixed File</div>
              <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 10 }}>
                Cleaned and corrected version, ready for court submission.
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn" style={{ fontSize: 12 }} disabled={loading}
                  onClick={() => run('/api/fix-to-start', 'Fully fixed file')}>
                  {loading ? 'Working…' : 'Create'}
                </button>
                <button className="btn btn-ghost" style={{ fontSize: 12 }} disabled={loading}
                  onClick={() => download('fully_fixed.csv')}>
                  Download
                </button>
              </div>
            </div>
          </div>
        </div>

        {error   && <div className="alert error"   style={{ marginTop: 12 }}>{error}</div>}
        {message && <div className="alert success" style={{ marginTop: 12 }}>{message}</div>}
      </div>
    </section>
  )
}
