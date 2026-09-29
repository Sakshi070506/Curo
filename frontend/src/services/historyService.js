/**
 * Module   : History Service
 * Owner    : Frontend Engineer
 * Purpose  : Calls history/interview endpoints.
 */

import { api } from './api'

export const historyService = {
  async startSession({ language = 'en', ayush_mode = false }) {
    const response = await api.post('/api/history/start-session', { language, ayush_mode })
    return response.data
  },

  async submitAnswer({ session_id, question_id, answer_text, audio_b64 }) {
    const response = await api.post('/api/history/answer', { session_id, question_id, answer_text, audio_b64 })
    return response.data
  },

  async getSession(session_id) {
    const response = await api.get(`/api/history/session/${session_id}`)
    return response.data
  },

  async checkRedFlag(text) {
    const response = await api.post('/api/history/redflag-check', { text })
    return response.data
  },
}

export default historyService