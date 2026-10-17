// HTTP measurements for optimizer candidates; these are not emulated-device results.
import {createRequire} from 'node:module'
import {writeFile} from 'node:fs/promises'
const require=createRequire(import.meta.url)
const {getImageProps}=require('next/image')
const sharp=createRequire(require.resolve('next/package.json'))('sharp')
const origin=new URL(process.argv[2])
if(origin.protocol!=='https:') throw Error('HTTPS preview origin required')
const cases=[
  {name:'category-tile',src:'/images/venues/playground.png',width:128,sizes:'(min-width: 768px) 144px, 128px'},
  {name:'home-hero',src:'/images/hero-dad.png',width:358,sizes:'(min-width: 1280px) 540px, (min-width: 1024px) calc(100vw - 336px), (min-width: 768px) 60vw, calc(100vw - 32px)'},
  {name:'place-detail-fallback',src:'/images/venues/playground.png',width:358,sizes:'(min-width: 768px) 480px, calc(100vw - 32px)'},
]
const output={observedAt:new Date().toISOString(),origin:origin.origin,commit:process.argv[4]??null,viewport:390,method:'Fetch/decode DPR candidate URLs from srcset; not browser DPR emulation',images:[]}
for(const sample of cases){
  const {props}=getImageProps({src:sample.src,alt:'',fill:true,sizes:sample.sizes})
  const candidates=props.srcSet.split(', ').map(entry=>({url:entry.split(' ')[0],width:Number(entry.split(' ')[1].slice(0,-1))}))
  for(const dpr of [1,2,3]){
    const candidate=candidates.find(c=>c.width>=sample.width*dpr)??candidates.at(-1)
    const url=new URL(candidate.url,origin);url.searchParams.set('q','60')
    const response=await fetch(url,{headers:{Accept:'image/avif,image/webp,image/*;q=0.8'},signal:AbortSignal.timeout(30000)})
    if(!response.ok)throw Error(`Image HTTP ${response.status}: ${url}`)
    const bytes=Buffer.from(await response.arrayBuffer()),metadata=await sharp(bytes).metadata()
    output.images.push({...sample,dpr,candidateWidth:candidate.width,url:url.href,contentType:response.headers.get('content-type'),encodedWidth:metadata.width,encodedHeight:metadata.height,encodedBytes:bytes.length,loading:props.loading})
  }
}
await writeFile(process.argv[3],JSON.stringify(output,null,2)+'\n')
console.log(JSON.stringify({images:output.images.length,output:process.argv[3]}))
