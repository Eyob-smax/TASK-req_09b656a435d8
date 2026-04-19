// FE-UNIT: AuditLogView — table renders, filter form exists, search dispatches.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'
import AuditLogView from '@/views/admin/AuditLogView.vue'

vi.mock('@/services/adminApi', () => ({
  searchAudit: vi.fn().mockResolvedValue({
    data: [
      {
        id: 'ae-1',
        event_type: 'login_success',
        actor_id: 'user-abc',
        actor_role: 'candidate',
        resource_type: 'user',
        resource_id: 'user-abc',
        occurred_at: '2024-01-01T10:00:00Z',
        trace_id: 'trace-1',
        outcome: 'success',
        detail: null,
      },
    ],
    pagination: { total: 1, page: 1, page_size: 20, total_pages: 1 },
  }),
  getFlags: vi.fn().mockResolvedValue([]),
  updateFlag: vi.fn(),
  listCohorts: vi.fn().mockResolvedValue([]),
  createCohort: vi.fn(),
  assignCohort: vi.fn(),
  listCacheStats: vi.fn().mockResolvedValue({ data: [], pagination: { total: 0 } }),
  getMetricsSummary: vi.fn().mockResolvedValue({}),
  listForecasts: vi.fn().mockResolvedValue({ data: [], pagination: { total: 0 } }),
  listExports: vi.fn().mockResolvedValue({ data: [], pagination: { total: 0 } }),
  getRbacPolicy: vi.fn().mockResolvedValue({}),
  getMaskingPolicy: vi.fn().mockResolvedValue({}),
  createExport: vi.fn(),
}))

describe('AuditLogView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders the audit log container', async () => {
    const wrapper = mount(AuditLogView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true, TimestampDisplay: true, PaginationControls: true } },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="audit-log-view"]').exists()).toBe(true)
  })

  it('renders the filter form', async () => {
    const wrapper = mount(AuditLogView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true, TimestampDisplay: true, PaginationControls: true } },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="audit-filter-form"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="filter-event-type"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="filter-actor-id"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="audit-search-btn"]').exists()).toBe(true)
  })

  it('renders audit entries after load', async () => {
    const wrapper = mount(AuditLogView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true, TimestampDisplay: true, PaginationControls: true } },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('login_success')
    expect(wrapper.text()).toContain('success')
  })

  it('search button triggers searchAudit with filter values', async () => {
    const { searchAudit } = await import('@/services/adminApi')
    const wrapper = mount(AuditLogView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true, TimestampDisplay: true, PaginationControls: true } },
    })
    await flushPromises()
    await wrapper.find('[data-testid="filter-event-type"]').setValue('login_failure')
    await wrapper.find('[data-testid="audit-filter-form"]').trigger('submit')
    await flushPromises()
    expect(searchAudit).toHaveBeenCalledWith(
      expect.objectContaining({ event_type: 'login_failure' }),
    )
  })
})
