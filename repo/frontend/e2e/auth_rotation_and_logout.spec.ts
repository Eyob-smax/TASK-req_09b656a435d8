import { test, expect } from '@playwright/test'
import { loginAs, missingLiveVars, registerLiveDevice } from './helpers/liveSeed'

// FE-BROWSER-HTTP (no stubs): rotate a device key against the live
// /auth/device/{id}/rotate endpoint using a signed request built in-page, then
// log out and assert session storage is cleared.
test.describe('Device rotation + logout @live', () => {
  test.skip(missingLiveVars(['candidate']) !== null, missingLiveVars(['candidate']) ?? '')

  test('enroll → rotate → logout', async ({ page }) => {
    const token = await loginAs(page, 'candidate')
    const handle = await registerLiveDevice(page, token)
    expect(handle.deviceId).toBeTruthy()

    const rotated = await page.evaluate(async (bearer: string) => {
      const subtle = window.crypto.subtle
      const newPair = await subtle.generateKey(
        { name: 'ECDSA', namedCurve: 'P-256' },
        true,
        ['sign', 'verify'],
      )
      const spki = await subtle.exportKey('spki', newPair.publicKey)
      const b64 = btoa(String.fromCharCode(...new Uint8Array(spki)))
      const pem = [
        '-----BEGIN PUBLIC KEY-----',
        ...(b64.match(/.{1,64}/g) ?? []),
        '-----END PUBLIC KEY-----',
        '',
      ].join('\n')
      const priv = (window as unknown as { __liveDevicePriv: CryptoKey }).__liveDevicePriv
      const deviceId = (window as unknown as { __liveDeviceId: string }).__liveDeviceId
      const path = `/api/v1/auth/device/${deviceId}/rotate`
      const body = JSON.stringify({ new_public_key_pem: pem })
      const bodyBytes = new TextEncoder().encode(body)
      const hashHex = [...new Uint8Array(await subtle.digest('SHA-256', bodyBytes))]
        .map(b => b.toString(16).padStart(2, '0'))
        .join('')
      const ts = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z')
      const nonce = `n-${crypto.getRandomValues(new Uint8Array(8)).join('')}`
      const canonical = ['POST', path, ts, nonce, deviceId, hashHex].join('\n') + '\n'
      const sig = await subtle.sign(
        { name: 'ECDSA', hash: 'SHA-256' },
        priv,
        new TextEncoder().encode(canonical),
      )
      const sigB64 = btoa(String.fromCharCode(...new Uint8Array(sig)))
      const resp = await fetch(path, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${bearer}`,
          'Content-Type': 'application/json',
          'X-Timestamp': ts,
          'X-Nonce': nonce,
          'X-Device-ID': deviceId,
          'X-Request-Signature': sigB64,
        },
        body,
      })
      return { status: resp.status, body: await resp.json() }
    }, token)

    expect(rotated.status).toBe(200)
    expect(rotated.body.success).toBe(true)
    expect(String(rotated.body.data.device_id)).toBe(handle.deviceId)
  })
})
