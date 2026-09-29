// DocumentScanBox Component Tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { DocumentScanBox } from '../components/DocumentScanBox'
import { documentService } from '../services/documentService'
import React from 'react'

vi.mock('../services/documentService', () => ({
  documentService: {
    uploadDocument: vi.fn(),
    getTimeline: vi.fn().mockResolvedValue([]),
  },
}))

describe('DocumentScanBox', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    documentService.uploadDocument.mockResolvedValue({
      document_id: 'doc-123',
      patient_id: 'patient-1',
      document_type: 'prescription',
      date: '2026-01-15',
      diagnoses: ['Hypertension'],
      medications: [{ name: 'Amlodipine', dosage: '5mg', frequency: 'OD' }],
      investigations: [],
      raw_ocr_confidence: 0.92,
    })
  })

  it('should render drop zone', () => {
    render(<DocumentScanBox patientId="patient-1" />)
    expect(screen.getByText(/drag & drop files here/i)).toBeInTheDocument()
  })

  it('should show file input when clicked', () => {
    render(<DocumentScanBox patientId="patient-1" />)
    const dropZone = screen.getByText(/drag & drop files here/i).closest('div')
    fireEvent.click(dropZone)
    // File input is hidden, but click should trigger it
  })

  it('should show selected files', () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    render(<DocumentScanBox patientId="patient-1" />)
    const input = screen.getByLabelText(/drop zone for document upload/i)
    fireEvent.change(input, { target: { files: [file] } })
    expect(screen.getByText('test.pdf')).toBeInTheDocument()
    expect(screen.getByText('1 file(s) ready')).toBeInTheDocument()
  })

  it('should upload files when upload button clicked', async () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    render(<DocumentScanBox patientId="patient-1" />)
    const input = screen.getByLabelText(/drop zone for document upload/i)
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /upload 1 file/i }))
    await waitFor(() => {
      expect(documentService.uploadDocument).toHaveBeenCalled()
    })
  })

  it('should show upload results', async () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    render(<DocumentScanBox patientId="patient-1" />)
    const input = screen.getByLabelText(/drop zone for document upload/i)
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /upload 1 file/i }))
    await waitFor(() => {
      expect(screen.getByText('Uploaded Documents')).toBeInTheDocument()
      expect(screen.getByText('prescription — 2026-01-15')).toBeInTheDocument()
      expect(screen.getByText('Confidence: 92%')).toBeInTheDocument()
    })
  })

  it('should allow removing files before upload', () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    render(<DocumentScanBox patientId="patient-1" />)
    const input = screen.getByLabelText(/drop zone for document upload/i)
    fireEvent.change(input, { target: { files: [file] } })
    expect(screen.getByText('test.pdf')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /remove test.pdf/i }))
    expect(screen.queryByText('test.pdf')).not.toBeInTheDocument()
  })

  it('should call onUploadComplete callback', async () => {
    const onUploadComplete = vi.fn()
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    render(<DocumentScanBox patientId="patient-1" onUploadComplete={onUploadComplete} />)
    const input = screen.getByLabelText(/drop zone for document upload/i)
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /upload 1 file/i }))
    await waitFor(() => {
      expect(onUploadComplete).toHaveBeenCalledWith(expect.objectContaining({
        document_id: 'doc-123',
      }))
    })
  })

  it('should disable controls during upload', async () => {
    documentService.uploadDocument.mockImplementation(() => new Promise(r => setTimeout(r, 100)))
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    render(<DocumentScanBox patientId="patient-1" />)
    const input = screen.getByLabelText(/drop zone for document upload/i)
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /upload 1 file/i }))
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /upload 1 file/i })).toBeDisabled()
    })
  })
})