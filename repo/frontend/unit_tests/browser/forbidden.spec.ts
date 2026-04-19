// FE-BROWSER: visiting a guarded route while unauthenticated lands on
// /login with the original path preserved in the redirect query; visiting
// /forbidden directly renders the forbidden shell.

import { test, expect } from '@playwright/test'

test.describe('Forbidden and auth-guard shell', () => {
  test('unauthenticated access to /admin redirects to /login?redirect=/admin', async ({ page }) => {
    await page.goto('/admin')
    await expect(page).toHaveURL(/\/login\?redirect=\/admin/)
  })

  test('unauthenticated access to /candidate redirects to /login', async ({ page }) => {
    await page.goto('/candidate')
    await expect(page).toHaveURL(/\/login\?redirect=\/candidate/)
  })

  test('/forbidden renders the forbidden shell', async ({ page }) => {
    await page.goto('/forbidden')
    await expect(page.getByText(/forbidden/i).first()).toBeVisible()
    await expect(page.getByTestId('forbidden-signout')).toBeVisible()
  })
})
