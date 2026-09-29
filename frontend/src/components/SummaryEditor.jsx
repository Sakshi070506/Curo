/**
 * Module   : Summary Editor
 * Owner    : Frontend Engineer
 * Purpose  : Editable structured summary fields for physician.
 */

import { useState, useCallback, useMemo } from 'react'

const SUMMARY_SECTIONS = [
  { key: 'chief_complaint', label: 'Chief Complaint', type: 'text' },
  { key: 'hpi', label: 'History of Present Illness', type: 'object' },
  { key: 'past_medical_history', label: 'Past Medical History', type: 'array' },
  { key: 'drug_allergy_history', label: 'Drug Allergy History', type: 'array' },
  { key: 'family_history', label: 'Family History', type: 'array' },
  { key: 'personal_history', label: 'Personal History', type: 'object' },
  { key: 'review_of_systems', label: 'Review of Systems', type: 'object' },
  { key: 'medications_from_docs', label: 'Medications from Documents', type: 'array' },
]

function ArrayEditor({ value, onChange, key }) {
  const [items, setItems] = useState(Array.isArray(value) ? [...value] : [])

  const handleItemChange = (index, newValue) => {
    const next = [...items]
    next[index] = newValue
    setItems(next)
    onChange(next)
  }

  const handleRemove = (index) => {
    setItems(items.filter((_, j) => j !== index))
    onChange(items.filter((_, j) => j !== index))
  }

  const handleAdd = () => {
    setItems([...items, ''])
    onChange([...items, ''])
  }

  return (
    <div className="space-y-2">
      {items.map((item, i) => (
        <div key={i} className="flex gap-2">
          <input
            type="text"
            value={item}
            onChange={(e) => handleItemChange(i, e.target.value)}
            className="flex-1"
          />
          <button type="button" className="btn btn-ghost btn-sm text-danger" onClick={() => handleRemove(i)} aria-label={`Remove item ${i + 1}`}>✕</button>
        </div>
      ))}
      <button type="button" className="btn btn-outline btn-sm" onClick={handleAdd}>+ Add</button>
    </div>
  )
}

function ObjectEditor({ value, onChange, key }) {
  return (
    <textarea
      value={typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
      onChange={(e) => onChange(e.target.value)}
      className="w-full min-h-[120px] font-mono text-sm"
      rows={8}
    />
  )
}

function TextEditor({ value, onChange, key }) {
  return (
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full"
    />
  )
}

export function SummaryEditor({
  summary,
  onSave,
  onCancel,
  className = '',
  readOnly = false,
}) {
  const [edits, setEdits] = useState({})
  const [expandedSections, setExpandedSections] = useState(new Set(['chief_complaint']))

  const handleChange = useCallback((sectionKey, value) => {
    setEdits((prev) => ({ ...prev, [sectionKey]: value }))
  }, [])

  const handleSave = useCallback(() => {
    onSave?.(edits)
  }, [edits, onSave])

  const handleCancel = useCallback(() => {
    setEdits({})
    onCancel?.()
  }, [onCancel])

  const toggleSection = useCallback((key) => {
    setExpandedSections((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }, [])

  const isExpanded = (key) => expandedSections.has(key)

  const renderValue = useCallback((section) => {
    const key = section.key
    const value = edits[key] !== undefined ? edits[key] : summary?.[key]

    if (value === undefined || value === null || (Array.isArray(value) && value.length === 0) || (typeof value === 'object' && Object.keys(value).length === 0)) {
      return <span className="text-muted italic">Not captured</span>
    }

    if (section.type === 'array') {
      return (
        <ul className="space-y-1">
          {value.map((item, i) => (
            <li key={i} className="text-sm">{typeof item === 'object' ? JSON.stringify(item) : item}</li>
          ))}
        </ul>
      )
    }

    if (section.type === 'object') {
      return (
        <pre className="text-sm bg-bg-secondary p-3 rounded overflow-auto max-h-64">
          {JSON.stringify(value, null, 2)}
        </pre>
      )
    }

    return <p className="text-sm">{value}</p>
  }, [edits, summary])

  const getEditor = useMemo(() => ({
    text: TextEditor,
    array: ArrayEditor,
    object: ObjectEditor,
  }), [])

  return (
    <div className={`summary-editor ${className}`} role="region" aria-label="Summary editor">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Case Summary</h2>
        <div className="flex gap-2">
          {!readOnly && Object.keys(edits).length > 0 && (
            <>
              <button type="button" className="btn btn-outline btn-sm" onClick={handleCancel}>Cancel</button>
              <button type="button" className="btn btn-primary btn-sm" onClick={handleSave}>Save Changes</button>
            </>
          )}
        </div>
      </div>

      <div className="space-y-3" role="list">
        {SUMMARY_SECTIONS.map((section) => {
          const hasEdits = edits[section.key] !== undefined
          const EditorComponent = getEditor[section.type]
          const value = edits[section.key] !== undefined ? edits[section.key] : summary?.[section.key] || ''

          return (
            <div key={section.key} className={`card ${hasEdits ? 'border-primary' : ''}`} role="listitem">
              <div className="card-header flex items-center justify-between">
                <button
                  type="button"
                  className="flex items-center gap-2 w-full text-left"
                  onClick={() => toggleSection(section.key)}
                  aria-expanded={isExpanded(section.key)}
                >
                  <span className="font-medium">{section.label}</span>
                  {hasEdits && <span className="badge bg-primary-light text-primary text-xs">Edited</span>}
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={`ml-auto transition-transform ${isExpanded(section.key) ? 'rotate-180' : ''}`} aria-hidden="true">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>
              </div>

              {isExpanded(section.key) && (
                <div className="mt-3">
                  {readOnly ? renderValue(section) : <EditorComponent key={section.key} value={value} onChange={(v) => handleChange(section.key, v)} />}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {Object.keys(edits).length > 0 && !readOnly && (
        <div className="mt-4 p-3 bg-info-bg border border-info rounded-lg text-sm">
          <p className="font-medium">Unsaved changes: {Object.keys(edits).length} section(s)</p>
        </div>
      )}
    </div>
  )
}

function renderValue(section) {
  // This is a placeholder - the actual renderValue is defined above with useCallback
  return null
}

export default SummaryEditor