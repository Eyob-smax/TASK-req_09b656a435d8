// Persistent device key handle.
//
// The keypair is non-extractable, so its private half never leaves the
// browser. IndexedDB persists the CryptoKey object graph along with the
// device ID and fingerprint so subsequent sessions reuse the same key.

import { exportPublicKeyPem, generateSigningKey } from './requestSigner'

const DB_NAME = 'merittrack-auth'
const STORE = 'device-keys'
const KEY_RECORD = 'current'

export interface StoredDeviceKey {
  id: typeof KEY_RECORD
  privateKey: CryptoKey
  publicKey: CryptoKey
  deviceId: string | null
  fingerprint: string
  publicKeyPem: string
  createdAt: string
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1)
    req.onupgradeneeded = () => {
      const db = req.result
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: 'id' })
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

async function loadRecord(): Promise<StoredDeviceKey | null> {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, 'readonly')
    const store = tx.objectStore(STORE)
    const req = store.get(KEY_RECORD)
    req.onsuccess = () => resolve((req.result as StoredDeviceKey) ?? null)
    req.onerror = () => reject(req.error)
  })
}

async function saveRecord(record: StoredDeviceKey): Promise<void> {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite')
    tx.objectStore(STORE).put(record)
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error)
  })
}

function randomFingerprint(): string {
  const arr = new Uint8Array(16)
  globalThis.crypto.getRandomValues(arr)
  let s = ''
  for (const b of arr) s += b.toString(16).padStart(2, '0')
  return `fp-${s}`
}

export async function getOrCreateDeviceKey(): Promise<StoredDeviceKey> {
  const existing = await loadRecord()
  if (existing) return existing
  const pair = await generateSigningKey()
  const pem = await exportPublicKeyPem(pair.publicKey)
  const record: StoredDeviceKey = {
    id: KEY_RECORD,
    privateKey: pair.privateKey,
    publicKey: pair.publicKey,
    deviceId: null,
    fingerprint: randomFingerprint(),
    publicKeyPem: pem,
    createdAt: new Date().toISOString(),
  }
  await saveRecord(record)
  return record
}

export async function setDeviceId(deviceId: string): Promise<void> {
  const rec = await loadRecord()
  if (!rec) throw new Error('No device key record to associate with device id.')
  rec.deviceId = deviceId
  await saveRecord(rec)
}

export async function clearDeviceKey(): Promise<void> {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite')
    tx.objectStore(STORE).delete(KEY_RECORD)
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error)
  })
}
