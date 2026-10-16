import { activitySchedule, scheduleDate, type ScheduleEvidence } from '@/lib/activity-schedule'

export function ActivityScheduleSummary({activity, now}: {activity: ScheduleEvidence; now?: string}) {
  const schedule = activitySchedule(activity, now ? new Date(now) : new Date())
  return <div className="space-y-1 break-words text-sm" aria-label="Activity schedule">
    {schedule.recurrence && <p className="font-semibold">{schedule.recurrence}</p>}
    {schedule.pattern && <p>Published pattern: {schedule.pattern}</p>}
    {schedule.nextDate && <p className="font-semibold">{schedule.state === 'listed-today' ? 'Listed today' : 'Next listed session'}: {scheduleDate(schedule.nextDate)}{activity.time_text ? ` · ${activity.time_text}` : ''}</p>}
    {schedule.programmeStart && schedule.programmeEnd && <p>Published programme period: {scheduleDate(schedule.programmeStart)} to {scheduleDate(schedule.programmeEnd)}</p>}
    <p className="text-muted-foreground">{schedule.message}</p>
  </div>
}
