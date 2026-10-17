const { test } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const ts = require('typescript')

/** Drive the real hook through render/effect boundaries with deferred requests. */
function harness() {
  const states=[], refs=[], effects=[], pending=[], requests=[], timers=new Map()
  let stateIndex=0,refIndex=0,effectIndex=0,timerId=0
  const react={
    useState(initial){const i=stateIndex++;if(!(i in states))states[i]=typeof initial==='function'?initial():initial;return [states[i],value=>{states[i]=typeof value==='function'?value(states[i]):value}]},
    useRef(initial){return refs[refIndex++]??={current:initial}},
    useEffect(callback,deps){const i=effectIndex++;if(!effects[i]||deps.some((value,j)=>value!==effects[i].deps[j]))pending.push(()=>{effects[i]?.cleanup?.();effects[i]={deps,cleanup:callback()}})},
  }
  const module={exports:{}}
  const code=ts.transpileModule(fs.readFileSync('hooks/use-directory-page.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText
  vm.runInNewContext(code,{module,exports:module.exports,AbortController,URLSearchParams,require:()=>react,
    setTimeout:fn=>{timers.set(++timerId,fn);return timerId},clearTimeout:id=>timers.delete(id),
    fetch:(url,options)=>new Promise((resolve,reject)=>requests.push({url,signal:options.signal,resolve,reject})),
  })
  return {
    requests,
    render(url,enabled=true,seed){stateIndex=refIndex=effectIndex=0;return module.exports.useDirectoryPage(url,enabled,seed)},
    flush(){while(pending.length)pending.shift()();for(const [id,fn] of timers){timers.delete(id);fn()}},
  }
}
const settle=()=>new Promise(setImmediate)
const respond=async(request,page)=>{request.resolve({ok:true,json:async()=>page});await settle()}

test('location/radius/filter changes hide previous totals immediately and reject out-of-order responses',async()=>{
  const h=harness()
  const urls=['/venues?lat=51&lng=0&radiusKm=10','/venues?lat=52&lng=0&radiusKm=25','/venues?lat=52&lng=0&radiusKm=25&free=true']
  h.render(urls[0]);h.flush()
  await respond(h.requests[0],{venues:[{id:'old'}],total:70})
  assert.equal(h.render(urls[0]).pages[0].total,70)
  let view=h.render(urls[1]);assert.equal(view.pages.length,0);assert.equal(view.loading,true);h.flush()
  view=h.render(urls[2]);assert.equal(view.pages.length,0);h.flush()
  await respond(h.requests[2],{venues:[{id:'new'}],total:1})
  await respond(h.requests[1],{venues:[{id:'stale'}],total:99})
  view=h.render(urls[2]);assert.equal(view.pages[0].total,1);assert.equal(view.pages[0].venues[0].id,'new')
  assert.equal(h.requests[1].signal.aborted,true)
})

test('a previous search error is hidden in the render before the next effect, and retry recovers',async()=>{
  const h=harness()
  h.render('/events?radiusKm=10');h.flush();h.requests[0].reject(new Error('First search failed'));await settle()
  assert.equal(h.render('/events?radiusKm=10').error,'First search failed')
  let view=h.render('/events?radiusKm=25');assert.equal(view.error,'');assert.equal(view.pages.length,0);h.flush()
  h.requests[1].resolve({ok:false});await settle()
  view=h.render('/events?radiusKm=25');assert.match(view.error,/Could not load/)
  view.retry();h.render('/events?radiusKm=25');h.flush()
  await respond(h.requests[2],{events:[],total:0})
  view=h.render('/events?radiusKm=25');assert.equal(view.error,'');assert.equal(view.loading,false);assert.equal(view.pages[0].total,0)
})

test('load-more cannot append stale places or totals after a location change',async()=>{
  const h=harness()
  h.render('/places?location=A');h.flush();await respond(h.requests[0],{venues:[{id:'first'}],total:30})
  const more=h.render('/places?location=A').loadMore(24)
  h.render('/places?location=B');h.flush()
  await respond(h.requests[2],{venues:[{id:'new-location'}],total:1})
  await respond(h.requests[1],{venues:[{id:'old-page-two'}],total:30});await more
  const view=h.render('/places?location=B');assert.equal(view.pages.length,1);assert.equal(view.pages[0].total,1)
  assert.equal(view.pages[0].venues[0].id,'new-location')
})

test('national seed is used only for its exact URL; disabled feeds expose no results or error',async()=>{
  const h=harness(),seed={url:'/places?national',page:{venues:[{id:'UK'}],total:100}}
  let view=h.render(seed.url,true,seed);assert.equal(view.pages[0].total,100);h.flush();assert.equal(h.requests.length,0)
  view=h.render('/places?local',true,seed);assert.equal(view.pages.length,0);h.flush()
  view=h.render('/places?local',false,seed);assert.equal(view.pages.length,0);assert.equal(view.error,'');h.flush()
  assert.equal(h.requests[0].signal.aborted,true)
})

test('load-more replaces a national page offset instead of appending a duplicate',async()=>{
  const h=harness(),url='/places?q=&offset=24'
  const seed={url,page:{venues:[{id:'page-two'}],total:50}}
  h.render(url,true,seed);h.flush()
  const more=h.render(url,true,seed).loadMore(48)
  const params=new URL(h.requests[0].url,'https://example.com').searchParams
  assert.deepEqual(params.getAll('offset'),['48'])
  await respond(h.requests[0],{venues:[{id:'last-page'}],total:50});await more
  assert.equal(h.render(url,true,seed).pages[1].venues[0].id,'last-page')
})
