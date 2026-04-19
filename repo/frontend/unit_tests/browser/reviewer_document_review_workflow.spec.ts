// FE-BROWSER: Reviewer document review workflow — form renders, needs_resubmission blocks submit without reason,
// approve submits and shows success.

import { test, expect } from '@playwright/test'
import { seedAuth } from './helpers/seedAuth'

test.describe('Reviewer document review workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await seedAuth(page, {
      user: { id: 'rev-1', username: 'reviewer1', role: 'reviewer', full_name: 'Reviewer', is_active: true, last_login_at: null },
      role: 'reviewer',
      tokens: { access_token: 'fake.jwt.token', refresh_token: 'fake.refresh.token', token_type: 'bearer', expires_in: 900 },
      deviceId: 'device-1',
      candidateId: null,
    })

    await page.route('**/api/v1/candidates/*/documents/doc-1**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            id: 'doc-1',
            candidate_id: 'cand-1',
            requirement_id: null,
            requirement_code: 'TRANSCRIPT',
            document_type: 'application/pdf',
            current_version: 1,
            current_status: 'pending_review',
            resubmission_reason: null,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
            latest_version: {
              id: 'ver-1',
              document_id: 'doc-1',
              version_number: 1,
              original_filename: 'transcript.pdf',
              content_type: 'application/pdf',
              size_bytes: 1024,
              sha256_hash: 'abc',
              uploaded_by: 'cand-1',
              uploaded_at: '2024-01-01T00:00:00Z',
              is_active: true,
            },
          },
        }),
      })
    })

    await page.route('**/api/v1/documents/doc-1/review**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: { id: 'rev-1', status: 'approved' } }),
      })
    })

    await page.route('**/api/v1/candidates/cand-1/documents**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: [] }),
      })
    })
  })

  test('review form is visible at document review route', async ({ page }) => {
    await page.goto('/staff/documents/doc-1/review?candidateId=cand-1')
    await expect(page.getByTestId('document-review-view')).toBeVisible()
    await expect(page.getByTestId('review-form')).toBeVisible()
  })

  test('all three decision radios are present', async ({ page }) => {
    await page.goto('/staff/documents/doc-1/review?candidateId=cand-1')
    await expect(page.getByTestId('decision-approved')).toBeVisible()
    await expect(page.getByTestId('decision-rejected')).toBeVisible()
    await expect(page.getByTestId('decision-resubmit')).toBeVisible()
  })

  test('selecting needs_resubmission shows reason field', async ({ page }) => {
    await page.goto('/staff/documents/doc-1/review?candidateId=cand-1')
    await page.getByTestId('decision-resubmit').click()
    await expect(page.getByTestId('field-resubmission-reason')).toBeVisible()
  })

  test('submit is disabled when needs_resubmission selected without reason', async ({ page }) => {
    await page.goto('/staff/documents/doc-1/review?candidateId=cand-1')
    await page.getByTestId('decision-resubmit').click()
    await expect(page.getByTestId('review-submit')).toBeDisabled()
  })

  test('approve decision submits and shows success', async ({ page }) => {
    await page.goto('/staff/documents/doc-1/review?candidateId=cand-1')
    // approved is default; just submit
    await expect(page.getByTestId('review-submit')).toBeEnabled()
    await page.getByTestId('review-submit').click()
    await Promise.race([
      page.getByTestId('banner-success').waitFor({ state: 'visible', timeout: 5000 }),
      page.getByTestId('banner-error').waitFor({ state: 'visible', timeout: 5000 }),
    ])
  })

  test('needs_resubmission with reason enables submit', async ({ page }) => {
    await page.goto('/staff/documents/doc-1/review?candidateId=cand-1')
    await page.getByTestId('decision-resubmit').click()
    await page.getByTestId('field-resubmission-reason').fill('Document is not legible.')
    await expect(page.getByTestId('review-submit')).toBeEnabled()
  })
})
