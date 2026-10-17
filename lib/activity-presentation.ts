export function activityPrice(value: string | null | undefined) {
  const supplied = value?.trim()
  if (!supplied || /^(?:unknown|n\/a|not supplied)$/i.test(supplied)) return 'Price unknown'
  return /^free[.!]?$/i.test(supplied) ? 'Free' : supplied
}

export function activitySource(activity: {event_url?: string | null; source_url?: string | null}) {
  for (const supplied of [activity.event_url, activity.source_url]) {
    if (!supplied?.trim()) continue
    try {
      const url = new URL(supplied.trim())
      if (['http:', 'https:'].includes(url.protocol) && !url.username && !url.password) return url.href
    } catch { /* Missing or malformed links are not invented. */ }
  }
  return null
}
