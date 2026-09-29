/**
 * Module   : Physician Console
 * Owner    : Frontend Engineer
 * Purpose  : Doctor-facing structured summary + edit/confirm.
 */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useSessionState } from '../hooks/useSessionState'
import { summaryService } from '../services/summaryService'
import { abdmService } from '../services/abdmService'
import { triageService } from '../services/triageService'
import { SummaryEditor } from '../components/SummaryEditor'
import { RedFlagBanner } from '../components/RedFlagBanner'

export function PhysicianConsole() {
  const navigate = useNavigate()
  const location = useLocation()
  const { state, summary, summaryId, patientId, setSummary, setLoading, setError, setTriageAlerts } = useSessionState()

  const [editing, setEditing] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [pushingFHIR, setPushingFHIR] = useState(false)
  const [fhirResult, setFhirResult] = useState(null)
  const [abdmStatus, setAbdmStatus] = useState(null)
  const [triageAlerts, setTriageAlertsState] = useState([])
  const [error, setLocalError] = useState('')
  const [activeTab, setActiveTab] = useState('summary')

  // Patient correction from SummaryReview
  const patientCorrection = location.state?.patientCorrection

  // Load triage queue periodically
  useEffect(() => {
    const loadQueue = async () => {
      try {
        const queue = await triageService.getQueue()
        setTriageAlertsState(queue.alerts || [])
        setTriageAlerts(queue.alerts || [])
      } catch (err) {
        console.warn('Could not load triage queue:', err)
      }
    }
    loadQueue()
    const interval = setInterval(loadQueue, 5000)
    return () => clearInterval(interval)
  }, [setTriageAlerts])

  // Load ABDM status
  useEffect(() => {
    if (patientId) {
      abdmService.getABDMStatus(patientId).then(setAbdmStatus).catch(console.warn)
    }
  }, [patientId])

  const handleEdit = useCallback(() => setEditing(true), [])
  const handleCancelEdit = useCallback(() => setEditing(false), [])

  const handleSave = useCallback(async (patches) => {
    if (!summaryId) return
    setLoading(true)
    try {
      const result = await summaryService.editSummary(summaryId, patches)
      setSummary(result.summary_id, result.summary)
      setEditing(false)
    } catch (err) {
      setLocalError(err.message || 'Failed to save edits')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [summaryId, setSummary, setLoading])

  const handleConfirm = useCallback(async () => {
    if (!summaryId) return
    setConfirming(true)
    try {
      await summaryService.confirmSummary(summaryId, { summary: summary, confirmed: true })
      alert('Summary confirmed!')
    } catch (err) {
      setLocalError(err.message || 'Failed to confirm')
      console.error(err)
    } finally {
      setConfirming(false)
    }
  }, [summaryId, summary])

  const handlePushFHIR = useCallback(async () => {
    if (!summary) return
    setPushingFHIR(true)
    try {
      const result = await abdmService.pushFHIR({
        patient: { id: patientId },
        chief_complaint: summary.chief_complaint,
        diagnoses: summary.hpi ? Object.values(summary.hpi) : [],
        medications: summary.medications_from_docs || [],
        investigations: [],
      })
      setFhirResult(result)
      setAbdmStatus({ ...abdmStatus, last_push: result, status: result.success ? 'success' : 'failed' })
      alert(result.success ? 'FHIR bundle pushed successfully!' : 'Push failed: ' + result.message)
    } catch (err) {
      setLocalError(err.message || 'FHIR push failed')
      console.error(err)
    } finally {
      setPushingFHIR(false)
    }
  }, [summary, patientId, abdmStatus])

  const acknowledgeAlert = useCallback(async (alertId) => {
    try {
      await triageService.acknowledgeAlert(alertId)
      setTriageAlertsState((prev) => prev.map(a => a.id === alertId ? { ...a, acknowledged: true } : a))
    } catch (err) {
      console.error('Failed to acknowledge:', err)
    }
  }, [])

  if (!summary) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted">No summary loaded. Redirecting...</p>
        </div>
      </div>
    )
  }

  const criticalAlerts = triageAlerts.filter(a => a.severity === 'critical' && !a.acknowledged)

  return (
    <div className="physician-console min-h-screen flex flex-col">
      <header className="p-4 border-b bg-surface sticky top-0 z-10">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">Physician Console</h1>
            <p className="text-sm text-muted">Patient: {patientId} • Summary: {summaryId}</p>
          </div>
          <div className="flex items-center gap-2">
            {criticalAlerts.length > 0 && (
              <span className="badge bg-danger text-danger-text px-3 py-1 text-sm">
                ⚠ {criticalAlerts.length} critical alert(s)
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full p-4">
        {error && <div className="alert alert-danger mb-4" role="alert">{error}</div>}
        {patientCorrection && (
          <div className="alert alert-warning mb-4" role="alert">
            <strong>Patient Flag:</strong> {patientCorrection}
          </div>
        )}

        {/* Red Flag Banner */}
        <RedFlagBanner redFlags={triageAlerts} onDismiss={acknowledgeAlert} />

        {/* Tab Navigation */}
        <div className="flex gap-1 mb-4 border-b" role="tablist">
          {['summary', 'triage', 'abdm'].map((tab) => (
            <button
              key={tab}
              role="tab"
              aria-selected={activeTab === tab}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === tab ? 'border-primary text-primary' : 'border-transparent text-muted hover:text-primary'}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Tab Panels */}
        {activeTab === 'summary' && (
          <div role="tabpanel" id="summary-panel">
            <SummaryEditor
              summary={summary}
              onSave={handleSave}
              onCancel={handleCancelEdit}
              readOnly={!editing}
            />

            <div className="mt-6 flex gap-3">
              {editing ? (
                <>
                  <button type="button" className="btn btn-outline" onClick={handleCancelEdit}>Cancel</button>
                  <button type="button" className="btn btn-primary" onClick={() => handleSave({})} disabled={confirming}>Save</button>
                </>
              ) : (
                <>
                  <button type="button" className="btn btn-outline" onClick={handleEdit}>Edit Summary</button>
                  <button type="button" className="btn btn-primary" onClick={handleConfirm} disabled={confirming}>
                    {confirming ? 'Confirming...' : 'Confirm Summary'}
                  </button>
                </>
              )}
            </div>
          </div>
        )}

        {activeTab === 'triage' && (
          <div role="tabpanel" id="triage-panel">
            <div className="card">
              <div className="card-header">
                <h2 className="font-semibold">Triage Alert Queue</h2>
              </div>
              {triageAlerts.length === 0 ? (
                <p className="text-muted text-center py-8">No triage alerts</p>
              ) : (
                <div className="space-y-3">
                  {triageAlerts.map((alert) => (
                    <div key={alert.id} className={`p-4 border rounded-lg ${alert.severity === 'critical' ? 'border-danger bg-danger-bg' : 'border-border'}`}>
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium">{alert.severity.toUpperCase()} — {alert.symptom || 'Clinical alert'}</p>
                          <p className="text-sm text-muted mt-1">Patient: {alert.patient_id} • Session: {alert.session_id}</p>
                          <p className="text-sm mt-1">{alert.matched_rules?.map(r => r.description).join(', ')}</p>
                          <p className="text-xs text-muted mt-1">Time: {new Date(alert.created_at).toLocaleString()}</p>
                        </div>
                        {!alert.acknowledged && (
                          <button
                            type="button"
                            className="btn btn-primary btn-sm"
                            onClick={() => acknowledgeAlert(alert.id)}
                          >
                            Acknowledge
                          </button>
                        )}
                        {alert.acknowledged && <span className="badge bg-secondary">Acknowledged</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'abdm' && (
          <div role="tabpanel" id="abdm-panel">
            <div className="grid md:grid-cols-2 gap-6">
              {/* FHIR Push */}
              <div className="card">
                <div className="card-header">
                  <h2 className="font-semibold">FHIR Push to ABDM</h2>
                </div>
                <div className="space-y-4">
                  <button
                    type="button"
                    className="btn btn-primary w-full btn-lg"
                    onClick={handlePushFHIR}
                    disabled={pushingFHIR}
                  >
                    {pushingFHIR ? (
                      <>
                        <span className="spinner mr-2" aria-hidden="true"></span>
                        Pushing to ABDM...
                      </>
                    ) : (
                      'Push Summary to ABDM'
                    )}
                  </button>

                  {fhirResult && (
                    <div className={`p-3 rounded ${fhirResult.success ? 'bg-success-bg border border-success' : 'bg-danger-bg border border-danger'}`}>
                      <p className="font-medium">{fhirResult.success ? 'Success' : 'Failed'}</p>
                      <p className="text-sm mt-1">{fhirResult.message}</p>
                      <p className="text-xs text-muted">Latency: {fhirResult.latency_ms}ms • Dry run: {fhirResult.dry_run ? 'Yes' : 'No'}</p>
                    </div>
                  )}

                  {abdmStatus && (
                    <div className="p-3 bg-bg-secondary rounded">
                      <p className="font-medium mb-1">Last Push Status</p>
                      <p className="text-sm">Status: <span className={`font-medium ${abdmStatus.status === 'success' ? 'text-success' : 'text-danger'}`}>{abdmStatus.status}</span></p>
                      {abdmStatus.last_push && (
                        <p className="text-sm text-muted">Last: {new Date(abdmStatus.last_push.latency_ms ? Date.now() - abdmStatus.last_push.latency_ms : Date.now()).toLocaleString()}</p>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Consent Status */}
              <div className="card">
                <div className="card-header">
                  <h2 className="font-semibold">Consent Status</h2>
                </div>
                {state.consent ? (
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Data Capture</span>
                      <span className={state.consent.data_capture ? 'text-success' : 'text-danger'}>
                        {state.consent.data_capture ? '✓ Granted' : '✗ Not Granted'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Share with HIS</span>
                      <span className={state.consent.share_with_his ? 'text-success' : 'text-muted'}>
                        {state.consent.share_with_his ? '✓ Granted' : '○ Not Granted'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Link ABHA PHR</span>
                      <span className={state.consent.link_abha_phr ? 'text-success' : 'text-muted'}>
                        {state.consent.link_abha_phr ? '✓ Granted' : '○ Not Granted'}
                      </span>
                    </div>
                    <div className="pt-2 border-t text-sm text-muted">
                      Language: {state.consent.consent_language} • {new Date(state.consent.timestamp).toLocaleString()}
                    </div>
                  </div>
                ) : (
                  <p className="text-muted">No consent recorded</p>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="p-4 text-center text-sm text-muted border-t">
        Curo v0.1.0 — Hackathon Demo
      </footer>
    </div>
  )
}

export default PhysicianConsole