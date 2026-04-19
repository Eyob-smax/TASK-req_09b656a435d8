<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDocumentStore } from '@/stores/document'
import StatusChip from '@/components/common/StatusChip.vue'
import BannerAlert from '@/components/common/BannerAlert.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TimestampDisplay from '@/components/common/TimestampDisplay.vue'
import type { DocumentReviewCreate, DocumentStatus } from '@/types/document'

const route = useRoute()
const router = useRouter()
const docStore = useDocumentStore()
const documentId = route.params.documentId as string
const candidateId = computed(() => {
  const raw = route.query.candidateId
  return typeof raw === 'string' ? raw : ''
})

const decision = reactive<DocumentReviewCreate>({
  version_id: '',
  status: 'approved',
  resubmission_reason: null,
  reviewer_notes: null,
})
const reviewed = ref(false)

const needsReason = computed<boolean>(() => decision.status === 'needs_resubmission')
const hasError = computed<boolean>(
  () => needsReason.value && !decision.resubmission_reason?.trim(),
)

onMounted(async () => {
  if (!candidateId.value) {
    docStore.error = 'Missing candidate context for this review item.'
    return
  }
  await docStore.loadDocument(candidateId.value, documentId)
  decision.version_id = docStore.current?.latest_version?.id ?? ''
})

async function submit(): Promise<void> {
  if (!decision.version_id) {
    docStore.error = 'No active document version found for review.'
    return
  }
  if (hasError.value) return
  const ok = await docStore.reviewDocument(documentId, { ...decision })
  if (ok) {
    reviewed.value = true
    setTimeout(() => router.push('/staff/documents'), 1500)
  }
}

async function download(): Promise<void> {
  await docStore.downloadDocument(documentId)
}
</script>

<template>
  <div class="document-review-view" data-testid="document-review-view">
    <div class="document-review-view__header">
      <h2>Review Document</h2>
      <router-link to="/staff/documents" class="back-link">← Document Queue</router-link>
    </div>

    <BannerAlert v-if="reviewed" type="success" message="Decision recorded. Redirecting…" />
    <BannerAlert v-if="docStore.error" type="error" :message="docStore.error" :dismissible="true" @dismiss="docStore.clearError()" />

    <div class="review-doc-info">
      <p>Document ID: <code>{{ documentId }}</code></p>
      <p v-if="candidateId">Candidate ID: <code>{{ candidateId }}</code></p>
      <button type="button" class="btn-secondary" @click="download">Download &amp; Verify</button>
    </div>

    <form class="review-form" @submit.prevent="submit" data-testid="review-form">
      <fieldset class="review-form__fieldset">
        <legend>Decision</legend>
        <label>
          <input v-model="decision.status" type="radio" value="approved" data-testid="decision-approved" />
          Approve
        </label>
        <label>
          <input v-model="decision.status" type="radio" value="rejected" data-testid="decision-rejected" />
          Reject
        </label>
        <label>
          <input v-model="decision.status" type="radio" value="needs_resubmission" data-testid="decision-resubmit" />
          Needs Resubmission
        </label>
      </fieldset>

      <label v-if="needsReason" class="review-form__field">
        Resubmission Reason *
        <textarea
          v-model="decision.resubmission_reason"
          rows="2"
          required
          data-testid="field-resubmission-reason"
        />
        <span v-if="hasError" class="review-form__error">Resubmission reason is required.</span>
      </label>

      <label class="review-form__field">
        Reviewer Notes (optional)
        <textarea v-model="decision.reviewer_notes" rows="2" data-testid="field-reviewer-notes" />
      </label>

      <button
        type="submit"
        class="btn-primary"
        :disabled="docStore.loading || hasError || reviewed"
        data-testid="review-submit"
      >
        {{ docStore.loading ? 'Submitting…' : 'Submit Decision' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.document-review-view { display: flex; flex-direction: column; gap: 1.25rem; max-width: 560px; }
.document-review-view__header { display: flex; align-items: center; justify-content: space-between; }
.document-review-view__header h2 { margin: 0; }
.back-link { font-size: 0.875rem; color: #1565c0; text-decoration: none; }
.review-doc-info { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; font-size: 0.875rem; }
.review-form { display: flex; flex-direction: column; gap: 1rem; }
.review-form__fieldset { border: 1px solid #e0e0e0; border-radius: 6px; padding: 0.75rem; display: flex; flex-direction: column; gap: 0.4rem; }
.review-form__fieldset label { display: flex; align-items: center; gap: 0.4rem; font-size: 0.9rem; }
.review-form__field { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.875rem; }
.review-form__field textarea { padding: 0.4rem 0.5rem; border: 1px solid #bdbdbd; border-radius: 4px; }
.review-form__error { color: #ef4444; font-size: 0.8rem; }
.btn-primary { padding: 0.5rem 1.25rem; background: #1565c0; color: white; border: none; border-radius: 4px; cursor: pointer; align-self: flex-start; }
.btn-primary:disabled { opacity: 0.6; cursor: wait; }
.btn-secondary { padding: 0.35rem 0.75rem; background: white; color: #1565c0; border: 1px solid #1565c0; border-radius: 4px; cursor: pointer; font-size: 0.8rem; }
</style>
