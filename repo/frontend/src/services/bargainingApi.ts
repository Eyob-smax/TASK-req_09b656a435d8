import { request } from './http'
import type { BargainingThread } from '@/types/order'

export function submitOffer(
  orderId: string,
  amount: string,
): Promise<{ id: string; offer_number: number; amount: string }> {
  return request({
    method: 'POST',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/bargaining/offer`,
    body: { amount },
  })
}

export function getBargainingThread(orderId: string): Promise<BargainingThread> {
  return request<BargainingThread>({
    method: 'GET',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/bargaining`,
  })
}

export function acceptOffer(
  orderId: string,
  offerId: string,
): Promise<BargainingThread> {
  return request<BargainingThread>({
    method: 'POST',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/bargaining/accept`,
    body: { offer_id: offerId },
  })
}

export function counterOffer(
  orderId: string,
  counterAmount: string,
): Promise<BargainingThread> {
  return request<BargainingThread>({
    method: 'POST',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/bargaining/counter`,
    body: { counter_amount: counterAmount },
  })
}

export function acceptCounter(orderId: string): Promise<BargainingThread> {
  return request<BargainingThread>({
    method: 'POST',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/bargaining/accept-counter`,
    body: {},
  })
}
