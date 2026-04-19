// FE-UNIT: ObservabilityView — metrics summary card shows values, cache stats table, trace search input.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'
import ObservabilityView from '@/views/admin/ObservabilityView.vue'

const MOCK_METRICS = {
  merittrack_login_attempts_total: { type: 'counter', total: 42, by_label: {} },
  merittrack_request_duration_seconds: { type: 'histogram', observations: 1000, sum: 25.5, avg: 0.0255 },
}

const MOCK_CACHE = {
  data: [
    {
      id: 'cs-1',
      window_start: '2024-01-01T00:00:00Z',
      window_end: '2024-01-01T00:15:00Z',
      asset_group: 'static',
      total_requests: 200,
      cache_hits: 190,
      cache_misses: 10,
      hit_rate_pct: 95.0,
      computed_at: '2024-01-01T00:15:00Z',
    },
  ],
  pagination: { total: 1 },
}

vi.mock('@/services/adminApi', () => ({
  getMetricsSummary: vi.fn().mockResolvedValue(MOCK_METRICS),
  listCacheStats: vi.fn().mockResolvedValue(MOCK_CACHE),
  getFlags: vi.fn().mockResolvedValue([]),
  updateFlag: vi.fn(),
  listCohorts: vi.fn().mockResolvedValue([]),
  createCohort: vi.fn(),
  assignCohort: vi.fn(),
  listForecasts: vi.fn().mockResolvedValue({ data: [], pagination: { total: 0 } }),
  listExports: vi.fn().mockResolvedValue({ data: [], pagination: { total: 0 } }),
  searchAudit: vi.fn().mockResolvedValue({ data: [], pagination: { total: 0, page: 1, page_size: 20, total_pages: 1 } }),
  getRbacPolicy: vi.fn().mockResolvedValue({}),
  getMaskingPolicy: vi.fn().mockResolvedValue({}),
  createExport: vi.fn(),
}))

describe('ObservabilityView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders the observability view', async () => {
    const wrapper = mount(ObservabilityView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true } },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="observability-view"]').exists()).toBe(true)
  })

  it('renders metrics summary cards', async () => {
    const wrapper = mount(ObservabilityView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true } },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="metrics-summary"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('merittrack_login_attempts_total')
    expect(wrapper.text()).toContain('42')  // total value
  })

  it('renders cache stats table', async () => {
    const wrapper = mount(ObservabilityView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true } },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="cache-stats-table"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('95.0%')
    expect(wrapper.text()).toContain('static')
  })

  it('trace search input is present', async () => {
    const wrapper = mount(ObservabilityView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true } },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="trace-search-input"]').exists()).toBe(true)
  })

  it('trace search input accepts user input', async () => {
    const wrapper = mount(ObservabilityView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true } },
    })
    await flushPromises()
    const input = wrapper.find('[data-testid="trace-search-input"]')
    await input.setValue('abc123')
    expect((input.element as HTMLInputElement).value).toBe('abc123')
  })
})
