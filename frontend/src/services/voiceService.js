/**
 * Module   : Voice Service
 * Owner    : Frontend Engineer
 * Purpose  : Calls TTS/ASR endpoints.
 */

import { api } from './api'

export const voiceService = {
  async textToSpeech(text, language = 'en') {
    const response = await api.post('/api/voice/tts', { text, language })
    return response.data
  },

  async speechToText(audioBase64, language = 'en') {
    const response = await api.post('/api/voice/asr', { audio_b64: audioBase64, language })
    return response.data
  },

  async getPrompts() {
    const response = await api.get('/api/voice/prompts')
    return response.data
  },
}

export default voiceService