import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as queueApi from '@/services/queueApi'
import type {
  DocumentQueueItem,
  PaymentQueueItem,
  OrderQueueItem,
  ExceptionQueueItem,
  AfterSalesQueueItem,
} from '@/types/queue'
import type { Pagination } from '@/types'

export const useQueueStore = defineStore('queue', () => {
  const documents = ref<DocumentQueueItem[]>([])
  const payments = ref<PaymentQueueItem[]>([])
  const orders = ref<OrderQueueItem[]>([])
  const exceptions = ref<ExceptionQueueItem[]>([])
  const afterSales = ref<AfterSalesQueueItem[]>([])
  const pagination = ref<Pagination | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadDocuments(params?: { page?: number }): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const result = await queueApi.getPendingDocuments(params)
      documents.value = result.data
      pagination.value = result.pagination
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function loadPayments(params?: { page?: number }): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const result = await queueApi.getPendingPayments(params)
      payments.value = result.data
      pagination.value = result.pagination
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function loadOrders(params?: { page?: number }): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const result = await queueApi.getPendingOrders(params)
      orders.value = result.data
      pagination.value = result.pagination
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function loadExceptions(params?: { status?: string; page?: number }): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const result = await queueApi.getPendingExceptions(params)
      exceptions.value = result.data
      pagination.value = result.pagination
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function loadAfterSales(params?: { page?: number }): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const result = await queueApi.getPendingAfterSales(params)
      afterSales.value = result.data
      pagination.value = result.pagination
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  function clearError(): void {
    error.value = null
  }

  return {
    documents,
    payments,
    orders,
    exceptions,
    afterSales,
    pagination,
    loading,
    error,
    loadDocuments,
    loadPayments,
    loadOrders,
    loadExceptions,
    loadAfterSales,
    clearError,
  }
})
