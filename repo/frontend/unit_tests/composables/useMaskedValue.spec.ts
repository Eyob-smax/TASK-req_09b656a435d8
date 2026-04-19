// FE-UNIT: masked value helpers — maskValue strategy matrix.

import { describe, it, expect } from 'vitest'
import { maskValue } from '@/composables/useMaskedValue'

describe('maskValue', () => {
  describe('last4 strategy', () => {
    it('shows last 4 digits, masks the rest', () => {
      expect(maskValue('123456789012', 'last4')).toBe('********9012')
    })

    it('returns **** for short value', () => {
      expect(maskValue('abc', 'last4')).toBe('****')
    })

    it('returns — for null', () => {
      expect(maskValue(null, 'last4')).toBe('—')
    })

    it('returns — for undefined', () => {
      expect(maskValue(undefined, 'last4')).toBe('—')
    })
  })

  describe('full strategy', () => {
    it('returns up to 12 asterisks', () => {
      expect(maskValue('SomeValue123', 'full')).toBe('************')
    })

    it('caps at 12 even for longer strings', () => {
      const result = maskValue('A'.repeat(50), 'full')
      expect(result).toBe('*'.repeat(12))
    })
  })

  describe('phone strategy', () => {
    it('shows last 4 with phone mask', () => {
      expect(maskValue('09123456789', 'phone')).toBe('***-***-6789')
    })

    it('returns **** for short value', () => {
      expect(maskValue('123', 'phone')).toBe('****')
    })
  })

  describe('name strategy', () => {
    it('shows first name and masked last name', () => {
      const result = maskValue('John Doe', 'name')
      expect(result).toMatch(/^John \*+$/)
    })

    it('handles single-word name', () => {
      const result = maskValue('Alice', 'name')
      expect(result).toMatch(/^A\*+$/)
    })
  })
})
