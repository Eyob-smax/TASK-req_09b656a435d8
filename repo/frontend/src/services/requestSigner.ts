// WebCrypto-backed ECDSA P-256 request signing.
//
// Primary path: non-extractable CryptoKeyPair generated via crypto.subtle.
// Fallback: when the platform advertises neither ECDSA via WebCrypto nor a
// compatible HMAC-in-IndexedDB shim, signing fails loudly.
//
// Canonical form matches the backend: METHOD\nPATH\nTIMESTAMP\nNONCE\nDEVICE_ID\nSHA256(body)\n

export interface CanonicalInput {
  method: string
  path: string
  timestamp: string
  nonce: string
  deviceId: string
  body: string | Uint8Array | null
}

export async function generateSigningKey(): Promise<CryptoKeyPair> {
  if (!globalThis.crypto?.subtle) {
    throw new Error('WebCrypto subtle is not available.')
  }
  return globalThis.crypto.subtle.generateKey(
    { name: 'ECDSA', namedCurve: 'P-256' },
    false,
    ['sign', 'verify'],
  )
}

export async function exportPublicKeyPem(pubKey: CryptoKey): Promise<string> {
  const spki = await globalThis.crypto.subtle.exportKey('spki', pubKey)
  const b64 = base64Encode(new Uint8Array(spki))
  return wrapPem(b64, 'PUBLIC KEY')
}

export async function sha256Hex(data: Uint8Array): Promise<string> {
  const hash = await globalThis.crypto.subtle.digest('SHA-256', data)
  return toHex(new Uint8Array(hash))
}

export async function buildCanonical(input: CanonicalInput): Promise<Uint8Array> {
  const bodyBytes = coerceBodyBytes(input.body)
  const bodyHash = await sha256Hex(bodyBytes)
  const text =
    `${input.method.toUpperCase()}\n` +
    `${input.path}\n` +
    `${input.timestamp}\n` +
    `${input.nonce}\n` +
    `${input.deviceId}\n` +
    `${bodyHash}\n`
  return new TextEncoder().encode(text)
}

export async function signRequest(
  privateKey: CryptoKey,
  input: CanonicalInput,
): Promise<string> {
  const canonical = await buildCanonical(input)
  const signature = await globalThis.crypto.subtle.sign(
    { name: 'ECDSA', hash: { name: 'SHA-256' } },
    privateKey,
    canonical,
  )
  return base64Encode(new Uint8Array(signature))
}

// Enrollment-time signatures are computed over the *raw* challenge nonce UTF-8
// bytes — not the request-canonical METHOD\nPATH\n… form. This matches
// backend `verify_enrollment_signature` in `security/device_keys.py`, which
// verifies the ECDSA signature directly against the stored challenge nonce.
export async function signEnrollmentNonce(
  privateKey: CryptoKey,
  nonce: string,
): Promise<string> {
  const nonceBytes = new TextEncoder().encode(nonce)
  const signature = await globalThis.crypto.subtle.sign(
    { name: 'ECDSA', hash: { name: 'SHA-256' } },
    privateKey,
    nonceBytes,
  )
  return base64Encode(new Uint8Array(signature))
}

export function generateNonce(): string {
  const arr = new Uint8Array(24)
  globalThis.crypto.getRandomValues(arr)
  return `n-${toHex(arr)}`
}

export function currentTimestamp(): string {
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z')
}

// ── helpers ────────────────────────────────────────────────────────────────

function coerceBodyBytes(body: string | Uint8Array | null): Uint8Array {
  if (body === null || body === undefined) return new Uint8Array()
  if (body instanceof Uint8Array) return body
  return new TextEncoder().encode(body)
}

function toHex(bytes: Uint8Array): string {
  let s = ''
  for (const b of bytes) s += b.toString(16).padStart(2, '0')
  return s
}

function base64Encode(bytes: Uint8Array): string {
  let s = ''
  for (const b of bytes) s += String.fromCharCode(b)
  return btoa(s)
}

function wrapPem(b64: string, label: string): string {
  const lines = b64.match(/.{1,64}/g) ?? []
  return `-----BEGIN ${label}-----\n${lines.join('\n')}\n-----END ${label}-----\n`
}
