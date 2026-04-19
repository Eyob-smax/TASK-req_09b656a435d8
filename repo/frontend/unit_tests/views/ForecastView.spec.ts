// FE-UNIT: ForecastView — snapshot table, empty state, trigger button.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'
import ForecastView from '@/views/admin/ForecastView.vue'

const MOCK_SNAPSHOT = {
  id: 'snap-1',
  computed_at: '2024-01-01T00:00:00Z',
  forecast_horizon_days: 30,
  input_window_days: 90,
  bandwidth_p50_bytes: 512_000,
  bandwidth_p95_bytes: 5_120_000,
  request_volume_forecast: { '2024-01-02': 100 },
  upload_volume_trend: { avg_daily_requests: 9600 },
}

vi.mock('@/services/adminApi', () => ({
  listForecasts: vi.fn().mockResolvedValue({ data: [MOCK_SNAPSHOT], pagination: { total: 1 } }),
  triggerForecast: vi.fn().mockResolvedValue(MOCK_SNAPSHOT),
  getFlags: vi.fn().mockResolvedValue([]),
  updateFlag: vi.fn(),
  listCohorts: vi.fn().mockResolvedValue([]),
  createCohort: vi.fn(),
  assignCohort: vi.fn(),
  listCacheStats: vi.fn().mockResolvedValue({ data: [], pagination: { total: 0 } }),
  getMetricsSummary: vi.fn().mockResolvedValue({}),
  listExports: vi.fn().mockResolvedValue({ data: [], pagination: { total: 0 } }),
  searchAudit: vi.fn().mockResolvedValue({ data: [], pagination: { total: 0, page: 1, page_size: 20, total_pages: 1 } }),
  getRbacPolicy: vi.fn().mockResolvedValue({}),
  getMaskingPolicy: vi.fn().mockResolvedValue({}),
  createExport: vi.fn(),
}))

describe('ForecastView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders the forecast view', async () => {
    const wrapper = mount(ForecastView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true, TimestampDisplay: true } },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="forecast-view"]').exists()).toBe(true)
  })

  it('renders forecast table with snapshot data', async () => {
    const wrapper = mount(ForecastView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true, TimestampDisplay: true } },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="forecast-table"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="forecast-row"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('30')   // horizon_days
    expect(wrapper.text()).toContain('90')   // input_window_days
  })

  it('shows bandwidth in MB', async () => {
    const wrapper = mount(ForecastView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true, TimestampDisplay: true } },
    })
    await flushPromises()
    // 512_000 bytes / 1_048_576 ≈ 0.5 MB
    expect(wrapper.text()).toContain('MB')
  })

  it('trigger forecast button exists', async () => {
    const wrapper = mount(ForecastView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true, TimestampDisplay: true } },
    })
    expect(wrapper.find('[data-testid="trigger-forecast-btn"]').exists()).toBe(true)
  })

  it('empty state shown when no snapshots', async () => {
    const { listForecasts } = await import('@/services/adminApi')
    ;(listForecasts as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ data: [], pagination: { total: 0 } })

    const wrapper = mount(ForecastView, {
      global: { stubs: { LoadingSpinner: true, EmptyState: true, TimestampDisplay: true } },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="forecast-table"]').exists()).toBe(false)
  })
})
