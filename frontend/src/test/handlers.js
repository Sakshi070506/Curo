// MSW request handlers for API mocking
import { http, HttpResponse } from 'msw'
import { faker } from '@faker-js/faker'

// In-memory test stores
const testStores = {
  userStore: {},
  documentStore: {},
  summaryStore: {},
  consentStore: {},
  abdmStatus: {},
  triageQueue: [],
  sessionStore: {},
}

export const handlers = [
  // Health
  http.get('/api/health', () => HttpResponse.json({ status: 'ok' })),

  // Auth
  http.post('/api/auth/register', async ({ request }) => {
    const body = await request.json()
    if (testStores.userStore[body.abha_id]) {
      return HttpResponse.json({ detail: 'ABHA ID already registered' }, { status: 400 })
    }
    testStores.userStore[body.abha_id] = {
      abha_id: body.abha_id,
      name: body.name,
      phone: body.phone,
      email: body.email,
      password_hash: 'hashed_defaultpass',
    }
    return HttpResponse.json({ message: 'Registered successfully', abha_id: body.abha_id }, { status: 201 })
  }),

  http.post('/api/auth/login', async ({ request }) => {
    const body = await request.json()
    const user = testStores.userStore[body.abha_id]
    if (!user || body.otp !== 'defaultpass') {
      return HttpResponse.json({ detail: 'Invalid ABHA ID or OTP' }, { status: 401 })
    }
    return HttpResponse.json({ access_token: 'mock-token-' + body.abha_id, token_type: 'bearer' })
  }),

  http.post('/api/auth/abha-verify', async ({ request }) => {
    const body = await request.json()
    if (testStores.userStore[body.abha_id]) {
      return HttpResponse.json({ verified: true, access_token: 'mock-token-' + body.abha_id, token_type: 'bearer' })
    }
    return HttpResponse.json({ verified: false, message: 'ABHA ID not found' })
  }),

  http.get('/api/auth/me', ({ request }) => {
    const auth = request.headers.get('Authorization')
    if (!auth || !auth.startsWith('Bearer ')) {
      return HttpResponse.json({ authenticated: false })
    }
    const token = auth.slice(7)
    const abha_id = token.replace('mock-token-', '')
    const user = testStores.userStore[abha_id]
    if (!user) return HttpResponse.json({ authenticated: false })
    return HttpResponse.json({
      authenticated: true,
      abha_id: user.abha_id,
      name: user.name,
      phone: user.phone,
      email: user.email,
    })
  }),

  // History / Interview
  http.post('/api/history/start-session', async ({ request }) => {
    const body = await request.json()
    const session_id = faker.string.uuid()
    testStores.sessionStore[session_id] = {
      session_id,
      language: body.language || 'en',
      ayush_mode: body.ayush_mode || false,
      state: 'CHIEF_COMPLAINT',
      chief_complaint: '',
      hpi: {},
      past_medical_history: [],
      drug_allergy_history: [],
      family_history: [],
      personal_history: {},
      review_of_systems: {},
      ayush: {},
      red_flags_triggered: [],
    }
    return HttpResponse.json({
      session_id,
      next_question: { question_id: 'chief_complaint', prompt: 'What brings you in today?', state: 'CHIEF_COMPLAINT' },
    }, { status: 201 })
  }),

  http.post('/api/history/answer', async ({ request }) => {
    const body = await request.json()
    const session = testStores.sessionStore[body.session_id]
    if (!session) {
      return HttpResponse.json({ detail: 'Session not found' }, { status: 404 })
    }
    const answer = body.answer_text || 'mock answer'
    // Simulate state progression
    const states = ['CHIEF_COMPLAINT', 'HPI_LOOP', 'PAST_HISTORY', 'DRUG_ALLERGY_HISTORY', 'FAMILY_HISTORY', 'PERSONAL_HISTORY', 'ROS', 'COMPLETE']
    const idx = states.indexOf(session.state)
    const nextState = states[Math.min(idx + 1, states.length - 1)]
    session.state = nextState
    const complete = nextState === 'COMPLETE'

    return HttpResponse.json({
      session_id: body.session_id,
      state: nextState,
      red_flag: { triggered: false, matched_rules: [], severity: 'none' },
      next_question: complete ? null : { question_id: `q_${nextState}`, prompt: `Next question for ${nextState}`, state: nextState },
      complete,
    })
  }),

  http.get('/api/history/session/:session_id', ({ params }) => {
    const session = testStores.sessionStore[params.session_id]
    if (!session) {
      return HttpResponse.json({ detail: 'Session not found' }, { status: 404 })
    }
    return HttpResponse.json(session)
  }),

  http.post('/api/history/redflag-check', async ({ request }) => {
    const body = await request.json()
    const triggered = body.text.toLowerCase().includes('chest pain')
    return HttpResponse.json({
      triggered,
      matched_rules: triggered ? [{ id: 'acute_coronary_syndrome', description: 'Chest pain with breathlessness', severity: 'critical' }] : [],
      highest_severity: triggered ? 'critical' : 'none',
    })
  }),

  // Documents
  http.post('/api/documents/upload', async ({ request }) => {
    const formData = await request.formData()
    const file = formData.get('file')
    const patient_id = formData.get('patient_id') || 'anonymous'
    const document_id = faker.string.uuid()
    const doc = {
      document_id,
      patient_id,
      document_type: 'prescription',
      date: new Date().toISOString().split('T')[0],
      diagnoses: ['Hypertension'],
      medications: [{ name: 'Amlodipine', dosage: '5mg', frequency: 'OD' }],
      investigations: [],
      procedures: [],
      raw_text: 'Mock OCR text',
      raw_ocr_confidence: 0.92,
    }
    if (!testStores.documentStore[patient_id]) testStores.documentStore[patient_id] = []
    testStores.documentStore[patient_id].push(doc)
    return HttpResponse.json(doc, { status: 201 })
  }),

  http.get('/api/documents/:patient_id/timeline', ({ params }) => {
    const docs = testStores.documentStore[params.patient_id] || []
    const ordered = [...docs].sort((a, b) => (a.date || '').localeCompare(b.date || ''))
    return HttpResponse.json(ordered.map(d => ({
      document_id: d.document_id,
      type: d.document_type,
      date: d.date,
      diagnoses: d.diagnoses,
      medications: d.medications,
      investigations: d.investigations,
      procedures: d.procedures || [],
    })))
  }),

  // Summary
  http.post('/api/summary/generate', async ({ request }) => {
    const body = await request.json()
    const session = testStores.sessionStore[body.session_id]
    if (!session) {
      return HttpResponse.json({ detail: 'Session not found' }, { status: 404 })
    }
    const patient_id = session.patient_id || body.patient_id || body.session_id
    const docs = testStores.documentStore[patient_id] || []
    const summary_id = `summary_${body.session_id.slice(0, 8)}`
    const summary = {
      summary_id,
      patient_id,
      session_id: body.session_id,
      summary: {
        chief_complaint: session.chief_complaint || 'Chest pain',
        hpi: session.hpi,
        past_medical_history: session.past_medical_history,
        drug_allergy_history: session.drug_allergy_history,
        family_history: session.family_history,
        personal_history: session.personal_history,
        review_of_systems: session.review_of_systems,
        medications_from_docs: docs.flatMap(d => d.medications),
      },
      source_attribution: { chief_complaint: 'interview', hpi: 'interview' },
      missing_sections: [],
      status: 'draft',
    }
    testStores.summaryStore[summary_id] = summary
    return HttpResponse.json({
      summary_id,
      summary: summary.summary,
      source_attribution: summary.source_attribution,
      missing_sections: summary.missing_sections,
    }, { status: 201 })
  }),

  http.get('/api/summary/:summary_id', ({ params }) => {
    const summary = testStores.summaryStore[params.summary_id]
    if (!summary) return HttpResponse.json({ detail: 'Summary not found' }, { status: 404 })
    return HttpResponse.json(summary)
  }),

  http.post('/api/summary/:summary_id/confirm', async ({ params, request }) => {
    const body = await request.json()
    if (!testStores.summaryStore[params.summary_id]) {
      return HttpResponse.json({ detail: 'Summary not found' }, { status: 404 })
    }
    if (!body.confirmed) return HttpResponse.json({ detail: 'Confirmation required' }, { status: 400 })
    testStores.summaryStore[params.summary_id].status = 'confirmed'
    return HttpResponse.json({ status: 'confirmed', summary_id: params.summary_id })
  }),

  http.patch('/api/summary/:summary_id/edit', async ({ params, request }) => {
    const body = await request.json()
    if (!testStores.summaryStore[params.summary_id]) {
      return HttpResponse.json({ detail: 'Summary not found' }, { status: 404 })
    }
    testStores.summaryStore[params.summary_id].summary = { ...testStores.summaryStore[params.summary_id].summary, ...body }
    testStores.summaryStore[params.summary_id].status = 'edited'
    return HttpResponse.json({ status: 'edited', summary_id: params.summary_id, summary: testStores.summaryStore[params.summary_id].summary })
  }),

  // Consent / ABDM
  http.post('/api/consent/grant', async ({ request }) => {
    const body = await request.json()
    const consent_id = faker.string.uuid()
    const record = {
      consent_id,
      patient_id: body.patient_id,
      data_capture: body.data_capture,
      share_with_his: body.share_with_his,
      link_abha_phr: body.link_abha_phr,
      consent_language: body.consent_language || 'en',
      timestamp: new Date().toISOString(),
      audit_trail_id: faker.string.uuid(),
    }
    testStores.consentStore[consent_id] = record
    return HttpResponse.json(record, { status: 201 })
  }),

  http.get('/api/consent/status/:patient_id', ({ params }) => {
    const consents = Object.values(testStores.consentStore).filter(c => c.patient_id === params.patient_id)
    if (!consents.length) return HttpResponse.json({ detail: 'No consent found for patient' }, { status: 404 })
    const latest = consents.reduce((a, b) => a.timestamp > b.timestamp ? a : b)
    return HttpResponse.json(latest)
  }),

  http.delete('/api/consent/revoke/:consent_id', ({ params }) => {
    if (!testStores.consentStore[params.consent_id]) {
      return HttpResponse.json({ detail: 'Consent not found' }, { status: 404 })
    }
    delete testStores.consentStore[params.consent_id]
    return HttpResponse.json({ revoked: true, consent_id: params.consent_id })
  }),

  http.post('/api/abdm/push-fhir', async ({ request }) => {
    const body = await request.json()
    const patient_id = body.patient?.id || 'unknown'
    const result = {
      success: true,
      status_code: 200,
      dry_run: true,
      message: 'FHIR bundle pushed to ABDM sandbox (dry run)',
      latency_ms: 150,
    }
    testStores.abdmStatus[patient_id] = result
    return HttpResponse.json(result)
  }),

  http.get('/api/abdm/status/:patient_id', ({ params }) => {
    const last = testStores.abdmStatus[params.patient_id]
    if (!last) {
      return HttpResponse.json({ patient_id: params.patient_id, last_push: null, status: 'not_attempted' })
    }
    return HttpResponse.json({ patient_id: params.patient_id, last_push: last, status: last.success ? 'success' : 'failed' })
  }),

  // Voice
  http.post('/api/voice/tts', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({
      audio_b64: 'bW9jay1hdWRpbw==',
      content_type: 'audio/wav',
      language: body.language || 'en',
      cached: false,
      provider: 'MockTTSProvider',
      latency_ms: 50,
    })
  }),

  http.post('/api/voice/asr', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({
      transcript: 'mock transcript',
      confidence: 0.95,
      language: body.language || 'en',
      provider: 'MockASRProvider',
      latency_ms: 80,
    })
  }),

  http.get('/api/voice/prompts', () => {
    return HttpResponse.json({
      prompts: {
        consent: { en: 'We need your consent to process your health data.', hi: 'हमें आपके स्वास्थ्य डेटा को संसाधित करने के लिए आपकी सहमति चाहिए।' },
        greeting: { en: 'Welcome to Curo. Please select your language.', hi: 'क्यूरो में आपका स्वागत है। कृपया अपनी भाषा चुनें।' },
      },
    })
  }),

  // Triage
  http.get('/api/triage/queue', () => {
    const alerts = testStores.triageQueue.map(a => ({ ...a }))
    return HttpResponse.json({ alerts })
  }),

  http.post('/api/triage/alert', async ({ request }) => {
    const body = await request.json()
    const alert = {
      id: faker.string.uuid(),
      patient_id: body.patient_id,
      session_id: body.session_id,
      severity: body.severity,
      matched_rules: body.matched_rules,
      created_at: Date.now(),
      acknowledged: false,
      requires_immediate_attention: body.severity === 'critical',
    }
    testStores.triageQueue.push(alert)
    return HttpResponse.json(alert, { status: 201 })
  }),

  http.post('/api/triage/acknowledge/:alert_id', ({ params }) => {
    const alert = testStores.triageQueue.find(a => a.id === params.alert_id)
    if (!alert) return HttpResponse.json({ detail: 'Alert not found' }, { status: 404 })
    alert.acknowledged = true
    return HttpResponse.json({ acknowledged: true })
  }),

  // Knowledge / RAG
  http.post('/api/knowledge/search', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({
      results: [
        { id: '1', content: 'Mock knowledge result for ' + body.query, score: 0.9, metadata: { category: 'clinical' } },
      ],
    })
  }),

  http.post('/api/knowledge/drug-interactions', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({
      interactions: [],
      highest_severity: 'none',
    })
  }),
]