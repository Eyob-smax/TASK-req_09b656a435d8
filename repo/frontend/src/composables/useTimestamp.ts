// 12-hour timestamp formatting utilities.
// All backend timestamps are UTC ISO strings; display in local 12-hour format.

export function format12h(isoString: string | null | undefined): string {
  if (!isoString) return '—'
  const d = new Date(isoString)
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  })
}

export function format12hTime(isoString: string | null | undefined): string {
  if (!isoString) return '—'
  const d = new Date(isoString)
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleString(undefined, {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  })
}

export function formatDate(isoString: string | null | undefined): string {
  if (!isoString) return '—'
  const d = new Date(isoString)
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function useTimestamp() {
  function msUntil(isoString: string | null | undefined): number {
    if (!isoString) return 0
    const target = new Date(isoString)
    return Math.max(0, target.getTime() - Date.now())
  }

  function isExpired(isoString: string | null | undefined): boolean {
    if (!isoString) return false
    return new Date(isoString) <= new Date()
  }

  return { format12h, format12hTime, formatDate, msUntil, isExpired }
}
