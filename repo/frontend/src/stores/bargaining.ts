import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as bargainingApi from '@/services/bargainingApi'
import type { BargainingThread } from '@/types/order'

export const useBargainingStore = defineStore('bargaining', () => {
  const thread = ref<BargainingThread | null>(null)
  const loading = ref(false)
  const submitting = ref(false)
  const error = ref<string | null>(null)

  const offersRemaining = computed(() => {
    if (!thread.value) return 3
    return Math.max(0, 3 - thread.value.offers.length)
  })

  const windowExpiresAt = computed<Date | null>(() => {
    if (!thread.value) return null
    return new Date(thread.value.window_expires_at)
  })

  const isExpired = computed<boolean>(() => {
    if (!windowExpiresAt.value) return false
    return windowExpiresAt.value < new Date()
  })

  const canSubmitOffer = computed<boolean>(() => {
    if (!thread.value) return false
    return (
      !isExpired.value &&
      offersRemaining.value > 0 &&
      thread.value.status === 'open'
    )
  })

  const canAcceptCounter = computed<boolean>(() => {
    if (!thread.value) return false
    return thread.value.status === 'countered' && !isExpired.value
  })

  async function loadThread(orderId: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      thread.value = await bargainingApi.getBargainingThread(orderId)
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function submitOffer(orderId: string, amount: string): Promise<boolean> {
    submitting.value = true
    error.value = null
    try {
      await bargainingApi.submitOffer(orderId, amount)
      await loadThread(orderId)
      return true
    } catch (e) {
      error.value = (e as Error).message
      return false
    } finally {
      submitting.value = false
    }
  }

  async function acceptOffer(orderId: string, offerId: string): Promise<boolean> {
    submitting.value = true
    error.value = null
    try {
      thread.value = await bargainingApi.acceptOffer(orderId, offerId)
      return true
    } catch (e) {
      error.value = (e as Error).message
      return false
    } finally {
      submitting.value = false
    }
  }

  async function counterOffer(orderId: string, amount: string): Promise<boolean> {
    submitting.value = true
    error.value = null
    try {
      thread.value = await bargainingApi.counterOffer(orderId, amount)
      return true
    } catch (e) {
      error.value = (e as Error).message
      return false
    } finally {
      submitting.value = false
    }
  }

  async function acceptCounter(orderId: string): Promise<boolean> {
    submitting.value = true
    error.value = null
    try {
      thread.value = await bargainingApi.acceptCounter(orderId)
      return true
    } catch (e) {
      error.value = (e as Error).message
      return false
    } finally {
      submitting.value = false
    }
  }

  function clearError(): void {
    error.value = null
  }

  function reset(): void {
    thread.value = null
    error.value = null
  }

  return {
    thread,
    loading,
    submitting,
    error,
    offersRemaining,
    windowExpiresAt,
    isExpired,
    canSubmitOffer,
    canAcceptCounter,
    loadThread,
    submitOffer,
    acceptOffer,
    counterOffer,
    acceptCounter,
    clearError,
    reset,
  }
})
