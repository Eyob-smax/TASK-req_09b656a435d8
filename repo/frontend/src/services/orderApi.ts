import { request } from './http'
import type { Order, OrderCreate, ServiceItem } from '@/types/order'
import type { ApiListSuccess, Pagination } from '@/types'
import { generateNonce } from './requestSigner'

export function listServiceItems(): Promise<ServiceItem[]> {
  return request<ServiceItem[]>({
    method: 'GET',
    path: '/api/v1/services',
  })
}

export function createOrder(data: OrderCreate): Promise<Order> {
  return request<Order>({
    method: 'POST',
    path: '/api/v1/orders',
    body: data,
    idempotencyKey: generateNonce(),
  })
}

export function listOrders(params?: {
  status?: string
  page?: number
  page_size?: number
}): Promise<{ data: Order[]; pagination: Pagination }> {
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  if (params?.page) qs.set('page', String(params.page))
  if (params?.page_size) qs.set('page_size', String(params.page_size))
  const query = qs.toString() ? `?${qs}` : ''
  return fetch(`/api/v1/orders${query}`, {
    method: 'GET',
    credentials: 'same-origin',
  }).then(async (r) => {
    const body = await r.json()
    if (!r.ok) throw new Error(body?.error?.message ?? `HTTP ${r.status}`)
    return { data: body.data, pagination: body.pagination }
  })
}

export async function listOrdersPaginated(params?: {
  status?: string
  page?: number
  page_size?: number
}): Promise<{ data: Order[]; pagination: Pagination }> {
  const { useAuthStore } = await import('@/stores/auth')
  const auth = useAuthStore()
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  if (params?.page) qs.set('page', String(params.page))
  if (params?.page_size) qs.set('page_size', String(params.page_size))
  const query = qs.toString() ? `?${qs}` : ''
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (auth.tokens?.access_token) headers['Authorization'] = `Bearer ${auth.tokens.access_token}`
  const r = await fetch(`/api/v1/orders${query}`, {
    method: 'GET',
    credentials: 'same-origin',
    headers,
  })
  const body = await r.json()
  if (!r.ok) throw new Error(body?.error?.message ?? `HTTP ${r.status}`)
  return { data: body.data, pagination: body.pagination }
}

export function getOrder(orderId: string): Promise<Order> {
  return request<Order>({
    method: 'GET',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}`,
  })
}

export function cancelOrder(orderId: string, notes?: string): Promise<Order> {
  return request<Order>({
    method: 'POST',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/cancel`,
    body: notes ? { notes } : {},
  })
}

export function confirmReceipt(orderId: string): Promise<Order> {
  return request<Order>({
    method: 'POST',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/confirm-receipt`,
    body: {},
  })
}

export function advanceOrder(orderId: string, notes?: string): Promise<Order> {
  return request<Order>({
    method: 'POST',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/advance`,
    body: notes ? { notes } : {},
  })
}
