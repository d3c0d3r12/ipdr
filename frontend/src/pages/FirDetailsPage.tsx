import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { apiRequest } from '../lib/api'
import { useAuth } from '../lib/auth'

type Stats = {
  total_ip_lookups?: number
  unique_ips?: number
  unique_countries?: number
  unique_cities?: number
  top_isps?: Array<{ isp: string; count: number }>
}

type LookupRow = {
  ip_address?: string
  country?: string
  city?: string
  isp?: string
  lookup_status?: string
}

export default function FirDetailsPage() {
  const { token } = useAuth()
  const { firNumber = '' } = useParams()
  const [stats, setStats] = useState<Stats>({})
  const [rows, setRows] = useState<LookupRow[]>([])

  useEffect(() => {
    const fir = decodeURIComponent(firNumber)
    Promise.all([
      apiRequest<Stats>(`/api/fir/${encodeURIComponent(fir)}/statistics`, {}, token),
      apiRequest<{ ip_lookups: LookupRow[] }>(`/api/fir/${encodeURIComponent(fir)}/ip-lookups?limit=200`, {}, token)
    ]).then(([a, b]) => {
      if (a.success && a.data) setStats(a.data)
      if (b.success) setRows(b.data?.ip_lookups || [])
    })
  }, [firNumber, token])

  return (
    <section>
      <h1>FIR Details: {decodeURIComponent(firNumber)}</h1>
      <div className="grid-3">
        <div className="card metric"><strong>{stats.total_ip_lookups || 0}</strong><span>Total Lookups</span></div>
        <div className="card metric"><strong>{stats.unique_ips || 0}</strong><span>Unique IPs</span></div>
        <div className="card metric"><strong>{stats.unique_countries || 0}</strong><span>Countries</span></div>
      </div>

      <div className="card">
        <h2>IP Lookup Records</h2>
        <table>
          <thead>
            <tr>
              <th>IP</th>
              <th>Country</th>
              <th>City</th>
              <th>ISP</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={`${r.ip_address}-${i}`}>
                <td>{r.ip_address || '-'}</td>
                <td>{r.country || '-'}</td>
                <td>{r.city || '-'}</td>
                <td>{r.isp || '-'}</td>
                <td>{r.lookup_status || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
