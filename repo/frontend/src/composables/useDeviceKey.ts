// Device-key bootstrap flow: if IndexedDB does not yet hold a keypair, this
// composable generates one, requests an enrollment challenge, signs the raw
// nonce (NOT the request-canonical form) and posts to /auth/device/activate,
// which atomically registers the device and returns the assigned device_id.
//
// The activate endpoint is the single enrollment sink — /auth/device/register
// is a service-managed direct path and is not called from the browser flow.
// The non-extractable private key never leaves the browser.

import { ref } from 'vue'
import * as authApi from '@/services/authApi'
import { getOrCreateDeviceKey, setDeviceId } from '@/services/deviceKey'
import {
  currentTimestamp,
  generateNonce,
  signEnrollmentNonce,
} from '@/services/requestSigner'
import { useAuthStore } from '@/stores/auth'

export function useDeviceKey() {
  const auth = useAuthStore()
  const enrolling = ref(false)
  const lastError = ref<string | null>(null)

  async function ensureEnrolled(): Promise<string | null> {
    enrolling.value = true
    lastError.value = null
    try {
      const record = await getOrCreateDeviceKey()
      if (record.deviceId) {
        auth.setDeviceId(record.deviceId)
        return record.deviceId
      }

      const ch = await authApi.challenge({
        device_fingerprint: record.fingerprint,
        public_key_pem: record.publicKeyPem,
      })
      // Enrollment signatures are over the raw nonce bytes — the backend
      // `verify_enrollment_signature` helper does NOT reconstruct the request
      // canonical form for enrollment.
      const signature = await signEnrollmentNonce(record.privateKey, ch.nonce)

      const activated = await authApi.activate({
        challenge_id: ch.challenge_id,
        device_fingerprint: record.fingerprint,
        public_key_pem: record.publicKeyPem,
        signature,
      })

      await setDeviceId(activated.device_id)
      auth.setDeviceId(activated.device_id)
      return activated.device_id
    } catch (err) {
      lastError.value = (err as Error).message
      throw err
    } finally {
      enrolling.value = false
    }
  }

  return { ensureEnrolled, enrolling, lastError, generateNonce, currentTimestamp }
}
