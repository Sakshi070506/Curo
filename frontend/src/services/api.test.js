// API Client Tests
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { api, setAuthToken, clearAuthToken, getAuthToken } from '../services/api'

describe('API Client', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    clearAuthToken()
    localStorage.clear()
    delete window.__CURO_TOKEN__
  })

  afterEach(() => {
    clearAuthToken()
    localStorage.clear()
    delete window.__CURO_TOKEN__
  })

  it('should create axios instance with correct baseURL', () => {
    expect(api.defaults.baseURL).toBe('/api')
    expect(api.defaults.timeout).toBe(30000)
    expect(api.defaults.headers.common['Content-Type']).toBe('application/json')
  })

  it('should set and get auth token', () => {
    setAuthToken('test-token-123')
    expect(getAuthToken()).toBe('test-token-123')
    expect(localStorage.getItem('curo_access_token')).toBe('test-token-123')
    expect(window.__CURO_TOKEN__).toBe('test-token-123')
  })

  it('should clear auth token', () => {
    setAuthToken('test-token')
    clearAuthToken()
    expect(getAuthToken()).toBeNull()
    expect(localStorage.getItem('curo_access_token')).toBeNull()
    expect(window.__CURO_TOKEN__).toBeNull()
  })

  it('should add Authorization header when token exists', async () => {
    setAuthToken('bearer-token')
    const requestInterceptor = api.interceptors.request.handlers[0]
    const config = { headers: {} }
    const result = await requestInterceptor.fulfilled(config)
    expect(result.headers.Authorization).toBe('Bearer bearer-token')
  })

  it('should add X-Request-ID header', async () => {
    const requestInterceptor = api.interceptors.request.handlers[0]
    const config = { headers: {}, data: {} }
    const result = await requestInterceptor.fulfilled(config)
    expect(result.headers['X-Request-ID']).toBeDefined()
    expect(result.headers['X-Request-ID'].length).toBeGreaterThan(0)
  })

  it('should remove Content-Type for FormData', async () => {
    const requestInterceptor = api.interceptors.request.handlers[0]
    const formData = new FormData()
    const config = { headers: { 'Content-Type': 'application/json' }, data: formData }
    const result = await requestInterceptor.fulfilled(config)
    expect(result.headers['Content-Type']).toBeUndefined()
  })

  it('should normalize error responses', async () => {
    const responseInterceptor = api.interceptors.response.handlers[0]
    const error = {
      response: { status: 400, data: { detail: 'Invalid input' } },
      message: 'Request failed',
    }
    await expect(responseInterceptor.rejected(error)).rejects.toThrow('Invalid input')
  })

  it('should handle 401 by clearing token', async () => {
    setAuthToken('expired-token')
    const responseInterceptor = api.interceptors.response.handlers[0]
    const error = {
      response: { status: 401, data: { detail: 'Unauthorized' } },
      message: 'Unauthorized',
    }
    await expect(responseInterceptor.rejected(error)).rejects.toThrow()
    expect(getAuthToken()).toBeNull()
  })
})