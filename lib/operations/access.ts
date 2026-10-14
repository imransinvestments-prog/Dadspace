// Operator identity is configured by the deployment owner, never by user metadata.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export function isOperationsUser(id: string, configuredIds: string | undefined) {
  if (!UUID.test(id)) return false
  const ids = (configuredIds || "").split(",").map(value => value.trim().toLowerCase())
  return ids.filter(value => UUID.test(value)).includes(id.toLowerCase())
}

export function isVerifiedOperationsEmail(user: { email?: string; email_confirmed_at?: string; is_anonymous?: boolean }, configuredEmails: string | undefined) {
  if (user.is_anonymous || !user.email || !user.email_confirmed_at) return false
  if (!Number.isFinite(Date.parse(user.email_confirmed_at))) return false
  const email = user.email.trim().toLowerCase()
  return (configuredEmails || "").split(",").map(value => value.trim().toLowerCase())
    .filter(value => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)).includes(email)
}
