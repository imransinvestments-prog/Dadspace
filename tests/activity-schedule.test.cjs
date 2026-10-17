const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript')
const moduleFor={exports:{}}
vm.runInNewContext(ts.transpileModule(fs.readFileSync('lib/activity-schedule.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{module:moduleFor,exports:moduleFor.exports,Intl,Date,require:name=>{throw Error(name)}})
const {activitySchedule}=moduleFor.exports
const now=new Date('2026-10-16T16:00:00Z')
test('past recurring occurrence is not programme expiry or an invented next week',()=>{
 const s=activitySchedule({recurrence:'recurring',start_date:'2026-10-13',end_date:'2026-10-13',schedule_text:'Published dates: 2026-10-13; Tuesday, 10.30am - 11.00am'},now)
 assert.equal(s.state,'past-dates');assert.equal(s.nextDate,null);assert.equal(s.programmeEnd,null);assert.match(s.message,/not confirmed/)
})
test('next listed date preserves real gaps and never extrapolates recurrence',()=>{
 const row={recurrence:'recurring',schedule_text:'Published dates: 2026-10-19, 2026-11-02; Monday, 9.30am-10am',start_date:'2026-10-19',end_date:'2026-11-02'}
 assert.equal(activitySchedule(row,now).nextDate,'2026-10-19')
 assert.equal(activitySchedule(row,new Date('2026-10-20T12:00Z')).nextDate,'2026-11-02')
 assert.equal(activitySchedule(row,new Date('2026-11-03T12:00Z')).nextDate,null)
})
test('single stored occurrence is usable without claiming a multi-day range means daily sessions',()=>{
 assert.equal(activitySchedule({start_date:'2026-10-17',end_date:'2026-10-17',time_text:'10am - 11am'},now).nextDate,'2026-10-17')
 assert.equal(activitySchedule({start_date:'2026-10-17',end_date:'2026-10-30'},now).nextDate,null)
})
test('missing/invalid/contradictory dates stay uncertain',()=>{
 assert.equal(activitySchedule({recurrence:'recurring'},now).state,'unknown')
 for(const schedule_text of ['Published dates: 2026-02-30','Published dates: 2026-10-19, invalid']) assert.equal(activitySchedule({schedule_text},now).state,'conflict')
 assert.equal(activitySchedule({schedule_text:'Published dates: 2026-10-19',start_date:'2026-10-13',end_date:'2026-10-13'},now).state,'conflict')
})
test('only the supported source-explicit programme period can establish its end; no recurrence expansion',()=>{
 const row={event_url:'https://www.coventry.gov.uk/events/event/8828/tots-time',start_date:'2026-07-09',end_date:'2027-01-08',schedule_text:'9th July 2026 - 8th January 2027 Recurs every other week on Thursday.; Time: 10:00 - 11:15; term time only'}
 assert.equal(activitySchedule(row,now).programmeEnd,'2027-01-08');assert.equal(activitySchedule(row,now).nextDate,null)
 assert.equal(activitySchedule(row,new Date('2027-01-09T12:00Z')).state,'programme-ended')
 assert.equal(activitySchedule({...row,event_url:'https://unreviewed.example/programme'},new Date('2027-01-09T12:00Z')).programmeEnd,null)
})
test('London dates handle midnight and DST; same-day dates never imply a session is still ahead',()=>{
 const row={start_date:'2026-10-17',end_date:'2026-10-17'}
 assert.equal(activitySchedule(row,new Date('2026-10-16T23:30Z')).state,'listed-today')
 assert.match(activitySchedule(row,new Date('2026-10-17T23:30Z')).message,/not confirmed/)
 assert.equal(activitySchedule({start_date:'2026-10-25',end_date:'2026-10-25'},new Date('2026-10-25T01:30Z')).state,'listed-today')
})

test('actual summary rendering retains source pattern and never labels raw bounds as programme lifetime',()=>{
 const box={exports:{}}
 vm.runInNewContext(ts.transpileModule(fs.readFileSync('components/activities/activity-schedule.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:box,exports:box.exports,Date,require:name=>name==='react/jsx-runtime'?require(name):moduleFor.exports})
 const html=require('react-dom/server').renderToStaticMarkup(box.exports.ActivityScheduleSummary({activity:{recurrence:'recurring',schedule_text:'Published dates: 2026-10-13; Tuesday, 10.30am - 11.00am',start_date:'2026-10-13',end_date:'2026-10-13'},now:now.toISOString()}))
 assert.match(html,/Tuesday, 10.30am - 11.00am/);assert.match(html,/not confirmed/);assert(!html.includes('Programme ended'))
})
