// SummaryEditor Component Tests
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SummaryEditor } from '../components/SummaryEditor'
import React from 'react'

const mockSummary = {
  chief_complaint: 'Chest pain',
  hpi: { onset: 'sudden', severity: '8/10' },
  past_medical_history: ['Hypertension'],
  drug_allergy_history: ['Penicillin'],
  family_history: ['Father: heart disease'],
  personal_history: { smoking: 'Former smoker' },
  review_of_systems: { cardiovascular: 'Chest pain on exertion' },
  medications_from_docs: [{ name: 'Aspirin', dosage: '75mg' }],
}

describe('SummaryEditor', () => {
  it('should render summary sections in read-only mode', () => {
    render(<SummaryEditor summary={mockSummary} readOnly />)
    expect(screen.getByText('Chest pain')).toBeInTheDocument()
    expect(screen.getByText('Hypertension')).toBeInTheDocument()
    expect(screen.getByText('Penicillin')).toBeInTheDocument()
  })

  it('should show "Not captured" for empty sections', () => {
    render(<SummaryEditor summary={{ chief_complaint: 'Test' }} readOnly />)
    expect(screen.getByText('Not captured')).toBeInTheDocument()
  })

  it('should expand/collapse sections', () => {
    render(<SummaryEditor summary={mockSummary} readOnly />)
    const chiefComplaintButton = screen.getByRole('button', { name: /chief complaint/i })
    expect(chiefComplaintButton).toHaveAttribute('aria-expanded', 'true')
    // Click to collapse
    fireEvent.click(chiefComplaintButton)
    expect(chiefComplaintButton).toHaveAttribute('aria-expanded', 'false')
  })

  it('should show edit mode when not readOnly', () => {
    render(<SummaryEditor summary={mockSummary} onSave={vi.fn()} />)
    expect(screen.getByRole('button', { name: /edit summary/i })).toBeInTheDocument()
  })

  it('should show editor when editing', () => {
    render(<SummaryEditor summary={mockSummary} onSave={vi.fn()} />)
    fireEvent.click(screen.getByRole('button', { name: /edit summary/i }))
    expect(screen.getByDisplayValue('Chest pain')).toBeInTheDocument()
  })

  it('should save edits', () => {
    const onSave = vi.fn()
    render(<SummaryEditor summary={mockSummary} onSave={onSave} />)
    fireEvent.click(screen.getByRole('button', { name: /edit summary/i }))
    const input = screen.getByDisplayValue('Chest pain')
    fireEvent.change(input, { target: { value: 'Updated complaint' } })
    fireEvent.click(screen.getByRole('button', { name: /save/i }))
    expect(onSave).toHaveBeenCalledWith(expect.objectContaining({
      chief_complaint: 'Updated complaint',
    }))
  })

  it('should cancel edits', () => {
    const onCancel = vi.fn()
    render(<SummaryEditor summary={mockSummary} onSave={vi.fn()} onCancel={onCancel} />)
    fireEvent.click(screen.getByRole('button', { name: /edit summary/i }))
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(onCancel).toHaveBeenCalled()
  })

  it('should show unsaved changes indicator', () => {
    const onSave = vi.fn()
    render(<SummaryEditor summary={mockSummary} onSave={onSave} />)
    fireEvent.click(screen.getByRole('button', { name: /edit summary/i }))
    const input = screen.getByDisplayValue('Chest pain')
    fireEvent.change(input, { target: { value: 'Updated' } })
    expect(screen.getByText(/unsaved changes: 1 section/i)).toBeInTheDocument()
  })

  it('should render array fields as list', () => {
    render(<SummaryEditor summary={mockSummary} readOnly />)
    expect(screen.getByText('Hypertension')).toBeInTheDocument()
    expect(screen.getByText('Penicillin')).toBeInTheDocument()
    expect(screen.getByText('Father: heart disease')).toBeInTheDocument()
  })

  it('should render object fields as JSON', () => {
    render(<SummaryEditor summary={mockSummary} readOnly />)
    expect(screen.getByText('onset')).toBeInTheDocument()
    expect(screen.getByText('sudden')).toBeInTheDocument()
  })
})