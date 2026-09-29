/**
 * Module   : Document Scan Box
 * Owner    : Frontend Engineer
 * Purpose  : Camera capture / drag-drop upload widget.
 */

import { useState, useCallback, useRef } from 'react'
import { documentService } from '../services/documentService'

export function DocumentScanBox({
  patientId,
  onUploadComplete,
  className = '',
}) {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState({})
  const [results, setResults] = useState([])
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const handleFileSelect = useCallback((e) => {
    const newFiles = Array.from(e.target.files)
    setFiles((prev) => [...prev, ...newFiles])
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    e.currentTarget.classList.add('drag-over')
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    e.currentTarget.classList.remove('drag-over')
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    e.currentTarget.classList.remove('drag-over')
    const newFiles = Array.from(e.dataTransfer.files)
    setFiles((prev) => [...prev, ...newFiles])
  }, [])

  const removeFile = useCallback((index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const uploadFiles = useCallback(async () => {
    if (files.length === 0) return
    setUploading(true)
    setError(null)
    const newResults = []

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      setProgress((p) => ({ ...p, [file.name]: 0 }))
      try {
        const result = await documentService.uploadDocument(file, {
          patientId,
          onProgress: (p) => setProgress((prev) => ({ ...prev, [file.name]: p })),
        })
        newResults.push(result)
        if (onUploadComplete) onUploadComplete(result)
      } catch (err) {
        setError(err.message || `Failed to upload ${file.name}`)
        console.error(err)
      }
      setProgress((p) => ({ ...p, [file.name]: 100 }))
    }

    setResults((prev) => [...prev, ...newResults])
    setFiles([])
    setUploading(false)
  }, [files, patientId, onUploadComplete])

  const triggerFileInput = () => fileInputRef.current?.click()

  return (
    <div className={`document-scan-box ${className}`}>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*,application/pdf"
        multiple
        onChange={handleFileSelect}
        className="sr-only"
        id="document-upload"
        disabled={uploading}
      />

      <div
        className={`drop-zone border-2 border-dashed rounded-lg p-8 text-center transition-colors ${files.length > 0 ? 'border-primary' : 'border-border'} ${uploading ? 'opacity-50' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={triggerFileInput}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') triggerFileInput() }}
        aria-label="Drop zone for document upload"
      >
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="mx-auto text-muted mb-3" aria-hidden="true">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <p className="text-lg font-medium">{files.length > 0 ? `${files.length} file(s) ready` : 'Drag & drop files here, or click to browse'}</p>
        <p className="text-sm text-muted mt-1">Supports: JPG, PNG, PDF (max 10MB each)</p>
      </div>

      {files.length > 0 && (
        <div className="file-list mt-4 space-y-2" role="list" aria-label="Selected files">
          {files.map((file, index) => (
            <div key={`${file.name}-${index}`} className="flex items-center gap-3 p-3 bg-surface border rounded-lg" role="listitem">
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{file.name}</p>
                <p className="text-sm text-muted">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              {progress[file.name] !== undefined && (
                <div className="w-32" style={{ height: '6px' }}>
                  <div className="progress-bar">
                    <div className="progress-bar-fill" style={{ width: `${progress[file.name]}%` }} />
                  </div>
                </div>
              )}
              <button
                type="button"
                className="btn btn-ghost btn-sm text-danger"
                onClick={() => removeFile(index)}
                disabled={uploading}
                aria-label={`Remove ${file.name}`}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 flex gap-2">
        {files.length > 0 && !uploading && (
          <button
            type="button"
            className="btn btn-primary flex-1"
            onClick={uploadFiles}
            disabled={uploading}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            Upload {files.length} file(s)
          </button>
        )}

        {!uploading && files.length === 0 && (
          <button
            type="button"
            className="btn btn-outline flex-1"
            onClick={triggerFileInput}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            Choose files
          </button>
        )}
      </div>

      {error && (
        <div className="alert alert-danger mt-3" role="alert">{error}</div>
      )}

      {results.length > 0 && (
        <div className="mt-6" role="region" aria-label="Upload results">
          <h3 className="font-semibold mb-3">Uploaded Documents</h3>
          <div className="space-y-2">
            {results.map((doc, index) => (
              <div key={`${doc.document_id}-${index}`} className="p-3 bg-success-bg border border-success-text rounded-lg">
                <p className="font-medium">{doc.document_type} — {doc.date}</p>
                <p className="text-sm text-success-text">Confidence: {(doc.raw_ocr_confidence * 100).toFixed(0)}%</p>
                <p className="text-sm mt-1">Diagnoses: {doc.diagnoses.join(', ') || 'None'}</p>
                <p className="text-sm">Medications: {doc.medications.map(m => m.name).join(', ') || 'None'}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default DocumentScanBox