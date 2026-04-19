// FE-UNIT: offline status — initial state, online/offline events.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

// Mock the offlineQueue module before importing useOfflineStatus
vi.mock('@/services/offlineQueue', () => ({
  replayQueue: vi.fn().mockResolvedValue({ replayed: 0, failed: 0 }),
  getOfflineQueue: vi.fn(),
  __resetOfflineQueueForTests: vi.fn(),
}))

import { useOfflineStatus } from '@/composables/useOfflineStatus'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, nextTick } from 'vue'

function makeWrapper() {
  return mount(
    defineComponent({
      setup() {
        return useOfflineStatus()
      },
      template: '<div></div>',
    }),
  )
}

describe('useOfflineStatus', () => {
  it('isOnline reflects navigator.onLine initial state', () => {
    const wrapper = makeWrapper()
    // jsdom defaults navigator.onLine to true
    expect(wrapper.vm.isOnline).toBe(true)
    wrapper.unmount()
  })

  it('isOnline becomes false when offline event fires', async () => {
    const wrapper = makeWrapper()
    window.dispatchEvent(new Event('offline'))
    await nextTick()
    expect(wrapper.vm.isOnline).toBe(false)
    wrapper.unmount()
  })

  it('isOnline becomes true when online event fires', async () => {
    const wrapper = makeWrapper()
    window.dispatchEvent(new Event('offline'))
    await nextTick()
    window.dispatchEvent(new Event('online'))
    await flushPromises()
    expect(wrapper.vm.isOnline).toBe(true)
    wrapper.unmount()
  })

  it('dismissConflict removes the message at given index', async () => {
    const wrapper = makeWrapper()
    wrapper.vm.conflictMessages.push('Error 1', 'Error 2')
    wrapper.vm.dismissConflict(0)
    expect(wrapper.vm.conflictMessages).toHaveLength(1)
    expect(wrapper.vm.conflictMessages[0]).toBe('Error 2')
    wrapper.unmount()
  })
})
