/**
 * Module   : Red-Flag Alert Banner
 * Owner    : Frontend Engineer
 * Purpose  : Visual alert when emergency symptom detected.
 */

export function RedFlagBanner({
  redFlags = [],
  onDismiss,
  className = '',
}) {
  if (!redFlags || redFlags.length === 0) return null

  const highestSeverity = redFlags.reduce((max, flag) => {
    const order = { none: 0, low: 1, medium: 2, high: 3, critical: 4 }
    return order[flag.severity] > order[max.severity] ? flag : max
  }, { severity: 'none' })

  const severityColors = {
    critical: 'alert-danger',
    high: 'alert-danger',
    medium: 'alert-warning',
    low: 'alert-info',
    none: 'alert-info',
  }

  return (
    <div
      className={`red-flag-banner alert ${severityColors[highestSeverity.severity]} ${className}`}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0" aria-hidden="true">
          {highestSeverity.severity === 'critical' && (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
            </svg>
          )}
          {highestSeverity.severity === 'high' && (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" />
            </svg>
          )}
          {highestSeverity.severity === 'medium' && (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm0-4h-2V7h2v6z" />
            </svg>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <p className="font-semibold">⚠ Medical Alert Detected</p>
          <p className="text-sm mt-1">
            {redFlags.map((f, i) => (
              <span key={i}>{f.description || f.id} ({f.severity}){i < redFlags.length - 1 ? '; ' : ''}</span>
            ))}
          </p>
          {highestSeverity.symptom && (
            <p className="text-sm mt-1 font-mono">{highestSeverity.symptom}</p>
          )}
        </div>

        {onDismiss && (
          <button
            type="button"
            className="btn btn-ghost btn-sm flex-shrink-0"
            onClick={onDismiss}
            aria-label="Dismiss alert"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}
      </div>
    </div>
  )
}

export default RedFlagBanner