const envApiBase = import.meta.env.VITE_API_BASE as string | undefined
const envApiTimeout = import.meta.env.VITE_API_TIMEOUT as string | undefined

// Request timeout in milliseconds (default: 120 seconds)
const REQUEST_TIMEOUT = Number(envApiTimeout) > 0 ? Number(envApiTimeout) : 120000

function resolveApiBase() {
  if (envApiBase && envApiBase.trim()) return envApiBase.trim()

  if (typeof window !== 'undefined') {
    const host = window.location.hostname || 'localhost'
    return `http://${host}:8000`
  }

  return 'http://localhost:8000'
}

export const API_BASE = resolveApiBase()

export type ApiResult<T> = {
  success: boolean
  data?: T
  error?: string
}

/**
 * Make an API request with automatic error handling and timeout
 * @param path - API endpoint path (e.g., '/api/data')
 * @param options - Fetch options
 * @param token - Optional JWT token for authentication
 * @returns Wrapped API response with success flag and data or error
 */
export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<ApiResult<T>> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT)

  try {
    const headers = new Headers(options.headers || {})
    if (!(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json')
    }
    if (token) headers.set('Authorization', `Bearer ${token}`)

    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      signal: controller.signal
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      return { success: false, error: data.detail || data.error || data.message || 'Request failed' }
    }

    return { success: true, data: data as T }
  } catch (error) {
    // Handle fetch aborts across browsers/runtime variants.
    const isAbort =
      (typeof DOMException !== 'undefined' &&
        error instanceof DOMException &&
        error.name === 'AbortError') ||
      (error instanceof Error &&
        /abort/i.test(`${error.name} ${error.message}`))

    if (isAbort) {
      return {
        success: false,
        error: `Request timeout - server took longer than ${REQUEST_TIMEOUT / 1000} seconds to respond`
      }
    }

    const message = error instanceof Error ? error.message : 'Network error'
    const isLoadFailed = /load failed|failed to fetch|networkerror/i.test(message)

    return {
      success: false,
      error: isLoadFailed
        ? `Cannot connect to backend (${API_BASE}). Ensure backend is running on port 8000.`
        : message
    }
  } finally {
    clearTimeout(timeoutId)
  }
}

