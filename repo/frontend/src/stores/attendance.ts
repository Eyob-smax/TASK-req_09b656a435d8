import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as attendanceApi from '@/services/attendanceApi'
import type { AttendanceException, AttendanceAnomaly, ReviewDecisionCreate, ProofUploadResponse } from '@/types/attendance'
import type { Pagination } from '@/types'

export const useAttendanceStore = defineStore('attendance', () => {
  const exceptions = ref<AttendanceException[]>([])
  const anomalies = ref<AttendanceAnomaly[]>([])
  const currentException = ref<AttendanceException | null>(null)
  const pagination = ref<Pagination | null>(null)
  const loading = ref(false)
  const submitting = ref(false)
  const error = ref<string | null>(null)

  async function loadExceptions(params?: { status?: string; page?: number }): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const result = await attendanceApi.listExceptions(params)
      exceptions.value = result.data
      pagination.value = result.pagination
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function loadException(exceptionId: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      currentException.value = await attendanceApi.getException(exceptionId)
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function createException(statement: string): Promise<AttendanceException | null> {
    submitting.value = true
    error.value = null
    try {
      const exc = await attendanceApi.createException({ candidate_statement: statement })
      currentException.value = exc
      return exc
    } catch (e) {
      error.value = (e as Error).message
      return null
    } finally {
      submitting.value = false
    }
  }

  async function uploadProof(
    exceptionId: string,
    file: File,
  ): Promise<ProofUploadResponse | null> {
    submitting.value = true
    error.value = null
    try {
      const result = await attendanceApi.uploadProof(exceptionId, file)
      await loadException(exceptionId)
      return result
    } catch (e) {
      error.value = (e as Error).message
      return null
    } finally {
      submitting.value = false
    }
  }

  async function submitReview(
    exceptionId: string,
    data: ReviewDecisionCreate,
  ): Promise<boolean> {
    submitting.value = true
    error.value = null
    try {
      await attendanceApi.submitReview(exceptionId, data)
      await loadException(exceptionId)
      return true
    } catch (e) {
      error.value = (e as Error).message
      return false
    } finally {
      submitting.value = false
    }
  }

  async function loadAnomalies(candidateId?: string): Promise<void> {
    try {
      anomalies.value = await attendanceApi.listAnomalies(candidateId)
    } catch (e) {
      error.value = (e as Error).message
    }
  }

  function clearError(): void {
    error.value = null
  }

  function reset(): void {
    exceptions.value = []
    anomalies.value = []
    currentException.value = null
    error.value = null
  }

  return {
    exceptions,
    anomalies,
    currentException,
    pagination,
    loading,
    submitting,
    error,
    loadExceptions,
    loadException,
    createException,
    uploadProof,
    submitReview,
    loadAnomalies,
    clearError,
    reset,
  }
})
