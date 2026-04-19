import { describe, it, expect } from 'vitest'
import { isNullableString, isRecord, isString, loadFixture } from './helpers'

function isPaymentProofResponse(value: unknown): boolean {
  if (!isRecord(value)) return false
  return (
    isString(value.order_id) &&
    isString(value.payment_method) &&
    isNullableString(value.reference_number) &&
    isString(value.amount) &&
    typeof value.confirmed === 'boolean'
  )
}

function isConfirmResponse(value: unknown): boolean {
  if (!isRecord(value)) return false
  return isString(value.order_id) && isString(value.status)
}

describe('FE<->BE contract: payment', () => {
  it('matches payment proof and confirm fixtures', () => {
    const fixture = loadFixture<unknown>('paymentContracts.json')
    expect(isRecord(fixture)).toBe(true)
    if (!isRecord(fixture)) return
    expect(isPaymentProofResponse(fixture.proof)).toBe(true)
    expect(isConfirmResponse(fixture.confirm)).toBe(true)
  })
})
