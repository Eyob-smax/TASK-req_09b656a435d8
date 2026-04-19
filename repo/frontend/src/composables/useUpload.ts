import { ref } from 'vue'

const ALLOWED_MIME = ['application/pdf', 'image/jpeg', 'image/png']
const MAX_BYTES = 25 * 1024 * 1024 // 25 MB

export interface UploadValidationError {
  code: 'INVALID_MIME' | 'TOO_LARGE' | 'NO_FILE'
  message: string
}

export function validateFile(file: File | null): UploadValidationError | null {
  if (!file) return { code: 'NO_FILE', message: 'No file selected.' }
  if (!ALLOWED_MIME.includes(file.type)) {
    return { code: 'INVALID_MIME', message: 'Only PDF, JPEG, and PNG files are allowed.' }
  }
  if (file.size > MAX_BYTES) {
    return { code: 'TOO_LARGE', message: 'File must be 25 MB or smaller.' }
  }
  return null
}

export function useUpload() {
  const selectedFile = ref<File | null>(null)
  const validationError = ref<UploadValidationError | null>(null)
  const uploading = ref(false)

  function selectFile(file: File | null): void {
    selectedFile.value = file
    validationError.value = validateFile(file)
  }

  function reset(): void {
    selectedFile.value = null
    validationError.value = null
    uploading.value = false
  }

  return { selectedFile, validationError, uploading, selectFile, reset, validateFile }
}
