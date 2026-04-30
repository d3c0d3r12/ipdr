import { useEffect, useMemo, useState } from 'react'
import { apiRequest } from '../lib/api'
import { useAuth } from '../lib/auth'

type RecordRow = { country?: string; city?: string; ip?: string }

export default function MapPage() {
  const { token } = useAuth()
  const [rows, setRows] = useState<RecordRow[]>([])

  useEffect(() => {
    apiRequest<{ records: RecordRow[] }>('/api/data/?limit=500', {}, token).then((res) => {
      if (res.success) setRows(res.data?.records || [])
    })
  }, [token])

  const grouped = useMemo(() => {
    const map = new Map<string, number>()
    rows.forEach((r) => {
      const key = `${r.country || 'Unknown'} / ${r.city || 'Unknown'}`
      map.set(key, (map.get(key) || 0) + 1)
    })
    return [...map.entries()].sort((a, b) => b[1] - a[1])
  }, [rows])

  return (
    <section>
      <h1>Geo Heat Overview</h1>
      <div className="card">
        <p className="muted">Geographic clusters from processed IP intelligence.</p>
        <ul className="list">
          {grouped.map(([loc, count]) => (
            <li key={loc}><span>{loc}</span><strong>{count}</strong></li>
          ))}
        </ul>
      </div>
    </section>
  )
}
