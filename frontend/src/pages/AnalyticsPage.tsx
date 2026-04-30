import { useEffect, useMemo, useState } from 'react'
import { apiRequest } from '../lib/api'
import { useAuth } from '../lib/auth'

type RecordRow = { country?: string; isp?: string }

export default function AnalyticsPage() {
  const { token } = useAuth()
  const [summary, setSummary] = useState({ total: 0, countries: 0, cities: 0, suspicious: 0 })
  const [rows, setRows] = useState<RecordRow[]>([])

  useEffect(() => {
    const load = async () => {
      const [a, b] = await Promise.all([
        apiRequest<any>('/api/data/summary', {}, token),
        apiRequest<{ records: RecordRow[] }>('/api/data/?limit=500', {}, token)
      ])
      if (a.success) setSummary(a.data)
      if (b.success) setRows(b.data?.records || [])
    }
    load()
  }, [token])

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
      <h1>Analytics</h1>
      <p className="muted">Distribution view of records by geography and ISP intelligence.</p>

      <div className="grid-3">
        <div className="card metric"><strong>{summary.total}</strong><span>Total Records</span></div>
        <div className="card metric"><strong>{summary.countries}</strong><span>Countries</span></div>
        <div className="card metric"><strong>{summary.cities}</strong><span>Cities</span></div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h2>Top Countries</h2>
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
        </div>

        <div className="card">
          <h2>Top ISPs</h2>
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
        </div>
      </div>
    </section>
  )
}
