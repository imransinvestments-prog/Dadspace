const { test } = require('node:test'), assert = require('node:assert/strict'), fs = require('node:fs'), vm = require('node:vm'), ts = require('typescript')
const React = require('react'), {renderToStaticMarkup} = require('react-dom/server')
function load(file, dependencies = {}) {
 const module={exports:{}}
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}).outputText,{module,exports:module.exports,Date,Intl,URL,require:name=>name==='react/jsx-runtime'?require(name):dependencies[name] ?? (()=>{throw Error(name)})()})
 return module.exports
}
const presentation=load('lib/activity-presentation.ts'), schedule=load('lib/activity-schedule.ts')
const summary=load('components/activities/activity-schedule.tsx',{'@/lib/activity-schedule':schedule})
const {ActivityCard}=load('components/activities/activity-card.tsx',{
 'next/link':{default:({children,...props})=>React.createElement('a',props,children)},'lucide-react':{MapPin:()=>null},
 '@/lib/activity-slug':{activitySlug:row=>row.id},'@/lib/activity-presentation':presentation,'./activity-schedule':summary,
})
const base={id:'sample',title:'Reviewed activity',age_range:'0–5 with an adult',cost_text:null,description:null,venue_name:'Library',location:null,postcode:'W3 9LN',recurrence:'recurring',schedule_text:null}
test('free, paid and unknown prices are explicit without inventing free entry from absent data',()=>{
 for(const [value,expected] of [[null,'Price unknown'],['  ','Price unknown'],['unknown','Price unknown'],['FREE','Free'],['£5 per child; adults free','£5 per child; adults free'],['Free trial, then £12','Free trial, then £12']]) {
  assert.equal(presentation.activityPrice(value),expected)
  assert(renderToStaticMarkup(ActivityCard({activity:{...base,cost_text:value}})).includes(expected))
 }
})
test('source action prefers a valid listing and safely falls back, rejecting credentials/unsafe schemes',()=>{
 for(const invalid of ['javascript:alert(1)','data:text/html,hello','https://user:secret@example.com/','/relative','not a link']) {
  assert.equal(presentation.activitySource({event_url:invalid}),null)
  assert.equal(presentation.activitySource({event_url:invalid,source_url:'https://source.example/'}),'https://source.example/')
 }
 const html=renderToStaticMarkup(ActivityCard({activity:{...base,event_url:'https://listing.example/session',source_url:'https://source.example/'}}))
 assert(html.includes('href="https://listing.example/session"'));assert(html.includes('noopener noreferrer'))
 assert(!renderToStaticMarkup(ActivityCard({activity:base})).includes('Check source'))
})
test('card keeps supplied age/price conditions, concise next date and a details route without raw date lists',()=>{
 const dates='Published dates: 2099-10-19, 2099-10-26, 2099-11-02; Monday 19 Oct 2099, 9am'
 const html=renderToStaticMarkup(ActivityCard({activity:{...base,schedule_text:dates,start_date:'2099-10-19',end_date:'2099-11-02',cost_text:'£5 per child; adults free',event_url:'https://source.example/'+'a'.repeat(1000)}}))
 assert(html.includes('Next listed session'));assert(html.includes('0–5 with an adult'));assert(html.includes('£5 per child; adults free'))
 assert(!html.includes('Published dates:'));assert(!html.includes('2099-10-26'));assert(html.includes('href="/activities/sample"'))
 assert(html.includes('min-w-0'));assert(html.includes('overflow-wrap:anywhere'))
})
