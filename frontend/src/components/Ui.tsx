import { ReactNode } from 'react'
import { Link } from 'react-router-dom'

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'success' | 'warning' | 'danger' | 'info' }) {
  return <span className={`badge ${tone}`}>{children}</span>
}

export function EmptyState({
  title,
  description,
  primaryCta,
  secondaryCta
}: {
  title: string
  description: string
  primaryCta: { label: string; to: string }
  secondaryCta?: { label: string; to: string }
}) {
  return (
    <div className="empty">
      <div className="empty-icon" aria-hidden="true">◎</div>
      <div className="empty-body">
        <div className="empty-title">{title}</div>
        <div className="empty-desc">{description}</div>
        <div className="row-gap" style={{ marginTop: 12 }}>
          <Link className="btn btn-primary" to={primaryCta.to}>{primaryCta.label}</Link>
          {secondaryCta && <Link className="btn btn-ghost" to={secondaryCta.to}>{secondaryCta.label}</Link>}
        </div>
      </div>
    </div>
  )
}
