/**
 * Module   : Language Selection Screen
 * Owner    : Frontend Engineer
 * Purpose  : First screen: pick language, enter ABHA, start session.
 */

import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSessionState } from '../hooks/useSessionState'
import { abdmService } from '../services/abdmService'

const LANGUAGES = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳' },
  { code: 'mr', name: 'Marathi', nativeName: 'मराठी', flag: '🇮🇳' },
  { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்', flag: '🇮🇳' },
  { code: 'te', name: 'Telugu', nativeName: 'తెలుగు', flag: '🇮🇳' },
  { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', flag: '🇮🇳' },
  { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી', flag: '🇮🇳' },
  { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ', flag: '🇮🇳' },
  { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം', flag: '🇮🇳' },
  { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ', flag: '🇮🇳' },
]

export function LanguageSelect() {
  const navigate = useNavigate()
  const { state, setLanguage, setAyushMode, setIdentity, setSession, setLoading, setError, isLoading } = useSessionState()

  const [selectedLanguage, setSelectedLanguage] = useState('en')
  const [ayushMode, setAyushModeState] = useState(false)
  const [abhaId, setAbhaId] = useState('')
  const [name, setName] = useState('')
  const [verifying, setVerifying] = useState(false)
  const [error, setLocalError] = useState('')

  const handleStart = useCallback(async (e) => {
    e.preventDefault()
    setLocalError('')

    if (!abhaId.trim()) {
      setLocalError('Please enter your ABHA ID')
      return
    }

    if (!name.trim()) {
      setLocalError('Please enter your name')
      return
    }

    setLoading(true)
    setVerifying(true)

    try {
      // Verify ABHA ID
      const verifyResult = await abdmService.abhaVerify({ abha_id: abhaId.trim() })

      let accessToken = null
      if (verifyResult.verified && verifyResult.access_token) {
        accessToken = verifyResult.access_token
      } else {
        // Try login with default password
        try {
          const loginResult = await abdmService.login({ abha_id: abhaId.trim(), otp: 'defaultpass' })
          accessToken = loginResult.access_token
        } catch {
          // If login fails, register new user
          const regResult = await abdmService.register({ abha_id: abhaId.trim(), name: name.trim() })
          const loginResult = await abdmService.login({ abha_id: abhaId.trim(), otp: 'defaultpass' })
          accessToken = loginResult.access_token
        }
      }

      // Set identity in session
      setIdentity(abhaId.trim(), name.trim(), abhaId.trim(), accessToken)
      setLanguage(selectedLanguage)
      setAyushModeState(ayushMode)

      // Start interview session
      const session = await abdmService.startSession ? abdmService.startSession({ language: selectedLanguage, ayush_mode: ayushMode }) :
        fetch('/api/history/start-session', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${accessToken}` },
          body: JSON.stringify({ language: selectedLanguage, ayush_mode: ayushMode }),
        }).then(r => r.json())

      setSession(session.session_id, session.next_question?.state || 'CHIEF_COMPLAINT')
      navigate('/consent')
    } catch (err) {
      setLocalError(err.message || 'Failed to start session. Please try again.')
      console.error(err)
    } finally {
      setLoading(false)
      setVerifying(false)
    }
  }, [abhaId, name, selectedLanguage, ayushMode, setIdentity, setLanguage, setAyushModeState, setSession, setLoading, navigate])

  // Mock startSession function for demo
  const mockStartSession = async ({ language, ayush_mode }) => {
    const res = await fetch('/api/history/start-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ language, ayush_mode }),
    })
    if (!res.ok) throw new Error('Failed to start session')
    return res.json()
  }

  // Override the handleStart to use mock when needed
  const handleStartDemo = async (e) => {
    e.preventDefault()
    setLocalError('')

    if (!abhaId.trim()) { setLocalError('Please enter your ABHA ID'); return }
    if (!name.trim()) { setLocalError('Please enter your name'); return }

    setLoading(true)

    try {
      // Direct API call for demo
      const session = await mockStartSession({ language: selectedLanguage, ayush_mode: ayushMode })
      setIdentity(abhaId.trim(), name.trim(), abhaId.trim(), 'mock-token')
      setLanguage(selectedLanguage)
      setAyushModeState(ayushMode)
      setSession(session.session_id, session.next_question?.state || 'CHIEF_COMPLAINT')
      navigate('/consent')
    } catch (err) {
      setLocalError(err.message || 'Failed to start session')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="language-select min-h-screen flex flex-col">
      <header className="p-6 border-b">
        <h1 className="text-3xl font-bold">Curo</h1>
        <p className="text-muted mt-1">AI-Powered Patient Case-Taking</p>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-4">
        <div className="w-full max-w-2xl">
          <div className="card">
            <div className="card-header text-center mb-6">
              <h2 className="text-2xl font-semibold">Welcome</h2>
              <p className="text-muted mt-1">Select your language and enter your details to begin</p>
            </div>

            <form onSubmit={handleStartDemo} className="space-y-6">
              {/* Language Grid */}
              <fieldset>
                <legend className="font-medium mb-4">Language / भाषा / भाषा</legend>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3" role="radiogroup" aria-label="Select language">
                  {LANGUAGES.map((lang) => (
                    <label
                      key={lang.code}
                      className={`relative cursor-pointer ${selectedLanguage === lang.code ? 'ring-2 ring-primary' : ''}`}
                    >
                      <input
                        type="radio"
                        name="language"
                        value={lang.code}
                        checked={selectedLanguage === lang.code}
                        onChange={() => setSelectedLanguage(lang.code)}
                        className="sr-only"
                      />
                      <div className={`p-4 text-center rounded-lg border transition-all min-h-[100px] flex flex-col items-center justify-center ${selectedLanguage === lang.code ? 'bg-primary-light border-primary' : 'border-border hover:border-primary'}`}>
                        <span className="text-3xl" aria-hidden="true">{lang.flag}</span>
                        <span className="font-medium mt-1">{lang.nativeName}</span>
                        <span className="text-xs text-muted">{lang.name}</span>
                      </div>
                    </label>
                  ))}
                </div>
              </fieldset>

              {/* AYUSH Mode Toggle */}
              <label className="flex items-center gap-3 p-3 bg-bg-secondary rounded-lg cursor-pointer">
                <input
                  type="checkbox"
                  checked={ayushMode}
                  onChange={(e) => setAyushModeState(e.target.checked)}
                  className="w-5 h-5 accent-primary"
                />
                <div>
                  <p className="font-medium">AYUSH Mode (Dashavidha Pariksha)</p>
                  <p className="text-sm text-muted">Include traditional Ayurvedic assessment</p>
                </div>
              </label>

              {/* ABHA ID Input */}
              <div>
                <label htmlFor="abha-id" className="block font-medium mb-2">ABHA ID (14 digits)</label>
                <input
                  id="abha-id"
                  type="text"
                  value={abhaId}
                  onChange={(e) => setAbhaId(e.target.value.replace(/\D/g, '').slice(0, 14))}
                  placeholder="12-3456-7890-1234"
                  className="w-full font-mono text-lg"
                  maxLength={14}
                  required
                  autoComplete="off"
                />
              </div>

              {/* Name Input */}
              <div>
                <label htmlFor="patient-name" className="block font-medium mb-2">Full Name</label>
                <input
                  id="patient-name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your full name"
                  className="w-full"
                  required
                  autoComplete="name"
                />
              </div>

              {error && <div className="alert alert-danger" role="alert">{error}</div>}

              <button
                type="submit"
                className="btn btn-primary w-full btn-lg py-4 text-lg"
                disabled={isLoading || verifying}
              >
                {verifying ? (
                  <>
                    <span className="spinner mr-2" aria-hidden="true"></span>
                    Verifying ABHA...
                  </>
                ) : isLoading ? (
                  'Starting Session...'
                ) : (
                  'Start Interview'
                )}
              </button>

              <p className="text-center text-sm text-muted">
                Demo: Use any 14-digit ABHA ID. Default OTP is "defaultpass"
              </p>
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

export default LanguageSelect