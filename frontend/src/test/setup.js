// Test setup for Vitest + React Testing Library + MSW
import { beforeAll, afterAll, afterEach, vi } from 'vitest'
import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

// MSW server for API mocking
export const server = setupServer(...handlers)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterAll(() => server.close())
afterEach(() => {
  cleanup()
  server.resetHandlers()
})

// Mock Web Speech API for voice tests
global.SpeechRecognition = class SpeechRecognition {
  constructor() {
    this.continuous = false
    this.interimResults = false
    this.lang = 'en-US'
    this.onstart = null
    this.onend = null
    this.onresult = null
    this.onerror = null
  }
  start() { if (this.onstart) this.onstart() }
  stop() { if (this.onend) this.onend() }
  abort() { if (this.onend) this.onend() }
}

// Mock MediaRecorder
global.MediaRecorder = class MediaRecorder {
  constructor(stream, options) {
    this.stream = stream
    this.mimeType = options?.mimeType || 'audio/webm'
    this.state = 'inactive'
    this.ondataavailable = null
    this.onstop = null
    this.onerror = null
  }
  start() {
    this.state = 'recording'
    // Simulate data available after a short delay
    setTimeout(() => {
      if (this.ondataavailable) {
        this.ondataavailable({ data: new Blob(['mock-audio'], { type: this.mimeType }) })
      }
      if (this.onstop) this.onstop()
    }, 10)
  }
  stop() { this.state = 'inactive' }
  static isTypeSupported(type) { return true }
}

// Mock navigator.mediaDevices
Object.defineProperty(global.navigator, 'mediaDevices', {
  value: {
    getUserMedia: vi.fn().mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }]
    })
  },
  writable: true
})

// Mock matchMedia
Object.defineProperty(global.window, 'matchMedia', {
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
  writable: true
})

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(global.window, 'localStorage', { value: localStorageMock, writable: true })

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(global.window, 'sessionStorage', { value: sessionStorageMock, writable: true })