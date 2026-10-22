export function activeThisWeek(row: {start_date: string | null; end_date: string | null; recurrence: string | null}, start: string, end: string) {
  if (row.start_date && row.start_date > end) return false
  if (row.end_date) return row.end_date >= start
  if (row.recurrence === "recurring") return true
  return Boolean(row.start_date && row.start_date >= start)
}
