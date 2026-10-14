// Operator identity is configured by the deployment owner, never by user metadata.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export function isOperationsUser(id: string, configuredIds: string | undefined) {
  if (!UUID.test(id)) return false
  const ids = (configuredIds || "").split(",").map(value => value.trim().toLowerCase())
  return ids.filter(value => UUID.test(value)).includes(id.toLowerCase())
}
