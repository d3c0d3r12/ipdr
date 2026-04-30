import { useMemo } from 'react'

export function Sparkline({ values, stroke = 'currentColor' }: { values: number[]; stroke?: string }) {
  const { points, min, max } = useMemo(() => {
    const safe = values.length ? values : [0]
    const mi = Math.min(...safe)
    const ma = Math.max(...safe)
    const span = ma - mi || 1
    const pts = safe
      .map((v, i) => {
        const x = (i / Math.max(1, safe.length - 1)) * 100
        const y = 100 - ((v - mi) / span) * 100
        return `${x.toFixed(2)},${y.toFixed(2)}`
      })
      .join(' ')
    return { points: pts, min: mi, max: ma }
  }, [values])

  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="sparkline" aria-hidden="true">
      <polyline points={points} fill="none" stroke={stroke} strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />
      <title>{`min ${min} max ${max}`}</title>
    </svg>
  )
}

export function DonutChart({
  data,
  size = 140
}: {
  data: { label: string; value: number; color: string }[]
  size?: number
}) {
  const total = data.reduce((a, b) => a + (b.value || 0), 0) || 1
  const r = 44
  const c = 2 * Math.PI * r
  let offset = 0

  return (
    <svg width={size} height={size} viewBox="0 0 120 120" className="donut" role="img" aria-label="Case Status Mix">
      <circle cx="60" cy="60" r={r} fill="none" stroke="var(--border)" strokeWidth="12" />
      {data.map((s) => {
        const dash = (s.value / total) * c
        const seg = (
          <circle
            key={s.label}
            cx="60"
            cy="60"
            r={r}
            fill="none"
            stroke={s.color}
            strokeWidth="12"
            strokeDasharray={`${dash} ${c - dash}`}
            strokeDashoffset={-offset}
            strokeLinecap="butt"
            transform="rotate(-90 60 60)"
          />
        )
        offset += dash
        return seg
      })}
      <circle cx="60" cy="60" r="30" fill="var(--panel)" />
      <text x="60" y="64" textAnchor="middle" fontSize="14" fill="var(--text)" fontWeight={700}>
        {total}
      </text>
      <text x="60" y="78" textAnchor="middle" fontSize="10" fill="var(--muted)">
        cases
      </text>
    </svg>
  )
}

export function BarChart({
  data
}: {
  data: { label: string; value: number; color: string }[]
}) {
  const max = Math.max(...data.map((d) => d.value), 1)
  return (
    <div className="bars" role="img" aria-label="Priority Distribution">
      {data.map((d) => (
        <div key={d.label} className="bar-row">
          <div className="bar-label">{d.label}</div>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${Math.round((d.value / max) * 100)}%`, background: d.color }} />
          </div>
          <div className="bar-value">{d.value}</div>
        </div>
      ))}
    </div>
  )
}

export function TrendPill({ value }: { value: number | null }) {
  if (value === null) return <span className="trend neutral">—</span>
  const sign = value > 0 ? '+' : ''
  const cls = value > 0 ? 'up' : value < 0 ? 'down' : 'neutral'
  return (
    <span className={`trend ${cls}`}>{`${sign}${value.toFixed(0)}%`}</span>
  )
}
