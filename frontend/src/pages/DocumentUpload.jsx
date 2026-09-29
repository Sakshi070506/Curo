/**
 * Module   : Document Upload Screen
 * Owner    : Frontend Engineer
 * Purpose  : Scan/upload prior medical documents.
 */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSessionState } from '../hooks/useSessionState'
import { DocumentScanBox } from '../components/DocumentScanBox'
import { TimelineView } from '../components/TimelineView'
import { documentService } from '../services/documentService'

export function DocumentUpload() {
  const navigate = useNavigate()
  const { state, patientId, setDocuments, setLoading, setError, sessionId } = useSessionState()

  const [documents, setDocumentsState] = useState([])
  const [loading, setLocalLoading] = useState(false)

  // Load existing documents on mount
  useEffect(() => {
    const loadTimeline = async () => {
      if (!patientId) return
      try {
        const timeline = await documentService.getTimeline(patientId)
        setDocumentsState(timeline)
        setDocuments(timeline)
      } catch (err) {
        console.warn('Could not load timeline:', err)
      }
    }
    loadTimeline()
  }, [patientId, setDocuments])

  const handleUploadComplete = useCallback((doc) => {
    setDocumentsState((prev) => [...prev, doc])
  }, [])

  const handleContinue = useCallback(() => {
    navigate('/review')
  }, [navigate])

  return (
    <div className="document-upload min-h-screen flex flex-col">
      <header className="p-4 border-b bg-surface sticky top-0 z-10">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="font-semibold">Documents</h1>
            <p className="text-sm text-muted">Upload prior medical records</p>
          </div>
          <div className="text-right text-sm text-muted">
            Patient: {patientId}
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full p-4">
        <div className="space-y-6">
          {/* Upload Section */}
          <section aria-labelledby="upload-heading">
            <h2 id="upload-heading" className="text-lg font-semibold mb-4">Upload Documents</h2>
            <DocumentScanBox
              patientId={patientId}
              onUploadComplete={handleUploadComplete}
            />
          </section>

          {/* Timeline Section */}
          {documents.length > 0 && (
            <section aria-labelledby="timeline-heading">
              <div className="flex items-center justify-between mb-4">
                <h2 id="timeline-heading" className="text-lg font-semibold">Medical Timeline</h2>
                <span className="badge bg-primary-light text-primary">{documents.length} document(s)</span>
              </div>
              <TimelineView documents={documents} />
            </section>
          )}

          {/* Continue Button */}
          <div className="flex justify-end pt-4 border-t">
            <button
              type="button"
              className="btn btn-primary btn-lg"
              onClick={handleContinue}
            >
              Continue to Summary Review
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="ml-2" aria-hidden="true">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </button>
          </div>
        </div>
      </main>

      <footer className="p-4 text-center text-sm text-muted border-t">
        Curo v0.1.0 — Hackathon Demo
      </footer>
    </div>
  )
}

export default DocumentUpload