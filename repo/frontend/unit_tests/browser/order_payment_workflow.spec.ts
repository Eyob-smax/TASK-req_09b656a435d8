// FE-BROWSER: Fixed-price order payment submission workflow — form renders, submits proof, shows success.

import { test, expect } from '@playwright/test'
import { seedAuth } from './helpers/seedAuth'

const FAKE_ORDER = {
  id: 'order-1', candidate_id: 'user-1', item_id: 'item-1',
  status: 'pending_payment',
  pricing_mode: 'fixed', agreed_price: null,
  auto_cancel_at: null, completed_at: null, canceled_at: null, cancellation_reason: null,
  created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z',
  events: [],
}

test.describe('Order payment submission workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await seedAuth(page, {
      user: { id: 'user-1', username: 'cand1', role: 'candidate', full_name: 'Test', is_active: true, last_login_at: null },
      role: 'candidate',
      tokens: { access_token: 'fake.jwt.token', refresh_token: 'fake.refresh.token', token_type: 'bearer', expires_in: 900 },
      deviceId: 'device-1',
      candidateId: 'cand-1',
    })

    await page.route('**/api/v1/orders/order-1', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: FAKE_ORDER }),
      })
    })

    await page.route('**/api/v1/services', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: [
            {
              id: 'item-1',
              item_code: 'SVC-1',
              name: 'NMAT Review Course',
              description: null,
              pricing_mode: 'fixed',
              fixed_price: '1200.00',
              is_capacity_limited: false,
              bargaining_enabled: false,
              available_slots: null,
            },
          ],
        }),
      })
    })
  })

  test('payment view renders with correct order amount pre-filled', async ({ page }) => {
    await page.goto('/candidate/orders/order-1/payment')
    await expect(page.getByTestId('payment-view')).toBeVisible()
    await expect(page.getByTestId('field-amount')).toHaveValue('1200.00')
  })

  test('payment form has all required fields', async ({ page }) => {
    await page.goto('/candidate/orders/order-1/payment')
    await expect(page.getByTestId('field-payment-method')).toBeVisible()
    await expect(page.getByTestId('field-reference-number')).toBeVisible()
    await expect(page.getByTestId('field-amount')).toBeVisible()
  })

  test('submit proof shows success banner and hides form', async ({ page }) => {
    await page.route('**/api/v1/orders/order-1/payment/proof', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: { id: 'pay-1', confirmed_by: null } }),
      })
    })
    await page.goto('/candidate/orders/order-1/payment')
    await page.getByTestId('field-payment-method').selectOption('bank_transfer')
    await page.getByTestId('field-reference-number').fill('TXN-12345')
    await page.getByTestId('payment-submit').click()
    await expect(page.getByText(/Payment proof submitted/i)).toBeVisible({ timeout: 5000 })
    await expect(page.getByTestId('payment-form')).toHaveCount(0)
  })
})
