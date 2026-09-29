// RedFlagBanner Component Tests
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { RedFlagBanner } from '../components/RedFlagBanner'
import React from 'react'

describe('RedFlagBanner', () => {
  it('should not render when no red flags', () => {
    render(<RedFlagBanner redFlags={[]} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('should render alert for critical red flag', () => {
    render(<RedFlagBanner redFlags={[{ severity: 'critical', description: 'Chest pain' }]} />)
    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(alert).toHaveAttribute('aria-live', 'assertive')
    expect(screen.getByText('Medical Alert Detected')).toBeInTheDocument()
    expect(screen.getByText('Chest pain (critical)')).toBeInTheDocument()
  })

  it('should render alert for high severity', () => {
    render(<RedFlagBanner redFlags={[{ severity: 'high', description: 'Shortness of breath' }]} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText('Shortness of breath (high)')).toBeInTheDocument()
  })

  it('should show symptom when provided', () => {
    render(<RedFlagBanner redFlags={[{ severity: 'critical', description: 'Rule', symptom: 'Chest pain with breathlessness' }]} />)
    expect(screen.getByText('Chest pain with breathlessness')).toBeInTheDocument()
  })

  it('should call onDismiss when dismiss button clicked', () => {
    const onDismiss = vi.fn()
    render(<RedFlagBanner redFlags={[{ severity: 'critical', description: 'Test' }]} onDismiss={onDismiss} />)
    fireEvent.click(screen.getByRole('button', { name: /dismiss alert/i }))
    expect(onDismiss).toHaveBeenCalled()
  })

  it('should not show dismiss button when onDismiss not provided', () => {
    render(<RedFlagBanner redFlags={[{ severity: 'critical', description: 'Test' }]} />)
    expect(screen.queryByRole('button', { name: /dismiss alert/i })).not.toBeInTheDocument()
  })

  it('should show highest severity when multiple flags', () => {
    render(<RedFlagBanner redFlags={[
      { severity: 'low', description: 'Low' },
      { severity: 'critical', description: 'Critical' },
      { severity: 'medium', description: 'Medium' },
    ]} />)
    expect(screen.getByText('Critical (critical)')).toBeInTheDocument()
  })
})