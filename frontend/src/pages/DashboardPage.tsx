import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiRequest } from '../lib/api'
import { useAuth } from '../lib/auth'
import Pagination from '../components/Pagination'

type FirCase = {
  fir_number: string
  case_title: string
  status?: string
  priority?: string
  total_ips?: number
  created_at?: string
}

type Summary = { total: number; countries: number; cities: number }

const STATUS_COLORS: Record<string, string> = {
  active:   'var(--cyan)',
  closed:   'var(--muted)',
  pending:  'var(--orange)',
  unknown:  'var(--muted)',
}

const PRIORITY_COLORS: Record<string, string> = {
  high:     'var(--red)',
  critical: 'var(--red)',
  medium:   'var(--orange)',
  low:      'var(--green)',
  unknown:  'var(--muted)',
}

function StatusBadge({ status }: { status?: string }) {
  const s = (status || 'unknown').toLowerCase()
  const tone = s === 'active' ? 'info' : s === 'closed' ? 'neutral' : s === 'pending' ? 'warning' : 'neutral'
  return <span className={`badge ${tone}`}>{status || '—'}</span>
}

function PriorityBadge({ priority }: { priority?: string }) {
  const p = (priority || 'unknown').toLowerCase()
  const tone = ['high','critical'].includes(p) ? 'danger' : p === 'medium' ? 'warning' : p === 'low' ? 'success' : 'neutral'
  return <span className={`badge ${tone}`}>{priority || '—'}</span>
}

function StatCard({
  label, value, icon, color = 'var(--cyan)', sub,
}: { label: string; value: number | string; icon: React.ReactNode; color?: string; sub?: string }) {
  return (
    <div className="stat-card">
      <div className="stat-head">
        <div className="stat-ico" style={{ background: `${color}15`, borderColor: `${color}30`, color }}>
          {icon}
        </div>
      </div>
      <div>
        <div className="stat-value" style={{ color }}>{value}</div>
        <div className="stat-label">{label}</div>
        {sub && <div style={{ fontSize: 10, color: 'var(--muted)', marginTop: 3 }}>{sub}</div>}
      </div>
    </div>
  )
}

function BarGroup({
  title, data, colorFn,
}: { title: string; data: [string, number][]; colorFn: (k: string) => string }) {
  const max = Math.max(...data.map(([, v]) => v), 1)
  return (
    <div className="card" style={{ marginBottom: 0 }}>
      <h2>{title}</h2>
      {data.length === 0 ? (
        <p className="muted" style={{ fontSize: 13 }}>No data yet.</p>
      ) : (
        <div className="bars">
          {data.map(([key, count]) => (
            <div className="bar-row" key={key}>
              <div className="bar-label" style={{ textTransform: 'capitalize' }}>{key}</div>
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{
                    width: `${(count / max) * 100}%`,
                    background: `linear-gradient(90deg, ${colorFn(key)}, ${colorFn(key)}88)`,
                  }}
                />
              </div>
              <div className="bar-value">{count}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function DashboardPage() {
  const { token, user } = useAuth()
  const [cases, setCases] = useState<FirCase[]>([])
  const [summary, setSummary] = useState<Summary>({ total: 0, countries: 0, cities: 0 })
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 10

  const paginated = useMemo(
    () => cases.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [cases, page]
  )

  const statusCount = cases.reduce<Record<string, number>>((acc, item) => {
    const k = (item.status || 'unknown').toLowerCase()
    acc[k] = (acc[k] || 0) + 1
    return acc
  }, {})

  const priorityCount = cases.reduce<Record<string, number>>((acc, item) => {
    const k = (item.priority || 'unknown').toLowerCase()
    acc[k] = (acc[k] || 0) + 1
    return acc
  }, {})

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      const [firRes, sumRes] = await Promise.all([
        apiRequest<{ cases: FirCase[] }>('/api/fir/', {}, token),
        apiRequest<Summary>('/api/data/summary', {}, token),
      ])
      if (firRes.success) setCases(firRes.data?.cases ?? [])
      if (sumRes.success && sumRes.data) setSummary(sumRes.data)
      setLoading(false)
    }
    load()
  }, [token])

  const now = new Date().toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: true,
  })

  return (
    <section>
      {/* ── PAGE HEADER ── */}
      <div style={{ marginBottom: 22, display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1>Command Center</h1>
          <p className="muted" style={{ fontSize: 12, margin: 0, letterSpacing: '0.4px' }}>
            Welcome back, <span style={{ color: 'var(--cyan)' }}>{user?.full_name || user?.username}</span>
            &nbsp;·&nbsp;{now}
          </p>
        </div>
        <Link to="/upload" className="btn btn-primary">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          New Case
        </Link>
      </div>

      {/* ── WORKFLOW GUIDE ── */}
      <div style={{
        display: 'flex', gap: 0, marginBottom: 20, overflowX: 'auto', paddingBottom: 4,
      }}>
        {[
          { n: '1', label: 'Upload IPDR',       sub: 'New Case',         to: '/upload' },
          { n: '2', label: 'IP Lookup',          sub: 'Enrich IPs',      to: '/ip-lookup' },
          { n: '3', label: 'Generate Reports',   sub: 'Master File',     to: '/report-creation' },
          { n: '4', label: 'ISP Letters',        sub: 'Send to ISPs',    to: '/isp-letters' },
        ].map((step, i) => (
          <div key={step.n} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
            <a href={step.to} style={{
              display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none',
              padding: '10px 16px',
              background: 'rgba(0,229,255,0.03)',
              border: '1px solid var(--border)',
              borderRadius: 8, transition: 'border-color 0.15s',
            }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(0,229,255,0.35)')}
              onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
            >
              <span style={{
                width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: 'rgba(0,229,255,0.1)', border: '1px solid rgba(0,229,255,0.25)',
                color: 'var(--cyan)', fontSize: 11, fontWeight: 700,
              }}>{step.n}</span>
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-bright)', lineHeight: 1.2 }}>{step.label}</div>
                <div style={{ fontSize: 10, color: 'var(--muted)' }}>{step.sub}</div>
              </div>
            </a>
            {i < 3 && (
              <svg width="20" height="10" viewBox="0 0 20 10" fill="none" style={{ flexShrink: 0 }}>
                <path d="M0 5h18M14 1l4 4-4 4" stroke="var(--border)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
          </div>
        ))}
      </div>

      {/* ── STAT CARDS ── */}
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <StatCard
          label="FIR Cases"
          value={loading ? '—' : cases.length}
          color="var(--cyan)"
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M7 3h8l4 4v14H7V3Zm8 0v4h4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          }
        />
        <StatCard
          label="Total IP Records"
          value={loading ? '—' : summary.total.toLocaleString()}
          color="var(--purple)"
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <rect x="2" y="2" width="20" height="20" rx="2" stroke="currentColor" strokeWidth="1.8" />
              <path d="M8 12h8M12 8v8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          }
        />
        <StatCard
          label="Countries"
          value={loading ? '—' : summary.countries}
          color="var(--green)"
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.8" />
              <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" stroke="currentColor" strokeWidth="1.8" />
            </svg>
          }
        />
        <StatCard
          label="Cities Tracked"
          value={loading ? '—' : summary.cities}
          color="var(--orange)"
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9Z" stroke="currentColor" strokeWidth="1.8" />
              <path d="M9 22V12h6v10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          }
        />
      </div>

      {/* ── STATUS + PRIORITY CHARTS ── */}
      <div className="grid-2" style={{ marginBottom: 16 }}>
        <BarGroup
          title="Case Status Distribution"
          data={Object.entries(statusCount).sort(([, a], [, b]) => b - a)}
          colorFn={k => STATUS_COLORS[k] ?? 'var(--muted)'}
        />
        <BarGroup
          title="Priority Distribution"
          data={Object.entries(priorityCount).sort(([, a], [, b]) => b - a)}
          colorFn={k => PRIORITY_COLORS[k] ?? 'var(--muted)'}
        />
      </div>

      {/* ── RECENT FIR CASES TABLE ── */}
      <div className="card">
        <div className="section-head">
          <h2 style={{ margin: 0 }}>
            <span style={{ color: 'var(--cyan)', marginRight: 8 }}>▶</span>
            Recent FIR Cases
          </h2>
        </div>

        {loading ? (
          <div style={{ display: 'grid', gap: 8 }}>
            {[1,2,3].map(i => (
              <div key={i} className="skeleton" style={{ height: 40, borderRadius: 8 }} />
            ))}
          </div>
        ) : cases.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M7 3h8l4 4v14H7V3Zm8 0v4h4M10 12h6m-6 4h4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </div>
            <div className="empty-body">
              <div className="empty-title">No FIR cases yet</div>
              <div className="empty-desc">Start a new case by uploading an IPDR file.</div>
              <div style={{ marginTop: 12 }}>
                <Link to="/upload" className="btn btn-primary">Start New Case</Link>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>FIR Number</th>
                  <th>Case Title</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>IP Records</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {paginated.map(row => (
                  <tr key={row.fir_number}>
                    <td>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: 'var(--cyan)' }}>
                        {row.fir_number}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-bright)', maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {row.case_title}
                    </td>
                    <td><StatusBadge   status={row.status} /></td>
                    <td><PriorityBadge priority={row.priority} /></td>
                    <td>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>
                        {row.total_ips ?? '—'}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <Link
                        to={`/fir/${encodeURIComponent(row.fir_number)}`}
                        className="btn"
                        style={{ fontSize: 11, padding: '4px 10px' }}
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          <Pagination
            page={page}
            total={cases.length}
            pageSize={PAGE_SIZE}
            onPage={setPage}
          />
          </div>
        )}
      </div>

      {/* ── INFO FOOTER ── */}
      <div style={{
        display: 'flex', gap: 16, flexWrap: 'wrap',
        padding: '10px 14px',
        border: '1px solid var(--border)',
        borderRadius: 10,
        background: 'rgba(0,229,255,0.02)',
        fontSize: 11, color: 'var(--muted)',
      }}>
        <span>
          <span style={{ color: 'var(--green)', marginRight: 6 }}>●</span>
          System Operational
        </span>
        <span>Delhi Police Cyber Cell · IPDR Intelligence Platform</span>
        <span style={{ marginLeft: 'auto' }}>
          Total Records:{' '}
          <span style={{ color: 'var(--cyan)', fontFamily: 'JetBrains Mono, monospace' }}>
            {summary.total.toLocaleString()}
          </span>
        </span>
      </div>
    </section>
  )
}
