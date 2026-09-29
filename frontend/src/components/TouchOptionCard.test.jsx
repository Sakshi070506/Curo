// TouchOptionCard Component Tests
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { TouchOptionCard } from '../components/TouchOptionCard'
import React from 'react'

describe('TouchOptionCard', () => {
  it('should render universal options by default', () => {
    render(<TouchOptionCard questionId="test" onSelect={vi.fn()} />)
    expect(screen.getByRole('button', { name: /yes/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /no/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /not sure/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /skip/i })).toBeInTheDocument()
  })

  it('should render 1-10 scale for severity questions', () => {
    render(<TouchOptionCard questionId="severity_1" onSelect={vi.fn()} />)
    for (let i = 1; i <= 10; i++) {
      expect(screen.getByRole('button', { name: String(i) })).toBeInTheDocument()
    }
  })

  it('should render yes/no/not sure for yes/no questions', () => {
    render(<TouchOptionCard questionId="any_symptoms" onSelect={vi.fn()} />)
    expect(screen.getByRole('button', { name: /yes/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /no/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /not sure/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /skip/i })).not.toBeInTheDocument()
  })

  it('should call onSelect with option id and label', () => {
    const onSelect = vi.fn()
    render(<TouchOptionCard questionId="test" onSelect={onSelect} />)
    fireEvent.click(screen.getByRole('button', { name: /yes/i }))
    expect(onSelect).toHaveBeenCalledWith('yes', 'Yes')
  })

  it('should not call onSelect when disabled', () => {
    const onSelect = vi.fn()
    render(<TouchOptionCard questionId="test" onSelect={onSelect} disabled />)
    fireEvent.click(screen.getByRole('button', { name: /yes/i }))
    expect(onSelect).not.toHaveBeenCalled()
  })

  it('should show question text when provided', () => {
    render(<TouchOptionCard questionId="test" questionText="Do you have pain?" onSelect={vi.fn()} />)
    expect(screen.getByText('For: Do you have pain?')).toBeInTheDocument()
  })

  it('should have proper accessibility roles', () => {
    render(<TouchOptionCard questionId="test" onSelect={vi.fn()} />)
    const group = screen.getByRole('group', { name: /answer options/i })
    expect(group).toBeInTheDocument()
  })
})