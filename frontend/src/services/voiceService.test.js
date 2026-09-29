// Voice Service Tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { voiceService } from './voiceService'
import { server } from '../test/setup'
import { http, HttpResponse } from 'msw'

describe('Voice Service', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('should convert text to speech', async () => {
    const result = await voiceService.textToSpeech('Hello world', 'en')
    expect(result).toHaveProperty('audio_b64')
    expect(result).toHaveProperty('content_type', 'audio/wav')
    expect(result).toHaveProperty('language', 'en')
    expect(result).toHaveProperty('provider')
    expect(result).toHaveProperty('latency_ms')
  })

  it('should use specified language', async () => {
    const result = await voiceService.textToSpeech('नमस्ते', 'hi')
    expect(result.language).toBe('hi')
  })

  it('should convert speech to text', async () => {
    const result = await voiceService.speechToText('base64audio', 'en')
    expect(result).toHaveProperty('transcript')
    expect(result).toHaveProperty('confidence')
    expect(result).toHaveProperty('language', 'en')
    expect(result).toHaveProperty('provider')
    expect(result).toHaveProperty('latency_ms')
  })

  it('should reject invalid base64 audio', async () => {
    await expect(voiceService.speechToText('invalid-base64!', 'en')).rejects.toThrow('Invalid audio_b64')
  })

  it('should get preloaded prompts', async () => {
    const result = await voiceService.getPrompts()
    expect(result).toHaveProperty('prompts')
    expect(result.prompts).toHaveProperty('consent')
    expect(result.prompts.consent).toHaveProperty('en')
    expect(result.prompts.consent).toHaveProperty('hi')
  })

  it('should return mock provider for TTS in test env', async () => {
    const result = await voiceService.textToSpeech('Test', 'en')
    expect(result.provider).toBe('MockTTSProvider')
  })

  it('should return mock provider for ASR in test env', async () => {
    const result = await voiceService.speechToText('base64audio', 'en')
    expect(result.provider).toBe('MockASRProvider')
  })
})