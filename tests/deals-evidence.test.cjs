const {test}=require('node:test')
const assert=require('node:assert/strict')
const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript')
function load(access, result, publicResult={items:[],loadFailed:false}) {
  let reads=0
  const chain={select:()=>chain,eq:()=>chain,in:()=>chain,not:()=>chain,order:()=>chain,range:()=>chain,abortSignal:async()=>result}
  const module={exports:{}}
  const deps={'server-only':{},'@/lib/supabase':{getSupabase:()=>({from:()=>{reads++;return chain}})},'@/lib/deals':{getDeals:async()=>publicResult},'./session':{operationsAccess:async()=>access},'./evidence-shared':{evidenceUrl:value=>value?.startsWith('https://')?value:null}}
  vm.runInNewContext(ts.transpileModule(fs.readFileSync('lib/operations/deals-evidence.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{module,exports:module.exports,require:name=>deps[name]??require(name),AbortSignal,Set,JSON,String,Number})
  return {get:module.exports.getDealsEvidence,reads:()=>reads}
}
test('Deals queues deny before privileged reads',async()=>{
  for(const access of ['denied','sign-in','unavailable']) {
    const m=load(access,{data:[],count:0,error:null})
    assert.equal((await m.get('offers',1,'all')).access,access)
    assert.equal(m.reads(),0)
  }
})
test('failed Deals requests never become genuine empty queues',async()=>{
  const m=load('allowed',{data:null,count:null,error:{message:'private infrastructure detail'}})
  const r=await m.get('sources',1,'all')
  assert.equal(r.evidence.available,false)
  assert.equal(JSON.stringify(r).includes('private infrastructure'),false)
})
test('stored live rows outside exact public selection are not labelled displayed',async()=>{
  const m=load('allowed',{data:[{id:7,title:'Offer',status:'live',link:'https://example.com/offer'}],count:1,error:null})
  const r=await m.get('offers',1,'all')
  assert.match(r.evidence.rows[0].state,/outside/)
  const unavailable=load('allowed',{data:[{id:7,title:'Offer',status:'live'}],count:1,error:null},{items:[],loadFailed:true})
  assert.equal((await unavailable.get('offers',1,'all')).evidence.rows[0].state,'Public status unavailable')
})
test('successful source fetch and empty yield remain separately inspectable',async()=>{
  const m=load('allowed',{data:[{id:17,name:'AWIN',active:true,source_type:'awin',url:'config://awin',last_status:'ok',last_counts:{fetched:10,verified:0}}],count:1,error:null})
  const row=(await m.get('sources',1,'all')).evidence.rows[0]
  assert.equal(row.url,null)
  assert.match(row.detail,/Verified offers: 0/)
  assert.match(row.detail,/does not prove useful offers/)
})
test('displayed-only filter fails closed when public membership cannot be established',async()=>{
  const m=load('allowed',{data:[],count:0,error:null},{items:[],loadFailed:true})
  assert.equal((await m.get('offers',1,'displayed')).evidence.available,false)
  const empty=load('allowed',{data:[],count:0,error:null})
  const r=await empty.get('offers',1,'displayed')
  assert.equal(r.evidence.available,true)
  assert.equal(r.evidence.total,0)
  assert.equal(empty.reads(),0)
})
