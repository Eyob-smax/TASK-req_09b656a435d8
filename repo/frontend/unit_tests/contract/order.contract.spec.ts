import { describe, it, expect } from 'vitest'
import { isNullableString, isRecord, isString, loadFixture } from './helpers'

function isOrderEvent(value: unknown): boolean {
  if (!isRecord(value)) return false
  return (
    isString(value.id) &&
    typeof value.sequence_number === 'number' &&
    isString(value.event_type) &&
    isNullableString(value.previous_state) &&
    isString(value.new_state) &&
    isNullableString(value.actor_id) &&
    isNullableString(value.actor_role) &&
    isNullableString(value.notes) &&
    isString(value.occurred_at)
  )
}

function isOrderRead(value: unknown): boolean {
  if (!isRecord(value)) return false
  if (!Array.isArray(value.events)) return false
  return (
    isString(value.id) &&
    isString(value.candidate_id) &&
    isString(value.item_id) &&
    isString(value.status) &&
    isString(value.pricing_mode) &&
    (isString(value.agreed_price) || value.agreed_price === null) &&
    isNullableString(value.auto_cancel_at) &&
    isNullableString(value.completed_at) &&
    isNullableString(value.canceled_at) &&
    isNullableString(value.cancellation_reason) &&
    isString(value.created_at) &&
    isString(value.updated_at) &&
    value.events.every(isOrderEvent)
  )
}

describe('FE<->BE contract: order', () => {
  it('matches OrderRead fixture shape', () => {
    const fixture = loadFixture<unknown>('orderRead.json')
    expect(isOrderRead(fixture)).toBe(true)
  })
})
