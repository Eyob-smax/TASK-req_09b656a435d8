// Sensitive-field masking helpers aligned to backend policy.
// Candidates see masked values by default; privileged roles (reviewer, admin)
// see plaintext. Views import this composable rather than hardcoding mask logic.

import { computed } from 'vue'
import { usePermissions } from './usePermissions'

export type MaskStrategy = 'last4' | 'full' | 'phone' | 'name'

export function maskValue(value: string | null | undefined, strategy: MaskStrategy): string {
  if (!value) return '—'
  switch (strategy) {
    case 'last4':
      return value.length > 4 ? `${'*'.repeat(value.length - 4)}${value.slice(-4)}` : '****'
    case 'full':
      return '*'.repeat(Math.min(value.length, 12))
    case 'phone':
      return value.length > 4 ? `***-***-${value.slice(-4)}` : '****'
    case 'name': {
      const parts = value.trim().split(/\s+/)
      if (parts.length === 1) return `${parts[0][0] ?? '*'}***`
      return `${parts[0]} ${'*'.repeat(parts[parts.length - 1].length)}`
    }
    default:
      return '****'
  }
}

export function useMaskedValue() {
  const { isStaff } = usePermissions()

  function display(
    value: string | null | undefined,
    strategy: MaskStrategy = 'last4',
  ): string {
    if (isStaff.value) return value ?? '—'
    return maskValue(value, strategy)
  }

  const canSeeUnmasked = computed(() => isStaff.value)

  return { display, maskValue, canSeeUnmasked }
}
