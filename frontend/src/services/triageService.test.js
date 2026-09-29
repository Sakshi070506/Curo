// Triage Service Tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { triageService } from './triageService'
import { server } from '../test/setup'
import { http, HttpResponse } from 'msw'

describe('Triage Service', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('should get triage queue', async () => {
    const result = await triageService.getQueue()
    expect(result).toHaveProperty('alerts')
    expect(Array.isArray(result.alerts)).toBe(true)
  })

  it('should push a triage alert', async () => {
    const result = await triageService.pushAlert({
      patient_id: 'patient-1',
      session_id: 'session-1',
      severity: 'critical',
      matched_rules: [{ id: 'test', description: 'Test rule', severity: 'critical' }],
    })
    expect(result).toHaveProperty('id')
    expect(result.patient_id).toBe('patient-1')
    expect(result.severity).toBe('critical')
    expect(result.requires_immediate_attention).toBe(true)
  })

  it('should set requires_immediate_attention for critical severity', async () => {
    const result = await triageService.pushAlert({
      patient_id: 'p1',
      session_id: 's1',
      severity: 'critical',
      matched_rules: [],
    })
    expect(result.requires_immediate_attention).toBe(true)
  })

  it('should not set requires_immediate_attention for high severity', async () => {
    const result = await triageService.pushAlert({
      patient_id: 'p1',
      session_id: 's1',
      severity: 'high',
      matched_rules: [],
    })
    expect(result.requires_immediate_attention).toBe(false)
  })

  it('should acknowledge an alert', async () => {
    const pushed = await triageService.pushAlert({
      patient_id: 'p2',
      session_id: 's2',
      severity: 'high',
      matched_rules: [],
    })
    const result = await triageService.acknowledgeAlert(pushed.id)
    expect(result.acknowledged).toBe(true)
  })

  it('should return 404 for unknown alert', async () => {
    await expect(triageService.acknowledgeAlert('unknown-id')).rejects.toThrow('Alert not found')
  })

  it('should include alert in queue after push', async () => {
    await triageService.pushAlert({
      patient_id: 'p3',
      session_id: 's3',
      severity: 'high',
      matched_rules: [],
    })
    const queue = await triageService.getQueue()
    expect(queue.alerts.length).toBeGreaterThan(0)
    const alert = queue.alerts.find(a => a.patient_id === 'p3')
    expect(alert).toBeDefined()
  })
})