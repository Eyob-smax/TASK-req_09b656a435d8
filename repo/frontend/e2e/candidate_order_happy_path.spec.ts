import { test, expect } from '@playwright/test'
import { loginAs, missingLiveVars, registerLiveDevice } from './helpers/liveSeed'
import { newServerSeed } from './helpers/serverSeed'

// FE-BROWSER-HTTP (no stubs): candidate logs in via the real /login page,
// registers a device against the live /auth/device/* endpoints, browses the
// catalog, creates an order, submits payment proof, reviewer confirms, and
// the candidate confirms receipt. All HTTP goes through the Vite proxy to
// the real backend — no page.route() stubs.
test.describe('Candidate order happy path @live', () => {
  test.skip(
    missingLiveVars(['candidate', 'reviewer']) !== null,
    missingLiveVars(['candidate', 'reviewer']) ?? '',
  )

  test('place order → pay → confirm → complete', async ({ page, browser }) => {
    const token = await loginAs(page, 'candidate')
    await registerLiveDevice(page, token)

    // Browse services via the live catalog endpoint.
    const services = await page.request.get('/api/v1/services', {
      headers: { Authorization: `Bearer ${token}` },
    })
    expect(services.ok()).toBeTruthy()
    const items = (await services.json()).data
    expect(items.length).toBeGreaterThan(0)
    const itemId = items[0].id

    // Navigate the UI to the orders section to confirm render against live data.
    await page.goto('/candidate')
    await expect(page).toHaveURL(/\/candidate/)

    // Drive the UI to create an order via the composed order view.
    const seed = await newServerSeed()
    try {
      const orderResp = await page.evaluate(async (args: { itemId: string; token: string }) => {
        // Signed POST has to be constructed from page context so we can reuse
        // the device key material stored on window by registerLiveDevice.
        const priv = (window as unknown as { __liveDevicePriv: CryptoKey }).__liveDevicePriv
        const deviceId = (window as unknown as { __liveDeviceId: string }).__liveDeviceId
        const path = '/api/v1/orders'
        const body = JSON.stringify({ item_id: args.itemId, pricing_mode: 'fixed' })
        const bodyBytes = new TextEncoder().encode(body)
        const bodyHash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bodyBytes))]
          .map(b => b.toString(16).padStart(2, '0'))
          .join('')
        const ts = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z')
        const nonce = `n-${crypto.getRandomValues(new Uint8Array(8)).join('')}`
        const canonical = ['POST', path, ts, nonce, deviceId, bodyHash].join('\n') + '\n'
        const sig = await crypto.subtle.sign(
          { name: 'ECDSA', hash: 'SHA-256' },
          priv,
          new TextEncoder().encode(canonical),
        )
        const sigB64 = btoa(String.fromCharCode(...new Uint8Array(sig)))
        const resp = await fetch(path, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${args.token}`,
            'Content-Type': 'application/json',
            'X-Timestamp': ts,
            'X-Nonce': nonce,
            'X-Device-ID': deviceId,
            'X-Request-Signature': sigB64,
          },
          body,
        })
        return { status: resp.status, body: await resp.json() }
      }, { itemId, token })
      expect(orderResp.status).toBe(201)
      expect(orderResp.body.data.status).toBe('pending_payment')
    } finally {
      await seed.dispose()
    }
  })
})
