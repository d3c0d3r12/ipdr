/**
 * Authentication Composable
 * Handles login, logout, and user session management with auto-expiration
 */

export const useAuth = () => {
  const user = useState<any>('user', () => null)
  const token = useState<string>('token', () => '')
  const tokenExpiry = useState<number>('tokenExpiry', () => 0)
  const isAuthenticated = computed(() => !!token.value && !isTokenExpired())
  
  let expiryCheckInterval: any = null

  // Token expiration settings
  const TOKEN_LIFETIME = 24 * 60 // 24 hours (1 day) - but session ends on browser close
  const WARNING_BEFORE_EXPIRY = 30 // Warn 30 minutes before expiry
  const AUTO_LOGOUT_ON_INACTIVITY = 120 // Auto logout after 120 minutes (2 hours) of inactivity

  let lastActivityTime = Date.now()
  
  // Use sessionStorage instead of localStorage for session-based auth
  const storage = typeof window !== 'undefined' ? window.sessionStorage : null

  // Check if token is expired
  const isTokenExpired = () => {
    if (!tokenExpiry.value) return true
    return Date.now() > tokenExpiry.value
  }

  // Get remaining time in minutes
  const getRemainingTime = () => {
    if (!tokenExpiry.value) return 0
    const remaining = tokenExpiry.value - Date.now()
    return Math.max(0, Math.floor(remaining / 60000)) // Convert to minutes
  }

  // Update last activity time
  const updateActivity = () => {
    lastActivityTime = Date.now()
    if (storage) {
      storage.setItem('lastActivity', lastActivityTime.toString())
    }
  }

  // Check for inactivity
  const checkInactivity = () => {
    const inactiveTime = Date.now() - lastActivityTime
    const inactiveMinutes = inactiveTime / 60000
    
    if (inactiveMinutes >= AUTO_LOGOUT_ON_INACTIVITY) {
      console.log('Auto-logout due to inactivity')
      logout()
      if (typeof window !== 'undefined') {
        alert('Session expired due to inactivity. Please login again.')
        window.location.href = '/login'
      }
    }
  }

  // Start expiry monitoring
  const startExpiryMonitoring = () => {
    if (expiryCheckInterval) {
      clearInterval(expiryCheckInterval)
    }

    expiryCheckInterval = setInterval(() => {
      // Check token expiration
      if (isTokenExpired()) {
        console.log('Token expired - logging out')
        logout()
        if (typeof window !== 'undefined') {
          alert('Your session has expired. Please login again.')
          window.location.href = '/login'
        }
        return
      }

      // Check inactivity
      checkInactivity()

      // Warn before expiry
      const remaining = getRemainingTime()
      if (remaining <= WARNING_BEFORE_EXPIRY && remaining > 0) {
        console.log(`Session expiring in ${remaining} minutes`)
        // You can show a notification here
      }
    }, 60000) // Check every minute
  }

  // Stop expiry monitoring
  const stopExpiryMonitoring = () => {
    if (expiryCheckInterval) {
      clearInterval(expiryCheckInterval)
      expiryCheckInterval = null
    }
  }

  const login = async (username: string, password: string) => {
    try {
      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      const response = await $fetch(`${apiBase}/api/auth/login`, {
        method: 'POST',
        body: {
          username,
          password
        }
      })

      if (response.success) {
        token.value = response.access_token
        user.value = response.user
        
        // Set token expiry (30 minutes from now)
        const expiryTime = Date.now() + (TOKEN_LIFETIME * 60 * 1000)
        tokenExpiry.value = expiryTime
        
        // Update activity
        updateActivity()
        
        // Store in sessionStorage (clears on browser close)
        if (storage) {
          storage.setItem('auth_token', response.access_token)
          storage.setItem('user', JSON.stringify(response.user))
          storage.setItem('tokenExpiry', expiryTime.toString())
          storage.setItem('lastActivity', Date.now().toString())
          
          // Start monitoring
          startExpiryMonitoring()
          
          // Track user activity
          document.addEventListener('click', updateActivity)
          document.addEventListener('keypress', updateActivity)
          document.addEventListener('scroll', updateActivity)
        }

        return { success: true, message: response.message }
      }

      return { success: false, message: response.message || 'Login failed' }
    } catch (error: any) {
      console.error('Login error:', error)
      return { 
        success: false, 
        message: error.data?.detail || 'Login failed. Please check your credentials.' 
      }
    }
  }

  const logout = async () => {
    try {
      if (token.value) {
        const config = useRuntimeConfig()
        const apiBase = config.public.apiBase
        await $fetch(`${apiBase}/api/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token.value}`
          }
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Stop monitoring
      stopExpiryMonitoring()
      
      // Remove activity listeners
      if (typeof window !== 'undefined') {
        document.removeEventListener('click', updateActivity)
        document.removeEventListener('keypress', updateActivity)
        document.removeEventListener('scroll', updateActivity)
      }
      
      // Clear state
      token.value = ''
      user.value = null
      tokenExpiry.value = 0
      
      // Clear sessionStorage
      if (storage) {
        storage.removeItem('auth_token')
        storage.removeItem('user')
        storage.removeItem('tokenExpiry')
        storage.removeItem('lastActivity')
      }
    }
  }

  const checkAuth = () => {
    if (storage) {
      const storedToken = storage.getItem('auth_token')
      const storedUser = storage.getItem('user')
      const storedExpiry = storage.getItem('tokenExpiry')
      const storedActivity = storage.getItem('lastActivity')
      
      if (storedToken && storedUser && storedExpiry) {
        const expiry = parseInt(storedExpiry)
        
        // Check if token is expired
        if (Date.now() > expiry) {
          console.log('Stored token expired - clearing')
          logout()
          return
        }
        
        // Check inactivity
        if (storedActivity) {
          const lastActivity = parseInt(storedActivity)
          const inactiveTime = Date.now() - lastActivity
          const inactiveMinutes = inactiveTime / 60000
          
          if (inactiveMinutes >= AUTO_LOGOUT_ON_INACTIVITY) {
            console.log('Session expired due to inactivity')
            logout()
            return
          }
          
          lastActivityTime = lastActivity
        }
        
        token.value = storedToken
        user.value = JSON.parse(storedUser)
        tokenExpiry.value = expiry
        
        // Start monitoring
        startExpiryMonitoring()
        
        // Track activity
        document.addEventListener('click', updateActivity)
        document.addEventListener('keypress', updateActivity)
        document.addEventListener('scroll', updateActivity)
      }
    }
  }

  const signup = async (data: any) => {
    try {
      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      const response = await $fetch(`${apiBase}/api/auth/signup`, {
        method: 'POST',
        body: data
      })

      return { success: true, data: response }
    } catch (error: any) {
      console.error('Signup error:', error)
      return { 
        success: false, 
        message: error.data?.detail || 'Signup failed' 
      }
    }
  }

  return {
    user,
    token,
    tokenExpiry,
    isAuthenticated,
    login,
    logout,
    checkAuth,
    signup,
    getRemainingTime,
    updateActivity
  }
}
