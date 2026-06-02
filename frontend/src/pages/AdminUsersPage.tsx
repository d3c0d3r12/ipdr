import { useCallback, useEffect, useState } from 'react'
import { apiRequest } from '../lib/api'
import { useAuth } from '../lib/auth'

type AdminUser = {
  id: string
  username: string
  email: string
  full_name?: string
  role: string
  department?: string
  badge_number?: string
  designation?: string
  phone_number?: string
  is_active: boolean
  is_approved: boolean
  created_at?: string
  approved_at?: string
  last_login?: string
}

type Filter = 'pending' | 'approved' | 'all'

function fmt(d?: string) {
  if (!d) return '—'
  const date = new Date(d)
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString()
}

export default function AdminUsersPage() {
  const { token } = useAuth()
  const [filter, setFilter] = useState<Filter>('pending')
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busyId, setBusyId] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    const qs = filter === 'all' ? '' : `?user_status=${filter}`
    const res = await apiRequest<{ success: boolean; users: AdminUser[] }>(
      `/api/auth/admin/users${qs}`,
      { method: 'GET' },
      token,
    )
    if (!res.success || !res.data?.users) {
      setError(res.error || 'Failed to load users')
      setUsers([])
    } else {
      setUsers(res.data.users)
    }
    setLoading(false)
  }, [filter, token])

  useEffect(() => { load() }, [load])

  const approve = async (u: AdminUser) => {
    setBusyId(u.id)
    setNotice('')
    const res = await apiRequest<{ success: boolean; message: string }>(
      `/api/auth/admin/users/${u.id}/approve`,
      { method: 'POST' },
      token,
    )
    setBusyId(null)
    if (res.success) {
      setNotice(`Approved ${u.username}.`)
      load()
    } else {
      setError(res.error || 'Failed to approve user')
    }
  }

  const reject = async (u: AdminUser) => {
    if (!window.confirm(`Reject and permanently remove "${u.username}"? This cannot be undone.`)) return
    setBusyId(u.id)
    setNotice('')
    const res = await apiRequest<{ success: boolean; message: string }>(
      `/api/auth/admin/users/${u.id}/reject`,
      { method: 'POST' },
      token,
    )
    setBusyId(null)
    if (res.success) {
      setNotice(`Rejected ${u.username}.`)
      load()
    } else {
      setError(res.error || 'Failed to reject user')
    }
  }

  const tabs: { key: Filter; label: string }[] = [
    { key: 'pending', label: 'Pending Approval' },
    { key: 'approved', label: 'Approved' },
    { key: 'all', label: 'All Users' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {tabs.map(t => (
          <button
            key={t.key}
            className={`btn ${filter === t.key ? '' : 'btn-ghost'}`}
            onClick={() => setFilter(t.key)}
          >
            {t.label}
          </button>
        ))}
        <button className="btn btn-ghost" onClick={() => load()} style={{ marginLeft: 'auto' }}>
          Refresh
        </button>
      </div>

      {notice && <div className="badge info" style={{ padding: '8px 12px' }}>{notice}</div>}
      {error && <div className="badge warning" style={{ padding: '8px 12px' }}>{error}</div>}

      <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ textAlign: 'left', color: 'var(--muted)' }}>
              <th style={{ padding: '12px 14px' }}>User</th>
              <th style={{ padding: '12px 14px' }}>Email</th>
              <th style={{ padding: '12px 14px' }}>Role</th>
              <th style={{ padding: '12px 14px' }}>Status</th>
              <th style={{ padding: '12px 14px' }}>Registered</th>
              <th style={{ padding: '12px 14px', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={6} style={{ padding: 20, textAlign: 'center', color: 'var(--muted)' }}>Loading…</td></tr>
            )}
            {!loading && users.length === 0 && (
              <tr><td colSpan={6} style={{ padding: 20, textAlign: 'center', color: 'var(--muted)' }}>
                {filter === 'pending' ? 'No users awaiting approval.' : 'No users found.'}
              </td></tr>
            )}
            {!loading && users.map(u => (
              <tr key={u.id} style={{ borderTop: '1px solid var(--border)' }}>
                <td style={{ padding: '12px 14px' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-bright)' }}>{u.full_name || u.username}</div>
                  <div style={{ color: 'var(--muted)', fontSize: 11 }}>@{u.username}{u.badge_number ? ` · ${u.badge_number}` : ''}</div>
                </td>
                <td style={{ padding: '12px 14px' }}>{u.email}</td>
                <td style={{ padding: '12px 14px' }}>
                  <span className="badge neutral">{u.role?.replace(/_/g, ' ')}</span>
                </td>
                <td style={{ padding: '12px 14px' }}>
                  {u.is_approved
                    ? <span className="badge info">Approved</span>
                    : <span className="badge warning">Pending</span>}
                </td>
                <td style={{ padding: '12px 14px', color: 'var(--muted)' }}>{fmt(u.created_at)}</td>
                <td style={{ padding: '12px 14px', textAlign: 'right', whiteSpace: 'nowrap' }}>
                  {!u.is_approved ? (
                    <>
                      <button
                        className="btn"
                        disabled={busyId === u.id}
                        onClick={() => approve(u)}
                        style={{ marginRight: 6 }}
                      >
                        {busyId === u.id ? '…' : 'Approve'}
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={busyId === u.id}
                        onClick={() => reject(u)}
                      >
                        Reject
                      </button>
                    </>
                  ) : (
                    <span style={{ color: 'var(--muted)', fontSize: 12 }}>—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
