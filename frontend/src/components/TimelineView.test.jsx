// TimelineView Component Tests
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TimelineView } from '../components/TimelineView'
import React from 'react'

const mockDocuments = [
  {
    document_id: 'doc-1',
    type: 'prescription',
    date: '2026-01-15',
    diagnoses: ['Hypertension', 'Diabetes'],
    medications: [{ name: 'Amlodipine', dosage: '5mg', frequency: 'OD' }],
    investigations: [],
    procedures: [],
  },
  {
    document_id: 'doc-2',
    type: 'lab_report',
    date: '2026-01-10',
    diagnoses: [],
    medications: [],
    investigations: [{ name: 'HbA1c', value: '7.2%' }],
    procedures: [],
  },
]

describe('TimelineView', () => {
  it('should show empty state when no documents', () => {
    render(<TimelineView documents={[]} />)
    expect(screen.getByText('No documents yet')).toBeInTheDocument()
    expect(screen.getByText('Upload a prescription or lab report')).toBeInTheDocument()
  })

  it('should render documents sorted by date (newest first)', () => {
    render(<TimelineView documents={mockDocuments} />)
    const cards = screen.getAllByRole('listitem')
    expect(cards.length).toBe(2)
    // First card should be the newer document (Jan 15)
    expect(cards[0]).toHaveTextContent('prescription')
    expect(cards[0]).toHaveTextContent('Jan 15, 2026')
  })

  it('should show document type and date', () => {
    render(<TimelineView documents={mockDocuments} />)
    expect(screen.getByText('Prescription')).toBeInTheDocument()
    expect(screen.getByText('Lab Report')).toBeInTheDocument()
  })

  it('should show diagnoses as badges', () => {
    render(<TimelineView documents={mockDocuments} />)
    expect(screen.getByText('Hypertension')).toBeInTheDocument()
    expect(screen.getByText('Diabetes')).toBeInTheDocument()
  })

  it('should show medications with dosage and frequency', () => {
    render(<TimelineView documents={mockDocuments} />)
    expect(screen.getByText('Amlodipine')).toBeInTheDocument()
    expect(screen.getByText('5mg')).toBeInTheDocument()
    expect(screen.getByText('OD')).toBeInTheDocument()
  })

  it('should show investigations', () => {
    render(<TimelineView documents={mockDocuments} />)
    expect(screen.getByText('HbA1c')).toBeInTheDocument()
  })

  it('should handle missing optional fields', () => {
    const docs = [{ document_id: 'doc-3', type: 'note', date: '2026-01-01', diagnoses: [], medications: [], investigations: [], procedures: [] }]
    render(<TimelineView documents={docs} />)
    expect(screen.getByText('Note')).toBeInTheDocument()
  })

  it('should have proper accessibility', () => {
    render(<TimelineView documents={mockDocuments} />)
    expect(screen.getByRole('region', { name: /medical timeline/i })).toBeInTheDocument()
  })
})