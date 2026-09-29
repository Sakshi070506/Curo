// VoiceInputBar Component Tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { VoiceInputBar } from '../components/VoiceInputBar'
import { useVoiceCapture, useWebSpeechASR } from '../hooks/useVoiceCapture'
import React from 'react'

// eslint-disable-next-line no-unused-vars
vi.mock('../hooks/useVoiceCapture', () => ({
  useVoiceCapture: vi.fn(),
  useWebSpeechASR: vi.fn(),
}))

vi.mock('../services/voiceService', () => ({
  voiceService: {
    textToSpeech: vi.fn().mockResolvedValue({ provider: 'MockTTSProvider' }),
  },
}))

describe('VoiceInputBar', () => {
  const mockUseVoiceCapture = {
    isRecording: false,
    transcript: '',
    error: null,
    isSupported: true,
    startRecording: vi.fn().mockResolvedValue(true),
    stopRecording: vi.fn(),
    clearTranscript: vi.fn(),
    submitToASR: vi.fn(),
  }

  const mockUseWebSpeechASR = {
    isListening: false,
    transcript: '',
    error: null,
    startListening: vi.fn(),
    stopListening: vi.fn(),
  }

  beforeEach(() => {
    vi.resetAllMocks()
    useVoiceCapture.mockReturnValue(mockUseVoiceCapture)
    useWebSpeechASR.mockReturnValue(mockUseWebSpeechASR)
  })

  it('should render voice controls', () => {
    render(<VoiceInputBar language="en" />)
    expect(screen.getByRole('button', { name: /start recording/i })).toBeInTheDocument()
  })

  it('should show transcript when available', () => {
    useVoiceCapture.mockReturnValue({ ...mockUseVoiceCapture, transcript: 'Hello world' })
    render(<VoiceInputBar language="en" />)
    expect(screen.getByText('Hello world')).toBeInTheDocument()
  })

  it('should call onTranscript callback', () => {
    const onTranscript = vi.fn()
    useVoiceCapture.mockReturnValue({ ...mockUseVoiceCapture, transcript: 'Test transcript' })
    render(<VoiceInputBar language="en" onTranscript={onTranscript} />)
    expect(onTranscript).toHaveBeenCalledWith('Test transcript')
  })

  it('should toggle between MediaRecorder and Web Speech', () => {
    render(<VoiceInputBar language="en" />)
    const checkbox = screen.getByRole('checkbox', { name: /use browser speech recognition/i })
    expect(checkbox).not.toBeChecked()
    fireEvent.click(checkbox)
    expect(checkbox).toBeChecked()
  })

  it('should disable controls when disabled prop is true', () => {
    render(<VoiceInputBar language="en" disabled />)
    expect(screen.getByRole('button', { name: /start recording/i })).toBeDisabled()
  })

  it('should show error message', () => {
    useVoiceCapture.mockReturnValue({ ...mockUseVoiceCapture, error: 'Microphone access denied' })
    render(<VoiceInputBar language="en" />)
    expect(screen.getByText('Microphone access denied')).toBeInTheDocument()
  })

  it('should show clear button when transcript exists', () => {
    useVoiceCapture.mockReturnValue({ ...mockUseVoiceCapture, transcript: 'Some text' })
    render(<VoiceInputBar language="en" />)
    expect(screen.getByRole('button', { name: /clear transcript/i })).toBeInTheDocument()
  })
})