/**
 * Module   : Triage Service
 * Owner    : Frontend Engineer
 * Purpose  : Calls triage queue endpoints.
 */

import { api } from './api'

export const triageService = {
  async getQueue() {
    const response = await api.get('/api/triage/queue')
    return response.data
  },

  async acknowledgeAlert(alert_id) {
    const response = await api.post(`/api/triage/acknowledge/${alert_id}`)
    return response.data
  },

  async pushAlert(payload) {
    const response = await api.post('/api/triage/alert', payload)
    return response.data
  },
}

export default triageService