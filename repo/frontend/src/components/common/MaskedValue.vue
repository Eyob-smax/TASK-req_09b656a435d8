<script setup lang="ts">
import { ref } from 'vue'
import { useMaskedValue, type MaskStrategy } from '@/composables/useMaskedValue'

const props = defineProps<{
  value: string | null | undefined
  strategy?: MaskStrategy
  allowReveal?: boolean
}>()

const { display, canSeeUnmasked } = useMaskedValue()
const revealed = ref(false)

function shown(): string {
  if (revealed.value || canSeeUnmasked.value) return props.value ?? '—'
  return display(props.value, props.strategy ?? 'last4')
}
</script>

<template>
  <span class="masked-value" data-testid="masked-value">
    <span class="masked-value__text">{{ shown() }}</span>
    <button
      v-if="allowReveal && !canSeeUnmasked"
      class="masked-value__toggle"
      type="button"
      :aria-label="revealed ? 'Hide value' : 'Reveal value'"
      @click="revealed = !revealed"
    >
      {{ revealed ? '🙈' : '👁' }}
    </button>
  </span>
</template>

<style scoped>
.masked-value { display: inline-flex; align-items: center; gap: 0.25rem; }
.masked-value__toggle {
  background: none; border: none; cursor: pointer; padding: 0;
  font-size: 0.85rem; line-height: 1;
}
</style>
