/**
 * Module   : Document Service
 * Owner    : Frontend Engineer
 * Purpose  : Calls document upload/digitization endpoints.
 */

import { api } from './api'

export const documentService = {
  async uploadDocument(file, { patientId, onProgress }) {
    const formData = new FormData()
    formData.append('file', file)
    if (patientId) formData.append('patient_id', patientId)

    const response = await api.post('/api/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress ? (progressEvent) => {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percent)
      } : undefined,
    })
    return response.data
  },

  async extractDocument(file) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/api/documents/extract', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  async getTimeline(patientId) {
    const response = await api.get(`/api/documents/${patientId}/timeline`)
    return response.data
  },
}

export default documentService