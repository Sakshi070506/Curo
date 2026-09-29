/**
 * Module   : History Interview Screen
 * Owner    : Frontend Engineer
 * Purpose  : Core voice+touch Q&A interview UI.
 */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSessionState } from '../hooks/useSessionState'
import { historyService } from '../services/historyService'
import { VoiceInputBar } from '../components/VoiceInputBar'
import { TouchOptionCard } from '../components/TouchOptionCard'
import { RedFlagBanner } from '../components/RedFlagBanner'

export function HistoryInterview() {
  const navigate = useNavigate()
  const { state, sessionId, currentQuestion, sessionState, setQuestion, setLoading, setError, addRedFlag, patientId } = useSessionState()

  const [answer, setAnswer] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [localError, setLocalError] = useState('')
  const [showTextInput, setShowTextInput] = useState(true)

  // Load question on mount or when sessionId changes
  useEffect(() => {
    if (sessionId && !currentQuestion) {
      // Question should already be in state from LanguageSelect
      // If not, we could fetch it, but for now assume it's there
    }
  }, [sessionId, currentQuestion])

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault()
    setLocalError('')

    if (!answer.trim()) {
      setLocalError('Please provide an answer')
      return
    }

    if (!sessionId) {
      setLocalError('Session not found')
      return
    }

    setSubmitting(true)
    try {
      const result = await historyService.submitAnswer({
        session_id: sessionId,
        question_id: currentQuestion?.question_id,
        answer_text: answer.trim(),
      })

      // Check for red flag
      if (result.red_flag?.triggered) {
        addRedFlag({
          ...result.red_flag,
          symptom: currentQuestion?.prompt,
        })
      }

      // Update question
      setQuestion(result.next_question)

      // Clear answer
      setAnswer('')

      // Navigate if complete
      if (result.complete) {
        navigate('/documents')
      }
    } catch (err) {
      setLocalError(err.message || 'Failed to submit answer')
      console.error(err)
    } finally {
      setSubmitting(false)
    }
  }, [answer, sessionId, currentQuestion, setQuestion, addRedFlag, navigate])

  const handleVoiceTranscript = useCallback((transcript) => {
    setAnswer(transcript)
  }, [])

  if (!sessionId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted">No active session. Redirecting...</p>
        </div>
      </div>
    )
  }

  const progress = currentQuestion ? 1 : 0 // Could calculate actual progress from sessionState

  return (
    <div className="history-interview min-h-screen flex flex-col">
      <header className="p-4 border-b bg-surface sticky top-0 z-10">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="font-semibold">Interview</h1>
            <p className="text-sm text-muted">{sessionState} • {currentQuestion?.question_id || 'Loading...'}</p>
          </div>
          <div className="text-right text-sm text-muted">
            Patient: {patientId}
          </div>
        </div>
        <div className="mt-2 max-w-3xl mx-auto">
          <div className="progress-bar" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
            <div className="progress-bar-fill" style={{ width: `${Math.min(progress * 100, 100)}%` }} />
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-3xl mx-auto w-full p-4">
        {/* Red Flag Banner */}
        <RedFlagBanner redFlags={state.redFlags} />

        {localError && <div className="alert alert-danger mb-4" role="alert">{localError}</div>}

        {/* Question Card */}
        <div className="card mb-6" role="region" aria-labelledby="question-title">
          <div className="card-header">
            <h2 id="question-title" className="text-xl font-semibold">
              {currentQuestion?.prompt || 'Loading question...'}
            </h2>
            <p className="text-sm text-muted mt-1">
              Question: {currentQuestion?.question_id} • State: {currentQuestion?.state || sessionState}
            </p>
          </div>

          <div className="space-y-4">
            {/* Voice Input */}
            <VoiceInputBar
              language={state.language}
              onTranscript={handleVoiceTranscript}
              disabled={submitting}
            />

            {/* Text Input Fallback */}
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showTextInput}
                  onChange={(e) => setShowTextInput(e.target.checked)}
                />
                <span className="text-sm">Show text input</span>
              </label>
            </div>

            {showTextInput && (
              <form onSubmit={handleSubmit} className="space-y-3">
                <div>
                  <label htmlFor="answer" className="sr-only">Your answer</label>
                  <textarea
                    id="answer"
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    placeholder="Type your answer here..."
                    className="w-full min-h-[100px] resize-y"
                    rows={4}
                    disabled={submitting}
                  />
                </div>

                {/* Touch Options */}
                <TouchOptionCard
                  questionId={currentQuestion?.question_id}
                  questionText={currentQuestion?.prompt}
                  onSelect={(id, label) => {
                    setAnswer(label)
                    handleSubmit(new Event('submit'))
                  }}
                  disabled={submitting}
                />

                <div className="flex gap-2">
                  <button
                    type="submit"
                    className="btn btn-primary flex-1 btn-lg"
                    disabled={submitting || !answer.trim()}
                  >
                    {submitting ? 'Submitting...' : 'Submit Answer'}
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={() => setAnswer('')}
                    disabled={submitting}
                  >
                    Clear
                  </button>
                </div>
              </form>
            )}

            {!showTextInput && (
              <div className="text-center text-muted py-4">
                <p>Use the microphone button above to speak your answer.</p>
                <p className="text-sm">Text input is hidden. Check "Show text input" to type.</p>
              </div>
            )}
          </div>
        </div>

        {/* Session State Display */}
        <details className="mt-4">
          <summary className="cursor-pointer text-sm text-muted">Session Details</summary>
          <pre className="mt-2 text-xs bg-bg-secondary p-3 rounded overflow-auto max-h-48">
            {JSON.stringify({ sessionState, question: currentQuestion?.question_id, answerLength: answer.length }, null, 2)}
          </pre>
        </details>
      </main>

      <footer className="p-4 text-center text-sm text-muted border-t">
        Curo v0.1.0 — Hackathon Demo
      </footer>
    </div>
  )
}

export default HistoryInterview