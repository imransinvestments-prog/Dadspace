/** Calendar boundaries are London midnight, including BST and year rollover. */
export function newsMonth(now = new Date()) {
  const parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", year: "numeric", month: "2-digit" }).formatToParts(now)
  const year = Number(parts.find(p => p.type === "year")!.value)
  const month = Number(parts.find(p => p.type === "month")!.value)
  const midnight = (y: number, m: number) => {
    const date = new Date(Date.UTC(y, m - 1, 1))
    const hour = Number(new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", hourCycle: "h23" }).format(date))
    return new Date(date.getTime() - hour * 3_600_000).toISOString()
  }
  return { start: midnight(year, month), end: midnight(year, month + 1), label: new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", month: "long", year: "numeric" }).format(now) }
}
