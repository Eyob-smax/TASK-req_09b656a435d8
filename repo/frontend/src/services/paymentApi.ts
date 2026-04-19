// All mutation helpers here post to `/api/v1/orders/*` and are therefore signed
// automatically via the `shouldSign(path)` prefix match in http.ts (see
// SIGNED_PATHS). Backend enforcement lives in `src/api/routes/payment.py` via
// Depends(require_signed_request) on payment/proof, payment/confirm, voucher,
// and milestones.
import { request } from './http'
import type {
  PaymentRecord,
  Voucher,
  FulfillmentMilestone,
  PaymentProofSubmit,
  PaymentConfirmPayload,
  VoucherCreate,
  MilestoneCreate,
} from '@/types/order'

export function submitPaymentProof(
  orderId: string,
  data: PaymentProofSubmit,
): Promise<PaymentRecord> {
  return request<PaymentRecord>({
    method: 'POST',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/payment/proof`,
    body: data,
  })
}

export function confirmPayment(
  orderId: string,
  data: PaymentConfirmPayload,
): Promise<{ id: string; status: string }> {
  return request({
    method: 'POST',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/payment/confirm`,
    body: data,
  })
}

export function issueVoucher(orderId: string, data: VoucherCreate): Promise<Voucher> {
  return request<Voucher>({
    method: 'POST',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/voucher`,
    body: data,
  })
}

export function getVoucher(orderId: string): Promise<Voucher | null> {
  return request<Voucher | null>({
    method: 'GET',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/voucher`,
  })
}

export function addMilestone(
  orderId: string,
  data: MilestoneCreate,
): Promise<FulfillmentMilestone> {
  return request<FulfillmentMilestone>({
    method: 'POST',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/milestones`,
    body: data,
  })
}

export function listMilestones(orderId: string): Promise<FulfillmentMilestone[]> {
  return request<FulfillmentMilestone[]>({
    method: 'GET',
    path: `/api/v1/orders/${encodeURIComponent(orderId)}/milestones`,
  })
}
