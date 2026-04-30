import { FormEvent, useState } from 'react'
import { apiRequest } from '../lib/api'
import { useAuth } from '../lib/auth'

export default function IpLookupPage() {
  const { token } = useAuth()
  const [runDir, setRunDir] = useState(localStorage.getItem('latest_run_dir') || '')
  const [status, setStatus] = useState<string>('')
  const [statusDetails, setStatusDetails] = useState<any>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Single IP lookup state
  const [singleIp, setSingleIp] = useState('')
  const [singleResult, setSingleResult] = useState<any>(null)
  const [singleError, setSingleError] = useState('')
  const [singleLoading, setSingleLoading] = useState(false)

  const lookupSingleIp = async (e: FormEvent) => {
    e.preventDefault()
    const ip = singleIp.trim()
    if (!ip) return
    setSingleLoading(true)
    setSingleError('')
    setSingleResult(null)
    const result = await apiRequest<any>(`/api/lookup/single?ip=${encodeURIComponent(ip)}`, {}, token)
    setSingleLoading(false)
    if (!result.success) {
      setSingleError(result.error || 'Lookup failed')
      return
    }
    setSingleResult(result.data?.data || result.data)
  }

  const normalizeRunDir = (value: string) => {
    const normalized = value.trim().replace(/\\/g, '/')
    const parts = normalized.split('/').filter(Boolean)
    if (parts.length === 0) return ''
    return parts[parts.length - 1]
  }

  const startLookup = async (e: FormEvent) => {
    e.preventDefault()
    const runDirName = normalizeRunDir(runDir)
    if (!runDirName) return

    setRunDir(runDirName)
    localStorage.setItem('latest_run_dir', runDirName)

    setLoading(true)
    setError('')
    setStatusDetails(null)

    const result = await apiRequest<any>(`/api/lookup/start?run_dir=${encodeURIComponent(runDirName)}`, {
      method: 'POST'
    }, token)

    setLoading(false)
    if (!result.success) {
      setError(result.error || 'Failed to start lookup')
      return
    }

    setStatus(result.data?.message || 'Lookup started')
  }

  const checkStatus = async () => {
    const runDirName = normalizeRunDir(runDir)
    if (!runDirName) return

    setRunDir(runDirName)
    localStorage.setItem('latest_run_dir', runDirName)

    setError('')
    const result = await apiRequest<any>(`/api/lookup/status?run_dir=${encodeURIComponent(runDirName)}`, {}, token)
    if (!result.success) {
      setError(result.error || 'Status check failed')
      return
    }

    const d = result.data
    setStatusDetails(d)
    setStatus(`Results: ${d?.results_count || 0}/${d?.total_ips || 0}, Success rate: ${d?.success_rate || 0}%`)
  }

  return (
    <section>
      <h1>IP Lookup Console</h1>

      {/* ── Single IP Check ── */}
      <form className="card form-card" onSubmit={lookupSingleIp} style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ marginTop: 0 }}>Single IP Check</h2>
        <label>IP Address</label>
        <input
          value={singleIp}
          onChange={(e) => setSingleIp(e.target.value)}
          placeholder="e.g. 115.114.5.89"
          required
        />
        <button className="btn btn-primary" disabled={singleLoading}>
          {singleLoading ? 'Looking up…' : 'Lookup IP'}
        </button>
        {singleError && <div className="alert error">{singleError}</div>}
        {singleResult && (
          <div style={{ marginTop: '0.75rem' }}>
            {/* Threat badge row */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
              {singleResult.is_tor ? (
                <span style={{
                  padding: '4px 12px', borderRadius: 6, fontSize: 12, fontWeight: 700,
                  background: 'rgba(255,59,59,0.15)', border: '1px solid rgba(255,59,59,0.5)',
                  color: '#ff6b6b', letterSpacing: '0.3px',
                }}>
                  ⚠ TOR EXIT NODE
                </span>
              ) : singleResult.is_vpn ? (
                <span style={{
                  padding: '4px 12px', borderRadius: 6, fontSize: 12, fontWeight: 700,
                  background: 'rgba(255,165,0,0.12)', border: '1px solid rgba(255,165,0,0.4)',
                  color: '#ffb347', letterSpacing: '0.3px',
                }}>
                  ⚡ VPN / DATACENTER
                </span>
              ) : (
                <span style={{
                  padding: '4px 12px', borderRadius: 6, fontSize: 12, fontWeight: 700,
                  background: 'rgba(0,200,100,0.1)', border: '1px solid rgba(0,200,100,0.35)',
                  color: '#4caf90', letterSpacing: '0.3px',
                }}>
                  ✓ RESIDENTIAL / ISP
                </span>
              )}
              <span style={{
                padding: '4px 12px', borderRadius: 6, fontSize: 12,
                background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border, #333)',
                color: 'var(--muted, #888)',
              }}>
                {singleResult.connection_type || 'Unknown'}
              </span>
            </div>

            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                {[
                  ['IP Address',   singleResult.ip],
                  ['ISP',          singleResult.isp],
                  ['Organization', singleResult.organization],
                  ['Country',      singleResult.country],
                  ['Region',       singleResult.region],
                  ['City',         singleResult.city],
                  ['Timezone',     singleResult.timezone],
                  ['Latitude',     singleResult.latitude],
                  ['Longitude',    singleResult.longitude],
                  ['Postal Code',  singleResult.postal_code],
                  ['Source',       singleResult.source],
                ].map(([label, value]) => (
                  <tr key={label} style={{ borderBottom: '1px solid var(--border, #333)' }}>
                    <td style={{ padding: '6px 12px', fontWeight: 600, opacity: 0.7, width: '38%', fontSize: 12 }}>{label}</td>
                    <td style={{ padding: '6px 12px', fontFamily: label === 'IP Address' ? 'monospace' : undefined, fontSize: 13 }}>{value || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </form>

      {/* ── Bulk Lookup ── */}
      <form className="card form-card" onSubmit={startLookup}>
        <h2 style={{ marginTop: 0 }}>Bulk IP Lookup</h2>
        <p className="muted" style={{ fontSize: 12, marginBottom: 12 }}>
          Run IP lookup for all IPs in a processed case folder.
        </p>
        <label>Run Directory</label>
        <input
          value={runDir}
          onChange={(e) => setRunDir(e.target.value)}
          placeholder="e.g. 20260430_061822_FIR201"
          required
        />

        <div className="row-gap">
          <button className="btn btn-primary" disabled={loading}>
            {loading ? 'Starting...' : 'Start Lookup'}
          </button>
          <button type="button" className="btn" onClick={checkStatus}>Check Status</button>
        </div>

        {error && <div className="alert error">{error}</div>}
        {status && <div className="alert success">{status}</div>}

        {statusDetails && (
          <div className="mini-grid">
            <div className="metric-box">
              <strong>{statusDetails.total_ips || 0}</strong>
              <span>Total IPs</span>
            </div>
            <div className="metric-box">
              <strong>{statusDetails.results_count || 0}</strong>
              <span>Resolved</span>
            </div>
            <div className="metric-box">
              <strong>{statusDetails.success_rate || 0}%</strong>
              <span>Success</span>
            </div>
          </div>
        )}
      </form>
    </section>
  )
}
