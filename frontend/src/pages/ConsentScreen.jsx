/**
 * Module   : Consent Screen
 * Owner    : Frontend Engineer
 * Purpose  : Audio-guided consent capture.
 */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSessionState } from '../hooks/useSessionState'
import { abdmService } from '../services/abdmService'
import { voiceService } from '../services/voiceService'

export function ConsentScreen() {
  const navigate = useNavigate()
  const { state, setConsent, setLoading, setError, patientId, language } = useSessionState()

  const [consent, setConsentState] = useState({
    data_capture: false,
    share_with_his: false,
    link_abha_phr: false,
  })
  const [consentLanguage, setConsentLanguage] = useState(language)
  const [playing, setPlaying] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setLocalError] = useState('')

  // Load prompts on mount
  useEffect(() => {
    const loadPrompts = async () => {
      try {
        const prompts = await voiceService.getPrompts()
        // Prompts loaded, available for TTS
      } catch (err) {
        console.warn('Could not load voice prompts:', err)
      }
    }
    loadPrompts()
  }, [])

  const playConsentScript = useCallback(async () => {
    setPlaying(true)
    try {
      // Use the consent prompt for the current language
      const prompts = await voiceService.getPrompts()
      const script = prompts.prompts?.consent?.[consentLanguage] || prompts.prompts?.consent?.en || 'We need your consent to process your health data.'
      await voiceService.textToSpeech(script, consentLanguage)
    } catch (err) {
      console.warn('TTS failed:', err)
      // Fallback: just show the text
      const prompts = await voiceService.getPrompts()
      const script = prompts.prompts?.consent?.[consentLanguage] || prompts.prompts?.consent?.en || 'We need your consent to process your health data.'
      alert(`Consent script (${consentLanguage}): ${script}`)
    } finally {
      setPlaying(false)
    }
  }, [consentLanguage])

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault()
    setLocalError('')

    if (!consent.data_capture) {
      setLocalError('Data capture consent is required to proceed')
      return
    }

    setSubmitting(true)
    try {
      const result = await abdmService.grantConsent({
        patient_id: patientId,
        ...consent,
        consent_language: consentLanguage,
      })
      setConsent(result)
      navigate('/interview')
    } catch (err) {
      setLocalError(err.message || 'Failed to record consent')
      console.error(err)
    } finally {
      setSubmitting(false)
    }
  }, [consent, consentLanguage, patientId, setConsent, navigate])

  const canProceed = consent.data_capture

  return (
    <div className="consent-screen min-h-screen flex flex-col">
      <header className="p-6 border-b">
        <h1 className="text-2xl font-bold">Curo — Consent</h1>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-4">
        <div className="w-full max-w-2xl">
          <div className="card">
            <div className="card-header text-center mb-6">
              <h2 className="text-2xl font-semibold">Your Consent Matters</h2>
              <p className="text-muted mt-1">We explain how your data will be used. Please listen and choose.</p>
            </div>

            {/* Audio player */}
            <div className="mb-6 p-4 bg-bg-secondary rounded-lg">
              <button
                type="button"
                className={`btn btn-outline w-full ${playing ? 'btn-primary' : ''}`}
                onClick={playConsentScript}
                disabled={playing}
              >
                {playing ? (
                  <>
                    <span className="spinner mr-2" aria-hidden="true"></span>
                    Playing consent explanation...
                  </>
                ) : (
                  <>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" className="mr-2" aria-hidden="true">
                      <polygon points="5 3 19 12 5 21" />
                    </svg>
                    Play Consent Explanation ({consentLanguage.toUpperCase()})
                  </>
                )}
              </button>
              <p className="text-sm text-muted mt-2 text-center">
                Listen to understand how your data will be used before giving consent.
              </p>
            </div>

            {/* Consent toggles */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <fieldset className="space-y-4">
                <legend className="font-medium mb-2">Consent Options</legend>

                {/* Required: Data Capture */}
                <label className={`flex items-start gap-3 p-4 rounded-lg border transition-colors ${consent.data_capture ? 'bg-primary-light border-primary' : 'border-border hover:border-primary'}`}>
                  <input
                    type="checkbox"
                    checked={consent.data_capture}
                    onChange={(e) => setConsentState({ ...consent, data_capture: e.target.checked })}
                    className="w-5 h-5 mt-0.5 accent-primary"
                    required
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">Data Capture & Processing <span className="text-danger">*</span></span>
                      <span className="badge bg-primary-light text-primary text-xs">Required</span>
                    </div>
                    <p className="text-sm text-muted mt-1">
                      Allow Curo to capture, store, and process your health interview responses and uploaded documents for the purpose of generating a medical case summary.
                    </p>
                  </div>
                </label>

                {/* Optional: Share with HIS */}
                <label className={`flex items-start gap-3 p-4 rounded-lg border transition-colors ${consent.share_with_his ? 'bg-secondary-light border-secondary' : 'border-border hover:border-primary'}`}>
                  <input
                    type="checkbox"
                    checked={consent.share_with_his}
                    onChange={(e) => setConsentState({ ...consent, share_with_his: e.target.checked })}
                    className="w-5 h-5 mt-0.5 accent-primary"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">Share with Hospital Information System (HIS)</span>
                      <span className="badge bg-muted text-muted text-xs">Optional</span>
                    </div>
                    <p className="text-sm text-muted mt-1">
                      Allow your case summary to be shared with the hospital's electronic medical record system for continuity of care.
                    </p>
                  </div>
                </label>

                {/* Optional: Link ABHA PHR */}
                <label className={`flex items-start gap-3 p-4 rounded-lg border transition-colors ${consent.link_abha_phr ? 'bg-info-light border-info' : 'border-border hover:border-primary'}`}>
                  <input
                    type="checkbox"
                    checked={consent.link_abha_phr}
                    onChange={(e) => setConsentState({ ...consent, link_abha_phr: e.target.checked })}
                    className="w-5 h-5 mt-0.5 accent-primary"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">Link to ABHA Personal Health Record</span>
                      <span className="badge bg-muted text-muted text-xs">Optional</span>
                    </div>
                    <p className="text-sm text-muted mt-1">
                      Link this encounter to your Ayushman Bharat Health Account (ABHA) Personal Health Record for portable health records.
                    </p>
                  </div>
                </label>
              </fieldset>

              {error && <div className="alert alert-danger" role="alert">{error}</div>}

              <button
                type="submit"
                className="btn btn-primary w-full btn-lg"
                disabled={submitting || !canProceed}
              >
                {submitting ? 'Recording Consent...' : 'Continue to Interview'}
              </button>

              {!canProceed && (
                <p className="text-center text-sm text-muted">
                  Please enable "Data Capture & Processing" to proceed.
                </p>
              )}
            </form>
          </div>
        </div>
      </main>

      <footer className="p-4 text-center text-sm text-muted border-t">
        Curo v0.1.0 — Hackathon Demo
      </footer>
    </div>
  )
}

export default ConsentScreen