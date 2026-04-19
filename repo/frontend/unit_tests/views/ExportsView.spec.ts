// FE-UNIT: ExportsView — export list, create form, success message, download link.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'
import ExportsView from '@/views/admin/ExportsView.vue'

vi.mock('@/services/adminApi', () => ({
  listExports: vi.fn().mockResolvedValue({
    data: [
      {
        id: 'job-1',
        requested_by: 'admin-1',
        export_type: 'audit_csv',
        status: 'completed',
        sha256_hash: 'a'.repeat(64),
        watermark_applied: true,
        completed_at: '2024-01-01T00:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
      },
    ],
    pagination: { total: 1 },
  }),
  createExport: vi.fn().mockResolvedValue({
    id: 'job-1',
    requested_by: 'admin-1',
    export_type: 'audit_csv',
    status: 'completed',
    sha256_hash: 'a'.repeat(64),
    watermark_applied: true,
    completed_at: '2024-01-01T00:00:00Z',
    created_at: '2024-01-01T00:00:00Z',
  }),
  getFlags: vi.fn().mockResolvedValue([]),
  updateFlag: vi.fn(),
  listCohorts: vi.fn().mockResolvedValue([]),
  createCohort: vi.fn(),
  assignCohort: vi.fn(),
  listCacheStats: vi.fn().mockResolvedValue({ data: [], pagination: { total: 0 } }),
  getMetricsSummary: vi.fn().mockResolvedValue({}),
  listForecasts: vi.fn().mockResolvedValue({ data: [], pagination: { total: 0 } }),
  searchAudit: vi.fn().mockResolvedValue({ data: [], pagination: { total: 0, page: 1, page_size: 20, total_pages: 1 } }),
  getRbacPolicy: vi.fn().mockResolvedValue({}),
  getMaskingPolicy: vi.fn().mockResolvedValue({}),
}))

describe('ExportsView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders the exports view', async () => {
    const wrapper = mount(ExportsView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true, TimestampDisplay: true } },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="exports-view"]').exists()).toBe(true)
  })

  it('renders the create export form', async () => {
    const wrapper = mount(ExportsView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true, TimestampDisplay: true } },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="export-create-form"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="export-type-select"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="export-create-btn"]').exists()).toBe(true)
  })

  it('renders existing export jobs', async () => {
    const wrapper = mount(ExportsView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true, TimestampDisplay: true } },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="export-list-table"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="export-row"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('audit_csv')
  })

  it('download link present for completed export', async () => {
    const wrapper = mount(ExportsView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true, TimestampDisplay: true } },
    })
    await flushPromises()
    const link = wrapper.find('[data-testid="export-download-link"]')
    expect(link.exists()).toBe(true)
    expect(link.attributes('href')).toContain('/api/v1/admin/exports/job-1/download')
  })

  it('create export form submit shows success message', async () => {
    const { createExport } = await import('@/services/adminApi')
    const wrapper = mount(ExportsView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true, TimestampDisplay: true } },
    })
    await flushPromises()
    await wrapper.find('[data-testid="export-create-form"]').trigger('submit')
    await flushPromises()
    expect(createExport).toHaveBeenCalled()
    expect(wrapper.find('[data-testid="export-success"]').exists()).toBe(true)
  })
})
