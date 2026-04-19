<script setup lang="ts">
import { ref } from 'vue'
import { useUpload } from '@/composables/useUpload'

const props = defineProps<{
  label?: string
  requirementCode?: string | null
  accept?: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'upload', payload: { file: File; requirementCode?: string | null }): void
}>()

const { selectedFile, validationError, selectFile } = useUpload()
const inputRef = ref<HTMLInputElement | null>(null)

function onFileChange(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] ?? null
  selectFile(file)
}

function onDrop(event: DragEvent): void {
  event.preventDefault()
  const file = event.dataTransfer?.files?.[0] ?? null
  selectFile(file)
}

function triggerInput(): void {
  inputRef.value?.click()
}

function submit(): void {
  if (!selectedFile.value || validationError.value) return
  emit('upload', { file: selectedFile.value, requirementCode: props.requirementCode })
}
</script>

<template>
  <div
    class="upload-panel"
    :class="{ 'upload-panel--disabled': disabled }"
    @drop.prevent="onDrop"
    @dragover.prevent
    data-testid="upload-panel"
  >
    <p class="upload-panel__label">{{ label ?? 'Upload document' }}</p>
    <p class="upload-panel__hint">PDF, JPEG, or PNG · max 25 MB</p>

    <input
      ref="inputRef"
      type="file"
      class="upload-panel__input"
      :accept="accept ?? 'application/pdf,image/jpeg,image/png'"
      :disabled="disabled"
      aria-label="Select file"
      @change="onFileChange"
    />
    <button
      type="button"
      class="upload-panel__browse"
      :disabled="disabled"
      @click="triggerInput"
    >
      Browse…
    </button>

    <p v-if="selectedFile" class="upload-panel__filename">
      Selected: <strong>{{ selectedFile.name }}</strong>
      ({{ (selectedFile.size / 1024).toFixed(0) }} KB)
    </p>

    <p v-if="validationError" class="upload-panel__error" role="alert" data-testid="upload-error">
      {{ validationError.message }}
    </p>

    <button
      type="button"
      class="upload-panel__submit"
      :disabled="!selectedFile || !!validationError || disabled"
      data-testid="upload-submit"
      @click="submit"
    >
      Upload
    </button>
  </div>
</template>

<style scoped>
.upload-panel {
  border: 2px dashed #bdbdbd; border-radius: 8px; padding: 1.25rem;
  display: flex; flex-direction: column; gap: 0.5rem; text-align: center;
}
.upload-panel--disabled { opacity: 0.5; pointer-events: none; }
.upload-panel__label { font-weight: 600; margin: 0; }
.upload-panel__hint { margin: 0; font-size: 0.8rem; color: #757575; }
.upload-panel__input { display: none; }
.upload-panel__browse {
  align-self: center; padding: 0.375rem 1rem; background: #f5f5f5;
  border: 1px solid #bdbdbd; border-radius: 4px; cursor: pointer;
}
.upload-panel__filename { font-size: 0.85rem; margin: 0; }
.upload-panel__error { color: #ef4444; font-size: 0.85rem; margin: 0; }
.upload-panel__submit {
  align-self: center; padding: 0.5rem 1.25rem; background: #1565c0;
  color: white; border: none; border-radius: 4px; cursor: pointer;
}
.upload-panel__submit:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
