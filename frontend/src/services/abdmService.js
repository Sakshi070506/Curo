/**
 * Module   : ABDM / Consent / Auth Service
 * Owner    : Frontend Engineer
 * Purpose  : Calls consent/ABDM/auth endpoints.
 */

import { api } from './api'

export const abdmService = {
  // Consent
  async grantConsent(payload) {
    const response = await api.post('/api/consent/grant', payload)
    return response.data
  },

  async getConsentStatus(patientId) {
    const response = await api.get(`/api/consent/status/${patientId}`)
    return response.data
  },

  async revokeConsent(consentId) {
    const response = await api.delete(`/api/consent/revoke/${consentId}`)
    return response.data
  },

  // ABDM FHIR push
  async pushFHIR(payload) {
    const response = await api.post('/api/abdm/push-fhir', payload)
    return response.data
  },

  async getABDMStatus(patientId) {
    const response = await api.get(`/api/abdm/status/${patientId}`)
    return response.data
  },

  // Auth
  async register(payload) {
    const response = await api.post('/api/auth/register', payload)
    return response.data
  },

  async login(payload) {
    const response = await api.post('/api/auth/login', payload)
    return response.data
  },

  async abhaVerify(payload) {
    const response = await api.post('/api/auth/abha-verify', payload)
    return response.data
  },

  async getMe() {
    const response = await api.get('/api/auth/me')
    return response.data
  },
}

export default abdmService