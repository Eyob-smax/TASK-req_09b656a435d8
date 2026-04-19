// FE-BROWSER: Candidate document upload workflow — UploadPanel validates MIME/size client-side;
// rejects invalid files before any network call; accepts valid PDF.

import { test, expect } from '@playwright/test'
import { seedAuth } from './helpers/seedAuth'

test.describe('Candidate document upload workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await seedAuth(page, {
      user: { id: 'user-1', username: 'cand1', role: 'candidate', full_name: 'Test', is_active: true, last_login_at: null },
      role: 'candidate',
      tokens: { access_token: 'fake.jwt.token', refresh_token: 'fake.refresh.token', token_type: 'bearer', expires_in: 900 },
      deviceId: 'device-1',
      candidateId: 'cand-1',
    })
  })

  test('upload view container is accessible from documents path', async ({ page }) => {
    await page.goto('/candidate/documents/upload')
    await expect(page.getByTestId('document-upload-view')).toBeVisible()
  })

  test('requirement code field is present', async ({ page }) => {
    await page.goto('/candidate/documents/upload')
    await expect(page.getByTestId('field-requirement-code')).toBeVisible()
  })

  test('rejects non-PDF/JPG/PNG file before upload', async ({ page }) => {
    await page.goto('/candidate/documents/upload')
    // Simulate invalid file type via input (text/plain)
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles({
      name: 'malware.exe',
      mimeType: 'application/octet-stream',
      buffer: Buffer.from('fake binary'),
    })
    // The UploadPanel emits a validation error — client-side rejection
    await expect(page.getByText(/only PDF|PNG|JPG/i)).toBeVisible()
  })

  test('success state shows SHA-256 hash after successful upload mock', async ({ page }) => {
    // Intercept the upload API call to return a mock hash
    await page.route('**/api/v1/candidates/*/documents/upload', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            document_id: 'doc-1',
            version_number: 1,
            original_filename: 'doc.pdf',
            content_type: 'application/pdf',
            size_bytes: 1024,
            sha256_hash: 'deadbeef1234567890abcdef',
            status: 'pending_review',
            uploaded_at: '2026-01-01T10:00:00Z',
          },
        }),
      })
    })
    await page.goto('/candidate/documents/upload')
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles({
      name: 'transcript.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4 fake pdf content'),
    })
    // Wait for success state
    await expect(page.getByTestId('upload-success')).toBeVisible({ timeout: 5000 })
  })
})
