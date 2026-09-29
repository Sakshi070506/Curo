// Knowledge Service Tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { knowledgeService } from './knowledgeService'
import { server } from '../test/setup'
import { http, HttpResponse } from 'msw'

describe('Knowledge Service', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('should search knowledge base', async () => {
    const result = await knowledgeService.search({ query: 'chest pain', k: 5 })
    expect(result).toHaveProperty('results')
    expect(Array.isArray(result.results)).toBe(true)
    expect(result.results.length).toBeGreaterThan(0)
    expect(result.results[0]).toHaveProperty('id')
    expect(result.results[0]).toHaveProperty('content')
    expect(result.results[0]).toHaveProperty('score')
  })

  it('should use default parameters', async () => {
    const result = await knowledgeService.search({ query: 'headache' })
    expect(result.results).toBeDefined()
  })

  it('should filter by category', async () => {
    const result = await knowledgeService.search({ query: 'diabetes', category: 'clinical', min_similarity: 0.5 })
    expect(result.results).toBeDefined()
  })

  it('should check drug interactions', async () => {
    const medications = [
      { name: 'Aspirin', dosage: '75mg' },
      { name: 'Warfarin', dosage: '5mg' },
    ]
    const result = await knowledgeService.checkDrugInteractions(medications)
    expect(result).toHaveProperty('interactions')
    expect(result).toHaveProperty('highest_severity')
    expect(Array.isArray(result.interactions)).toBe(true)
  })

  it('should return no interactions for safe combination', async () => {
    const medications = [{ name: 'Paracetamol', dosage: '500mg' }]
    const result = await knowledgeService.checkDrugInteractions(medications)
    expect(result.highest_severity).toBe('none')
    expect(result.interactions).toEqual([])
  })

  it('should handle empty medications list', async () => {
    const result = await knowledgeService.checkDrugInteractions([])
    expect(result.highest_severity).toBe('none')
    expect(result.interactions).toEqual([])
  })
})