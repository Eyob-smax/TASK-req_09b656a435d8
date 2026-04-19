// All mutation helpers here post to `/api/v1/orders/*` and are therefore signed
// automatically via the `shouldSign(path)` prefix match in http.ts (see
// SIGNED_PATHS). Backend enforcement lives in `src/api/routes/refunds.py` via
// Depends(require_signed_request) on refund, refund/process, after-sales,
// and after-sales/{request_id}/resolve.
import { request } from './http'
import type { RefundRecord, AfterSalesRequest, AfterSalesRequestCreate, RefundCreate } from '@/types/order'

export function initiateRefund(orderId: string, data: RefundCreate): Promise<RefundRecord> {
  return request<RefundRecord>({
    method: 'POST',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/refund`,
    body: data,
  })
}

export function processRefund(orderId: string): Promise<RefundRecord> {
  return request<RefundRecord>({
    method: 'POST',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/refund/process`,
    body: {},
  })
}

export function getRefund(orderId: string): Promise<RefundRecord | null> {
  return request<RefundRecord | null>({
    method: 'GET',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/refund`,
  })
}

export function submitAfterSales(
  orderId: string,
  data: AfterSalesRequestCreate,
): Promise<AfterSalesRequest> {
  return request<AfterSalesRequest>({
    method: 'POST',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/after-sales`,
    body: data,
  })
}

export function listAfterSales(orderId: string): Promise<AfterSalesRequest[]> {
  return request<AfterSalesRequest[]>({
    method: 'GET',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/after-sales`,
  })
}

export function resolveAfterSales(
  orderId: string,
  requestId: string,
  resolutionNotes: string,
): Promise<AfterSalesRequest> {
  return request<AfterSalesRequest>({
    method: 'POST',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/after-sales/${encodeURIComponent(requestId)}/resolve`,
    body: { resolution_notes: resolutionNotes },
  })
}
