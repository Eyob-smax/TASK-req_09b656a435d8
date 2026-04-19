<script setup lang="ts">
const props = defineProps<{
  status: string
  size?: 'sm' | 'md'
}>()

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending_payment:       { label: 'Pending Payment',        color: '#f59e0b' },
  pending_fulfillment:   { label: 'Pending Fulfillment',    color: '#3b82f6' },
  pending_receipt:       { label: 'Pending Receipt',        color: '#8b5cf6' },
  completed:             { label: 'Completed',              color: '#10b981' },
  canceled:              { label: 'Canceled',               color: '#6b7280' },
  refund_in_progress:    { label: 'Refund In Progress',     color: '#f97316' },
  refunded:              { label: 'Refunded',               color: '#14b8a6' },
  pending_review:        { label: 'Pending Review',         color: '#f59e0b' },
  approved:              { label: 'Approved',               color: '#10b981' },
  rejected:              { label: 'Rejected',               color: '#ef4444' },
  needs_resubmission:    { label: 'Needs Resubmission',     color: '#f97316' },
  pending_proof:         { label: 'Pending Proof',          color: '#f59e0b' },
  pending_initial_review:{ label: 'Initial Review',         color: '#3b82f6' },
  pending_final_review:  { label: 'Final Review',           color: '#8b5cf6' },
  open:                  { label: 'Open',                   color: '#3b82f6' },
  resolved:              { label: 'Resolved',               color: '#10b981' },
  pending:               { label: 'Pending',                color: '#f59e0b' },
  accepted:              { label: 'Accepted',               color: '#10b981' },
  countered:             { label: 'Countered',              color: '#f97316' },
  counter_accepted:      { label: 'Counter Accepted',       color: '#14b8a6' },
  expired:               { label: 'Expired',                color: '#6b7280' },
}

function info(): { label: string; color: string } {
  return STATUS_MAP[props.status] ?? { label: props.status, color: '#6b7280' }
}
</script>

<template>
  <span
    class="status-chip"
    :class="[`status-chip--${size ?? 'md'}`]"
    :style="{ '--chip-color': info().color }"
    :data-testid="`status-chip-${status}`"
  >
    {{ info().label }}
  </span>
</template>

<style scoped>
.status-chip {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: 999px;
  font-weight: 600;
  background: color-mix(in srgb, var(--chip-color) 15%, white);
  color: var(--chip-color);
  border: 1px solid color-mix(in srgb, var(--chip-color) 40%, white);
  white-space: nowrap;
}
.status-chip--sm { font-size: 0.7rem; padding: 0.0625rem 0.375rem; }
.status-chip--md { font-size: 0.8rem; }
</style>
