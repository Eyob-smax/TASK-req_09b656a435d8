// FE-UNIT: upload validation — MIME type gating and size limit.

import { describe, it, expect } from 'vitest'
import { validateFile } from '@/composables/useUpload'

function makeFile(name: string, type: string, sizeBytes: number): File {
  const blob = new Blob([new Uint8Array(sizeBytes)], { type })
  return new File([blob], name, { type })
}

describe('validateFile', () => {
  it('returns NO_FILE error for null', () => {
    const err = validateFile(null)
    expect(err?.code).toBe('NO_FILE')
  })

  it('accepts PDF', () => {
    expect(validateFile(makeFile('doc.pdf', 'application/pdf', 100))).toBeNull()
  })

  it('accepts JPEG', () => {
    expect(validateFile(makeFile('img.jpg', 'image/jpeg', 100))).toBeNull()
  })

  it('accepts PNG', () => {
    expect(validateFile(makeFile('img.png', 'image/png', 100))).toBeNull()
  })

  it('rejects other MIME types', () => {
    const err = validateFile(makeFile('doc.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 100))
    expect(err?.code).toBe('INVALID_MIME')
  })

  it('rejects files exceeding 25 MB', () => {
    const err = validateFile(makeFile('large.pdf', 'application/pdf', 26 * 1024 * 1024))
    expect(err?.code).toBe('TOO_LARGE')
  })

  it('accepts files at exactly 25 MB', () => {
    const err = validateFile(makeFile('ok.pdf', 'application/pdf', 25 * 1024 * 1024))
    expect(err).toBeNull()
  })
})
