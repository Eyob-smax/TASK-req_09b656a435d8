export interface DocumentQueueItem {
  document_id: string
  candidate_id: string
  document_type: string
  current_status: string
  submitted_at: string
  requirement_code: string | null
}

export interface PaymentQueueItem {
  order_id: string
  candidate_id: string
  item_name: string
  amount: string
  payment_method: string
  reference_number: string | null
  submitted_at: string
}

export interface OrderQueueItem {
  order_id: string
  candidate_id: string
  item_name: string
  status: string
  agreed_price: string | null
  updated_at: string
}

export interface ExceptionQueueItem {
  exception_id: string
  candidate_id: string
  anomaly_type: string | null
  status: string
  current_stage: string
  submitted_at: string
}

export interface AfterSalesQueueItem {
  request_id: string
  order_id: string
  candidate_id: string
  request_type: string
  status: string
  window_expires_at: string
  created_at: string
}
