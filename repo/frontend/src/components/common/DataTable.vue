<script setup lang="ts" generic="T extends Record<string, unknown>">
import EmptyState from './EmptyState.vue'

export interface Column<R> {
  key: string
  label: string
  align?: 'left' | 'center' | 'right'
  render?: (row: R) => string
}

const props = defineProps<{
  columns: Column<T>[]
  rows: T[]
  emptyMessage?: string
  loading?: boolean
}>()
</script>

<template>
  <div class="data-table-wrap" data-testid="data-table">
    <table v-if="!loading && rows.length > 0" class="data-table">
      <thead>
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            class="data-table__th"
            :style="{ textAlign: col.align ?? 'left' }"
          >
            {{ col.label }}
          </th>
          <th v-if="$slots.actions" class="data-table__th">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, i) in rows" :key="i" class="data-table__row">
          <td
            v-for="col in columns"
            :key="col.key"
            class="data-table__td"
            :style="{ textAlign: col.align ?? 'left' }"
          >
            <slot :name="col.key" :row="row">
              {{ col.render ? col.render(row) : row[col.key] }}
            </slot>
          </td>
          <td v-if="$slots.actions" class="data-table__td">
            <slot name="actions" :row="row" />
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else-if="loading" class="data-table__loading">Loading…</div>
    <EmptyState v-else :message="emptyMessage" />
  </div>
</template>

<style scoped>
.data-table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.data-table__th {
  padding: 0.5rem 0.75rem; background: #f5f5f5;
  border-bottom: 2px solid #e0e0e0; font-weight: 600; white-space: nowrap;
}
.data-table__row:hover { background: #fafafa; }
.data-table__td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #e0e0e0; vertical-align: top; }
.data-table__loading { padding: 2rem; text-align: center; color: #888; }
</style>
