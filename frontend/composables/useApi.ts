/**
 * API Service Layer
 * Centralized API calls with authentication
 */

export const useApi = () => {
  const { token } = useAuth()
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase

  const apiCall = async (endpoint: string, options: any = {}) => {
    const headers: any = {
      'Content-Type': 'application/json',
      ...options.headers
    }

    if (token.value) {
      headers['Authorization'] = `Bearer ${token.value}`
    }

    try {
      const response = await $fetch(`${baseURL}${endpoint}`, {
        ...options,
        headers
      })
      return { success: true, data: response }
    } catch (error: any) {
      console.error('API Error:', error)
      return { 
        success: false, 
        error: error.data?.detail || error.message || 'API request failed' 
      }
    }
  }

  // FIR Management APIs
  const fir = {
    create: (data: any) => apiCall('/api/fir/create', {
      method: 'POST',
      body: data
    }),

    list: (status?: string) => {
      const query = status ? `?status=${status}` : ''
      return apiCall(`/api/fir/${query}`)
    },

    get: (firNumber: string) => apiCall(`/api/fir/${firNumber}`),

    getIpLookups: (firNumber: string, limit = 100, offset = 0) => 
      apiCall(`/api/fir/${firNumber}/ip-lookups?limit=${limit}&offset=${offset}`),

    getStatistics: (firNumber: string) => 
      apiCall(`/api/fir/${firNumber}/statistics`),

    getTimeline: (firNumber: string, limit = 50) => 
      apiCall(`/api/fir/${firNumber}/timeline?limit=${limit}`),

    storeIpResults: async (firNumber: string, file: File) => {
      const formData = new FormData()
      formData.append('file', file)

      return await $fetch(`${baseURL}/api/fir/store-ip-results/${firNumber}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token.value}`
        },
        body: formData
      })
    }
  }

  // IP Lookup APIs
  const ipLookup = {
    stream: (runDir: string) => {
      // EventSource for SSE
      const eventSource = new EventSource(
        `${baseURL}/api/lookup/stream?run_dir=${encodeURIComponent(runDir)}`
      )
      return eventSource
    },

    start: (runDir: string) => apiCall('/api/lookup/start', {
      method: 'POST',
      body: { run_dir: runDir }
    }),

    status: (runDir: string) => 
      apiCall(`/api/lookup/status?run_dir=${encodeURIComponent(runDir)}`)
  }

  // User Activity Tracking
  const tracking = {
    logActivity: (activityType: string, description: string, pageUrl?: string) => 
      apiCall('/api/auth/track-activity', {
        method: 'POST',
        params: {
          activity_type: activityType,
          activity_description: description,
          page_url: pageUrl
        }
      })
  }

  return {
    apiCall,
    fir,
    ipLookup,
    tracking
  }
}
