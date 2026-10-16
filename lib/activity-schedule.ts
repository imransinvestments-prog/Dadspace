export type ScheduleEvidence = {
  recurrence?: string | null; schedule_text?: string | null; time_text?: string | null
  start_date?: string | null; end_date?: string | null; event_url?: string | null
}
type State = 'future-date' | 'listed-today' | 'past-dates' | 'programme-period' | 'programme-ended' | 'unknown' | 'conflict'
export type ActivitySchedule = {
  state: State; recurrence: string | null; nextDate: string | null
  pattern: string | null
  programmeStart: string | null; programmeEnd: string | null; message: string
}
function validDate(value: string | null | undefined): string | null {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null
  const parsed = new Date(`${value}T00:00:00Z`)
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0,10) === value ? value : null
}
const months = ['january','february','march','april','may','june','july','august','september','october','november','december']
function englishDate(day: string, month: string, year: string) {
  const index = months.indexOf(month.toLowerCase())
  return index < 0 ? null : validDate(`${year}-${String(index+1).padStart(2,'0')}-${day.padStart(2,'0')}`)
}

// Deliberately bounded: source parser output, not arbitrary prose/calendar inference.
// A day/date is never expanded into next week's session. Stored range endpoints
// are not programme-validity evidence unless a supported source explicitly says so.
export function activitySchedule(row: ScheduleEvidence, now = new Date()): ActivitySchedule {
  const today = new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/London'}).format(now)
  const raw = row.schedule_text?.trim() || ''
  const recurrence = row.recurrence?.trim() === 'recurring' ? 'Regular activity; check current schedule' : row.recurrence?.trim() || null
  const suffix = raw.replace(/^Published (?:dates|session):[^;]+;\s*/i,'')
  const pattern = /^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b/i.test(suffix) && !/\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)/i.test(suffix) && suffix.length <= 120 ? suffix : null
  const base: ActivitySchedule = {state:'unknown',recurrence,pattern,nextDate:null,programmeStart:null,programmeEnd:null,message:'Next published session not confirmed. Check the organiser’s schedule.'}
  const conflict = {...base,state:'conflict' as const,message:'Schedule evidence is unclear or inconsistent. Check the organiser’s schedule.'}
  const start = validDate(row.start_date), end = validDate(row.end_date)
  if ((row.start_date && !start) || (row.end_date && !end) || (start && end && end < start)) return conflict

  // Coventry's existing, reviewed adapter copies programme bounds and recurrence
  // from the page's Date field. Require the same bounds in both copied text and
  // stored fields; a range from another source is not enough to claim expiry.
  const period = /^(\d{1,2})(?:st|nd|rd|th)? ([A-Za-z]+) (\d{4}) - (\d{1,2})(?:st|nd|rd|th)? ([A-Za-z]+) (\d{4}) Recurs\b/i.exec(raw)
  if (period && /^https:\/\/www\.coventry\.gov\.uk\/events\/event\/\d+\//.test(row.event_url || '')) {
    const from = englishDate(period[1],period[2],period[3]), through = englishDate(period[4],period[5],period[6])
    if (!from || !through || from !== start || through !== end) return conflict
    const restrictions = raw.slice(period[0].length).replace(/^\s*/,'').split(';').filter(part=>!/^\s*Time:/i.test(part)).join(';').trim()
    return {...base,pattern:`Recurs ${restrictions}`,state:through < today ? 'programme-ended' : 'programme-period',programmeStart:from,programmeEnd:through,
      message:through < today ? 'Published programme period ended. Check whether a new programme is available.' : 'Published programme period; individual sessions and exceptions must be checked with the organiser.'}
  }
  let dates: string[] = []
  const published = /^Published dates:\s*([^;]+)/i.exec(raw)
  const session = /^Published session:\s*([^;]+)/i.exec(raw)
  if (published || session) {
    const tokens = (published || session)![1].split(',').map(v=>v.trim())
    if (!tokens.length || tokens.some(v=>!validDate(v))) return conflict
    dates = [...new Set(tokens)].sort()
    if ((start && dates.some(d=>d < start)) || (end && dates.some(d=>d > end))) return conflict
  } else if (start && (!end || start === end)) dates = [start]
  const next = dates.find(d=>d >= today)
  if (next) return {...base,state:next === today ? 'listed-today' : 'future-date',nextDate:next,
    message:next === today ? 'A session is listed today; check its time and availability.' : 'Next explicitly listed session; check availability with the organiser.'}
  if (dates.length) return {...base,state:'past-dates',message:'The listed session dates are in the past. Next published session not confirmed.'}
  return base
}

export function scheduleDate(date: string) {
  return new Intl.DateTimeFormat('en-GB',{timeZone:'UTC',weekday:'short',day:'numeric',month:'short',year:'numeric'}).format(new Date(`${date}T00:00:00Z`))
}
