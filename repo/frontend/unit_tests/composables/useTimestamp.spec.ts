// FE-UNIT: 12-hour timestamp formatting — format12h, formatDate, isExpired, msUntil.

import { describe, it, expect } from 'vitest'
import { format12h, formatDate, useTimestamp } from '@/composables/useTimestamp'

describe('format12h', () => {
  it('returns — for null', () => {
    expect(format12h(null)).toBe('—')
  })

  it('returns — for undefined', () => {
    expect(format12h(undefined)).toBe('—')
  })

  it('returns — for invalid date string', () => {
    expect(format12h('not-a-date')).toBe('—')
  })

  it('formats a valid ISO string in 12-hour style', () => {
    const result = format12h('2024-06-15T14:30:00Z')
    // Exact format depends on locale; assert it contains AM or PM
    expect(result).toMatch(/AM|PM/i)
  })
})

describe('formatDate', () => {
  it('returns — for null', () => {
    expect(formatDate(null)).toBe('—')
  })

  it('formats a date-only style', () => {
    const result = formatDate('2024-06-15T00:00:00Z')
    // Should contain 2024 somewhere
    expect(result).toContain('2024')
  })
})

describe('useTimestamp', () => {
  it('isExpired returns false for future date', () => {
    const { isExpired } = useTimestamp()
    const future = new Date(Date.now() + 100_000).toISOString()
    expect(isExpired(future)).toBe(false)
  })

  it('isExpired returns true for past date', () => {
    const { isExpired } = useTimestamp()
    const past = new Date(Date.now() - 100_000).toISOString()
    expect(isExpired(past)).toBe(true)
  })

  it('isExpired returns false for null', () => {
    const { isExpired } = useTimestamp()
    expect(isExpired(null)).toBe(false)
  })

  it('msUntil returns 0 for past date', () => {
    const { msUntil } = useTimestamp()
    const past = new Date(Date.now() - 10_000).toISOString()
    expect(msUntil(past)).toBe(0)
  })

  it('msUntil returns positive for future date', () => {
    const { msUntil } = useTimestamp()
    const future = new Date(Date.now() + 60_000).toISOString()
    expect(msUntil(future)).toBeGreaterThan(0)
  })
})
