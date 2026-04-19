<script setup lang="ts">
import type { Pagination } from '@/types'

defineProps<{ pagination: Pagination | null }>()
const emit = defineEmits<{ (e: 'page', p: number): void }>()
</script>

<template>
  <div v-if="pagination && pagination.total_pages > 1" class="pagination" data-testid="pagination">
    <button
      type="button"
      class="pagination__btn"
      :disabled="pagination.page <= 1"
      @click="emit('page', pagination.page - 1)"
    >
      ‹ Prev
    </button>
    <span class="pagination__info">
      Page {{ pagination.page }} of {{ pagination.total_pages }}
      ({{ pagination.total }} total)
    </span>
    <button
      type="button"
      class="pagination__btn"
      :disabled="pagination.page >= pagination.total_pages"
      @click="emit('page', pagination.page + 1)"
    >
      Next ›
    </button>
  </div>
</template>

<style scoped>
.pagination { display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 0; }
.pagination__btn {
  padding: 0.25rem 0.75rem; border: 1px solid #bdbdbd; border-radius: 4px;
  background: white; cursor: pointer;
}
.pagination__btn:disabled { opacity: 0.4; cursor: default; }
.pagination__info { font-size: 0.85rem; color: #555; }
</style>
