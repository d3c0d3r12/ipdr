import { useEffect, useMemo, useState } from 'react'
import { apiRequest } from '../lib/api'
import { useAuth } from '../lib/auth'
import Pagination from '../components/Pagination'

type RecordRow = {
  id?: number
  timestamp?: string
  ip?: string
  country?: string
  region?: string
  city?: string
  isp?: string
}

const PAGE_SIZE_OPTIONS = [25, 50, 100]

export default function IpListPage() {
  const { token } = useAuth()
  const [rows, setRows] = useState<RecordRow[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)

  useEffect(() => {
    const load = async () => {
      const result = await apiRequest<{ records: RecordRow[] }>('/api/data/?limit=5000', {}, token)
      if (result.success) setRows(result.data?.records || [])
      setLoading(false)
    }
    load()
  }, [token])

  // Reset to page 1 on search change
  useEffect(() => { setPage(1) }, [search])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return rows
    return rows.filter(r =>
      [r.ip, r.country, r.region, r.city, r.isp].some(v => v?.toLowerCase().includes(q))
    )
  }, [rows, search])

  const paginated = useMemo(
    () => filtered.slice((page - 1) * pageSize, page * pageSize),
    [filtered, page, pageSize]
  )

  return (
    <section>
      {/* Header */}
      <div style={{ marginBottom: 22, display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1>IP Records</h1>
          <p className="muted" style={{ fontSize: 13, margin: 0 }}>
            All enriched IP records across FIR cases
          </p>
        </div>
        {!loading && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px',
            borderRadius: 8, border: '1px solid var(--border)', background: 'rgba(0,229,255,0.04)',
          }}>
            <span style={{ fontSize: 11, color: 'var(--muted)' }}>Total</span>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 14, color: 'var(--cyan)', fontWeight: 700 }}>
              {rows.length.toLocaleString()}
            </span>
          </div>
        )}
      </div>

      <div className="card">
        {/* Search bar */}
        <div style={{ marginBottom: 16, display: 'flex', gap: 10, alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: 380 }}>
            <svg
              width="14" height="14" viewBox="0 0 24 24" fill="none"
              style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--muted)', pointerEvents: 'none' }}
            >
              <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2" />
              <path d="m21 21-4.35-4.35" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search IP, country, city, ISP…"
              style={{ paddingLeft: 32, margin: 0 }}
            />
          </div>
          {search && (
            <button className="btn btn-ghost" onClick={() => setSearch('')} style={{ fontSize: 12 }}>
              Clear
            </button>
          )}
          {search && filtered.length !== rows.length && (
            <span style={{ fontSize: 12, color: 'var(--muted)' }}>
              {filtered.length.toLocaleString()} match{filtered.length !== 1 ? 'es' : ''}
            </span>
          )}
        </div>

        {loading ? (
          <div style={{ display: 'grid', gap: 8 }}>
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="skeleton" style={{ height: 38, borderRadius: 8 }} />
            ))}
          </div>
        ) : rows.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M6 6h14M6 12h14M6 18h14M3 6h.01M3 12h.01M3 18h.01" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </div>
            <div className="empty-body">
              <div className="empty-title">No IP records found</div>
              <div className="empty-desc">Upload and process an IPDR HTML file to populate this list.</div>
            </div>
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--muted)', fontSize: 13 }}>
            No records match "<span style={{ color: 'var(--text)' }}>{search}</span>"
          </div>
        ) : (
          <>
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>IP Address</th>
                    <th>Country</th>
                    <th>Region</th>
                    <th>City</th>
                    <th>ISP</th>
                  </tr>
                </thead>
                <tbody>
                  {paginated.map((r, i) => (
                    <tr key={`${r.ip}-${(page - 1) * pageSize + i}`}>
                      <td style={{ color: 'var(--muted)', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }}>
                        {(page - 1) * pageSize + i + 1}
                      </td>
                      <td>
                        <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: 'var(--cyan)' }}>
                          {r.ip || '—'}
                        </span>
                      </td>
                      <td>{r.country || '—'}</td>
                      <td>{r.region || '—'}</td>
                      <td>{r.city || '—'}</td>
                      <td style={{ color: 'var(--muted)', fontSize: 12 }}>{r.isp || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <Pagination
              page={page}
              total={filtered.length}
              pageSize={pageSize}
              onPage={setPage}
              pageSizeOptions={PAGE_SIZE_OPTIONS}
              onPageSize={n => { setPageSize(n); setPage(1) }}
            />
          </>
        )}
      </div>
    </section>
  )
}
