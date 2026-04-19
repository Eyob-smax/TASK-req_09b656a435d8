// FE-UNIT: useDeviceKey.ensureEnrolled — end-to-end enrollment contract.
//
// Verifies:
//   1. challenge is called with `{device_fingerprint, public_key_pem}` (BE
//      `DeviceChallengeRequest` shape), NOT the old `{fingerprint}` form.
//   2. activate is called with `{challenge_id, device_fingerprint,
//      public_key_pem, signature}` (BE `DeviceActivateRequest` shape).
//   3. The signature is produced via `signEnrollmentNonce` over the RAW
//      challenge nonce UTF-8 bytes — never via `signRequest` / canonical form.
//   4. `registerDevice` is NOT called — activate is atomic and registers the
//      device in a single step.
//   5. The returned `device_id` from activate is persisted both to IndexedDB
//      (via setDeviceId) and to the Pinia auth store.
//
// Also keeps lightweight crypto correctness tests for the raw-nonce signer.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/services/deviceKey', () => ({
  getOrCreateDeviceKey: vi.fn().mockResolvedValue({
    deviceId: null,
    fingerprint: 'fp-abcdef0123',
    publicKeyPem: '-----BEGIN PUBLIC KEY-----\nAAAA\n-----END PUBLIC KEY-----\n',
    // Fake CryptoKey-ish — we mock signEnrollmentNonce so the real key type
    // doesn't matter for this test.
    privateKey: { _fake: 'priv' } as unknown as CryptoKey,
  }),
  setDeviceId: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('@/services/authApi', () => ({
  challenge: vi.fn().mockResolvedValue({
    challenge_id: 'ch-1',
    nonce: 'NONCE-DEADBEEF',
    expires_at: '2026-04-18T12:05:00Z',
  }),
  activate: vi.fn().mockResolvedValue({
    device_id: 'dev-xyz',
    device_fingerprint: 'fp-abcdef0123',
    registered_at: '2026-04-18T12:01:00Z',
  }),
  registerDevice: vi.fn(),
}))

vi.mock('@/services/requestSigner', async () => {
  const actual = await vi.importActual<typeof import('@/services/requestSigner')>(
    '@/services/requestSigner',
  )
  return {
    ...actual,
    signEnrollmentNonce: vi.fn().mockResolvedValue('SIG-RAW-NONCE'),
    signRequest: vi.fn(),
  }
})

import * as authApi from '@/services/authApi'
import * as signer from '@/services/requestSigner'
import * as deviceKey from '@/services/deviceKey'
import { useDeviceKey } from '@/composables/useDeviceKey'
import { useAuthStore } from '@/stores/auth'

describe('useDeviceKey.ensureEnrolled — enrollment contract', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('calls challenge with device_fingerprint + public_key_pem (not legacy fingerprint)', async () => {
    const { ensureEnrolled } = useDeviceKey()
    await ensureEnrolled()
    expect(authApi.challenge).toHaveBeenCalledWith({
      device_fingerprint: 'fp-abcdef0123',
      public_key_pem: '-----BEGIN PUBLIC KEY-----\nAAAA\n-----END PUBLIC KEY-----\n',
    })
  })

  it('signs the raw nonce (not a request-canonical form)', async () => {
    const { ensureEnrolled } = useDeviceKey()
    await ensureEnrolled()
    expect(signer.signEnrollmentNonce).toHaveBeenCalledTimes(1)
    const args = (signer.signEnrollmentNonce as unknown as { mock: { calls: unknown[][] } }).mock.calls[0]
    // Second arg must be the raw nonce string, not a canonical METHOD\nPATH\n…
    expect(args[1]).toBe('NONCE-DEADBEEF')
    // signRequest must NOT be used for enrollment.
    expect(signer.signRequest).not.toHaveBeenCalled()
  })

  it('calls activate with the full five-field payload', async () => {
    const { ensureEnrolled } = useDeviceKey()
    await ensureEnrolled()
    expect(authApi.activate).toHaveBeenCalledWith({
      challenge_id: 'ch-1',
      device_fingerprint: 'fp-abcdef0123',
      public_key_pem: '-----BEGIN PUBLIC KEY-----\nAAAA\n-----END PUBLIC KEY-----\n',
      signature: 'SIG-RAW-NONCE',
    })
  })

  it('does NOT call registerDevice after activate (activate is atomic)', async () => {
    const { ensureEnrolled } = useDeviceKey()
    await ensureEnrolled()
    expect(authApi.registerDevice).not.toHaveBeenCalled()
  })

  it('persists device_id to IndexedDB and auth store from activate response', async () => {
    const { ensureEnrolled } = useDeviceKey()
    const id = await ensureEnrolled()
    expect(id).toBe('dev-xyz')
    expect(deviceKey.setDeviceId).toHaveBeenCalledWith('dev-xyz')
    const auth = useAuthStore()
    expect(auth.deviceId).toBe('dev-xyz')
  })
})

describe('signEnrollmentNonce — raw nonce signing', () => {
  it('produces a base64 ECDSA signature that decodes to the 64-byte r||s form', async () => {
    const { generateSigningKey, signEnrollmentNonce } = await vi.importActual<
      typeof import('@/services/requestSigner')
    >('@/services/requestSigner')
    const pair = await generateSigningKey()
    const sig = await signEnrollmentNonce(pair.privateKey, 'NONCE-XYZ')
    expect(sig).toMatch(/^[A-Za-z0-9+/]+=*$/)
    const bytes = Uint8Array.from(atob(sig), (c) => c.charCodeAt(0))
    expect(bytes.length).toBe(64)
  })
})
