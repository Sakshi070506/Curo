// Summary Service Tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { summaryService } from './summaryService'
import { server } from '../test/setup'
import { http, HttpResponse } from 'msw'

describe('Summary Service', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('should generate summary from session', async () => {
    const result = await summaryService.generateSummary({
      patient_id: 'patient-1',
      session_id: 'session-123',
    })
    expect(result).toHaveProperty('summary_id')
    expect(result).toHaveProperty('summary')
    expect(result).toHaveProperty('source_attribution')
    expect(result).toHaveProperty('missing_sections')
    expect(result.summary).toHaveProperty('chief_complaint')
  })

  it('should include documents in summary', async () => {
    // The mock handler includes documents from the document store
    const result = await summaryService.generateSummary({
      patient_id: 'patient-with-docs',
      session_id: 'session-456',
    })
    expect(result.summary).toHaveProperty('medications_from_docs')
  })

  it('should get summary by ID', async () => {
    const generated = await summaryService.generateSummary({
      patient_id: 'patient-2',
      session_id: 'session-789',
    })
    const result = await summaryService.getSummary(generated.summary_id)
    expect(result.summary_id).toBe(generated.summary_id)
    expect(result.summary).toEqual(generated.summary)
  })

  it('should return 404 for unknown summary', async () => {
    await expect(summaryService.getSummary('unknown-summary')).rejects.toThrow('Summary not found')
  })

  it('should confirm summary', async () => {
    const generated = await summaryService.generateSummary({
      patient_id: 'patient-3',
      session_id: 'session-999',
    })
    const result = await summaryService.confirmSummary(generated.summary_id, {
      summary: generated.summary,
      confirmed: true,
    })
    expect(result.status).toBe('confirmed')
    expect(result.summary_id).toBe(generated.summary_id)
  })

  it('should reject confirmation without confirmed=true', async () => {
    const generated = await summaryService.generateSummary({
      patient_id: 'patient-4',
      session_id: 'session-111',
    })
    await expect(summaryService.confirmSummary(generated.summary_id, {
      summary: generated.summary,
      confirmed: false,
    })).rejects.toThrow('Confirmation required')
  })

  it('should edit summary', async () => {
    const generated = await summaryService.generateSummary({
      patient_id: 'patient-5',
      session_id: 'session-222',
    })
    const result = await summaryService.editSummary(generated.summary_id, {
      chief_complaint: 'Updated complaint',
    })
    expect(result.status).toBe('edited')
    expect(result.summary.chief_complaint).toBe('Updated complaint')
  })

  it('should deep merge nested edits', async () => {
    const generated = await summaryService.generateSummary({
      patient_id: 'patient-6',
      session_id: 'session-333',
    })
    const result = await summaryService.editSummary(generated.summary_id, {
      hpi: { onset: 'sudden' },
    })
    expect(result.summary.hpi).toHaveProperty('onset', 'sudden')
    // Original fields should be preserved
    expect(result.summary).toHaveProperty('chief_complaint')
  })
})