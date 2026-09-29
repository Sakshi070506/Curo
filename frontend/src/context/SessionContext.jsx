/**
 * Module   : Session Context
 * Owner    : Frontend Lead
 * Purpose  : Global state: patient/session/language.
 */

import { createContext, useContext, useReducer, useEffect, ReactNode } from 'react'

const SessionContext = createContext(null)

const STORAGE_KEY = 'curo_session_state'

const initialState = {
  // Identity
  abhaId: null,
  name: null,
  patientId: null,
  isAuthenticated: false,
  accessToken: null,

  // Session
  language: 'en',
  ayushMode: false,
  sessionId: null,
  currentQuestion: null,
  sessionState: 'START', // START, LANGUAGE_SELECTED, CONSENT_GRANTED, CHIEF_COMPLAINT, HPI_LOOP, PAST_HISTORY, DRUG_ALLERGY_HISTORY, FAMILY_HISTORY, PERSONAL_HISTORY, ROS, DASHAVIDHA_PARIKSHA, COMPLETE

  // Interview data
  redFlags: [],
  history: {},

  // Documents
  documents: [],

  // Summary
  summaryId: null,
  summary: null,

  // Consent
  consent: null,

  // Triage
  triageAlerts: [],

  // UI state
  isLoading: false,
  error: null,
}

function sessionReducer(state, action) {
  switch (action.type) {
    case 'SET_IDENTITY':
      return { ...state, abhaId: action.payload.abhaId, name: action.payload.name, patientId: action.payload.patientId, isAuthenticated: true, accessToken: action.payload.accessToken }
    case 'CLEAR_IDENTITY':
      return { ...state, abhaId: null, name: null, patientId: null, isAuthenticated: false, accessToken: null }
    case 'SET_LANGUAGE':
      return { ...state, language: action.payload }
    case 'SET_AYUSH_MODE':
      return { ...state, ayushMode: action.payload }
    case 'SET_SESSION':
      return { ...state, sessionId: action.payload.sessionId, sessionState: action.payload.state || 'CHIEF_COMPLAINT' }
    case 'SET_QUESTION':
      return { ...state, currentQuestion: action.payload, sessionState: action.payload?.state || state.sessionState }
    case 'SET_HISTORY':
      return { ...state, history: action.payload }
    case 'ADD_RED_FLAG':
      return { ...state, redFlags: [...state.redFlags, action.payload] }
    case 'SET_DOCUMENTS':
      return { ...state, documents: action.payload }
    case 'ADD_DOCUMENT':
      return { ...state, documents: [...state.documents, action.payload] }
    case 'SET_SUMMARY':
      return { ...state, summaryId: action.payload.summaryId, summary: action.payload.summary }
    case 'SET_CONSENT':
      return { ...state, consent: action.payload }
    case 'SET_TRIAGE_ALERTS':
      return { ...state, triageAlerts: action.payload }
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload }
    case 'SET_ERROR':
      return { ...state, error: action.payload }
    case 'RESET':
      return initialState
    default:
      return state
  }
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(sessionReducer, initialState, (saved) => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY)
      if (stored) {
        return { ...initialState, ...JSON.parse(stored) }
      }
    } catch {}
    return initialState
  })

  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  }, [state])

  const actions = {
    setIdentity: (abhaId, name, patientId, accessToken) => dispatch({ type: 'SET_IDENTITY', payload: { abhaId, name, patientId, accessToken } }),
    clearIdentity: () => dispatch({ type: 'CLEAR_IDENTITY' }),
    setLanguage: (language) => dispatch({ type: 'SET_LANGUAGE', payload: language }),
    setAyushMode: (ayushMode) => dispatch({ type: 'SET_AYUSH_MODE', payload: ayushMode }),
    setSession: (sessionId, state) => dispatch({ type: 'SET_SESSION', payload: { sessionId, state } }),
    setQuestion: (question) => dispatch({ type: 'SET_QUESTION', payload: question }),
    setHistory: (history) => dispatch({ type: 'SET_HISTORY', payload: history }),
    addRedFlag: (redFlag) => dispatch({ type: 'ADD_RED_FLAG', payload: redFlag }),
    setDocuments: (documents) => dispatch({ type: 'SET_DOCUMENTS', payload: documents }),
    addDocument: (document) => dispatch({ type: 'ADD_DOCUMENT', payload: document }),
    setSummary: (summaryId, summary) => dispatch({ type: 'SET_SUMMARY', payload: { summaryId, summary } }),
    setConsent: (consent) => dispatch({ type: 'SET_CONSENT', payload: consent }),
    setTriageAlerts: (alerts) => dispatch({ type: 'SET_TRIAGE_ALERTS', payload: alerts }),
    setLoading: (isLoading) => dispatch({ type: 'SET_LOADING', payload: isLoading }),
    setError: (error) => dispatch({ type: 'SET_ERROR', payload: error }),
    reset: () => dispatch({ type: 'RESET' }),
  }

  return (
    <SessionContext.Provider value={{ state, actions }}>
      {children}
    </SessionContext.Provider>
  )
}

export function useSession() {
  const context = useContext(SessionContext)
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider')
  }
  return context
}