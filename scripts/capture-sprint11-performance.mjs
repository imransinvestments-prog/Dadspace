import fs from 'node:fs'
import { createRequire } from 'node:module'
import { pathToFileURL } from 'node:url'
const require=createRequire(new URL('../review/lighthouse-runtime/package.json',import.meta.url))
const {default:lighthouse}=await import(pathToFileURL(require.resolve('lighthouse')).href)
const lighthouseRequire=createRequire(require.resolve('lighthouse'))
const {launch}=await import(pathToFileURL(lighthouseRequire.resolve('chrome-launcher')).href)
const origin=process.env.SPRINT11_ORIGIN || 'https://www.dad-space.co.uk'
const sha=process.env.SPRINT11_SHA
if(!/^[a-f0-9]{40}$/.test(sha||''))throw new Error('Set the verified deployed SHA')
const routes=['/','/venues','/venues/hounslow-library--44edbcfa-3c4b-42dc-82ba-fd973dab751a','/places/hounslow/libraries']
const output={captured_at:new Date().toISOString(),origin,deployed_sha:sha,lighthouse:'13.0.1',method:'Separate headless Chrome launch per run; Lighthouse default simulated throttling, clean storage; 3 runs per route/device. Lab observations, not CrUX or INP acceptance.',runs:[],medians:[]}
const outputPath=process.env.SPRINT11_OUTPUT || 'artefacts/data/sprint11-performance.json'
const reportDirectory=process.env.SPRINT11_REPORT_DIRECTORY || 'review/lighthouse'
fs.mkdirSync(reportDirectory,{recursive:true})
const save=()=>fs.writeFileSync(outputPath,JSON.stringify(output,null,2)+'\n')
for(const route of routes)for(const device of ['mobile','desktop']){
 const group=[]
 for(let run=1;run<=3;run++){
  let chrome
  try{
   chrome=await launch({chromePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',chromeFlags:['--headless=new','--no-first-run','--disable-extensions']})
   const result=await lighthouse(origin+route,{port:chrome.port,onlyCategories:['performance','accessibility','best-practices','seo'],output:'json',logLevel:'error',...(device==='desktop'?{formFactor:'desktop',screenEmulation:{mobile:false,width:1350,height:940,deviceScaleFactor:1,disabled:false},throttling:{rttMs:40,throughputKbps:10240,cpuSlowdownMultiplier:1}}:{})})
   const lhr=result.lhr
   const row={route,device,run,requested_url:lhr.requestedUrl,final_url:lhr.finalDisplayedUrl,runtime_error:lhr.runtimeError||null,warnings:lhr.runWarnings,conditions:lhr.configSettings,performance:lhr.categories.performance.score,lcp_ms:lhr.audits['largest-contentful-paint'].numericValue,cls:lhr.audits['cumulative-layout-shift'].numericValue,tbt_ms:lhr.audits['total-blocking-time'].numericValue,seo:lhr.categories.seo.score,accessibility:lhr.categories.accessibility.score}
   group.push(row);output.runs.push(row)
   fs.writeFileSync(`${reportDirectory}/${routes.indexOf(route)}-${device}-${run}.json`,result.report)
   console.log(JSON.stringify({route,device,run,lcp_ms:row.lcp_ms,cls:row.cls,error:row.runtime_error}))
  }catch(e){output.runs.push({route,device,run,error:String(e)})}
  finally{if(chrome)await chrome.kill();save()}
 }
 const median=key=>{const values=group.filter(x=>!x.runtime_error&&Number.isFinite(x[key])).map(x=>x[key]).sort((a,b)=>a-b);return values.length===3?values[1]:null}
 output.medians.push({route,device,successful_runs:group.filter(x=>!x.runtime_error).length,lcp_ms:median('lcp_ms'),cls:median('cls'),tbt_ms:median('tbt_ms'),performance:median('performance')});save()
}
