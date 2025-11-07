/**
 * Authenticated Fetch Composable
 * Automatically handles 401 errors and redirects to login while preserving state
 */

export const useAuthenticatedFetch = () => {
  const router = useRouter()
  const route = useRoute()
  
  /**
   * Make an authenticated API call with automatic 401 handling
   * Preserves current page state and redirects to login if unauthorized
   */
  const authenticatedFetch = async (url: string, options: any = {}) => {
    try {
      // Get token from sessionStorage (session-based auth)
      const token = typeof window !== 'undefined' ? sessionStorage.getItem('auth_token') : null
      
      if (!token) {
        // No token - save current state and redirect to login
        saveCurrentState()
        await router.push({
          path: '/login',
          query: { redirect: route.fullPath, reason: 'no_token' }
        })
        throw new Error('Not authenticated. Please login first.')
      }
      
      // Add authorization header
      const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
      }
      
      // Make the request
      const response = await fetch(url, {
        ...options,
        headers
      })
      
      // Handle 401 Unauthorized
      if (response.status === 401) {
        console.warn('🔒 401 Unauthorized - Redirecting to login...')
        
        // Save current state before redirect
        saveCurrentState()
        
        // Clear invalid token from sessionStorage
        if (typeof window !== 'undefined') {
          sessionStorage.removeItem('auth_token')
          sessionStorage.removeItem('user')
          sessionStorage.removeItem('tokenExpiry')
          sessionStorage.removeItem('lastActivity')
        }
        
        // Show user-friendly message
        if (typeof window !== 'undefined') {
          alert('⚠️ Session expired or invalid. Please login again.\n\n✅ Your research data is preserved and will be restored after login.')
        }
        
        // Redirect to login with return URL
        await router.push({
          path: '/login',
          query: { 
            redirect: route.fullPath,
            reason: 'unauthorized'
          }
        })
        
        throw new Error('Authentication failed. Please login again.')
      }
      
      return response
      
    } catch (error: any) {
      // If it's a network error or other error, just throw it
      if (error.message && (error.message.includes('Authentication') || error.message.includes('authenticated'))) {
        throw error
      }
      
      console.error('API call error:', error)
      throw error
    }
  }
  
  /**
   * Save current page state to localStorage
   * This preserves research data, form inputs, etc.
   */
  const saveCurrentState = () => {
    if (typeof window === 'undefined') return
    
    try {
      const state = {
        path: route.fullPath,
        timestamp: Date.now(),
        // Save any page-specific data
        pageData: {
          runDir: localStorage.getItem('current_run_dir'),
          results: localStorage.getItem('current_results'),
          masterFile: localStorage.getItem('current_master_file'),
          fixedFile: localStorage.getItem('current_fixed_file')
        }
      }
      
      localStorage.setItem('preserved_state', JSON.stringify(state))
      console.log('✅ State preserved:', state)
    } catch (error) {
      console.error('Failed to save state:', error)
    }
  }
  
  /**
   * Restore previously saved state
   * Called after successful login
   */
  const restoreState = () => {
    if (typeof window === 'undefined') return null
    
    try {
      const savedState = localStorage.getItem('preserved_state')
      if (!savedState) return null
      
      const state = JSON.parse(savedState)
      
      // Check if state is not too old (max 1 hour)
      const age = Date.now() - state.timestamp
      if (age > 60 * 60 * 1000) {
        console.log('Saved state too old, discarding')
        localStorage.removeItem('preserved_state')
        return null
      }
      
      console.log('✅ State restored:', state)
      
      // Clear the saved state
      localStorage.removeItem('preserved_state')
      
      return state
    } catch (error) {
      console.error('Failed to restore state:', error)
      return null
    }
  }
  
  return {
    authenticatedFetch,
    saveCurrentState,
    restoreState
  }
}
