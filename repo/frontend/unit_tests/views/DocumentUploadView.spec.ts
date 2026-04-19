// FE-UNIT: DocumentUploadView — upload panel rendered, success state shows hash, error banner shown.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import DocumentUploadView from '@/views/candidate/documents/DocumentUploadView.vue'
import { useDocumentStore } from '@/stores/document'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/services/documentApi', () => ({
  listDocuments: vi.fn().mockResolvedValue([]),
  uploadDocument: vi.fn().mockResolvedValue({
    document_id: 'doc-1',
    version_number: 1,
    original_filename: 'file.pdf',
    content_type: 'application/pdf',
    size_bytes: 1024,
    sha256_hash: 'abc123def456',
    status: 'pending_review',
    uploaded_at: '2026-01-01T10:00:00Z',
  }),
  reviewDocument: vi.fn(),
  downloadDocument: vi.fn(),
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/candidate/documents/upload', component: DocumentUploadView },
    { path: '/candidate/documents', component: { template: '<div />' } },
  ],
})

describe('DocumentUploadView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.user = { id: 'user-1', username: 'testuser', role: 'candidate', full_name: 'Test User', is_active: true, last_login_at: null }
    auth.candidateId = 'cand-1'
  })

  it('renders the upload view container', async () => {
    const wrapper = mount(DocumentUploadView, { global: { plugins: [router] } })
    expect(wrapper.find('[data-testid="document-upload-view"]').exists()).toBe(true)
  })

  it('shows requirement code input field', async () => {
    const wrapper = mount(DocumentUploadView, { global: { plugins: [router] } })
    expect(wrapper.find('[data-testid="field-requirement-code"]').exists()).toBe(true)
  })

  it('shows success banner and SHA-256 hash after upload', async () => {
    const wrapper = mount(DocumentUploadView, { global: { plugins: [router] } })
    const docStore = useDocumentStore()
    docStore.upload = vi.fn().mockResolvedValue({ sha256_hash: 'abc123def456' })
    // Simulate a successful upload by setting uploadedHash directly
    await wrapper.vm.$forceUpdate()
    // Trigger handleUpload via the store mock
    const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    await (wrapper.vm as any).handleUpload({ file: mockFile, requirementCode: null })
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-testid="upload-success"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('abc123def456')
  })

  it('shows error banner when upload fails', async () => {
    const wrapper = mount(DocumentUploadView, { global: { plugins: [router] } })
    const docStore = useDocumentStore()
    docStore.uploadError = 'File too large'
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('File too large')
  })

  it('does not show success state initially', async () => {
    const wrapper = mount(DocumentUploadView, { global: { plugins: [router] } })
    expect(wrapper.find('[data-testid="upload-success"]').exists()).toBe(false)
  })
})
