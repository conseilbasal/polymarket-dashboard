import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const API_PASSWORD = import.meta.env.VITE_API_PASSWORD || ''

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token management
let accessToken: string | null = null

// Login function to get JWT token
export const login = async (): Promise<void> => {
  if (!API_PASSWORD) {
    console.warn('No API password configured')
    return
  }

  try {
    const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
      password: API_PASSWORD,
    })
    accessToken = response.data.access_token
  } catch (error) {
    console.error('Login failed:', error)
    throw error
  }
}

// Request interceptor - add JWT token to all requests
apiClient.interceptors.request.use(
  async (config) => {
    // If no token, try to login first
    if (!accessToken && API_PASSWORD) {
      await login()
    }

    // Add token to request if available
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle 401 errors by re-authenticating
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // If 401 and haven't retried yet, try to login again
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        await login()
        originalRequest.headers.Authorization = `Bearer ${accessToken}`
        return apiClient(originalRequest)
      } catch (loginError) {
        console.error('Re-authentication failed:', loginError)
        return Promise.reject(loginError)
      }
    }

    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default apiClient
