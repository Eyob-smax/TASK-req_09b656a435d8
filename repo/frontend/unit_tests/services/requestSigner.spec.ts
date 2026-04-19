// FE-UNIT: request signing — canonical form, nonce uniqueness, SHA-256 body hash.

import { describe, it, expect } from 'vitest'
import {
  buildCanonical,
  generateNonce,
  currentTimestamp,
  sha256Hex,
} from '@/services/requestSigner'

describe('generateNonce', () => {
  it('returns a string starting with n-', () => {
    expect(generateNonce()).toMatch(/^n-[0-9a-f]+$/)
  })

  it('produces unique values', () => {
    const a = generateNonce()
    const b = generateNonce()
    expect(a).not.toBe(b)
  })
})

describe('currentTimestamp', () => {
  it('returns ISO 8601 UTC without milliseconds', () => {
    const ts = currentTimestamp()
    expect(ts).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/)
  })
})

describe('sha256Hex', () => {
  it('returns a 64-char hex string for known input', async () => {
    const hash = await sha256Hex(new TextEncoder().encode('hello'))
    expect(hash).toHaveLength(64)
    // SHA-256("hello") is deterministic
    expect(hash).toBe('2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824')
  })

  it('returns all-zeros hash for empty input', async () => {
    const hash = await sha256Hex(new Uint8Array())
    expect(hash).toBe('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
  })
})

describe('buildCanonical', () => {
  it('produces a Uint8Array with the correct structure', async () => {
    const canonical = await buildCanonical({
      method: 'POST',
      path: '/api/v1/orders',
      timestamp: '2024-01-01T00:00:00Z',
      nonce: 'n-abc123',
      deviceId: 'dev-xyz',
      body: '{"amount":"100"}',
    })
    const text = new TextDecoder().decode(canonical)
    expect(text).toContain('POST\n')
    expect(text).toContain('/api/v1/orders\n')
    expect(text).toContain('2024-01-01T00:00:00Z\n')
    expect(text).toContain('n-abc123\n')
    expect(text).toContain('dev-xyz\n')
    // body hash is last line
    const lines = text.split('\n')
    expect(lines).toHaveLength(7) // 6 fields + trailing \n
    expect(lines[5]).toHaveLength(64) // SHA-256 hex
  })

  it('handles null body as empty hash', async () => {
    const canonical = await buildCanonical({
      method: 'GET',
      path: '/api/v1/candidates',
      timestamp: '2024-01-01T00:00:00Z',
      nonce: 'n-abc',
      deviceId: 'dev',
      body: null,
    })
    const text = new TextDecoder().decode(canonical)
    const lines = text.split('\n')
    // SHA-256 of empty = e3b0c4...
    expect(lines[5]).toBe('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
  })
})
