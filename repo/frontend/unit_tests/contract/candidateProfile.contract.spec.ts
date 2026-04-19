import { describe, it, expect } from 'vitest'
import { isNullableString, isRecord, isString, loadFixture } from './helpers'

function isCandidateProfile(value: unknown): boolean {
  if (!isRecord(value)) return false
  return (
    isString(value.id) &&
    isString(value.user_id) &&
    (typeof value.application_year === 'number' || value.application_year === null) &&
    isString(value.application_status) &&
    isNullableString(value.preferred_name) &&
    isNullableString(value.program_code) &&
    isString(value.created_at) &&
    isString(value.updated_at) &&
    isNullableString(value.ssn_display) &&
    isNullableString(value.dob_display) &&
    isNullableString(value.phone_display) &&
    isNullableString(value.email_display)
  )
}

describe('FE<->BE contract: candidate profile', () => {
  it('matches CandidateProfileRead fixture shape', () => {
    const fixture = loadFixture<unknown>('candidateProfile.json')
    expect(isCandidateProfile(fixture)).toBe(true)
  })
})
