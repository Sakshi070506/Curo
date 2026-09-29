/**
 * Module   : Summary Service
 * Owner    : Frontend Engineer
 * Purpose  : Calls summary generation/management endpoints.
 */

import { api } from './api'

export const summaryService = {
  async generateSummary({ patient_id, session_id }) {
    const response = await api.post('/api/summary/generate', { patient_id, session_id })
    return response.data
  },

  async getSummary(summary_id) {
    const response = await api.get(`/api/summary/${summary_id}`)
    return response.data
  },

  async confirmSummary(summary_id, { summary, confirmed }) {
    const response = await api.post(`/api/summary/${summary_id}/confirm`, { summary, confirmed })
    return response.data
  },

  async editSummary(summary_id, patches) {
    const response = await api.patch(`/api/summary/${summary_id}/edit`, patches)
    return response.data
  },
}

export default summaryService