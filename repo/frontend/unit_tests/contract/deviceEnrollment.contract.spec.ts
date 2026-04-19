import { describe, it, expect } from 'vitest'
import { isRecord, isString, loadFixture } from './helpers'

function isDeviceChallenge(value: unknown): boolean {
  if (!isRecord(value)) return false
  return isString(value.challenge_id) && isString(value.nonce) && isString(value.expires_at)
}

function isDeviceRegistration(value: unknown): boolean {
  if (!isRecord(value)) return false
  return isString(value.device_id) && isString(value.device_fingerprint) && isString(value.registered_at)
}

describe('FE<->BE contract: device enrollment', () => {
  it('matches challenge and activation response fixtures', () => {
    const fixture = loadFixture<unknown>('deviceEnrollment.json')
    expect(isRecord(fixture)).toBe(true)
    if (!isRecord(fixture)) return
    expect(isDeviceChallenge(fixture.challenge)).toBe(true)
    expect(isDeviceRegistration(fixture.activation)).toBe(true)
  })
})
