/**
 * Module   : Session State Hook
 * Owner    : Frontend Engineer
 * Purpose  : Tracks interview session progress across pages.
 */

import { useSession } from '../context/SessionContext'

export function useSessionState() {
  const { state, actions } = useSession()

  return {
    // Identity
    abhaId: state.abhaId,
    name: state.name,
    patientId: state.patientId || state.abhaId || state.sessionId,
    isAuthenticated: state.isAuthenticated,
    accessToken: state.accessToken,

    // Session
    language: state.language,
    ayushMode: state.ayushMode,
    sessionId: state.sessionId,
    currentQuestion: state.currentQuestion,
    sessionState: state.sessionState,

    // Interview
    redFlags: state.redFlags,
    history: state.history,

    // Documents
    documents: state.documents,

    // Summary
    summaryId: state.summaryId,
    summary: state.summary,

    // Consent
    consent: state.consent,

    // Triage
    triageAlerts: state.triageAlerts,

    // UI
    isLoading: state.isLoading,
    error: state.error,

    // Actions
    ...actions,
  }
}