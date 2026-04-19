import { test, expect } from '@playwright/test'

test.describe('Application shell', () => {
  test('loads root route without JS errors', async ({ page }) => {
    const errors: string[] = []
    page.on('pageerror', (err) => errors.push(err.message))

    await page.goto('/')
    // Expect redirect to /login shell (or root renders without crash)
    await expect(page).toHaveURL(/\/(login)?/)
    expect(errors).toHaveLength(0)
  })

  test('login route is reachable', async ({ page }) => {
    await page.goto('/login')
    await expect(page).toHaveURL('/login')
    // Page must render something — not a blank white screen
    const body = await page.locator('body')
    await expect(body).not.toBeEmpty()
  })
})
