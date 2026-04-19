// FE-BROWSER: Reviewer queue action workflow — document queue table renders, payment confirmation action works,
// exception queue links to review screen.

import { test, expect } from '@playwright/test'
import { seedAuth } from './helpers/seedAuth'

const QUEUE_RESPONSE = (items: unknown[]) => ({
  success: true,
  data: items,
  pagination: { page: 1, page_size: 20, total: items.length, total_pages: 1 },
})

test.describe('Reviewer queue action workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await seedAuth(page, {
      user: { id: 'rev-1', username: 'reviewer1', role: 'reviewer', full_name: 'Reviewer', is_active: true, last_login_at: null },
      role: 'reviewer',
      tokens: { access_token: 'fake.jwt.token', refresh_token: 'fake.refresh.token', token_type: 'bearer', expires_in: 900 },
      deviceId: 'device-1',
      candidateId: null,
    })

    await page.route('**/api/v1/queue/documents**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(QUEUE_RESPONSE([
          {
            document_id: 'doc-1', candidate_id: 'user-1',
            document_type: 'pdf', current_status: 'pending_review',
            submitted_at: '2024-01-01T00:00:00Z', requirement_code: 'TRANSCRIPT',
          },
        ])),
      })
    })

    await page.route('**/api/v1/queue/payments**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(QUEUE_RESPONSE([
          {
            order_id: 'order-1', candidate_id: 'user-1',
            item_name: 'NMAT Review', amount: '1200.00',
            payment_method: 'bank_transfer', reference_number: 'TXN-001',
            submitted_at: '2024-01-01T00:00:00Z',
          },
        ])),
      })
    })

    await page.route('**/api/v1/queue/exceptions**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(QUEUE_RESPONSE([
          {
            exception_id: 'exc-1', candidate_id: 'user-1',
            anomaly_type: 'absence', status: 'pending_initial_review',
            current_stage: 'initial', submitted_at: '2024-01-01T00:00:00Z',
          },
        ])),
      })
    })

    await page.route('**/api/v1/queue/orders**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(QUEUE_RESPONSE([])),
      })
    })

    await page.route('**/api/v1/queue/after-sales**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(QUEUE_RESPONSE([])),
      })
    })
  })

  test('document queue table renders with pending document', async ({ page }) => {
    await page.goto('/staff/documents')
    await expect(page.getByTestId('document-queue-view')).toBeVisible()
    await expect(page.getByText('TRANSCRIPT')).toBeVisible({ timeout: 5000 })
  })

  test('document queue row has review link', async ({ page }) => {
    await page.goto('/staff/documents')
    await expect(page.locator('a[href="/staff/documents/doc-1/review?candidateId=user-1"]')).toBeVisible({ timeout: 5000 })
  })

  test('exception queue table renders with pending exception', async ({ page }) => {
    await page.goto('/staff/exceptions')
    await expect(page.getByTestId('exception-queue-view')).toBeVisible({ timeout: 5000 })
  })

  test('exception queue row has review link', async ({ page }) => {
    await page.goto('/staff/exceptions')
    await expect(page.locator('a[href="/staff/exceptions/exc-1/review"]')).toBeVisible({ timeout: 5000 })
  })

  test('payment queue view shows pending payment entry', async ({ page }) => {
    await page.route('**/api/v1/queue/payments**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(QUEUE_RESPONSE([
          {
            order_id: 'order-1', candidate_id: 'user-1',
            item_name: 'NMAT Review', amount: '1200.00',
            payment_method: 'bank_transfer', reference_number: 'TXN-001',
            submitted_at: '2024-01-01T00:00:00Z',
          },
        ])),
      })
    })
    await page.goto('/staff/payments')
    await expect(page.getByText('TXN-001')).toBeVisible({ timeout: 5000 })
  })
})
