import { test, expect } from '@playwright/test'
import { loginAs, missingLiveVars } from './helpers/liveSeed'

// FE-BROWSER-HTTP (no stubs): admin creates an export, lists it, downloads
// it, asserts the CSV is non-empty and its SHA-256 matches the create-time
// hash. Also probes the audit log endpoint.
test.describe('Admin exports + audit @live', () => {
  test.skip(missingLiveVars(['admin']) !== null, missingLiveVars(['admin']) ?? '')

  test('create export → download → sha256 parity', async ({ page }) => {
    const token = await loginAs(page, 'admin')
    const auth = { Authorization: `Bearer ${token}` }

    const create = await page.request.post('/api/v1/admin/exports', {
      headers: auth,
      data: { export_type: 'audit_csv', filters: null },
    })
    expect([200, 201]).toContain(create.status())
    const createdData = (await create.json()).data
    expect(createdData.sha256_hash).toBeTruthy()
    expect(createdData.watermark_applied).toBe(true)

    const download = await page.request.get(
      `/api/v1/admin/exports/${createdData.id}/download`,
      { headers: auth },
    )
    expect(download.ok()).toBeTruthy()
    const disposition = download.headers()['content-disposition'] ?? ''
    expect(disposition).toContain('attachment')
    expect(disposition).toContain('.csv')
    const bytes = await download.body()
    expect(bytes.byteLength).toBeGreaterThan(0)
    const digest = await crypto.subtle.digest('SHA-256', bytes)
    const hex = [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('')
    expect(hex).toBe(createdData.sha256_hash)

    const audit = await page.request.get('/api/v1/admin/audit', { headers: auth })
    expect(audit.ok()).toBeTruthy()
  })
})
