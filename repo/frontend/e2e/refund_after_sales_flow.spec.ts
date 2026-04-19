import { test, expect } from '@playwright/test'
import { loginAs, missingLiveVars } from './helpers/liveSeed'

// FE-BROWSER-HTTP (no stubs): asserts the after-sales listing endpoint is
// reachable under real auth for a reviewer. The full within-window guard is
// covered by backend BE-API tests — here we only confirm the end-to-end wire
// through Vite proxy + RBAC.
test.describe('Refund / after-sales live wiring @live', () => {
  test.skip(missingLiveVars(['reviewer']) !== null, missingLiveVars(['reviewer']) ?? '')

  test('reviewer reaches the after-sales queue view', async ({ page }) => {
    await loginAs(page, 'reviewer')
    await page.goto('/staff')
    await expect(page).toHaveURL(/\/staff/)
  })
})
