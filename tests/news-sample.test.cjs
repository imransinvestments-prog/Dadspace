const assert = require('node:assert/strict')
const { test } = require('node:test')
const fs = require('node:fs')
const vm = require('node:vm')
const ts = require('typescript')
const { createHash } = require('node:crypto')
const sample = JSON.parse(fs.readFileSync('artefacts/data/news-quality-sample-2026-10-15.json', 'utf8'))
const moduleValue = { exports: {} }
const checksModule={exports:{}}
vm.runInNewContext(ts.transpileModule(fs.readFileSync('lib/operations/news-checks.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{module:checksModule,exports:checksModule.exports})
const code = ts.transpileModule(fs.readFileSync('lib/operations/news-sample.ts', 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true } }).outputText
vm.runInNewContext(code, { module: moduleValue, exports: moduleValue.exports, require: name => name==='./news-checks'?checksModule.exports:name.startsWith('@/artefacts/') ? sample : require(name) })
const news = moduleValue.exports
function comment(id, row, checks, author = 'imransinvestments-prog') {
  const hash = createHash('sha256').update(JSON.stringify(row)).digest('hex')
  return { id, user: { login: author }, body: `Dadspace owner review v1\n\nDecision: Approved for stated scope\n${checks ? `News quality checks: ${JSON.stringify(checks)}\n` : ''}Reviewed record: ${row.id}\nSnapshot SHA-256: ${hash}\n` }
}
test('frozen sample contains 50 distinct records with geographic fields and preserves prior IDs', () => {
  assert.equal(sample.rows.length, 50); assert.equal(new Set(sample.rows.map(row => row.id)).size, 50)
  for (const row of sample.rows) for (const field of ['geo_scope','region','geo_region','admin_area','locality']) assert.ok(field in row.fields)
  assert.ok(sample.rows.some(row => row.id === '928')); assert.ok(sample.rows.some(row => row.id === '926'))
  assert.ok(sample.strata.every(stratum => stratum.selected > 0)); assert.equal(sample.strata.reduce((sum,s) => sum+s.selected,0),50)
})
test('legacy approvals count once without inventing rubric scores', () => {
  const progress = news.newsProgress([comment(1,sample.legacy_rows[0]),comment(2,sample.legacy_rows[0]),comment(3,sample.legacy_rows[1])])
  assert.equal(progress.reviewed,2); assert.equal(progress.remaining,48)
  assert.equal(progress.relevantAndAttributed,0); assert.equal(progress.linksWorking,0); assert.equal(progress.geographyChecked,0)
})
test('latest per-record rubric scores drive distinct counts and denominator stays 50', () => {
  const yes={relevance:'yes',attribution:'yes',destination:'yes',geography:'yes'}
  const progress = news.newsProgress([comment(1,sample.rows[0],yes),comment(2,sample.rows[0],{...yes,destination:'no'})])
  assert.equal(progress.reviewed,1); assert.equal(progress.relevantAndAttributed,1); assert.equal(progress.linksWorking,0); assert.equal(progress.linksChecked,1)
})
test('untrusted authors, mismatched snapshots and overall approvals do not advance progress', () => {
  const valid=comment(1,sample.rows[0])
  const altered=comment(2,{...sample.rows[0],title:'Changed'})
  assert.equal(news.newsProgress([comment(1,sample.rows[0],null,'outsider'),altered,{...valid,body:'Dadspace owner review v1\nDecision: Approved for stated scope\n'}]).reviewed,0)
})
test('geographic instructions distinguish local, national and unknown scope', () => {
  assert.ok(news.newsGeography({geo_scope:'local',region:'england',locality:'haringey'}).guidance.includes('does not need to be relevant nationwide'))
  assert.ok(news.newsGeography({}).guidance.includes('do not assume nationwide'))
  assert.equal(news.validNewsChecks({relevance:'yes',attribution:'yes',destination:'unknown',geography:'unknown'}),true)
  assert.equal(news.validNewsChecks({relevance:'invented'}),false)
})
function supplemental(id, rows=sample.rows, author='imransinvestments-prog') {
  return {id,user:{login:author},body:'Dadspace news supplemental review v1\nNews supplemental checks: '+JSON.stringify({sampleId:sample.id,records:rows.map(row=>({id:row.id,fingerprint:createHash('sha256').update(JSON.stringify(row)).digest('hex'),checks:{summary:'yes',date:'yes',sensitiveLabel:'yes',homepagePick:'yes'}}))})+'\n'}
}
test('cohort confirmation applies only four additional checks and preserves original decisions',()=>{
  const base=sample.rows.map((row,index)=>comment(index+1,row,{relevance:'yes',attribution:'yes',destination:'yes',geography:'no'}))
  const progress=news.newsProgress([...base,supplemental(100)])
  assert.equal(progress.reviewed,50);assert.equal(progress.geographyCorrect,0)
  assert.equal(progress.summariesAccepted,50);assert.equal(progress.datesAccepted,50);assert.equal(progress.sensitiveLabelsAccepted,50);assert.equal(progress.homepagePicksAccepted,50)
})
test('untrusted or mismatched cohort confirmations cannot mark records acceptable',()=>{
  const base=[comment(1,sample.rows[0])]
  assert.equal(news.newsProgress([...base,supplemental(100,sample.rows,'outsider')]).summariesAccepted,0)
  assert.equal(news.newsProgress([...base,supplemental(100,[{...sample.rows[0],title:'Changed'}])]).summariesAccepted,0)
  assert.equal(news.newsProgress([supplemental(100)]).reviewed,0)
})
test('a later per-record correction supersedes the cohort confirmation',()=>{
  const progress=news.newsProgress([comment(1,sample.rows[0]),supplemental(2),comment(3,sample.rows[0],{relevance:'yes',attribution:'yes',destination:'yes',geography:'no',summary:'no',date:'yes',sensitiveLabel:'unknown',homepagePick:'yes'})])
  assert.equal(progress.summariesAccepted,0);assert.equal(progress.datesAccepted,1);assert.equal(progress.sensitiveLabelsAccepted,0)
})
test('legacy four-check records remain valid but supplied invalid extra values are rejected',()=>{
  const core={relevance:'yes',attribution:'yes',destination:'yes',geography:'unknown'}
  assert.equal(news.validNewsChecks(core),true)
  assert.equal(news.validNewsChecks({...core,summary:'invented'}),false)
})
