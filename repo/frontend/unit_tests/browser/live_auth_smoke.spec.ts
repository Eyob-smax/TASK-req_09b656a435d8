import { test, expect } from '@playwright/test'

// FE-BROWSER-HTTP (no stubs): exercises real login + /auth/me flow through
// the Vite /api proxy against a running local backend.
test.describe('Live API auth smoke @live', () => {
  const username = process.env.PW_LIVE_USERNAME
  const password = process.env.PW_LIVE_PASSWORD

  test.skip(!username || !password, 'Set PW_LIVE_USERNAME and PW_LIVE_PASSWORD to run live API smoke tests.')

  test('login succeeds and redirects to role home without route stubs', async ({ page }) => {
    await page.goto('/login')
    await page.getByTestId('login-username').fill(username as string)
    await page.getByTestId('login-password').fill(password as string)
    await page.getByTestId('login-submit').click()

    await expect(page).toHaveURL(/\/(candidate|staff|admin)(\/|$)/, { timeout: 15000 })
  })
})
