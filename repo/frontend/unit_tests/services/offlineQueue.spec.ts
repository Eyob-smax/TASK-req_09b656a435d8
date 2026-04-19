// FE-UNIT: offline queue — enqueue, list, remove, clear, uniqueness of IDs.
// Uses the in-memory fallback since jsdom has no real IndexedDB.

import { describe, it, expect, beforeEach } from 'vitest'
import { getOfflineQueue, __resetOfflineQueueForTests } from '@/services/offlineQueue'

beforeEach(() => {
  __resetOfflineQueueForTests()
})

describe('offline queue (in-memory fallback)', () => {
  it('starts empty', async () => {
    const q = getOfflineQueue()
    expect(await q.list()).toHaveLength(0)
  })

  it('enqueue returns a unique ID', async () => {
    const q = getOfflineQueue()
    const id1 = await q.enqueue({ method: 'POST', path: '/a', body: {}, idempotencyKey: 'k1' })
    const id2 = await q.enqueue({ method: 'POST', path: '/b', body: {}, idempotencyKey: 'k2' })
    expect(id1).not.toBe(id2)
    expect(id1).toMatch(/^q-/)
  })

  it('list returns enqueued items', async () => {
    const q = getOfflineQueue()
    await q.enqueue({ method: 'POST', path: '/x', body: { a: 1 }, idempotencyKey: 'ik1' })
    const items = await q.list()
    expect(items).toHaveLength(1)
    expect(items[0].path).toBe('/x')
    expect(items[0].idempotencyKey).toBe('ik1')
  })

  it('remove deletes the specified item', async () => {
    const q = getOfflineQueue()
    const id = await q.enqueue({ method: 'POST', path: '/del', body: {}, idempotencyKey: 'k' })
    await q.remove(id)
    expect(await q.list()).toHaveLength(0)
  })

  it('clear empties the queue', async () => {
    const q = getOfflineQueue()
    await q.enqueue({ method: 'POST', path: '/1', body: {}, idempotencyKey: 'k1' })
    await q.enqueue({ method: 'POST', path: '/2', body: {}, idempotencyKey: 'k2' })
    await q.clear()
    expect(await q.list()).toHaveLength(0)
  })

  it('preserves enqueuedAt timestamp', async () => {
    const before = new Date().toISOString()
    const q = getOfflineQueue()
    const id = await q.enqueue({ method: 'GET', path: '/t', body: null, idempotencyKey: 'kt' })
    const after = new Date().toISOString()
    const items = await q.list()
    expect(items[0].enqueuedAt >= before).toBe(true)
    expect(items[0].enqueuedAt <= after).toBe(true)
  })

  it('singleton returns the same instance', () => {
    const q1 = getOfflineQueue()
    const q2 = getOfflineQueue()
    expect(q1).toBe(q2)
  })
})
