// Test data factories
import { faker } from '@faker-js/faker'

export const createMockSession = (overrides = {}) => ({
  session_id: faker.string.uuid(),
  language: 'en',
  ayush_mode: false,
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
  ...overrides,
})

export const createMockQuestion = (overrides = {}) => ({
  question_id: faker.string.uuid(),
  prompt: faker.lorem.sentence(),
  state: 'CHIEF_COMPLAINT',
  ...overrides,
})

export const createMockDocument = (overrides = {}) => ({
  document_id: faker.string.uuid(),
  patient_id: faker.string.uuid(),
  document_type: 'prescription',
  date: faker.date.recent().toISOString().split('T')[0],
  diagnoses: ['Hypertension'],
  medications: [{ name: 'Amlodipine', dosage: '5mg', frequency: 'OD' }],
  investigations: [],
  procedures: [],
  raw_text: 'Mock OCR text',
  raw_ocr_confidence: 0.92,
  ...overrides,
})

export const createMockSummary = (overrides = {}) => ({
  summary_id: `summary_${faker.string.alphanumeric(8)}`,
  patient_id: faker.string.uuid(),
  session_id: faker.string.uuid(),
  summary: {
    chief_complaint: 'Chest pain',
    hpi: {},
    past_medical_history: [],
    drug_allergy_history: [],
    family_history: [],
    personal_history: {},
    review_of_systems: {},
    medications_from_docs: [],
  },
  source_attribution: { chief_complaint: 'interview', hpi: 'interview' },
  missing_sections: [],
  status: 'draft',
  ...overrides,
})

export const createMockConsent = (overrides = {}) => ({
  consent_id: faker.string.uuid(),
  patient_id: faker.string.uuid(),
  data_capture: true,
  share_with_his: true,
  link_abha_phr: true,
  consent_language: 'en',
  timestamp: new Date().toISOString(),
  audit_trail_id: faker.string.uuid(),
  ...overrides,
})

export const createMockTriageAlert = (overrides = {}) => ({
  id: faker.string.uuid(),
  patient_id: faker.string.uuid(),
  session_id: faker.string.uuid(),
  severity: 'high',
  matched_rules: [{ id: 'test', description: 'Test rule', severity: 'high' }],
  created_at: Date.now(),
  acknowledged: false,
  requires_immediate_attention: false,
  symptom: 'Chest pain',
  timestamp: new Date().toISOString(),
  ...overrides,
})

export const createMockUser = (overrides = {}) => ({
  abha_id: '12-3456-7890-1234',
  name: faker.person.fullName(),
  phone: faker.phone.number(),
  email: faker.internet.email(),
  ...overrides,
})