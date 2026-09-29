/**
 * Module   : Touch Option Card
 * Owner    : Frontend Engineer
 * Purpose  : Tap-to-answer alternative to voice (universal quick-reply chips).
 */

import { useMemo } from 'react'

// Universal quick-reply options - no backend dependency
const UNIVERSAL_OPTIONS = [
  { id: 'yes', label: 'Yes', icon: '✓' },
  { id: 'no', label: 'No', icon: '✕' },
  { id: 'not_sure', label: 'Not sure', icon: '?' },
  { id: 'skip', label: 'Skip', icon: '⏭' },
]

export function TouchOptionCard({
  questionId,
  questionText,
  onSelect,
  disabled = false,
  className = '',
}) {
  // Derive contextual options based on question_id if needed
  const options = useMemo(() => {
    if (!questionId) return UNIVERSAL_OPTIONS

    const q = questionId.toLowerCase()
    // Severity questions -> 1-10 scale
    if (q.includes('severity') || q.includes('scale') || q.includes('how severe')) {
      return Array.from({ length: 10 }, (_, i) => ({
        id: `severity_${i + 1}`,
        label: String(i + 1),
        icon: null,
      }))
    }
    // Yes/No questions
    if (q.includes('yes') || q.includes('no') || q.includes('any') || q.includes('do you') || q.includes('are you')) {
      return UNIVERSAL_OPTIONS.slice(0, 3) // Yes, No, Not sure
    }
    // Default universal
    return UNIVERSAL_OPTIONS
  }, [questionId])

  return (
    <div className={`touch-option-card ${className}`} role="group" aria-label="Answer options">
      <div className="flex flex-wrap gap-2" style={{ minHeight: '56px' }}>
        {options.map((opt) => (
          <button
            key={opt.id}
            type="button"
            className="btn btn-outline flex-1"
            style={{
              minWidth: '72px',
              minHeight: '56px',
              padding: 'var(--space-3) var(--space-4)',
              fontSize: 'var(--font-size-lg)',
            }}
            onClick={() => onSelect?.(opt.id, opt.label)}
            disabled={disabled}
            aria-pressed={false}
          >
            {opt.icon && <span aria-hidden="true">{opt.icon}</span>}
            <span>{opt.label}</span>
          </button>
        ))}
      </div>

      {questionText && (
        <p className="text-sm text-muted mt-2" aria-hidden="true">
          For: {questionText}
        </p>
      )}
    </div>
  )
}

export default TouchOptionCard