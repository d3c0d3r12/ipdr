/**
 * User Tracking Composable
 * Automatically tracks user sessions, activities, and page views
 */

import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useRuntimeConfig } from '#app'

interface SessionData {
  sessionId: string | null
  startTime: number
  lastActivity: number
}

export const useTracking = () => {
  const config = useRuntimeConfig()
  const router = useRouter()
  const route = useRoute()
  const apiBase = config.public.apiBase || 'http://localhost:8000'
  
  const session = ref<SessionData>({
    sessionId: null,
    startTime: Date.now(),
    lastActivity: Date.now()
  })

  /**
   * Get device and browser information
   */
  const getDeviceInfo = () => {
    const nav = navigator as any
    
    return {
      user_agent: navigator.userAgent,
      screen_resolution: `${screen.width}x${screen.height}`,
      viewport_size: `${window.innerWidth}x${window.innerHeight}`,
      color_depth: screen.colorDepth,
      cookies_enabled: navigator.cookieEnabled,
      language: navigator.language,
      languages: navigator.languages ? Array.from(navigator.languages) : [navigator.language],
      do_not_track: navigator.doNotTrack === '1',
      connection_type: nav.connection?.type || null,
      effective_type: nav.connection?.effectiveType || null,
    }
  }

  /**
   * Start a new session
   */
  const startSession = async (username?: string, userRole?: string, isAuthenticated: boolean = false) => {
    try {
      const deviceInfo = getDeviceInfo()
      
      const response = await fetch(`${apiBase}/api/tracking/session/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          user_role: userRole,
          is_authenticated: isAuthenticated,
          referrer_url: document.referrer,
          entry_page: window.location.href,
          ...deviceInfo
        })
      })

      if (response.ok) {
        const data = await response.json()
        session.value.sessionId = data.session_id
        session.value.startTime = Date.now()
        
        // Store session ID in localStorage
        localStorage.setItem('tracking_session_id', data.session_id)
        localStorage.setItem('tracking_session_start', session.value.startTime.toString())
        
        console.log('✅ Session started:', data.session_id)
        return data
      }
    } catch (error) {
      console.error('❌ Error starting session:', error)
    }
  }

  /**
   * End the current session
   */
  const endSession = async () => {
    const sessionId = session.value.sessionId || localStorage.getItem('tracking_session_id')
    
    if (!sessionId) return

    try {
      await fetch(`${apiBase}/api/tracking/session/end`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          exit_page: window.location.href
        })
      })

      // Clear session data
      session.value.sessionId = null
      localStorage.removeItem('tracking_session_id')
      localStorage.removeItem('tracking_session_start')
      
      console.log('✅ Session ended')
    } catch (error) {
      console.error('❌ Error ending session:', error)
    }
  }

  /**
   * Log a user activity
   */
  const logActivity = async (
    activityType: string,
    description?: string,
    actionData?: any,
    status: string = 'success'
  ) => {
    const sessionId = session.value.sessionId || localStorage.getItem('tracking_session_id')
    
    if (!sessionId) return

    try {
      session.value.lastActivity = Date.now()
      
      await fetch(`${apiBase}/api/tracking/activity/log`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          activity_type: activityType,
          activity_description: description,
          page_url: window.location.href,
          page_title: document.title,
          action_category: getCategoryFromType(activityType),
          action_data: actionData,
          status
        })
      })
    } catch (error) {
      console.error('❌ Error logging activity:', error)
    }
  }

  /**
   * Log a page view
   */
  const logPageView = async (previousPage?: string) => {
    const sessionId = session.value.sessionId || localStorage.getItem('tracking_session_id')
    
    if (!sessionId) return

    try {
      await fetch(`${apiBase}/api/tracking/pageview/log`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          page_url: window.location.href,
          page_title: document.title,
          page_path: route.path,
          previous_page: previousPage
        })
      })
    } catch (error) {
      console.error('❌ Error logging page view:', error)
    }
  }

  /**
   * Get activity category from type
   */
  const getCategoryFromType = (type: string): string => {
    const categories: { [key: string]: string } = {
      'page_view': 'navigation',
      'upload': 'file_operation',
      'download': 'file_operation',
      'search': 'data_query',
      'filter': 'data_query',
      'login': 'authentication',
      'logout': 'authentication',
      'export': 'file_operation',
      'click': 'interaction',
      'form_submit': 'interaction'
    }
    return categories[type] || 'other'
  }

  /**
   * Track page navigation
   */
  const setupPageTracking = () => {
    let previousPage = window.location.href

    router.afterEach((to, from) => {
      logPageView(previousPage)
      previousPage = window.location.href
    })
  }

  /**
   * Track user interactions
   */
  const setupInteractionTracking = () => {
    // Track clicks on important elements
    document.addEventListener('click', (e) => {
      const target = e.target as HTMLElement
      
      // Track button clicks
      if (target.tagName === 'BUTTON' || target.closest('button')) {
        const button = target.tagName === 'BUTTON' ? target : target.closest('button')
        logActivity('click', `Clicked: ${button?.textContent?.trim() || 'button'}`, {
          element: 'button',
          text: button?.textContent?.trim()
        })
      }
      
      // Track link clicks
      if (target.tagName === 'A' || target.closest('a')) {
        const link = target.tagName === 'A' ? target : target.closest('a')
        logActivity('click', `Clicked link: ${link?.textContent?.trim()}`, {
          element: 'link',
          href: (link as HTMLAnchorElement)?.href,
          text: link?.textContent?.trim()
        })
      }
    })

    // Track form submissions
    document.addEventListener('submit', (e) => {
      const form = e.target as HTMLFormElement
      logActivity('form_submit', `Form submitted: ${form.id || 'unnamed'}`, {
        form_id: form.id,
        action: form.action
      })
    })
  }

  /**
   * Track session activity (heartbeat)
   */
  const setupActivityHeartbeat = () => {
    setInterval(() => {
      const sessionId = session.value.sessionId || localStorage.getItem('tracking_session_id')
      if (sessionId) {
        session.value.lastActivity = Date.now()
      }
    }, 30000) // Every 30 seconds
  }

  /**
   * Handle page visibility changes
   */
  const setupVisibilityTracking = () => {
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        logActivity('page_hidden', 'User switched tab or minimized window')
      } else {
        logActivity('page_visible', 'User returned to tab')
      }
    })
  }

  /**
   * Handle page unload (user leaving)
   */
  const setupUnloadTracking = () => {
    window.addEventListener('beforeunload', () => {
      // Use sendBeacon for reliable tracking on page unload
      const sessionId = session.value.sessionId || localStorage.getItem('tracking_session_id')
      if (sessionId) {
        const data = JSON.stringify({
          session_id: sessionId,
          exit_page: window.location.href
        })
        navigator.sendBeacon(`${apiBase}/api/tracking/session/end`, data)
      }
    })
  }

  /**
   * Initialize tracking
   */
  const initTracking = async (username?: string, userRole?: string, isAuthenticated: boolean = false) => {
    // Check if session already exists
    const existingSessionId = localStorage.getItem('tracking_session_id')
    const existingStartTime = localStorage.getItem('tracking_session_start')
    
    if (existingSessionId && existingStartTime) {
      // Resume existing session
      session.value.sessionId = existingSessionId
      session.value.startTime = parseInt(existingStartTime)
      console.log('✅ Resumed existing session:', existingSessionId)
    } else {
      // Start new session
      await startSession(username, userRole, isAuthenticated)
    }

    // Set up tracking
    setupPageTracking()
    setupInteractionTracking()
    setupActivityHeartbeat()
    setupVisibilityTracking()
    setupUnloadTracking()

    // Log initial page view
    logPageView()
  }

  /**
   * Update session with user info after login
   */
  const updateSessionUser = async (username: string, userRole: string) => {
    const sessionId = session.value.sessionId || localStorage.getItem('tracking_session_id')
    if (!sessionId) return

    // Log login activity
    await logActivity('login', `User logged in: ${username}`, {
      username,
      user_role: userRole
    })
  }

  return {
    session,
    initTracking,
    startSession,
    endSession,
    logActivity,
    logPageView,
    updateSessionUser
  }
}
