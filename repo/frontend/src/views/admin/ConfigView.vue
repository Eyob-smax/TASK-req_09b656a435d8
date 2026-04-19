<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAdminStore } from '@/stores/admin'
import { useSessionStore } from '@/stores/session'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import BannerAlert from '@/components/common/BannerAlert.vue'

const admin = useAdminStore()
const session = useSessionStore()

const editingKey = ref<string | null>(null)
const editValue = ref('')
const editReason = ref('')
const saveSuccess = ref<string | null>(null)

onMounted(async () => {
  await admin.loadFlags()
  await admin.loadCohorts()
})

function startEdit(key: string, currentValue: string) {
  editingKey.value = key
  editValue.value = currentValue
  editReason.value = ''
  saveSuccess.value = null
}

function cancelEdit() {
  editingKey.value = null
  editValue.value = ''
  editReason.value = ''
}

async function saveFlag() {
  if (!editingKey.value) return
  try {
    await admin.updateFlag(editingKey.value, editValue.value, editReason.value || undefined)
    saveSuccess.value = `Flag '${editingKey.value}' updated.`
    editingKey.value = null
  } catch {
    // error shown via admin.error
  }
}
</script>

<template>
  <div class="config-view" data-testid="config-view">
    <h2>System Configuration</h2>

    <BannerAlert v-if="saveSuccess" type="success" :message="saveSuccess" @dismiss="saveSuccess = null" />
    <BannerAlert v-if="admin.error" type="error" :message="admin.error" @dismiss="admin.clearError()" />

    <section class="config-section">
      <h3>Feature Flags</h3>
      <LoadingSpinner v-if="admin.loading && admin.flags.length === 0" label="Loading flags…" />
      <table v-else class="config-table" data-testid="flag-table">
        <thead>
          <tr><th>Flag</th><th>Value</th><th>Type</th><th>Action</th></tr>
        </thead>
        <tbody>
          <tr v-for="flag in admin.flags" :key="flag.key" :data-testid="`flag-row-${flag.key}`">
            <td><code>{{ flag.key }}</code></td>
            <td>
              <span v-if="editingKey !== flag.key">{{ flag.value }}</span>
              <input
                v-else
                v-model="editValue"
                class="config-input"
                data-testid="flag-edit-input"
              />
            </td>
            <td>{{ flag.value_type }}</td>
            <td>
              <template v-if="editingKey !== flag.key">
                <button
                  class="btn-sm"
                  :data-testid="`flag-edit-btn-${flag.key}`"
                  @click="startEdit(flag.key, flag.value)"
                >Edit</button>
              </template>
              <template v-else>
                <input
                  v-model="editReason"
                  placeholder="Reason (optional)"
                  class="config-input reason-input"
                  data-testid="flag-edit-reason"
                />
                <button class="btn-sm btn-primary" data-testid="flag-save-btn" @click="saveFlag">Save</button>
                <button class="btn-sm" data-testid="flag-cancel-btn" @click="cancelEdit">Cancel</button>
              </template>
            </td>
          </tr>
          <tr v-if="admin.flags.length === 0 && !admin.loading">
            <td colspan="4">No feature flags configured.</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="config-section">
      <h3>Cohort Definitions</h3>
      <table v-if="admin.cohorts.length > 0" class="config-table" data-testid="cohort-table">
        <thead>
          <tr><th>Key</th><th>Name</th><th>Active</th><th>Flag Overrides</th></tr>
        </thead>
        <tbody>
          <tr v-for="cohort in admin.cohorts" :key="cohort.id">
            <td><code>{{ cohort.cohort_key }}</code></td>
            <td>{{ cohort.name }}</td>
            <td>{{ cohort.is_active ? 'Yes' : 'No' }}</td>
            <td>
              <code v-if="cohort.flag_overrides">{{ JSON.stringify(cohort.flag_overrides) }}</code>
              <span v-else>—</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="config-section__note">No cohorts defined.</p>
    </section>

    <section class="config-section">
      <h3>Cohort Config (Session Snapshot)</h3>
      <pre class="config-pre">{{ JSON.stringify(session.cohort, null, 2) }}</pre>
    </section>
  </div>
</template>

<style scoped>
.config-view { display: flex; flex-direction: column; gap: 1.5rem; }
.config-view h2 { margin: 0; }
.config-section h3 { margin: 0 0 0.5rem; font-size: 1rem; }
.config-section__note { font-size: 0.8rem; color: #777; margin: 0; }
.config-table { border-collapse: collapse; font-size: 0.875rem; width: 100%; }
.config-table th, .config-table td { padding: 0.4rem 0.6rem; border: 1px solid #e0e0e0; text-align: left; }
.config-table th { background: #f5f5f5; }
.config-pre { background: #f5f5f5; padding: 0.75rem; border-radius: 6px; font-size: 0.8rem; overflow-x: auto; }
.config-input { border: 1px solid #aaa; border-radius: 4px; padding: 0.2rem 0.4rem; font-size: 0.85rem; }
.reason-input { margin-right: 0.5rem; }
.btn-sm { padding: 0.2rem 0.6rem; font-size: 0.8rem; cursor: pointer; border: 1px solid #aaa; border-radius: 4px; background: #fff; margin-right: 0.25rem; }
.btn-primary { background: #1565c0; color: #fff; border-color: #1565c0; }
</style>
