"use client"
import { useEffect, useRef, useState } from 'react'

/** A location/filter change hides the previous page immediately and cancels stale requests. */
export function useDirectoryPage<T>(url:string,enabled:boolean,seed?:{url:string;page:T;error?:string}){
  const [state,setState]=useState<{url:string;pages:T[]}>({url:seed?.url??'',pages:seed?[seed.page]:[]})
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState(seed?.error??'')
  const [retry,setRetry]=useState(0)
  const controller=useRef<AbortController|null>(null)
  const busy=useRef(false)
  useEffect(()=>{
    if(!enabled)return
    if(seed&&url===seed.url&&retry===0){
      const c=new AbortController();controller.current=c;busy.current=false
      setState({url,pages:[seed.page]});setLoading(false);setError(seed.error??'')
      return ()=>c.abort()
    }
    const c=new AbortController();controller.current=c
    setState({url,pages:[]});setLoading(true);setError('');busy.current=true
    const timer=setTimeout(async()=>{
      try{
        const r=await fetch(url,{signal:c.signal,cache:'no-store'})
        if(!r.ok)throw new Error('Could not load results. Please try again.')
        const page=await r.json() as T
        if(!c.signal.aborted)setState({url,pages:[page]})
      }catch(e){if(!c.signal.aborted)setError((e as Error).message)}
      finally{if(!c.signal.aborted){setLoading(false);busy.current=false}}
    },200)
    return ()=>{clearTimeout(timer);c.abort()}
  },[url,enabled,retry])
  async function loadMore(offset:number){
    if(busy.current||!controller.current||controller.current.signal.aborted)return
    const c=controller.current;busy.current=true;setLoading(true);setError('')
    try{
      const separator=url.includes('?')?'&':'?'
      const r=await fetch(`${url}${separator}offset=${offset}`,{signal:c.signal,cache:'no-store'})
      if(!r.ok)throw new Error('Could not load more results. Please try again.')
      const page=await r.json() as T
      if(!c.signal.aborted)setState(s=>s.url===url?{url,pages:[...s.pages,page]}:s)
    }catch(e){if(!c.signal.aborted)setError((e as Error).message)}
    finally{if(!c.signal.aborted){setLoading(false);busy.current=false}}
  }
  const pages=enabled&&state.url===url?state.pages:[]
  return {pages,loading:enabled&&(loading||state.url!==url),error,loadMore,retry:()=>setRetry(n=>n+1)}
}
