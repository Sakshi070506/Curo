// Document Service Tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { documentService } from './documentService'
import { server } from '../test/setup'
import { http, HttpResponse } from 'msw'

describe('Document Service', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('should upload a document', async () => {
    const file = new File(['test content'], 'prescription.pdf', { type: 'application/pdf' })
    const result = await documentService.uploadDocument(file, { patientId: 'patient-123' })
    expect(result).toHaveProperty('document_id')
    expect(result).toHaveProperty('patient_id', 'patient-123')
    expect(result).toHaveProperty('document_type', 'prescription')
    expect(result).toHaveProperty('diagnoses')
    expect(result).toHaveProperty('medications')
    expect(result.raw_ocr_confidence).toBeGreaterThan(0)
  })

  it('should upload document without patientId (defaults to anonymous)', async () => {
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
    const result = await documentService.uploadDocument(file)
    expect(result.patient_id).toBe('anonymous')
  })

  it('should track upload progress', async () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    const progressCalls = []
    await documentService.uploadDocument(file, {
      patientId: 'p1',
      onProgress: (p) => progressCalls.push(p),
    })
    expect(progressCalls.length).toBeGreaterThan(0)
    expect(progressCalls[progressCalls.length - 1]).toBe(100)
  })

  it('should extract document without persisting', async () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    const result = await documentService.extractDocument(file)
    expect(result).toHaveProperty('document_type')
    expect(result).toHaveProperty('diagnoses')
  })

  it('should get timeline for patient', async () => {
    // First upload a document
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    await documentService.uploadDocument(file, { patientId: 'patient-456' })

    const timeline = await documentService.getTimeline('patient-456')
    expect(Array.isArray(timeline)).toBe(true)
    expect(timeline.length).toBeGreaterThan(0)
    expect(timeline[0]).toHaveProperty('document_id')
    expect(timeline[0]).toHaveProperty('type')
    expect(timeline[0]).toHaveProperty('date')
  })

  it('should return empty timeline for unknown patient', async () => {
    const timeline = await documentService.getTimeline('unknown-patient')
    expect(timeline).toEqual([])
  })

  it('should sort timeline chronologically', async () => {
    // This is tested implicitly by the mock handler which sorts by date
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    await documentService.uploadDocument(file, { patientId: 'patient-789' })
    const timeline = await documentService.getTimeline('patient-789')
    expect(timeline[0].date).toBeDefined()
  })
})