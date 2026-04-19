<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  open: boolean
  title?: string
}>()

const emit = defineEmits<{ (e: 'close'): void }>()

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && props.open) emit('close')
}

onMounted(() => document.addEventListener('keydown', handleKeydown))
onUnmounted(() => document.removeEventListener('keydown', handleKeydown))
watch(() => props.open, (v) => {
  document.body.style.overflow = v ? 'hidden' : ''
})
</script>

<template>
  <teleport to="body">
    <transition name="modal">
      <div v-if="open" class="modal-overlay" role="dialog" :aria-modal="true" :aria-label="title" @click.self="emit('close')">
        <div class="modal-panel" data-testid="modal-panel">
          <header v-if="title" class="modal-panel__header">
            <h2 class="modal-panel__title">{{ title }}</h2>
            <button type="button" class="modal-panel__close" aria-label="Close" @click="emit('close')">&times;</button>
          </header>
          <div class="modal-panel__body">
            <slot />
          </div>
          <footer v-if="$slots.footer" class="modal-panel__footer">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-panel {
  background: white; border-radius: 8px; box-shadow: 0 8px 32px rgba(0,0,0,0.18);
  max-width: 520px; width: 92%; max-height: 90vh; overflow-y: auto;
  display: flex; flex-direction: column;
}
.modal-panel__header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1rem 1.25rem; border-bottom: 1px solid #e0e0e0;
}
.modal-panel__title { margin: 0; font-size: 1.1rem; }
.modal-panel__close {
  background: none; border: none; font-size: 1.4rem; cursor: pointer;
  line-height: 1; color: #555;
}
.modal-panel__body { padding: 1.25rem; flex: 1; }
.modal-panel__footer { padding: 0.75rem 1.25rem; border-top: 1px solid #e0e0e0; }
.modal-enter-active, .modal-leave-active { transition: opacity 0.15s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
