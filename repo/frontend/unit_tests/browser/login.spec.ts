// FE-BROWSER: /login shell renders, accepts input in both fields, and
// shows client-side validation when the password is too short. No backend
// calls are asserted — this is a shell-contract test.

import { test, expect } from '@playwright/test'

test.describe('Login shell', () => {
  test('renders form with username + password fields', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByTestId('login-username')).toBeVisible()
    await expect(page.getByTestId('login-password')).toBeVisible()
    await expect(page.getByTestId('login-submit')).toBeVisible()
  })

  test('enforces 12-char password client-side', async ({ page }) => {
    await page.goto('/login')
    await page.getByTestId('login-username').fill('candidate-1')
    await page.getByTestId('login-password').fill('short')
    await page.getByTestId('login-submit').click()
    await expect(page.getByText(/at least 12/i)).toBeVisible()
  })

  test('accepts entry that meets client-side policy', async ({ page }) => {
    await page.goto('/login')
    await page.getByTestId('login-username').fill('candidate-1')
    await page.getByTestId('login-password').fill('twelve-character-password')
    // Submit may error because no backend is running — we only verify
    // that the client did not block submission on policy grounds.
    await page.getByTestId('login-submit').click()
    await expect(page.getByText(/at least 12/i)).toHaveCount(0)
  })
})
