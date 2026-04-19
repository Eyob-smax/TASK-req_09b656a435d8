import { ref, computed } from 'vue'
import type { Pagination } from '@/types'

export function usePagination(defaultPageSize = 20) {
  const page = ref(1)
  const pageSize = ref(defaultPageSize)
  const pagination = ref<Pagination | null>(null)

  const totalPages = computed(() => pagination.value?.total_pages ?? 1)
  const hasNext = computed(() => page.value < totalPages.value)
  const hasPrev = computed(() => page.value > 1)

  function next(): void {
    if (hasNext.value) page.value++
  }

  function prev(): void {
    if (hasPrev.value) page.value--
  }

  function goTo(p: number): void {
    page.value = Math.max(1, Math.min(p, totalPages.value))
  }

  function applyPagination(p: Pagination): void {
    pagination.value = p
  }

  function reset(): void {
    page.value = 1
    pagination.value = null
  }

  return { page, pageSize, pagination, totalPages, hasNext, hasPrev, next, prev, goTo, applyPagination, reset }
}
