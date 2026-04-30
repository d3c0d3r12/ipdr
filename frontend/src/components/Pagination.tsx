type Props = {
  page: number          // 1-based
  total: number         // total row count
  pageSize: number
  onPage: (p: number) => void
  pageSizeOptions?: number[]
  onPageSize?: (n: number) => void
}

export default function Pagination({ page, total, pageSize, onPage, pageSizeOptions, onPageSize }: Props) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1
  const to   = Math.min(page * pageSize, total)

  // Build page window: always show first, last, current ±2
  const pages: (number | '…')[] = []
  const addPage = (n: number) => { if (!pages.includes(n)) pages.push(n) }
  addPage(1)
  for (let i = Math.max(2, page - 2); i <= Math.min(totalPages - 1, page + 2); i++) addPage(i)
  if (totalPages > 1) addPage(totalPages)

  const withEllipsis: (number | '…')[] = []
  let prev = 0
  for (const p of pages as number[]) {
    if (p - prev > 1) withEllipsis.push('…')
    withEllipsis.push(p)
    prev = p
  }

  const btn = (content: React.ReactNode, target: number, disabled: boolean, active = false) => (
    <button
      key={String(content) + target}
      onClick={() => !disabled && onPage(target)}
      disabled={disabled}
      style={{
        minWidth: 32, height: 32, padding: '0 8px',
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        borderRadius: 6, border: `1px solid ${active ? 'rgba(0,229,255,0.5)' : 'var(--border)'}`,
        background: active ? 'rgba(0,229,255,0.1)' : 'transparent',
        color: active ? 'var(--cyan)' : disabled ? 'var(--muted)' : 'var(--text)',
        fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: active ? 700 : 400,
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 150ms',
        opacity: disabled ? 0.4 : 1,
      }}
    >
      {content}
    </button>
  )

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      flexWrap: 'wrap', gap: 10,
      padding: '10px 0 2px',
      borderTop: '1px solid var(--border)',
      marginTop: 8,
    }}>
      {/* Info */}
      <span style={{ fontSize: 12, color: 'var(--muted)', fontFamily: 'JetBrains Mono, monospace' }}>
        {total === 0
          ? 'No records'
          : <>{from}–{to} of <span style={{ color: 'var(--text)' }}>{total.toLocaleString()}</span></>}
      </span>

      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
        {/* Page size selector */}
        {pageSizeOptions && onPageSize && (
          <select
            value={pageSize}
            onChange={e => { onPageSize(Number(e.target.value)); onPage(1) }}
            style={{
              height: 32, padding: '0 8px', borderRadius: 6,
              border: '1px solid var(--border)', background: 'var(--surface)',
              color: 'var(--text)', fontSize: 12,
              fontFamily: 'JetBrains Mono, monospace', cursor: 'pointer',
            }}
          >
            {pageSizeOptions.map(n => <option key={n} value={n}>{n} / page</option>)}
          </select>
        )}

        {/* Prev */}
        {btn(
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>,
          page - 1, page <= 1
        )}

        {/* Page buttons */}
        {withEllipsis.map((p, i) =>
          p === '…'
            ? <span key={`ellipsis-${i}`} style={{ fontSize: 13, color: 'var(--muted)', padding: '0 2px' }}>…</span>
            : btn(p, p as number, false, p === page)
        )}

        {/* Next */}
        {btn(
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>,
          page + 1, page >= totalPages
        )}
      </div>
    </div>
  )
}
