// useVoiceCapture Hook Tests
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useVoiceCapture, useWebSpeechASR } from './useVoiceCapture'

describe('useVoiceCapture', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    // Mock MediaRecorder
    global.MediaRecorder = vi.fn().mockImplementation(() => ({
      state: 'inactive',
      start: vi.fn(),
      stop: vi.fn(),
      ondataavailable: null,
      onstop: null,
    }))
    global.MediaRecorder.isTypeSupported = vi.fn().mockReturnValue(true)
    global.navigator.mediaDevices = {
      getUserMedia: vi.fn().mockResolvedValue({
        getTracks: () => [{ stop: vi.fn() }],
      }),
    }
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should return initial state', () => {
    const { result } = renderHook(() => useVoiceCapture())
    expect(result.current.isRecording).toBe(false)
    expect(result.current.transcript).toBe('')
    expect(result.current.error).toBeNull()
    expect(result.current.isSupported).toBe(true)
  })

  it('should start recording', async () => {
    const { result } = renderHook(() => useVoiceCapture())
    await act(async () => {
      const started = await result.current.startRecording('en')
      expect(started).toBe(true)
    })
    expect(result.current.isRecording).toBe(true)
  })

  it('should stop recording', async () => {
    const { result } = renderHook(() => useVoiceCapture())
    await act(async () => {
      await result.current.startRecording('en')
      result.current.stopRecording()
    })
    expect(result.current.isRecording).toBe(false)
  })

  it('should clear transcript', async () => {
    const { result } = renderHook(() => useVoiceCapture())
    act(() => {
      result.current.clearTranscript()
    })
    expect(result.current.transcript).toBe('')
  })

  it('should return isSupported false when MediaRecorder not available', () => {
    const originalMediaRecorder = global.MediaRecorder
    global.MediaRecorder = undefined
    const { result } = renderHook(() => useVoiceCapture())
    expect(result.current.isSupported).toBe(false)
    global.MediaRecorder = originalMediaRecorder
  })
})

describe('useWebSpeechASR', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    global.SpeechRecognition = vi.fn().mockImplementation(() => ({
      continuous: false,
      interimResults: false,
      lang: 'en-US',
      start: vi.fn(),
      stop: vi.fn(),
      onstart: null,
      onend: null,
      onresult: null,
      onerror: null,
    }))
    global.webkitSpeechRecognition = global.SpeechRecognition
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should return initial state', () => {
    const { result } = renderHook(() => useWebSpeechASR('en'))
    expect(result.current.isListening).toBe(false)
    expect(result.current.transcript).toBe('')
    expect(result.current.error).toBeNull()
  })

  it('should start listening', () => {
    const { result } = renderHook(() => useWebSpeechASR('en'))
    act(() => {
      result.current.startListening()
    })
    expect(result.current.isListening).toBe(true)
  })

  it('should stop listening', () => {
    const { result } = renderHook(() => useWebSpeechASR('en'))
    act(() => {
      result.current.startListening()
      result.current.stopListening()
    })
    expect(result.current.isListening).toBe(false)
  })

  it('should return error when SpeechRecognition not supported', () => {
    const originalSR = global.SpeechRecognition
    const originalWSR = global.webkitSpeechRecognition
    global.SpeechRecognition = undefined
    global.webkitSpeechRecognition = undefined
    const { result } = renderHook(() => useWebSpeechASR('en'))
    expect(result.current.error).toBe('Web Speech API not supported')
    global.SpeechRecognition = originalSR
    global.webkitSpeechRecognition = originalWSR
  })
})