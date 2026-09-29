/**
 * Module   : Knowledge / RAG Service
 * Owner    : Frontend Engineer
 * Purpose  : Calls knowledge search and drug interaction endpoints.
 */

import { api } from './api'

export const knowledgeService = {
  async search({ query, k = 5, category, min_similarity = 0.3 }) {
    const response = await api.post('/api/knowledge/search', { query, k, category, min_similarity })
    return response.data
  },

  async checkDrugInteractions(medications) {
    const response = await api.post('/api/knowledge/drug-interactions', { medications })
    return response.data
  },
}

export default knowledgeService