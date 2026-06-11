import { NavLink, useNavigate, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { useEffect, useMemo, useRef, useState } from 'react'

type NavItem = {
  to: string
  label: string
  icon: 'dashboard' | 'upload' | 'lookup' | 'list' | 'analytics' | 'map' | 'letters' | 'reports' | 'multi' | 'users'
  section: 'main' | 'investigate' | 'analyze' | 'reports' | 'admin'
  adminOnly?: boolean
}

const navItems: NavItem[] = [
  { to: '/dashboard',        label: 'Dashboard',    icon: 'dashboard',  section: 'main' },
  { to: '/upload',           label: 'New Case',     icon: 'upload',     section: 'investigate' },
  { to: '/ip-lookup',        label: 'IP Lookup',    icon: 'lookup',     section: 'investigate' },
  { to: '/ip-list',          label: 'IP Records',   icon: 'list',       section: 'investigate' },
  { to: '/analytics',        label: 'Analytics',    icon: 'analytics',  section: 'analyze' },
  { to: '/map',              label: 'Geo Map',      icon: 'map',        section: 'analyze' },
  { to: '/isp-letters',      label: 'ISP Letters',  icon: 'letters',    section: 'reports' },
  { to: '/isp-letters/templates', label: 'Letter Templates', icon: 'reports', section: 'reports' },
  { to: '/admin/users',      label: 'User Approvals', icon: 'users',    section: 'admin', adminOnly: true },
]

const SECTION_LABELS: Record<NavItem['section'], string> = {
  main:        'Overview',
  investigate: 'Investigation',
  analyze:     'Analysis',
  reports:     'Reports',
  admin:       'Administration',
}

function Icon({ name }: { name: NavItem['icon'] }) {
  const paths: Record<NavItem['icon'], string> = {
    dashboard: 'M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z',
    upload:    'M12 3v10m0-10 4 4m-4-4-4 4M4 17v2h16v-2',
    multi:     'M4 4h6v6H4V4zm10 0h6v6h-6V4zM4 14h6v6H4v-6zm10 3h2m2 0h2m-3-3v2m0 2v2',
    lookup:    'M10 18a8 8 0 1 1 5.29-14.01A8 8 0 0 1 10 18Zm8 2-3-3',
    list:      'M6 6h14M6 12h14M6 18h14M3 6h.01M3 12h.01M3 18h.01',
    analytics: 'M4 19V5m0 14h16M8 17V9m4 8V7m4 10v-6',
    map:       'M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2V6Z',
    letters:   'M4 4h16v16H4V4Zm0 3 8 6 8-6',
    reports:   'M7 3h8l4 4v14H7V3Zm8 0v4h4M10 12h6m-6 4h4',
    users:     'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm13 10v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75',
  }
  return (
    <svg className="nav-ico" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d={paths[name] ?? ''} stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function pageTitleFor(pathname: string): string {
  const map: Record<string, string> = {
    '/dashboard':         'Command Center',
    '/upload':            'New Case',
    '/multi-file-upload': 'Multi-File Upload',
    '/ip-lookup':         'IP Lookup',
    '/ip-list':           'IP Records',
    '/analytics':         'Analytics',
    '/map':               'Geo Intelligence',
    '/report-creation':   'Generate Reports',
    '/isp-letters':       'ISP Letters',
    '/isp-letters/templates': 'Letter Templates',
    '/admin/users':       'User Approvals',
    '/profile':           'Profile',
    '/settings':          'Settings',
  }
  if (pathname.startsWith('/fir/')) return 'FIR Details'
  return map[pathname] ?? 'IPDR Hub'
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement | null>(null)

  // Group nav items by section (admin-only items are hidden for non-admins)
  const isAdmin = user?.role === 'admin'
  const sections = useMemo(() => {
    const groups: Partial<Record<NavItem['section'], NavItem[]>> = {}
    for (const item of navItems) {
      if (item.adminOnly && !isAdmin) continue
      if (!groups[item.section]) groups[item.section] = []
      groups[item.section]!.push(item)
    }
    return groups
  }, [isAdmin])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  // Close dropdown on outside click
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (!menuRef.current?.contains(e.target as Node)) setMenuOpen(false)
    }
    window.addEventListener('click', onClick)
    return () => window.removeEventListener('click', onClick)
  }, [])

  const initials = (user?.full_name || user?.username || 'U')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map(x => x[0]?.toUpperCase())
    .join('')

  const pageTitle = pageTitleFor(location.pathname)

  return (
    <div className="app-shell">
      {/* ── SIDEBAR ── */}
      <aside className={`sidebar${sidebarOpen ? ' open' : ''}`}>
        {/* Logo */}
        <div className="sidebar-logo">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <img
              src="/Delhi_Police_Logo-1.png"
              alt="Delhi Police"
              style={{
                width: 44, height: 44,
                objectFit: 'contain',
                flexShrink: 0,
              }}
            />
            <div className="brand">
              <span className="brand-name">IPDR HUB</span>
              <span className="brand-sub">Delhi Police · Special Cell</span>
            </div>
          </div>
          <div style={{
            marginTop: 8,
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: '1.5px',
            textTransform: 'uppercase',
            color: 'var(--cyan)',
            textAlign: 'center',
          }}>
            IFSO Delhi Police
          </div>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          {(Object.keys(SECTION_LABELS) as NavItem['section'][]).map(section => {
            const items = sections[section]
            if (!items) return null
            return (
              <div key={section}>
                <div className="nav-section-label">{SECTION_LABELS[section]}</div>
                {items.map(item => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) => isActive ? 'active' : ''}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon name={item.icon} />
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </div>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <span className="status-dot" />
            <span style={{ fontSize: 11, color: 'var(--green)', letterSpacing: '0.3px' }}>All Systems Operational</span>
          </div>
          <div style={{
            fontSize: 10, color: 'var(--muted)', letterSpacing: '0.5px', lineHeight: 1.6,
            borderTop: '1px solid var(--border)', paddingTop: 10,
          }}>
            <div>IPDR Intelligence Platform</div>
            <div>© IFSO Delhi Police Special Cell</div>
          </div>
        </div>
      </aside>

      {/* ── APP BODY ── */}
      <div className="app-body">
        {/* Topbar */}
        <header className="app-header">
          <div className="app-header-left">
            {/* Mobile sidebar toggle */}
            <button
              className="btn btn-ghost"
              style={{ display: 'none', padding: '6px 8px' }}
              onClick={() => setSidebarOpen(v => !v)}
              aria-label="Toggle menu"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span className="status-live">
                <span className="status-dot" />
                LIVE
              </span>
              <span style={{
                fontFamily: 'Orbitron, monospace',
                fontSize: 13,
                fontWeight: 700,
                color: 'var(--text-bright)',
                letterSpacing: '0.8px',
              }}>
                {pageTitle}
              </span>
            </div>
          </div>

          {/* Right: user menu */}
          <div className="user-area">
            <div className="user-menu" ref={menuRef}>
              <button className="user-chip" type="button" onClick={() => setMenuOpen(v => !v)}>
                <span className="avatar">{initials}</span>
                <span className="user-meta">
                  <span className="user-name">{user?.full_name || user?.username}</span>
                  <span className="role-badge">{user?.role?.replace(/_/g, ' ') ?? 'Officer'}</span>
                </span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" style={{ color: 'var(--muted)', marginLeft: 2 }}>
                  <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </button>

              {menuOpen && (
                <div className="dropdown">
                  <Link to="/profile"  className="dropdown-item" onClick={() => setMenuOpen(false)}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ marginRight: 8 }}>
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                    Profile
                  </Link>
                  <Link to="/settings" className="dropdown-item" onClick={() => setMenuOpen(false)}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ marginRight: 8 }}>
                      <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" stroke="currentColor" strokeWidth="2" />
                      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z" stroke="currentColor" strokeWidth="2" />
                    </svg>
                    Settings
                  </Link>
                  <hr style={{ margin: '4px 0', border: 'none', borderTop: '1px solid var(--border)' }} />
                  <button className="dropdown-item danger" onClick={handleLogout}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ marginRight: 8 }}>
                      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="main-content">{children}</main>
      </div>
    </div>
  )
}
