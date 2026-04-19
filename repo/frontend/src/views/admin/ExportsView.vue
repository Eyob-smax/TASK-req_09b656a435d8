<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAdminStore } from '@/stores/admin'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import TimestampDisplay from '@/components/common/TimestampDisplay.vue'

const admin = useAdminStore()

const selectedType = ref('audit_csv')
const creating = ref(false)
const createError = ref<string | null>(null)
const createSuccess = ref<string | null>(null)

const EXPORT_TYPES = [
  { value: 'audit_csv', label: 'Audit Log (CSV)' },
  { value: 'forecast_csv', label: 'Forecast Snapshots (CSV)' },
]

onMounted(async () => {
  await admin.loadExports()
})

async function createExport() {
  creating.value = true
  createError.value = null
  createSuccess.value = null
  try {
    const job = await admin.createExport(selectedType.value)
    createSuccess.value = `Export '${job.id}' created with status: ${job.status}`
  } catch (e) {
    createError.value = (e as Error).message
  } finally {
    creating.value = false
  }
}

function downloadUrl(id: string): string {
  return `/api/v1/admin/exports/${id}/download`
}
</script>

<template>
  <div class="exports-view" data-testid="exports-view">
    <h2>Exports &amp; Reports</h2>

    <section class="exports-section">
      <h3>Create Export</h3>
      <form class="create-form" data-testid="export-create-form" @submit.prevent="createExport">
        <select v-model="selectedType" class="export-select" data-testid="export-type-select">
          <option v-for="t in EXPORT_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
        <button type="submit" :disabled="creating" class="btn-create" data-testid="export-create-btn">
          {{ creating ? 'Creating…' : 'Create Export' }}
        </button>
      </form>
      <p v-if="createSuccess" class="msg-success" data-testid="export-success">{{ createSuccess }}</p>
      <p v-if="createError" class="msg-error">{{ createError }}</p>
      <p class="exports-note">
        Exports are watermarked with your username and timestamp. SHA-256 is stored for integrity verification.
      </p>
    </section>

    <section class="exports-section">
      <h3>Export History</h3>
      <LoadingSpinner v-if="admin.loading && admin.exportJobs.length === 0" label="Loading exports…" />
      <EmptyState v-else-if="admin.exportJobs.length === 0" message="No export jobs yet." />
      <table v-else class="exports-table" data-testid="export-list-table">
        <thead>
          <tr>
            <th>ID</th><th>Type</th><th>Status</th>
            <th>Watermarked</th><th>SHA-256</th><th>Created</th><th>Download</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="job in admin.exportJobs" :key="job.id" data-testid="export-row">
            <td><code>{{ job.id.slice(0, 8) }}</code></td>
            <td>{{ job.export_type }}</td>
            <td>{{ job.status }}</td>
            <td>{{ job.watermark_applied ? 'Yes' : 'No' }}</td>
            <td>
              <code v-if="job.sha256_hash">{{ job.sha256_hash.slice(0, 12) }}…</code>
              <span v-else>—</span>
            </td>
            <td><TimestampDisplay :value="job.created_at" /></td>
            <td>
              <a
                v-if="job.status === 'completed'"
                :href="downloadUrl(job.id)"
                class="download-link"
                data-testid="export-download-link"
              >Download</a>
              <span v-else>—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<style scoped>
.exports-view { display: flex; flex-direction: column; gap: 1.5rem; }
.exports-view h2 { margin: 0; }
.exports-section h3 { margin: 0 0 0.75rem; font-size: 1rem; }
.create-form { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
.export-select { border: 1px solid #ccc; border-radius: 4px; padding: 0.3rem 0.5rem; font-size: 0.875rem; }
.btn-create { padding: 0.35rem 0.9rem; background: #1565c0; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 0.875rem; }
.btn-create:disabled { opacity: 0.6; cursor: not-allowed; }
.msg-success { color: #2e7d32; font-size: 0.875rem; margin: 0; }
.msg-error { color: #c62828; font-size: 0.875rem; margin: 0; }
.exports-note { font-size: 0.8rem; color: #777; margin: 0.25rem 0 0; }
.exports-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
.exports-table th, .exports-table td { padding: 0.4rem 0.6rem; border: 1px solid #e0e0e0; text-align: left; }
.exports-table th { background: #f5f5f5; }
.download-link { color: #1565c0; text-decoration: none; }
.download-link:hover { text-decoration: underline; }
</style>
