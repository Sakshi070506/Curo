/**
 * Module   : Voice Input Component
 * Owner    : Frontend Engineer
 * Purpose  : Mic button + live transcript display.
 */

import { useState, useCallback, useEffect } from 'react'
import { useVoiceCapture, useWebSpeechASR } from '../hooks/useVoiceCapture'
import { voiceService } from '../services/voiceService'

export function VoiceInputBar({
  language = 'en',
  onTranscript,
  disabled = false,
  className = '',
}) {
  const [useWebSpeech, setUseWebSpeech] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)

  const {
    isRecording,
    transcript,
    error,
    isSupported,
    startRecording,
    stopRecording,
    submitToASR,
    clearTranscript,
  } = useVoiceCapture()

  const {
    isListening,
    transcript: wsTranscript,
    error: wsError,
    startListening,
    stopListening,
  } = useWebSpeechASR(language)

  const activeTranscript = useWebSpeech ? wsTranscript : transcript
  const activeError = useWebSpeech ? wsError : error
  const activeIsActive = useWebSpeech ? isListening : isRecording

  // Notify parent of transcript changes
  useEffect(() => {
    if (activeTranscript && onTranscript) {
      onTranscript(activeTranscript)
    }
  }, [activeTranscript, onTranscript])

  const handleStart = useCallback(async () => {
    if (useWebSpeech) {
      startListening()
    } else {
      await startRecording(language)
    }
  }, [useWebSpeech, startListening, startRecording, language])

  const handleStop = useCallback(() => {
    if (useWebSpeech) {
      stopListening()
    } else {
      stopRecording()
    }
  }, [useWebSpeech, stopListening, stopRecording])

  const handleClear = useCallback(() => {
    if (!useWebSpeech) clearTranscript()
    else {
      // Web Speech ASR doesn't have a clear function, transcript is managed by the hook
    }
  }, [useWebSpeech, clearTranscript])

  // TTS playback for mock provider detection
  const playTTS = useCallback(async (text) => {
    if (isPlaying) return
    setIsPlaying(true)
    try {
      const result = await voiceService.textToSpeech(text, language)
      if (result.provider === 'MockTTSProvider') {
        console.warn('Mock TTS provider - audio playback not available')
        // Show text fallback instead of playing
        alert(`TTS (mock): ${text}`)
      } else {
        const audio = new Audio(`data:${result.content_type};base64,${result.audio_b64}`)
        audio.play()
      }
    } catch (err) {
      console.error('TTS playback failed:', err)
    } finally {
      setIsPlaying(false)
    }
  }, [language, isPlaying])

  if (!isSupported && !('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
    return (
      <div className={`voice-input-bar ${className}`} role="region" aria-label="Voice input not supported">
        <p className="text-muted">Voice input not supported in this browser. Please use text input.</p>
      </div>
    )
  }

  return (
    <div className={`voice-input-bar ${className}`} role="region" aria-label="Voice input">
      <div className="voice-controls flex gap-2 items-center">
        <button
          type="button"
          className={`btn ${activeIsActive ? 'btn-danger' : 'btn-primary'} btn-lg`}
          onClick={activeIsActive ? handleStop : handleStart}
          disabled={disabled}
          aria-pressed={activeIsActive}
          aria-label={activeIsActive ? 'Stop recording' : 'Start recording'}
          style={{ minWidth: '56px', minHeight: '56px' }}
        >
          {activeIsActive ? (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <rect x="6" y="4" width="12" height="16" rx="2" />
            </svg>
          ) : (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <circle cx="12" cy="12" r="8" />
            </svg>
          )}
        </button>

        {activeTranscript && (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={handleClear}
            aria-label="Clear transcript"
          >
            ✕ Clear
          </button>
        )}

        <label className="flex items-center gap-2 text-sm" style={{ minWidth: '200px' }}>
          <input
            type="checkbox"
            checked={useWebSpeech}
            onChange={(e) => setUseWebSpeech(e.target.checked)}
            disabled={activeIsActive}
          />
          Use browser speech recognition
        </label>
      </div>

      {activeTranscript && (
        <div className="transcript-display mt-3 p-3 bg-surface border rounded-lg min-h-[60px]" aria-live="polite">
          <p className="font-medium text-sm text-muted mb-1">Transcript:</p>
          <p>{activeTranscript}</p>
        </div>
      )}

      {activeError && (
        <div className="alert alert-danger mt-3" role="alert">
          {activeError}
        </div>
      )}
    </div>
  )
}

export default VoiceInputBar