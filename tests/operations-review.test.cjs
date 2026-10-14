const assert = require('node:assert/strict')
const { test } = require('node:test')
const fs = require('node:fs')
const vm = require('node:vm')
const ts = require('typescript')
function load(file, dependencies = {}, env = {}) {
  const module = { exports: {} }
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText
  vm.runInNewContext(code, { module, exports: module.exports, process: { env }, Buffer, Date, Number, Promise, AbortSignal, FormData,
    require: name => dependencies[name] ?? require(name) })
  return module.exports
}
const token = load('lib/operations/review-token.ts', { 'server-only': {} })
const owner = '12345678-1234-1234-1234-123456789abc'
const other = '12345678-1234-1234-1234-123456789def'
const fingerprint = '1'.repeat(32)
const secret = 'test-only-server-secret'
test('review tokens bind actor, reason, action, target, fingerprint, request and expiry', () => {
  const intent = token.reviewIntent('merge', owner, other, 'Verified independent branch evidence')
  const signed = token.signReview(intent, owner, fingerprint, secret, 1000)
  const verified = token.verifyReview(signed, owner, secret, 2000)
  assert.equal(verified.reason, intent.reason)
  assert.equal(verified.target, other)
  assert.equal(verified.fingerprint, fingerprint)
  assert.ok(token.validId(verified.request))
  assert.equal(token.verifyReview(signed, other, secret, 2000), null)
  assert.equal(token.verifyReview(signed, owner, 'wrong secret', 2000), null)
  assert.equal(token.verifyReview(signed, owner, secret, 901001), null)
  assert.equal(token.verifyReview(signed+'x', owner, secret, 2000), null)
  const parts = signed.split('.')
  const changed = JSON.parse(Buffer.from(parts[0], 'base64url').toString())
  changed.target = owner
  assert.equal(token.verifyReview(Buffer.from(JSON.stringify(changed)).toString('base64url')+'.'+parts[1], owner, secret, 2000), null)
  for (const args of [['unknown',owner,null,'Valid review reason'],['approve','invalid',null,'Valid reason'],['merge',owner,owner,'Valid reason'],['hide',owner,other,'Valid reason'],['approve',owner,null,'short']]) assert.equal(token.reviewIntent(...args), null)
})
const access = load('lib/operations/access.ts')
function reviewer(user, env={}) {
  return load('lib/operations/reviewer.ts', { 'server-only': {}, '@/lib/supabase/server': { createClient: async () => ({ auth: { getUser: async () => ({ data:{user},error:null }) } }) }, './access':access }, env)
}
test('reviewer permission is separate from operator permission and metadata claims', async () => {
  const user = { id: owner, email:'owner@example.com',email_confirmed_at:'2026-10-14T12:00:00Z',user_metadata:{reviewer:true} }
  assert.equal(await reviewer(user,{DADSPACE_REVIEWER_USER_IDS:owner}).reviewIdentity(),null)
  assert.equal((await reviewer(user,{DADSPACE_OPERATOR_EMAILS:user.email}).reviewIdentity()).reviewer,false)
  assert.equal((await reviewer(user,{DADSPACE_OPERATOR_EMAILS:user.email,DADSPACE_REVIEWER_USER_IDS:owner}).reviewIdentity()).reviewer,true)
  assert.equal(await reviewer({...user,is_anonymous:true},{DADSPACE_OPERATOR_EMAILS:user.email,DADSPACE_REVIEWER_USER_IDS:owner}).reviewIdentity(),null)
})
function actions(identity, result={data:null,error:{message:'private error'}}) {
  let calls=0; const requests=[]
  const db={rpc:(name,args)=>{requests.push({name,args});return{abortSignal:async()=>result}}}
  const module=load('app/ops/decision/actions.ts', {'next/cache':{revalidatePath:()=>{}}, '@/lib/supabase':{getSupabase:()=>{calls++;return db}}, '@/lib/operations/reviewer':{reviewIdentity:async()=>identity}, '@/lib/operations/review-token':token}, {DADSPACE_SUPABASE_SERVICE_ROLE_KEY:secret})
  return {module,requests,calls:()=>calls}
}
function previewForm(){ const form=new FormData();form.set('record',owner);form.set('action','approve');form.set('target','');form.set('reason','Verified identity, access and evidence');form.set('evidence','reviewed');return form }
test('unauthorised and read-only requests cannot write; unsigned and changed-actor requests fail before RPC', async () => {
  const absent=actions(null)
  await absent.module.previewDecision({},previewForm());await absent.module.applyDecision({},new FormData())
  assert.equal(absent.calls(),0)
  const reader=actions({id:owner,reviewer:false})
  await reader.module.applyDecision({},new FormData());assert.equal(reader.calls(),0)
  const writer=actions({id:owner,reviewer:true})
  const form=new FormData();form.set('token','unsigned');form.set('confirm','apply')
  await writer.module.applyDecision({},form);assert.equal(writer.calls(),0)
  const intent=token.reviewIntent('approve',owner,null,'Verified identity and evidence')
  form.set('token',token.signReview(intent,other,fingerprint,secret))
  await writer.module.applyDecision({},form);assert.equal(writer.calls(),0)
})
test('preview projects only display evidence and applying uses the exact signed actor-bound intent', async () => {
  const reader=actions({id:owner,reviewer:false},{data:{fingerprint,summary:'Publish reviewed venue',venues:[{id:owner,name:'Branch',postcode:'W4 2AB',public_visible:false,notes:'private notes'}],listings:0,provenance:0},error:null})
  const preview=await reader.module.previewDecision({},previewForm())
  assert.ok(preview.preview.token)
  assert.equal(JSON.stringify(preview).includes('private notes'),false)
  const writer=actions({id:owner,reviewer:true},{data:other,error:null})
  const form=new FormData();form.set('token',preview.preview.token);form.set('confirm','apply');form.set('action','hide');form.set('record',other)
  const result=await writer.module.applyDecision({},form)
  assert.equal(result.audit,other)
  assert.equal(writer.requests[0].args.p_action,'approve')
  assert.equal(writer.requests[0].args.p_record,owner)
  assert.equal(writer.requests[0].args.p_actor,owner)
  assert.equal(writer.requests[0].args.p_expected,fingerprint)
})
test('stale conflicts and failed evidence retain safe messages without payload or secret leakage', async () => {
  const failed=actions({id:owner,reviewer:true})
  const result=await failed.module.previewDecision({},previewForm())
  assert.equal(result.preview,undefined)
  assert.equal(JSON.stringify(result).includes('private error'),false)
  const form=new FormData();form.set('token',token.signReview(token.reviewIntent('approve',owner,null,'Verified evidence and identity'),owner,fingerprint,secret));form.set('confirm','apply')
  const applied=await failed.module.applyDecision({},form)
  assert.equal(applied.audit,undefined)
  assert.equal(JSON.stringify(applied).includes(secret),false)
})
