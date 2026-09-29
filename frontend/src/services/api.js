/**
 * Module   : API Client Base
 * Owner    : Frontend Engineer
 * Purpose  : Axios/fetch wrapper with base URL + auth headers.
 */

import axios from 'axios'
import { useSession } from '../context/SessionContext'

// Create axios instance
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: add auth token + request ID
api.interceptors.request.use(
  (config) => {
    // Get token from session context (will be set by SessionProvider)
    // We'll also check localStorage as fallback
    let token = null
    try {
      // Try to get from a global store (set by SessionContext)
      if (window.__CURO_TOKEN__) token = window.__CURO_TOKEN__
      else token = localStorage.getItem('curo_access_token')
    } catch {}

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add request ID for tracing
    const requestId = crypto.randomUUID()
    config.headers['X-Request-ID'] = requestId

    // Detect multipart/form-data
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }

    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: unwrap data, handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Normalize error response
    const normalizedError = new Error(
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'Request failed'
    )
    normalizedError.status = error.response?.status
    normalizedError.data = error.response?.data
    normalizedError.isAxiosError = true

    // Handle 401 - token expired or invalid
    if (error.response?.status === 401) {
      // Clear stored token
      localStorage.removeItem('curo_access_token')
      window.__CURO_TOKEN__ = null
      // Could redirect to login here if needed
      // window.location.href = '/language'
    }

    return Promise.reject(normalizedError)
  }
)

// Helper to set token globally (called after login)
export function setAuthToken(token) {
  window.__CURO_TOKEN__ = token
  localStorage.setItem('curo_access_token', token)
}

export function clearAuthToken() {
  window.__CURO_TOKEN__ = null
  localStorage.removeItem('curo_access_token')
}

export function getAuthToken() {
  return window.__CURO_TOKEN__ || localStorage.getItem('curo_access_token')
}

// Hook to use api with session context (for components)
export function useApi() {
  const { state, actions } = useSession()

  // Create a scoped axios instance with current token
  const scopedApi = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 30000,
  })

  scopedApi.interceptors.request.use((config) => {
    if (state.accessToken) {
      config.headers.Authorization = `Bearer ${state.accessToken}`
    }
    config.headers['X-Request-ID'] = crypto.randomUUID()
    if (config.data instanceof FormData) delete config.headers['Content-Type']
    return config
  })

  return scopedApi
}

// Default export for direct use
export default api