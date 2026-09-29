/**
 * Module   : Patient Summary Confirmation
 * Owner    : Frontend Engineer
 * Purpose  : Patient-facing audio confirmation of captured history.
 */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSessionState } from '../hooks/useSessionState'
import { summaryService } from '../services/summaryService'
import { voiceService } from '../services/voiceService'

export function SummaryReview() {
  const navigate = useNavigate()
  const { state, sessionId, patientId, summary, setSummary, setLoading, setError } = useSessionState()

  const [generating, setGenerating] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [correction, setCorrection] = useState('')
  const [error, setLocalError] = useState('')

  // Generate summary on mount if not already present
  useEffect(() => {
    if (!summary && sessionId && patientId) {
      generateSummary()
    }
  }, [summary, sessionId, patientId])

  const generateSummary = useCallback(async () => {
    setGenerating(true)
    setLocalError('')
    try {
      const result = await summaryService.generateSummary({ patient_id: patientId, session_id: sessionId })
      setSummary(result.summary_id, result.summary)
    } catch (err) {
      setLocalError(err.message || 'Failed to generate summary')
      console.error(err)
    } finally {
      setGenerating(false)
    }
  }, [patientId, sessionId, setSummary])

  const playSummary = useCallback(async () => {
    if (!summary || playing) return
    setPlaying(true)
    try {
      // Build readable text from summary
      const s = summary.summary || summary
      const textParts = []
      if (s.chief_complaint) textParts.push(`Chief complaint: ${s.chief_complaint}`)
      if (s.hpi && Object.keys(s.hpi).length > 0) {
        textParts.push('History: ' + Object.entries(s.hpi).map(([k, v]) => `${k}: ${v}`).join('; '))
      }
      if (s.past_medical_history?.length) textParts.push('Past history: ' + s.past_medical_history.join(', '))
      if (s.medications_from_docs?.length) textParts.push('Medications: ' + s.medications_from_docs.map(m => m.name).join(', '))
      const fullText = textParts.join('. ') || 'Summary generated. Please review on screen.'

      const result = await voiceService.textToSpeech(fullText, state.language)
      if (result.provider === 'MockTTSProvider') {
        alert(`Summary (TTS mock): ${fullText}`)
      } else {
        const audio = new Audio(`data:${result.content_type};base64,${result.audio_b64}`)
        await audio.play()
      }
    } catch (err) {
      console.warn('TTS playback failed:', err)
    } finally {
      setPlaying(false)
    }
  }, [summary, state.language, playing])

  const handleFlagCorrection = useCallback(() => {
    if (!correction.trim()) {
      alert('Please describe what needs correction')
      return
    }
    // Navigate to physician console with correction flag
    navigate('/doctor', { state: { patientCorrection: correction } })
  }, [correction, navigate])

  const handleProceed = useCallback(() => {
    navigate('/doctor')
  }, [navigate])

  if (generating) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <span className="spinner mx-auto mb-4" aria-hidden="true"></span>
          <p>Generating your case summary...</p>
        </div>
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted">No summary available. Redirecting...</p>
        </div>
      </div>
    )
  }

  const s = summary.summary || summary

  return (
    <div className="summary-review min-h-screen flex flex-col">
      <header className="p-4 border-b bg-surface sticky top-0 z-10">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="font-semibold">Review Summary</h1>
            <p className="text-sm text-muted">Confirm your case summary before sharing with the doctor</p>
          </div>
          <div className="text-right text-sm text-muted">
            Patient: {patientId}
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-3xl mx-auto w-full p-4">
        {error && <div className="alert alert-danger mb-4" role="alert">{error}</div>}

        <div className="card mb-6">
          <div className="card-header flex items-center justify-between">
            <h2 className="text-xl font-semibold">Your Case Summary</h2>
            <button
              type="button"
              className={`btn btn-outline ${playing ? 'btn-primary' : ''}`}
              onClick={playSummary}
              disabled={playing}
            >
              {playing ? (
                <>
                  <span className="spinner mr-2" aria-hidden="true"></span>
                  Playing...
                </>
              ) : (
                <>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" className="mr-2" aria-hidden="true">
                    <polygon points="5 3 19 12 5 21" />
                  </svg>
                  Play Summary
                </>
              )}
            </button>
          </div>

          <div className="space-y-4">
            {s.chief_complaint && (
              <div>
                <h3 className="font-medium text-muted mb-1">Chief Complaint</h3>
                <p>{s.chief_complaint}</p>
              </div>
            )}

            {s.hpi && Object.keys(s.hpi).length > 0 && (
              <div>
                <h3 className="font-medium text-muted mb-1">History of Present Illness</h3>
                <dl className="space-y-2">
                  {Object.entries(s.hpi).map(([key, value]) => (
                    <div key={key} className="flex gap-2">
                      <dt className="font-medium capitalize min-w-[150px]">{key.replace(/_/g, ' ')}</dt>
                      <dd className="flex-1">{value}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}

            {s.past_medical_history?.length && (
              <div>
                <h3 className="font-medium text-muted mb-1">Past Medical History</h3>
                <ul className="list-disc list-inside space-y-1">
                  {s.past_medical_history.map((item, i) => <li key={i}>{item}</li>)}
                </ul>
              </div>
            )}

            {s.drug_allergy_history?.length && (
              <div>
                <h3 className="font-medium text-muted mb-1">Drug Allergies</h3>
                <ul className="list-disc list-inside space-y-1 text-danger">
                  {s.drug_allergy_history.map((item, i) => <li key={i}>{item}</li>)}
                </ul>
              </div>
            )}

            {s.family_history?.length && (
              <div>
                <h3 className="font-medium text-muted mb-1">Family History</h3>
                <ul className="list-disc list-inside space-y-1">
                  {s.family_history.map((item, i) => <li key={i}>{item}</li>)}
                </ul>
              </div>
            )}

            {s.medications_from_docs?.length && (
              <div>
                <h3 className="font-medium text-muted mb-1">Medications (from documents)</h3>
                <ul className="space-y-1">
                  {s.medications_from_docs.map((m, i) => (
                    <li key={i} className="text-sm">{m.name} {m.dosage} {m.frequency}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Correction Flag */}
        <div className="card mb-4 border-warning">
          <div className="card-header">
            <h3 className="font-medium flex items-center gap-2">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-warning" aria-hidden="true">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              Something not right?
            </h3>
          </div>
          <div className="space-y-2">
            <textarea
              value={correction}
              onChange={(e) => setCorrection(e.target.value)}
              placeholder="Describe what needs correction (optional)..."
              className="w-full min-h-[80px] resize-y"
              rows={3}
            />
            <button
              type="button"
              className="btn btn-outline"
              onClick={handleFlagCorrection}
              disabled={!correction.trim()}
            >
              Flag for Doctor Review
            </button>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            type="button"
            className="btn btn-primary flex-1 btn-lg"
            onClick={handleProceed}
          >
            Looks Good — Share with Doctor
          </button>
          <button
            type="button"
            className="btn btn-outline flex-1 btn-lg"
            onClick={generateSummary}
          >
            Regenerate Summary
          </button>
        </div>
      </main>

      <footer className="p-4 text-center text-sm text-muted border-t">
        Curo v0.1.0 — Hackathon Demo
      </footer>
    </div>
  )
}

export default SummaryReview