import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as documentApi from '@/services/documentApi'
import type { Document, DocumentReviewCreate, DocumentUploadResponse } from '@/types/document'

export const useDocumentStore = defineStore('document', () => {
  const documents = ref<Document[]>([])
  const current = ref<Document | null>(null)
  const uploading = ref(false)
  const uploadProgress = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const uploadError = ref<string | null>(null)

  async function loadDocuments(candidateId: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      documents.value = await documentApi.listDocuments(candidateId)
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function loadDocument(candidateId: string, documentId: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      current.value = await documentApi.getDocument(candidateId, documentId)
    } catch (e) {
      error.value = (e as Error).message
      current.value = null
    } finally {
      loading.value = false
    }
  }

  async function upload(
    candidateId: string,
    file: File,
    requirementCode?: string | null,
  ): Promise<DocumentUploadResponse | null> {
    uploading.value = true
    uploadError.value = null
    try {
      const result = await documentApi.uploadDocument(candidateId, file, requirementCode)
      await loadDocuments(candidateId)
      return result
    } catch (e) {
      uploadError.value = (e as Error).message
      return null
    } finally {
      uploading.value = false
    }
  }

  async function reviewDocument(
    documentId: string,
    data: DocumentReviewCreate,
  ): Promise<boolean> {
    try {
      await documentApi.reviewDocument(documentId, data)
      if (current.value?.id === documentId) {
        const candidateId = current.value.candidate_id
        await loadDocuments(candidateId)
      }
      return true
    } catch (e) {
      error.value = (e as Error).message
      return false
    }
  }

  async function downloadDocument(documentId: string): Promise<void> {
    try {
      const { blob, filename } = await documentApi.downloadDocument(documentId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      error.value = (e as Error).message
    }
  }

  function clearError(): void {
    error.value = null
    uploadError.value = null
  }

  function reset(): void {
    documents.value = []
    current.value = null
    error.value = null
    uploadError.value = null
  }

  return {
    documents,
    current,
    uploading,
    uploadProgress,
    loading,
    error,
    uploadError,
    loadDocuments,
    loadDocument,
    upload,
    reviewDocument,
    downloadDocument,
    clearError,
    reset,
  }
})
