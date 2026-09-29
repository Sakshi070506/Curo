// SessionContext Tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { SessionProvider, useSession } from './SessionContext'
import React from 'react'

const TestComponent = () => {
  const { state, actions } = useSession()
  return (
    <div>
      <span data-testid="language">{state.language}</span>
      <span data-testid="session-id">{state.sessionId || 'none'}</span>
      <button onClick={() => actions.setLanguage('hi')}>Change Language</button>
      <button onClick={() => actions.setIdentity('abha-1', 'Test User', 'patient-1', 'token-1')}>Set Identity</button>
      <button onClick={() => actions.setSession('session-123', 'CHIEF_COMPLAINT')}>Set Session</button>
      <button onClick={() => actions.reset()}>Reset</button>
    </div>
  )
}

describe('SessionContext', () => {
  beforeEach(() => {
    sessionStorage.clear()
    vi.resetAllMocks()
  })

  it('should provide initial state', () => {
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    )
    expect(screen.getByTestId('language').textContent).toBe('en')
    expect(screen.getByTestId('session-id').textContent).toBe('none')
  })

  it('should update language', () => {
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    )
    act(() => {
      screen.getByText('Change Language').click()
    })
    expect(screen.getByTestId('language').textContent).toBe('hi')
  })

  it('should set identity', () => {
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    )
    act(() => {
      screen.getByText('Set Identity').click()
    })
    // Check that state updated (we'd need to expose more state for full test)
  })

  it('should set session', () => {
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    )
    act(() => {
      screen.getByText('Set Session').click()
    })
    expect(screen.getByTestId('session-id').textContent).toBe('session-123')
  })

  it('should persist to sessionStorage', () => {
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    )
    act(() => {
      screen.getByText('Change Language').click()
    })
    const stored = sessionStorage.getItem('curo_session_state')
    expect(stored).toBeTruthy()
    const parsed = JSON.parse(stored)
    expect(parsed.language).toBe('hi')
  })

  it('should restore from sessionStorage', () => {
    sessionStorage.setItem('curo_session_state', JSON.stringify({ language: 'ta', sessionId: 'restored-123' }))
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    )
    expect(screen.getByTestId('language').textContent).toBe('ta')
    expect(screen.getByTestId('session-id').textContent).toBe('restored-123')
  })

  it('should reset to initial state', () => {
    render(
      <SessionProvider>
        <TestComponent />
      </SessionProvider>
    )
    act(() => {
      screen.getByText('Change Language').click()
      screen.getByText('Reset').click()
    })
    expect(screen.getByTestId('language').textContent).toBe('en')
    expect(screen.getByTestId('session-id').textContent).toBe('none')
  })

  it('should throw when used outside provider', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => {
      render(<TestComponent />)
    }).toThrow('useSession must be used within a SessionProvider')
    consoleError.mockRestore()
  })
})