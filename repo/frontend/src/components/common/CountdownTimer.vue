<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps<{
  expiresAt: string | null | undefined
  label?: string
}>()

const emit = defineEmits<{ (e: 'expired'): void }>()

const remaining = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

function updateRemaining(): void {
  if (!props.expiresAt) { remaining.value = 0; return }
  remaining.value = Math.max(0, new Date(props.expiresAt).getTime() - Date.now())
  if (remaining.value === 0) emit('expired')
}

const formatted = computed<string>(() => {
  if (remaining.value <= 0) return 'Expired'
  const totalSec = Math.floor(remaining.value / 1000)
  const h = Math.floor(totalSec / 3600)
  const m = Math.floor((totalSec % 3600) / 60)
  const s = totalSec % 60
  if (h > 0) return `${h}h ${m.toString().padStart(2, '0')}m`
  if (m > 0) return `${m}m ${s.toString().padStart(2, '0')}s`
  return `${s}s`
})

const isUrgent = computed<boolean>(() => remaining.value > 0 && remaining.value < 5 * 60 * 1000)
const isExpired = computed<boolean>(() => remaining.value === 0)

function startTimer(): void {
  updateRemaining()
  timer = setInterval(updateRemaining, 1000)
}

onMounted(startTimer)
onUnmounted(() => { if (timer) clearInterval(timer) })
watch(() => props.expiresAt, () => { updateRemaining() })
</script>

<template>
  <span
    class="countdown"
    :class="{ 'countdown--urgent': isUrgent, 'countdown--expired': isExpired }"
    :aria-label="label ? `${label}: ${formatted}` : formatted"
    data-testid="countdown-timer"
  >
    <span class="countdown__label" v-if="label">{{ label }}:</span>
    <span class="countdown__value">{{ formatted }}</span>
  </span>
</template>

<style scoped>
.countdown { display: inline-flex; align-items: center; gap: 0.25rem; font-variant-numeric: tabular-nums; }
.countdown__label { font-size: 0.8rem; color: #555; }
.countdown__value { font-weight: 600; }
.countdown--urgent .countdown__value { color: #ef4444; }
.countdown--expired .countdown__value { color: #6b7280; }
</style>
