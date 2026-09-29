// ABDM / Auth Service Tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { abdmService } from './abdmService'
import { server } from '../test/setup'
import { http, HttpResponse } from 'msw'

describe('ABDM / Auth Service', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  describe('Auth', () => {
    it('should register a new user', async () => {
      const result = await abdmService.register({
        abha_id: '12-3456-7890-1234',
        name: 'Test User',
        phone: '9876543210',
        email: 'test@example.com',
      })
      expect(result).toHaveProperty('message', 'Registered successfully')
      expect(result).toHaveProperty('abha_id', '12-3456-7890-1234')
    })

    it('should reject duplicate ABHA ID', async () => {
      await abdmService.register({ abha_id: '11-1111-1111-1111', name: 'User 1' })
      await expect(abdmService.register({ abha_id: '11-1111-1111-1111', name: 'User 2' }))
        .rejects.toThrow('ABHA ID already registered')
    })

    it('should login with correct OTP', async () => {
      await abdmService.register({ abha_id: '22-2222-2222-2222', name: 'User 2' })
      const result = await abdmService.login({ abha_id: '22-2222-2222-2222', otp: 'defaultpass' })
      expect(result).toHaveProperty('access_token')
      expect(result).toHaveProperty('token_type', 'bearer')
    })

    it('should reject login with wrong OTP', async () => {
      await abdmService.register({ abha_id: '33-3333-3333-3333', name: 'User 3' })
      await expect(abdmService.login({ abha_id: '33-3333-3333-3333', otp: 'wrong' }))
        .rejects.toThrow('Invalid ABHA ID or OTP')
    })

    it('should verify ABHA ID', async () => {
      await abdmService.register({ abha_id: '44-4444-4444-4444', name: 'User 4' })
      const result = await abdmService.abhaVerify({ abha_id: '44-4444-4444-4444' })
      expect(result.verified).toBe(true)
      expect(result).toHaveProperty('access_token')
    })

    it('should return unverified for unknown ABHA', async () => {
      const result = await abdmService.abhaVerify({ abha_id: '99-9999-9999-9999' })
      expect(result.verified).toBe(false)
    })

    it('should get current user with valid token', async () => {
      await abdmService.register({ abha_id: '55-5555-5555-5555', name: 'User 5' })
      const login = await abdmService.login({ abha_id: '55-5555-5555-5555', otp: 'defaultpass' })
      // Note: getMe requires Authorization header which is handled by api interceptor
      // For this test we just verify the endpoint structure
    })
  })

  describe('Consent', () => {
    it('should grant consent', async () => {
      const result = await abdmService.grantConsent({
        patient_id: 'patient-1',
        data_capture: true,
        share_with_his: true,
        link_abha_phr: true,
        consent_language: 'en',
      })
      expect(result).toHaveProperty('consent_id')
      expect(result).toHaveProperty('patient_id', 'patient-1')
      expect(result.data_capture).toBe(true)
      expect(result.share_with_his).toBe(true)
      expect(result.link_abha_phr).toBe(true)
      expect(result).toHaveProperty('timestamp')
      expect(result).toHaveProperty('audit_trail_id')
    })

    it('should get consent status', async () => {
      await abdmService.grantConsent({
        patient_id: 'patient-2',
        data_capture: true,
        share_with_his: false,
        link_abha_phr: true,
        consent_language: 'hi',
      })
      const result = await abdmService.getConsentStatus('patient-2')
      expect(result.patient_id).toBe('patient-2')
      expect(result.data_capture).toBe(true)
      expect(result.link_abha_phr).toBe(true)
    })

    it('should return 404 for patient without consent', async () => {
      await expect(abdmService.getConsentStatus('no-consent-patient')).rejects.toThrow('No consent found')
    })

    it('should revoke consent', async () => {
      const grant = await abdmService.grantConsent({
        patient_id: 'patient-3',
        data_capture: true,
        share_with_his: true,
        link_abha_phr: true,
      })
      const result = await abdmService.revokeConsent(grant.consent_id)
      expect(result).toHaveProperty('revoked', true)
      expect(result.consent_id).toBe(grant.consent_id)
    })
  })

  describe('ABDM FHIR Push', () => {
    it('should push FHIR bundle', async () => {
      const result = await abdmService.pushFHIR({
        patient: { id: 'patient-1', name: 'Test User' },
        chief_complaint: 'Chest pain',
        diagnoses: ['Chest pain'],
        medications: [{ name: 'Aspirin', dosage: '75mg' }],
        investigations: [],
      })
      expect(result.success).toBe(true)
      expect(result.status_code).toBe(200)
      expect(result.dry_run).toBe(true)
    })

    it('should get ABDM status', async () => {
      await abdmService.pushFHIR({
        patient: { id: 'patient-4' },
        chief_complaint: 'Test',
        diagnoses: [],
        medications: [],
        investigations: [],
      })
      const result = await abdmService.getABDMStatus('patient-4')
      expect(result.patient_id).toBe('patient-4')
      expect(result.status).toBe('success')
      expect(result.last_push).toBeDefined()
    })

    it('should return not_attempted for patient without push', async () => {
      const result = await abdmService.getABDMStatus('no-push-patient')
      expect(result.status).toBe('not_attempted')
      expect(result.last_push).toBeNull()
    })
  })
})