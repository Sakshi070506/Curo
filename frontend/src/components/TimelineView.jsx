/**
 * Module   : Medical Timeline View
 * Owner    : Frontend Engineer
 * Purpose  : Chronological view of digitized documents.
 */

import { format } from 'date-fns'

export function TimelineView({
  documents = [],
  className = '',
}) {
  if (!documents || documents.length === 0) {
    return (
      <div className={`timeline-view ${className}`} role="region" aria-label="Medical timeline">
        <div className="text-center py-12 text-muted">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="mx-auto mb-3" aria-hidden="true">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          <p className="text-lg">No documents yet</p>
          <p className="text-sm mt-1">Upload a prescription or lab report to see your medical timeline</p>
        </div>
      </div>
    )
  }

  // Sort by date (newest first)
  const sorted = [...documents].sort((a, b) => {
    const da = a.date ? new Date(a.date).getTime() : 0
    const db = b.date ? new Date(b.date).getTime() : 0
    return db - da
  })

  return (
    <div className={`timeline-view ${className}`} role="region" aria-label="Medical timeline">
      <div className="relative">
        {/* Vertical timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-border" aria-hidden="true" />

        <div className="space-y-6">
          {sorted.map((doc, index) => (
            <div key={`${doc.document_id}-${index}`} className="relative flex gap-4">
              {/* Timeline marker */}
              <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center" aria-hidden="true">
                <div className="w-3 h-3 rounded-full bg-primary border-4 border-surface" />
              </div>

              {/* Document card */}
              <div className="flex-1 card p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-semibold text-lg">{doc.type?.charAt(0).toUpperCase() + doc.type?.slice(1) || 'Document'}</span>
                      {doc.date && (
                        <time className="text-sm text-muted" dateTime={doc.date}>
                          {doc.date.includes('T') ? format(new Date(doc.date), 'MMM d, yyyy') : doc.date}
                        </time>
                      )}
                    </div>

                    {doc.diagnoses && doc.diagnoses.length > 0 && (
                      <div className="mb-2">
                        <p className="text-sm font-medium text-muted mb-1">Diagnoses</p>
                        <div className="flex flex-wrap gap-1">
                          {doc.diagnoses.map((d, i) => (
                            <span key={i} className="px-2 py-0.5 bg-primary-light text-primary text-xs rounded-full">
                              {d}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {doc.medications && doc.medications.length > 0 && (
                      <div className="mb-2">
                        <p className="text-sm font-medium text-muted mb-1">Medications</p>
                        <ul className="text-sm space-y-0.5">
                          {doc.medications.map((m, i) => (
                            <li key={i} className="flex gap-2">
                              <span className="font-medium">{m.name}</span>
                              <span className="text-muted">{m.dosage}</span>
                              <span className="text-muted">{m.frequency}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {doc.investigations && doc.investigations.length > 0 && (
                      <div className="mb-2">
                        <p className="text-sm font-medium text-muted mb-1">Investigations</p>
                        <div className="flex flex-wrap gap-1">
                          {doc.investigations.map((inv, i) => (
                            <span key={i} className="px-2 py-0.5 bg-bg-tertiary text-sm rounded-full">
                              {inv.name || inv.test || JSON.stringify(inv)}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {doc.procedures && doc.procedures.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-muted mb-1">Procedures</p>
                        <div className="flex flex-wrap gap-1">
                          {doc.procedures.map((p, i) => (
                            <span key={i} className="px-2 py-0.5 bg-info-bg text-info text-xs rounded-full">
                              {p}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default TimelineView