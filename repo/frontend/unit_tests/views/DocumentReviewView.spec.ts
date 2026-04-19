// FE-UNIT: DocumentReviewView — radio decisions, resubmission reason required only for needs_resubmission, submit disabled when hasError.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import DocumentReviewView from '@/views/staff/documents/DocumentReviewView.vue'
import { useDocumentStore } from '@/stores/document'

vi.mock('@/services/documentApi', () => ({
  listDocuments: vi.fn().mockResolvedValue([]),
  getDocument: vi.fn().mockResolvedValue({
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
      size_bytes: 1234,
      sha256_hash: 'abc',
      uploaded_by: 'cand-1',
      uploaded_at: '2024-01-01T00:00:00Z',
      is_active: true,
    },
  }),
  uploadDocument: vi.fn(),
  reviewDocument: vi.fn().mockResolvedValue({ id: 'rev-1', status: 'approved' }),
  downloadDocument: vi.fn().mockResolvedValue(new Blob()),
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/staff/documents/:documentId/review', component: DocumentReviewView },
    { path: '/staff/documents', component: { template: '<div />' } },
  ],
})

describe('DocumentReviewView', () => {
  beforeEach(async () => {
    setActivePinia(createPinia())
    await router.push('/staff/documents/doc-1/review?candidateId=cand-1')
    await router.isReady()
  })

  it('renders the review form', async () => {
    const wrapper = mount(DocumentReviewView, { global: { plugins: [router] } })
    await flushPromises()
    expect(wrapper.find('[data-testid="review-form"]').exists()).toBe(true)
  })

  it('shows three decision radio buttons', async () => {
    const wrapper = mount(DocumentReviewView, { global: { plugins: [router] } })
    await flushPromises()
    expect(wrapper.find('[data-testid="decision-approved"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="decision-rejected"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="decision-resubmit"]').exists()).toBe(true)
  })

  it('does not show resubmission reason field when approved is selected', async () => {
    const wrapper = mount(DocumentReviewView, { global: { plugins: [router] } })
    await flushPromises()
    // default is approved
    expect(wrapper.find('[data-testid="field-resubmission-reason"]').exists()).toBe(false)
  })

  it('shows resubmission reason field when needs_resubmission is selected', async () => {
    const wrapper = mount(DocumentReviewView, { global: { plugins: [router] } })
    await flushPromises()
    await wrapper.find('[data-testid="decision-resubmit"]').trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-testid="field-resubmission-reason"]').exists()).toBe(true)
  })

  it('disables submit when needs_resubmission selected but no reason given', async () => {
    const wrapper = mount(DocumentReviewView, { global: { plugins: [router] } })
    await flushPromises()
    await wrapper.find('[data-testid="decision-resubmit"]').trigger('click')
    await wrapper.vm.$nextTick()
    const submitBtn = wrapper.find('[data-testid="review-submit"]')
    expect((submitBtn.element as HTMLButtonElement).disabled).toBe(true)
  })

  it('enables submit when needs_resubmission selected and reason is filled', async () => {
    const wrapper = mount(DocumentReviewView, { global: { plugins: [router] } })
    await flushPromises()
    await wrapper.find('[data-testid="decision-resubmit"]').trigger('click')
    await wrapper.vm.$nextTick()
    await wrapper.find('[data-testid="field-resubmission-reason"]').setValue('Missing pages')
    await wrapper.vm.$nextTick()
    const submitBtn = wrapper.find('[data-testid="review-submit"]')
    expect((submitBtn.element as HTMLButtonElement).disabled).toBe(false)
  })

  it('submit button is enabled by default (approved decision)', async () => {
    const wrapper = mount(DocumentReviewView, { global: { plugins: [router] } })
    await flushPromises()
    const submitBtn = wrapper.find('[data-testid="review-submit"]')
    expect((submitBtn.element as HTMLButtonElement).disabled).toBe(false)
  })

  it('shows success banner after successful submit', async () => {
    const wrapper = mount(DocumentReviewView, { global: { plugins: [router] } })
    await flushPromises()
    const docStore = useDocumentStore()
    docStore.reviewDocument = vi.fn().mockResolvedValue(true)
    await (wrapper.vm as any).submit()
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Decision recorded')
    expect(docStore.reviewDocument).toHaveBeenCalledWith('doc-1', expect.objectContaining({ version_id: 'ver-1' }))
  })
})
