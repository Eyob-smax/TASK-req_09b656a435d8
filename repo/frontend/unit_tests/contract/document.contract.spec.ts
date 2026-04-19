import { describe, it, expect } from 'vitest'
import { isNullableString, isRecord, isString, loadFixture } from './helpers'

function isDocumentVersion(value: unknown): boolean {
  if (!isRecord(value)) return false
  return (
    isString(value.id) &&
    isString(value.document_id) &&
    typeof value.version_number === 'number' &&
    isString(value.original_filename) &&
    isString(value.content_type) &&
    typeof value.size_bytes === 'number' &&
    isString(value.sha256_hash) &&
    isString(value.uploaded_by) &&
    isString(value.uploaded_at) &&
    typeof value.is_active === 'boolean'
  )
}

function isDocumentRead(value: unknown): boolean {
  if (!isRecord(value)) return false
  const latest = value.latest_version
  return (
    isString(value.id) &&
    isString(value.candidate_id) &&
    isNullableString(value.requirement_id) &&
    isNullableString(value.requirement_code) &&
    isString(value.document_type) &&
    typeof value.current_version === 'number' &&
    isString(value.current_status) &&
    isNullableString(value.resubmission_reason) &&
    isString(value.created_at) &&
    isString(value.updated_at) &&
    (latest === null || isDocumentVersion(latest))
  )
}

describe('FE<->BE contract: document', () => {
  it('matches DocumentRead fixture shape', () => {
    const fixture = loadFixture<unknown>('documentRead.json')
    expect(isDocumentRead(fixture)).toBe(true)
  })
})
