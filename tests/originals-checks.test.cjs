const assert=require('node:assert/strict')
const {test}=require('node:test')
const fs=require('node:fs')
const vm=require('node:vm')
const ts=require('typescript')
const mod={exports:{}}
const code=ts.transpileModule(fs.readFileSync('lib/operations/originals-checks.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText
vm.runInNewContext(code,{module:mod,exports:mod.exports})
const rubric=mod.exports
const checks={originality:'yes',claims:'unknown',tone:'no',length:'yes'}
const comment=(id,hash='hash',author='imransinvestments-prog',scores=checks)=>({id,user:{login:author},body:`Dadspace owner review v1\nOriginals editorial checks: ${JSON.stringify(scores)}\nReviewed record: daily-1\nSnapshot SHA-256: ${hash}\n`})
test('four editorial judgements validate independently without converting unknown to pass',()=>{
  assert.equal(rubric.validOriginalsChecks(checks),true)
  assert.equal(rubric.validOriginalsChecks({...checks,claims:'unknown'}),true)
  assert.equal(rubric.validOriginalsChecks({...checks,length:'long'}),false)
  assert.equal(rubric.validOriginalsChecks({originality:'yes'}),false)
})
test('saved checks restore only for matching record fingerprint and trusted audit author',()=>{
  assert.equal(rubric.previousOriginalsChecks([comment(1)],'daily-1','hash').claims,'unknown')
  assert.equal(rubric.previousOriginalsChecks([comment(1)],'daily-1','changed'),undefined)
  assert.equal(rubric.previousOriginalsChecks([comment(1,'hash','outsider')],'daily-1','hash'),undefined)
  assert.equal(rubric.previousOriginalsChecks([comment(1)],'different-article','hash'),undefined)
})
test('latest same-version judgement wins; generic approval does not invent checks',()=>{
  assert.equal(rubric.previousOriginalsChecks([comment(1),comment(2,'hash','imransinvestments-prog',{...checks,tone:'yes'})],'daily-1','hash').tone,'yes')
  assert.equal(rubric.previousOriginalsChecks([{id:3,user:{login:'imransinvestments-prog'},body:'Dadspace owner review v1\nDecision: Approved for stated scope\nReviewed record: daily-1\nSnapshot SHA-256: hash\n'}],'daily-1','hash'),undefined)
})
test('word count uses section headings and paragraphs without fabricating a length target',()=>{
  assert.equal(rubric.originalBodyWords({title:'Excluded title',summary:'Excluded summary',sections:[{heading:'One heading',paragraphs:['Three body words','Two more']}] }),7)
  assert.equal(rubric.originalBodyWords({}),null)
  assert.equal(rubric.originalBodyWords({sections:[]}),0)
})
