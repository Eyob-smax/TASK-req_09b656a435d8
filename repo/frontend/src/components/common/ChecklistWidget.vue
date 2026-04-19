<script setup lang="ts">
import StatusChip from './StatusChip.vue'
import type { ChecklistItemRead } from '@/types/document'

defineProps<{ items: ChecklistItemRead[] }>()
</script>

<template>
  <table class="checklist" data-testid="checklist-widget">
    <thead>
      <tr>
        <th class="checklist__th">Requirement</th>
        <th class="checklist__th">Mandatory</th>
        <th class="checklist__th">Status</th>
        <th class="checklist__th">Version</th>
      </tr>
    </thead>
    <tbody>
      <tr v-if="items.length === 0">
        <td colspan="4" class="checklist__empty">No requirements defined.</td>
      </tr>
      <tr v-for="item in items" :key="item.requirement_id" class="checklist__row">
        <td class="checklist__label">
          <strong>{{ item.display_name }}</strong>
          <p class="checklist__desc">{{ item.requirement_code }}</p>
        </td>
        <td class="checklist__center">{{ item.is_mandatory ? 'Yes' : 'No' }}</td>
        <td>
          <StatusChip v-if="item.status" :status="item.status" size="sm" />
          <span v-else class="checklist__missing">Not submitted</span>
        </td>
        <td class="checklist__center">{{ item.version_number ?? '—' }}</td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
.checklist { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.checklist__th {
  text-align: left; padding: 0.5rem; background: #f5f5f5;
  border-bottom: 2px solid #e0e0e0; font-weight: 600;
}
.checklist__row td { padding: 0.5rem; border-bottom: 1px solid #e0e0e0; vertical-align: top; }
.checklist__label { min-width: 140px; }
.checklist__desc { font-size: 0.75rem; color: #777; margin: 0.125rem 0 0; }
.checklist__center { text-align: center; }
.checklist__empty { text-align: center; color: #888; padding: 1.5rem; }
.checklist__missing { font-size: 0.75rem; color: #aaa; font-style: italic; }
</style>
