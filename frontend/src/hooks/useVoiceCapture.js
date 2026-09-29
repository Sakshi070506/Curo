/**
 * Module   : Voice Capture Hook
 * Owner    : Frontend Engineer
 * Purpose  : Custom hook wrapping mic capture + ASR call.
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { api } from '../services/api'

export function useVoiceCapture() {
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState(null)
  const [isSupported, setIsSupported] = useState(false)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const streamRef = useRef(null)

  useEffect(() => {
    const supported = 'MediaRecorder' in window && 'mediaDevices' in navigator
    setIsSupported(supported)
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop())
      }
    }
  }, [])

  const startRecording = useCallback(async (language = 'en') => {
    if (!isSupported) {
      setError('Voice recording not supported in this browser')
      return false
    }

    try {
      setError(null)
      setTranscript('')

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4'
      const recorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = recorder
      audioChunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        const blob = new Blob(audioChunksRef.current, { type: mimeType })
        const base64 = await blobToBase64(blob)
        await submitToASR(base64, language)
      }

      recorder.start(100) // Collect data every 100ms
      setIsRecording(true)
      return true
    } catch (err) {
      setError(err.message || 'Failed to start recording')
      return false
    }
  }, [isSupported])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop())
        streamRef.current = null
      }
      setIsRecording(false)
    }
  }, [])

  const submitToASR = useCallback(async (audioBase64, language) => {
    try {
      const response = await api.post('/api/voice/asr', { audio_b64: audioBase64, language })
      if (response.data.provider === 'MockASRProvider') {
        // Mock provider returns fake transcript; show it but warn
        setTranscript(response.data.transcript)
        console.warn('Mock ASR provider - transcript is not real')
      } else {
        setTranscript(response.data.transcript)
      }
      return response.data
    } catch (err) {
      setError(err.message || 'Speech recognition failed')
      return null
    }
  }, [])

  const clearTranscript = useCallback(() => setTranscript(''), [])

  return {
    isRecording,
    transcript,
    error,
    isSupported,
    startRecording,
    stopRecording,
    submitToASR,
    clearTranscript,
  }
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      const base64 = reader.result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

// Web Speech API fallback (for browsers without MediaRecorder support)
export function useWebSpeechASR(language = 'en') {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState(null)
  const recognitionRef = useRef(null)

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setError('Web Speech API not supported')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = language

    recognition.onstart = () => setIsListening(true)
    recognition.onend = () => setIsListening(false)
    recognition.onerror = (e) => setError(e.error)
    recognition.onresult = (e) => {
      const result = e.results[e.results.length - 1]
      if (result.isFinal) {
        setTranscript(result[0].transcript)
      }
    }

    recognitionRef.current = recognition
    return () => { recognition.stop() }
  }, [language])

  const startListening = useCallback(() => {
    if (recognitionRef.current) {
      setError(null)
      setTranscript('')
      recognitionRef.current.start()
    }
  }, [])

  const stopListening = useCallback(() => {
    if (recognitionRef.current) recognitionRef.current.stop()
  }, [])

  return { isListening, transcript, error, startListening, stopListening }
}