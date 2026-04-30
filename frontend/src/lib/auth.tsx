import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { apiRequest } from './api'

type User = {
  id: number
  username: string
  full_name?: string
  role?: string
  email?: string
}

type AuthContextType = {
  user: User | null
  token: string
  isAuthenticated: boolean
  initializing: boolean
  login: (username: string, password: string, rememberMe?: boolean) => Promise<{ success: boolean; message: string }>
  signup: (payload: Record<string, unknown>) => Promise<{ success: boolean; message: string }>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

const TOKEN_KEY   = 'auth_token'
const USER_KEY    = 'auth_user'
const REFRESH_KEY = 'auth_refresh'
const REMEMBER_KEY = 'auth_remember'

// Refresh 60 seconds before the access token expires
const REFRESH_MARGIN_MS = 60 * 1000

/** Decode JWT payload and return exp as milliseconds timestamp, or null */
function parseJwtExp(token: string): number | null {
  try {
    const b64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(b64))
    return typeof payload.exp === 'number' ? payload.exp * 1000 : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken]   = useState('')
  const [user, setUser]     = useState<User | null>(null)
  const [initializing, setInitializing] = useState(true)
  const timerRef            = useRef<ReturnType<typeof setTimeout> | null>(null)
  // Use a ref so the refresh function always closes over latest state without stale deps
  const refreshFnRef        = useRef<(rt: string) => Promise<void>>()

  const clearTimer = () => {
    if (timerRef.current) { clearTimeout(timerRef.current); timerRef.current = null }
  }

  const clearStoredAuth = () => {
    for (const store of [localStorage, sessionStorage]) {
      store.removeItem(TOKEN_KEY)
      store.removeItem(USER_KEY)
      store.removeItem(REFRESH_KEY)
      store.removeItem(REMEMBER_KEY)
    }
  }

  /** Schedule a silent token refresh just before the access token expires */
  const scheduleRefresh = (accessToken: string, refreshToken: string) => {
    clearTimer()
    if (!refreshToken) return
    const exp = parseJwtExp(accessToken)
    if (!exp) return
    const delay = Math.max(exp - Date.now() - REFRESH_MARGIN_MS, 0)
    timerRef.current = setTimeout(() => refreshFnRef.current?.(refreshToken), delay)
  }

  // Assign to ref on every render so it always captures the freshest scheduleRefresh
  refreshFnRef.current = async (rt: string) => {
    clearTimer()
    const result = await apiRequest<{ access_token: string }>(
      '/api/auth/refresh-token',
      { method: 'POST', body: JSON.stringify({ refresh_token: rt }) }
    )

    if (!result.success || !result.data?.access_token) {
      // Refresh token is also expired/invalid — force logout
      clearStoredAuth()
      setToken('')
      setUser(null)
      return
    }

    const newToken = result.data.access_token
    setToken(newToken)

    // Persist in whichever storage was originally used
    const persistent = !!localStorage.getItem(REMEMBER_KEY)
    const store = persistent ? localStorage : sessionStorage
    store.setItem(TOKEN_KEY, newToken)

    scheduleRefresh(newToken, rt)
  }

  // On mount: restore session from storage and schedule refresh if needed
  useEffect(() => {
    const persistent    = !!localStorage.getItem(REMEMBER_KEY)
    const store         = persistent ? localStorage : sessionStorage
    const storedToken   = store.getItem(TOKEN_KEY) || ''
    const storedUser    = store.getItem(USER_KEY) || ''
    const storedRefresh = store.getItem(REFRESH_KEY) || ''

    if (!storedToken) {
      setInitializing(false)
      return
    }

    const exp = parseJwtExp(storedToken)
    const hasTime = exp && (exp - Date.now() > 5_000)

    if (hasTime) {
      setToken(storedToken)
      if (storedUser) {
        try { setUser(JSON.parse(storedUser)) } catch { /* ignore */ }
      }
      if (storedRefresh) scheduleRefresh(storedToken, storedRefresh)
      setInitializing(false)
    } else if (storedRefresh) {
      // Access token expired but refresh token may still be valid — attempt silent refresh
      refreshFnRef.current?.(storedRefresh).finally(() => setInitializing(false))
    } else {
      // Nothing usable — clear stale data
      clearStoredAuth()
      setInitializing(false)
    }

    return clearTimer
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(async (username: string, password: string, rememberMe = false) => {
    const result = await apiRequest<{
      success: boolean
      message: string
      access_token?: string
      refresh_token?: string
      user?: User
    }>(
      '/api/auth/login',
      { method: 'POST', body: JSON.stringify({ username, password, remember_me: rememberMe }) }
    )

    if (!result.success || !result.data?.success || !result.data.access_token || !result.data.user) {
      return { success: false, message: result.error || result.data?.message || 'Login failed' }
    }

    const { access_token, refresh_token = '', user: userData } = result.data
    setToken(access_token)
    setUser(userData)

    // Clear any previous session before storing new one
    clearStoredAuth()
    const store = rememberMe ? localStorage : sessionStorage
    if (rememberMe) localStorage.setItem(REMEMBER_KEY, '1')
    store.setItem(TOKEN_KEY, access_token)
    store.setItem(USER_KEY, JSON.stringify(userData))
    if (refresh_token) {
      store.setItem(REFRESH_KEY, refresh_token)
      scheduleRefresh(access_token, refresh_token)
    }

    return { success: true, message: result.data.message || 'Login successful' }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const signup = useCallback(async (payload: Record<string, unknown>) => {
    const result = await apiRequest<{ success: boolean; message: string }>(
      '/api/auth/signup',
      { method: 'POST', body: JSON.stringify(payload) }
    )
    if (!result.success || !result.data?.success) {
      return { success: false, message: result.error || result.data?.message || 'Signup failed' }
    }
    return { success: true, message: result.data.message || 'Account created successfully' }
  }, [])

  const logout = useCallback(async () => {
    clearTimer()
    if (token) await apiRequest('/api/auth/logout', { method: 'POST' }, token).catch(() => {})
    clearStoredAuth()
    setToken('')
    setUser(null)
  }, [token]) // eslint-disable-line react-hooks/exhaustive-deps

  const value = useMemo<AuthContextType>(
    () => ({ user, token, isAuthenticated: !!token, initializing, login, signup, logout }),
    [token, user, initializing, login, signup, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
