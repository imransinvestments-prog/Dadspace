"use client"
import { useEffect, useId, useRef, useState } from "react"
import { useLocation, type Coords } from "@/components/location-provider"
type Destination = Coords & { label: string }
export function LocationControls() {
  const {status,label,request,setLocation} = useLocation()
  const id=useId()
  const [query,setQuery]=useState("")
  const [results,setResults]=useState<Destination[]>([])
  const [error,setError]=useState("")
  const [busy,setBusy]=useState(false)
  const lookup=useRef<AbortController|null>(null)
  useEffect(()=>()=>{lookup.current?.abort();lookup.current=null},[])
  function cancel() {lookup.current?.abort();lookup.current=null;setBusy(false)}
  async function submit(e:React.FormEvent) {
    e.preventDefault(); cancel()
    const controller=new AbortController();lookup.current=controller
    setBusy(true);setError("");setResults([])
    try {
      const r=await fetch("/api/location?q="+encodeURIComponent(query.trim()),{cache:"no-store",signal:controller.signal})
      const data=await r.json()
      if (!r.ok) throw new Error(data.error||"Location lookup unavailable. Try again.")
      if (lookup.current===controller) {
        setResults(data.results)
        if (!data.results.length) setError("No matching location found. Try a town name or full UK postcode.")
      }
    } catch(e) {if(lookup.current===controller&&!controller.signal.aborted)setError((e as Error).message)}
    finally {if(lookup.current===controller){lookup.current=null;setBusy(false)}}
  }
  return <div className="flex flex-col gap-3 rounded-xl border bg-card p-4">
    <p role="status" className="text-sm font-semibold">Searching near {label} · nearest first</p>
    <form onSubmit={submit} className="flex flex-wrap items-end gap-2">
      <div className="flex flex-col gap-1">
        <label htmlFor={id} className="text-sm font-medium">Search location</label>
        <input id={id} value={query} onChange={e=>{cancel();setQuery(e.target.value);setResults([]);setError("")}} placeholder="Town, city or UK postcode" maxLength={100} className="w-full rounded-lg border bg-background px-3 py-2 text-sm sm:w-64" />
      </div>
      <button disabled={busy||!query.trim()} className="rounded-full bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50">{busy?"Finding…":"Find location"}</button>
      <button type="button" onClick={()=>{cancel();setResults([]);setQuery("");setError("");request()}} disabled={status==="locating"} className="rounded-full border px-3 py-2 text-sm font-semibold disabled:opacity-50">{status==="locating"?"Finding location…":"Use my current location"}</button>
    </form>
    <p className="text-xs text-muted-foreground">Choose a destination to update nearby results across Dadspace. Distances are approximate straight-line distances.</p>
    {!!results.length && <ul aria-label="Matching locations" className="flex flex-col gap-2">{results.map((p,i)=><li key={`${p.label}-${i}`}><button type="button" onClick={()=>{setLocation(p,p.label);setResults([]);setQuery("")}} className="w-full rounded-lg border px-3 py-2 text-left text-sm hover:bg-muted">Search near {p.label}</button></li>)}</ul>}
    {error&&<p role="alert" className="text-sm text-destructive">{error}</p>}
    {(status==="denied"||status==="unavailable")&&<p role="alert" className="text-sm text-destructive">Could not use your device location. Your selected search area is unchanged. Check location permission and try again.</p>}
  </div>
}
