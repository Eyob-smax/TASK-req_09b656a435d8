import { ref, onMounted, onUnmounted } from 'vue'
import { replayQueue } from '@/services/offlineQueue'

export function useOfflineStatus() {
  const isOnline = ref(typeof navigator !== 'undefined' ? navigator.onLine : true)
  const isReconnecting = ref(false)
  const pendingCount = ref(0)
  const conflictMessages = ref<string[]>([])

  function onOnline(): void {
    isOnline.value = true
    isReconnecting.value = true
    replayQueue()
      .then(({ replayed, failed }) => {
        pendingCount.value = failed
        if (failed > 0) {
          conflictMessages.value.push(
            `${failed} pending action(s) could not be replayed and need attention.`,
          )
        }
      })
      .catch(() => {
        conflictMessages.value.push('Failed to replay offline queue.')
      })
      .finally(() => {
        isReconnecting.value = false
      })
  }

  function onOffline(): void {
    isOnline.value = false
  }

  function dismissConflict(index: number): void {
    conflictMessages.value.splice(index, 1)
  }

  onMounted(() => {
    window.addEventListener('online', onOnline)
    window.addEventListener('offline', onOffline)
  })

  onUnmounted(() => {
    window.removeEventListener('online', onOnline)
    window.removeEventListener('offline', onOffline)
  })

  return { isOnline, isReconnecting, pendingCount, conflictMessages, dismissConflict }
}
