import type {
  DocumentQueueItem,
  PaymentQueueItem,
  OrderQueueItem,
  ExceptionQueueItem,
  AfterSalesQueueItem,
} from '@/types/queue'
import type { Pagination } from '@/types'

interface QueueResponse<T> {
  data: T[]
  pagination: Pagination
}

async function fetchQueue<T>(
  path: string,
  params?: { status?: string; page?: number; page_size?: number },
): Promise<QueueResponse<T>> {
  const { useAuthStore } = await import('@/stores/auth')
  const auth = useAuthStore()
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  if (params?.page) qs.set('page', String(params.page))
  if (params?.page_size) qs.set('page_size', String(params.page_size))
  const query = qs.toString() ? `?${qs}` : ''
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (auth.tokens?.access_token) headers['Authorization'] = `Bearer ${auth.tokens.access_token}`
  const r = await fetch(`${path}${query}`, { method: 'GET', credentials: 'same-origin', headers })
  const body = await r.json()
  if (!r.ok) throw new Error(body?.error?.message ?? `HTTP ${r.status}`)
  return { data: body.data, pagination: body.pagination }
}

export function getPendingDocuments(
  params?: { page?: number; page_size?: number },
): Promise<QueueResponse<DocumentQueueItem>> {
  return fetchQueue<DocumentQueueItem>('/api/v1/queue/documents', params)
}

export function getPendingPayments(
  params?: { page?: number; page_size?: number },
): Promise<QueueResponse<PaymentQueueItem>> {
  return fetchQueue<PaymentQueueItem>('/api/v1/queue/payments', params)
}

export function getPendingOrders(
  params?: { page?: number; page_size?: number },
): Promise<QueueResponse<OrderQueueItem>> {
  return fetchQueue<OrderQueueItem>('/api/v1/queue/orders', params)
}

export function getPendingExceptions(
  params?: { status?: string; page?: number; page_size?: number },
): Promise<QueueResponse<ExceptionQueueItem>> {
  return fetchQueue<ExceptionQueueItem>('/api/v1/queue/exceptions', params)
}

export function getPendingAfterSales(
  params?: { page?: number; page_size?: number },
): Promise<QueueResponse<AfterSalesQueueItem>> {
  return fetchQueue<AfterSalesQueueItem>('/api/v1/queue/after-sales', params)
}
