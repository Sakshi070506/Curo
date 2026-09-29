/**
 * Module   : Root Component
 * Owner    : Frontend Lead
 * Purpose  : Top-level routing between kiosk screens.
 */

import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { SessionProvider } from './context/SessionContext'
import { LanguageSelect } from './pages/LanguageSelect'
import { ConsentScreen } from './pages/ConsentScreen'
import { HistoryInterview } from './pages/HistoryInterview'
import { DocumentUpload } from './pages/DocumentUpload'
import { SummaryReview } from './pages/SummaryReview'
import { PhysicianConsole } from './pages/PhysicianConsole'

// Simple error boundary
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-4">
          <div className="card max-w-md text-center">
            <h2 className="text-xl font-semibold text-danger mb-2">Something went wrong</h2>
            <pre className="text-sm text-left bg-bg-secondary p-3 rounded overflow-auto max-h-64">
              {this.state.error?.toString()}
            </pre>
            <button
              type="button"
              className="btn btn-primary mt-4"
              onClick={() => window.location.reload()}
            >
              Reload App
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <SessionProvider>
          <Routes>
            <Route path="/" element={<Navigate to="/language" replace />} />
            <Route path="/language" element={<LanguageSelect />} />
            <Route path="/consent" element={<ConsentScreen />} />
            <Route path="/interview" element={<HistoryInterview />} />
            <Route path="/documents" element={<DocumentUpload />} />
            <Route path="/review" element={<SummaryReview />} />
            <Route path="/doctor" element={<PhysicianConsole />} />
            <Route path="*" element={<Navigate to="/language" replace />} />
          </Routes>
        </SessionProvider>
      </ErrorBoundary>
    </BrowserRouter>
  )
}

export default App