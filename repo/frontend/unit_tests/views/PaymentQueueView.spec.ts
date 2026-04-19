// FE-UNIT: PaymentQueueView — staff confirms pending payments; the confirm call
// must forward `amount` + `payment_method` (H5 — BE `PaymentConfirmRequest`
// requires these fields with `amount > 0`).

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'
import PaymentQueueView from '@/views/staff/orders/PaymentQueueView.vue'
import { useQueueStore } from '@/stores/queue'

const { MOCK_PAYMENT, confirmPaymentMock } = vi.hoisted(() => ({
  MOCK_PAYMENT: {
    order_id: 'order-1',
    item_name: 'NMAT Review',
    amount: '1200.00',
    payment_method: 'bank_transfer',
    reference_number: 'REF-001',
    submitted_at: '2024-01-01T00:00:00Z',
  },
  confirmPaymentMock: vi.fn().mockResolvedValue({ id: 'order-1', status: 'pending_fulfillment' }),
}))

vi.mock('@/services/paymentApi', () => ({
  confirmPayment: (...args: unknown[]) => confirmPaymentMock(...args),
  submitPaymentProof: vi.fn(),
  issueVoucher: vi.fn(),
  getVoucher: vi.fn(),
  addMilestone: vi.fn(),
  listMilestones: vi.fn(),
}))

vi.mock('@/services/queueApi', () => ({
  getPendingPayments: vi.fn().mockResolvedValue({
    data: [MOCK_PAYMENT],
    pagination: { page: 1, page_size: 20, total: 1, total_pages: 1 },
  }),
  getPendingDocuments: vi.fn().mockResolvedValue({ data: [], pagination: { page: 1, page_size: 20, total: 0, total_pages: 0 } }),
  getPendingOrders: vi.fn().mockResolvedValue({ data: [], pagination: { page: 1, page_size: 20, total: 0, total_pages: 0 } }),
  getPendingExceptions: vi.fn().mockResolvedValue({ data: [], pagination: { page: 1, page_size: 20, total: 0, total_pages: 0 } }),
  getPendingAfterSales: vi.fn().mockResolvedValue({ data: [], pagination: { page: 1, page_size: 20, total: 0, total_pages: 0 } }),
}))

describe('PaymentQueueView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    confirmPaymentMock.mockClear()
  })

  it('renders pending payment rows from the queue store', async () => {
    const wrapper = mount(PaymentQueueView)
    await flushPromises()
    const store = useQueueStore()
    store.payments = [MOCK_PAYMENT]
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('NMAT Review')
    expect(wrapper.text()).toContain('bank_transfer')
  })

  it('forwards amount + payment_method when confirm is clicked (H5 contract)', async () => {
    const wrapper = mount(PaymentQueueView)
    await flushPromises()
    const store = useQueueStore()
    store.payments = [MOCK_PAYMENT]
    await wrapper.vm.$nextTick()

    await wrapper.find('.btn-confirm').trigger('click')
    await flushPromises()

    expect(confirmPaymentMock).toHaveBeenCalledTimes(1)
    const [orderIdArg, payloadArg] = confirmPaymentMock.mock.calls[0]
    expect(orderIdArg).toBe('order-1')
    expect(payloadArg.amount).toBe('1200.00')
    expect(payloadArg.payment_method).toBe('bank_transfer')
    expect(payloadArg.reference_number).toBe('REF-001')
  })
})
