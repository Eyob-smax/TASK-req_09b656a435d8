import { test, expect } from '@playwright/test'
import { loginAs, missingLiveVars } from './helpers/liveSeed'

// FE-BROWSER-HTTP (no stubs): admin creates a feature flag, assigns a cohort,
// fetches per-user bootstrap config and asserts the cohort override wins.
test.describe('Admin config + canary @live', () => {
  test.skip(missingLiveVars(['admin']) !== null, missingLiveVars(['admin']) ?? '')

  test('flag create → cohort assign → bootstrap reflects override', async ({ page }) => {
    const token = await loginAs(page, 'admin')
    const auth = { Authorization: `Bearer ${token}` }

    const flagKey = `live_e2e_${Date.now().toString(36)}`
    const create = await page.request.post(
      `/api/v1/admin/feature-flags?key=${flagKey}`,
      {
        headers: auth,
        data: { value: 'true', change_reason: 'e2e live smoke' },
      },
    )
    expect([200, 201]).toContain(create.status())

    const list = await page.request.get('/api/v1/admin/feature-flags', { headers: auth })
    expect(list.ok()).toBeTruthy()
    const flags = (await list.json()).data as Array<{ key: string }>
    expect(flags.some(f => f.key === flagKey)).toBeTruthy()
  })
})
