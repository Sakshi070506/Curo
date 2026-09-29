// History Service Tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { historyService } from './historyService'
import { server } from '../test/setup'
import { http, HttpResponse } from 'msw'

describe('History Service', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('should start a new session', async () => {
    const result = await historyService.startSession({ language: 'en', ayush_mode: false })
    expect(result).toHaveProperty('session_id')
    expect(result).toHaveProperty('next_question')
    expect(result.next_question).toHaveProperty('question_id', 'chief_complaint')
    expect(result.next_question).toHaveProperty('prompt', 'What brings you in today?')
  })

  it('should start session with AYUSH mode', async () => {
    const result = await historyService.startSession({ language: 'hi', ayush_mode: true })
    expect(result.next_question.question_id).toBe('chief_complaint')
  })

  it('should submit an answer', async () => {
    // First start a session
    const session = await historyService.startSession({ language: 'en' })
    const result = await historyService.submitAnswer({
      session_id: session.session_id,
      question_id: 'chief_complaint',
      answer_text: 'Chest pain',
    })
    expect(result).toHaveProperty('session_id', session.session_id)
    expect(result).toHaveProperty('state')
    expect(result).toHaveProperty('red_flag')
    expect(result).toHaveProperty('complete')
  })

  it('should submit answer with audio', async () => {
    const session = await historyService.startSession({ language: 'en' })
    const result = await historyService.submitAnswer({
      session_id: session.session_id,
      question_id: 'chief_complaint',
      audio_b64: 'base64audio',
    })
    expect(result.session_id).toBe(session.session_id)
  })

  it('should reject answer without text or audio', async () => {
    const session = await historyService.startSession({ language: 'en' })
    await expect(historyService.submitAnswer({
      session_id: session.session_id,
      question_id: 'chief_complaint',
    })).rejects.toThrow()
  })

  it('should get session details', async () => {
    const session = await historyService.startSession({ language: 'en' })
    const result = await historyService.getSession(session.session_id)
    expect(result.session_id).toBe(session.session_id)
    expect(result).toHaveProperty('chief_complaint')
    expect(result).toHaveProperty('hpi')
  })

  it('should return 404 for unknown session', async () => {
    await expect(historyService.getSession('unknown-id')).rejects.toThrow('Session not found')
  })

  it('should check red flag', async () => {
    const result = await historyService.checkRedFlag('I have chest pain and shortness of breath')
    expect(result).toHaveProperty('triggered', true)
    expect(result.matched_rules.length).toBeGreaterThan(0)
    expect(result.highest_severity).toBe('critical')
  })

  it('should return no red flag for normal text', async () => {
    const result = await historyService.checkRedFlag('I have a mild headache')
    expect(result.triggered).toBe(false)
    expect(result.highest_severity).toBe('none')
  })
})