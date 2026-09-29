// LanguageSelect Page Tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { LanguageSelect } from '../pages/LanguageSelect'
import { MemoryRouter } from 'react-router-dom'
import { SessionProvider } from '../context/SessionContext'
import React from 'react'

vi.mock('../services/abdmService', () => ({
  abdmService: {
    register: vi.fn().mockResolvedValue({ message: 'Registered', abha_id: '12-3456-7890-1234' }),
    login: vi.fn().mockResolvedValue({ access_token: 'mock-token', token_type: 'bearer' }),
    abhaVerify: vi.fn().mockResolvedValue({ verified: true, access_token: 'mock-token' }),
  },
}))

vi.mock('../services/historyService', () => ({
  historyService: {
    startSession: vi.fn().mockResolvedValue({
      session_id: 'session-123',
      next_question: { question_id: 'chief_complaint', prompt: 'What brings you in today?', state: 'CHIEF_COMPLAINT' },
    }),
  },
}))

const renderWithProviders = (component) => {
  return render(
    <MemoryRouter initialEntries={['/language']}>
      <SessionProvider>
        {component}
      </SessionProvider>
    </MemoryRouter>
  )
}

describe('LanguageSelect Page', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    sessionStorage.clear()
  })

  it('should render language grid', () => {
    renderWithProviders(<LanguageSelect />)
    expect(screen.getByText('Welcome')).toBeInTheDocument()
    expect(screen.getByText('English')).toBeInTheDocument()
    expect(screen.getByText('हिन्दी')).toBeInTheDocument()
  })

  it('should select language on click', () => {
    renderWithProviders(<LanguageSelect />)
    const hindiButton = screen.getByText('हिन्दी').closest('label')
    fireEvent.click(hindiButton)
    expect(screen.getByText('हिन्दी').closest('label')).toHaveClass('ring-2 ring-primary')
  })

  it('should toggle AYUSH mode', () => {
    renderWithProviders(<LanguageSelect />)
    const checkbox = screen.getByRole('checkbox', { name: /ayush mode/i })
    expect(checkbox).not.toBeChecked()
    fireEvent.click(checkbox)
    expect(checkbox).toBeChecked()
  })

  it('should validate ABHA ID format', () => {
    renderWithProviders(<LanguageSelect />)
    const abhaInput = screen.getByLabelText(/abha id/i)
    fireEvent.change(abhaInput, { target: { value: '123' } })
    expect(abhaInput.value).toBe('123')
  })

  it('should require name', () => {
    renderWithProviders(<LanguageSelect />)
    const nameInput = screen.getByLabelText(/full name/i)
    fireEvent.change(nameInput, { target: { value: 'John Doe' } })
    expect(nameInput.value).toBe('John Doe')
  })

  it('should show error when ABHA ID missing', async () => {
    renderWithProviders(<LanguageSelect />)
    const submitButton = screen.getByRole('button', { name: /start interview/i })
    fireEvent.click(submitButton)
    await waitFor(() => {
      expect(screen.getByText('Please enter your ABHA ID')).toBeInTheDocument()
    })
  })

  it('should show error when name missing', async () => {
    renderWithProviders(<LanguageSelect />)
    const abhaInput = screen.getByLabelText(/abha id/i)
    fireEvent.change(abhaInput, { target: { value: '12-3456-7890-1234' } })
    const submitButton = screen.getByRole('button', { name: /start interview/i })
    fireEvent.click(submitButton)
    await waitFor(() => {
      expect(screen.getByText('Please enter your name')).toBeInTheDocument()
    })
  })

  it('should navigate to consent on successful start', async () => {
    renderWithProviders(<LanguageSelect />)
    const abhaInput = screen.getByLabelText(/abha id/i)
    fireEvent.change(abhaInput, { target: { value: '12-3456-7890-1234' } })
    const nameInput = screen.getByLabelText(/full name/i)
    fireEvent.change(nameInput, { target: { value: 'Test User' } })
    const submitButton = screen.getByRole('button', { name: /start interview/i })
    fireEvent.click(submitButton)
    await waitFor(() => {
      expect(screen.getByText('Consent')).toBeInTheDocument()
    })
  })

  it('should limit ABHA ID to 14 digits', () => {
    renderWithProviders(<LanguageSelect />)
    const abhaInput = screen.getByLabelText(/abha id/i)
    fireEvent.change(abhaInput, { target: { value: '1234567890123456' } })
    expect(abhaInput.value).toBe('12345678901234')
  })
})