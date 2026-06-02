import { useEffect, useMemo, useState } from 'react'
import { apiRequest } from '../lib/api'
import { useAuth } from '../lib/auth'

type RecordRow = { country?: string; isp?: string }
type Summary = { total: number; countries: number; cities: number; suspicious: number }

const EMPTY_SUMMARY: Summary = { total: 0, countries: 0, cities: 0, suspicious: 0 }

export default function AnalyticsPage() {
  const { token } = useAuth()
  const [summary, setSummary] = useState<Summary>(EMPTY_SUMMARY)
  const [rows, setRows] = useState<RecordRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    const [a, b] = await Promise.all([
      apiRequest<Partial<Summary>>('/api/data/summary', {}, token),
      apiRequest<{ records: RecordRow[] }>('/api/data/?limit=500', {}, token),
    ])

    if (a.success && a.data) {
      // Merge over defaults so a missing field never renders blank.
      setSummary({ ...EMPTY_SUMMARY, ...a.data })
    }
    if (b.success) {
      setRows(b.data?.records ?? [])
    }

    if (!a.success && !b.success) {
      setError(a.error || b.error || 'Failed to load analytics data')
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [token]) // eslint-disable-line react-hooks/exhaustive-deps

  const topCountries = useMemo(() => {
    const m = new Map<string, number>()
    rows.forEach((r) => {
      const key = r.country || 'Unknown'
      m.set(key, (m.get(key) || 0) + 1)
    })
    return [...m.entries()].sort((x, y) => y[1] - x[1]).slice(0, 8)
  }, [rows])

  const topIsps = useMemo(() => {
    const m = new Map<string, number>()
    rows.forEach((r) => {
      const key = r.isp || 'Unknown ISP'
      m.set(key, (m.get(key) || 0) + 1)
    })
    return [...m.entries()].sort((x, y) => y[1] - x[1]).slice(0, 8)
  }, [rows])

  const maxCountry = Math.max(...topCountries.map((x) => x[1]), 1)
  const maxIsp = Math.max(...topIsps.map((x) => x[1]), 1)

  return (
    <section>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <h1>Analytics</h1>
          <p className="muted">Distribution view of records by geography and ISP intelligence.</p>
        </div>
        <button className="btn btn-ghost" onClick={load} disabled={loading}>
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="badge warning" style={{ padding: '10px 14px', margin: '8px 0' }}>
          {error} — is the backend running on port 8000?
        </div>
      )}

      <div className="grid-3">
        <div className="card metric"><strong>{loading ? '…' : summary.total.toLocaleString()}</strong><span>Total Records</span></div>
        <div className="card metric"><strong>{loading ? '…' : summary.countries.toLocaleString()}</strong><span>Countries</span></div>
        <div className="card metric"><strong>{loading ? '…' : summary.cities.toLocaleString()}</strong><span>Cities</span></div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h2>Top Countries</h2>
          {!loading && topCountries.length === 0 ? (
            <p className="muted" style={{ fontSize: 13 }}>No records to analyze yet.</p>
          ) : (
            <ul className="list">
              {topCountries.map(([country, count]) => (
                <li key={country}>
                  <div className="bar-wrap">
                    <span>{country}</span>
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width: `${(count / maxCountry) * 100}%` }} />
                    </div>
                  </div>
                  <strong>{count}</strong>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <h2>Top ISPs</h2>
          {!loading && topIsps.length === 0 ? (
            <p className="muted" style={{ fontSize: 13 }}>No records to analyze yet.</p>
          ) : (
            <ul className="list">
              {topIsps.map(([isp, count]) => (
                <li key={isp}>
                  <div className="bar-wrap">
                    <span>{isp}</span>
                    <div className="bar-track">
                      <div className="bar-fill isp" style={{ width: `${(count / maxIsp) * 100}%` }} />
                    </div>
                  </div>
                  <strong>{count}</strong>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  )
}
