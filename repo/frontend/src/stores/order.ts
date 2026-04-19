import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as orderApi from '@/services/orderApi'
import * as paymentApi from '@/services/paymentApi'
import * as refundApi from '@/services/refundApi'
import type { Order, ServiceItem, OrderCreate, PaymentProofSubmit, AfterSalesRequestCreate, RefundCreate, AfterSalesRequest, RefundRecord } from '@/types/order'
import type { Pagination } from '@/types'

export const useOrderStore = defineStore('order', () => {
  const items = ref<ServiceItem[]>([])
  const orders = ref<Order[]>([])
  const currentOrder = ref<Order | null>(null)
  // Service item attached to `currentOrder`. BE `OrderRead` does NOT embed
  // item_name/base_price — views derive those from the catalog entry fetched
  // here via `order.item_id`. Populated by `loadOrder` / `placeOrder`.
  const currentItem = ref<ServiceItem | null>(null)
  const pagination = ref<Pagination | null>(null)
  const loading = ref(false)
  const submitting = ref(false)
  const error = ref<string | null>(null)

  const pendingPaymentOrders = computed(() =>
    orders.value.filter((o) => o.status === 'pending_payment'),
  )

  async function loadServiceItems(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      items.value = await orderApi.listServiceItems()
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function loadOrders(params?: { status?: string; page?: number }): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const result = await orderApi.listOrdersPaginated(params)
      orders.value = result.data
      pagination.value = result.pagination
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function loadOrder(orderId: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const order = await orderApi.getOrder(orderId)
      currentOrder.value = order
      await _hydrateItemFor(order.item_id)
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function placeOrder(data: OrderCreate): Promise<Order | null> {
    submitting.value = true
    error.value = null
    try {
      const order = await orderApi.createOrder(data)
      currentOrder.value = order
      await _hydrateItemFor(order.item_id)
      return order
    } catch (e) {
      error.value = (e as Error).message
      return null
    } finally {
      submitting.value = false
    }
  }

  async function _hydrateItemFor(itemId: string): Promise<void> {
    const cached = items.value.find((i) => i.id === itemId)
    if (cached) {
      currentItem.value = cached
      return
    }
    // BE exposes a single catalog listing endpoint (`GET /services`); the
    // item-name/pricing the view wants lives there, not on OrderRead. We
    // cache into `items` so repeated lookups don't re-fetch.
    try {
      if (items.value.length === 0) {
        items.value = await orderApi.listServiceItems()
      }
      currentItem.value = items.value.find((i) => i.id === itemId) ?? null
    } catch {
      currentItem.value = null
    }
  }

  async function cancelOrder(orderId: string, notes?: string): Promise<boolean> {
    submitting.value = true
    error.value = null
    try {
      currentOrder.value = await orderApi.cancelOrder(orderId, notes)
      return true
    } catch (e) {
      error.value = (e as Error).message
      return false
    } finally {
      submitting.value = false
    }
  }

  async function confirmReceipt(orderId: string): Promise<boolean> {
    submitting.value = true
    error.value = null
    try {
      currentOrder.value = await orderApi.confirmReceipt(orderId)
      return true
    } catch (e) {
      error.value = (e as Error).message
      return false
    } finally {
      submitting.value = false
    }
  }

  async function advanceOrder(orderId: string): Promise<boolean> {
    submitting.value = true
    error.value = null
    try {
      currentOrder.value = await orderApi.advanceOrder(orderId)
      return true
    } catch (e) {
      error.value = (e as Error).message
      return false
    } finally {
      submitting.value = false
    }
  }

  async function submitPaymentProof(
    orderId: string,
    data: PaymentProofSubmit,
  ): Promise<boolean> {
    submitting.value = true
    error.value = null
    try {
      await paymentApi.submitPaymentProof(orderId, data)
      await loadOrder(orderId)
      return true
    } catch (e) {
      error.value = (e as Error).message
      return false
    } finally {
      submitting.value = false
    }
  }

  async function submitAfterSales(
    orderId: string,
    data: AfterSalesRequestCreate,
  ): Promise<AfterSalesRequest | null> {
    submitting.value = true
    error.value = null
    try {
      return await refundApi.submitAfterSales(orderId, data)
    } catch (e) {
      error.value = (e as Error).message
      return null
    } finally {
      submitting.value = false
    }
  }

  async function initiateRefund(
    orderId: string,
    data: RefundCreate,
  ): Promise<RefundRecord | null> {
    submitting.value = true
    error.value = null
    try {
      const record = await refundApi.initiateRefund(orderId, data)
      await loadOrder(orderId)
      return record
    } catch (e) {
      error.value = (e as Error).message
      return null
    } finally {
      submitting.value = false
    }
  }

  function clearError(): void {
    error.value = null
  }

  function reset(): void {
    items.value = []
    orders.value = []
    currentOrder.value = null
    currentItem.value = null
    pagination.value = null
    error.value = null
  }

  return {
    items,
    orders,
    currentOrder,
    currentItem,
    pagination,
    loading,
    submitting,
    error,
    pendingPaymentOrders,
    loadServiceItems,
    loadOrders,
    loadOrder,
    placeOrder,
    cancelOrder,
    confirmReceipt,
    advanceOrder,
    submitPaymentProof,
    submitAfterSales,
    initiateRefund,
    clearError,
    reset,
  }
})
