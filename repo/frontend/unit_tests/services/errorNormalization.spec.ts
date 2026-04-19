// FE-UNIT: HttpError envelope — error code and message extraction.

import { describe, it, expect } from 'vitest'
import { HttpError } from '@/services/http'

describe('HttpError', () => {
  it('surfaces error message from envelope', () => {
    const envelope = {
      success: false as const,
      error: { code: 'NOT_FOUND', message: 'Resource not found.' },
      meta: { trace_id: 'abc', timestamp: '2024-01-01T00:00:00Z' },
    }
    const err = new HttpError(404, envelope)
    expect(err.message).toBe('Resource not found.')
    expect(err.status).toBe(404)
    expect(err.envelope.error.code).toBe('NOT_FOUND')
  })

  it('falls back to generic message when envelope missing message', () => {
    const envelope = {
      success: false as const,
      error: { code: 'HTTP_ERROR', message: '' },
      meta: { trace_id: 'x', timestamp: '' },
    }
    const err = new HttpError(500, envelope)
    // empty string is falsy → falls back to "HTTP 500"
    expect(err.message).toBe('HTTP 500')
  })

  it('is an instanceof Error', () => {
    const err = new HttpError(403, {
      success: false,
      error: { code: 'FORBIDDEN', message: 'Forbidden' },
      meta: { trace_id: '', timestamp: '' },
    })
    expect(err).toBeInstanceOf(Error)
  })
})
