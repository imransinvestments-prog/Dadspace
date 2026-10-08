"use client"
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react"
import { parsePoint } from "@/lib/distance"
export type Coords = { lat: number; lng: number }
export type LocationStatus = "idle" | "locating" | "ready" | "denied" | "unavailable"
type Value = { coords: Coords | null; status: LocationStatus; label: string; request: () => void; setLocation: (p: Coords, label?: string) => void; browseAll: boolean }
const LocationContext=createContext<Value>({coords:null,status:"idle",label:"Current location",request:()=>{},setLocation:()=>{},browseAll:false})
const KEY="dadspace-location-v2"
export function LocationProvider({children}:{children:React.ReactNode}) {
  const [coords,setCoords]=useState<Coords|null>(null)
  const [status,setStatus]=useState<LocationStatus>("idle")
  const [label,setLabel]=useState("Current location")
  const [authorized,setAuthorized]=useState(false)
  const [query,setQuery]=useState("")
  const [searching,setSearching]=useState(false)
  const [searchError,setSearchError]=useState("")
  const [results,setResults]=useState<(Coords & {label:string})[]>([])
  const searchGeneration=useRef(0)
  const generation=useRef(0)
  const setLocation=useCallback((p:Coords,name="Selected destination")=>{
    const point=parsePoint(new URLSearchParams({lat:String(p.lat),lng:String(p.lng)}))
    if(!point)return
    setAuthorized(true)
    generation.current++;setCoords(point);setStatus("ready");setLabel(name)
    try {sessionStorage.setItem(KEY,JSON.stringify({point,label:name,authorized:true}))} catch {}
  },[])
  const request=useCallback(()=>{
    const ticket=++generation.current
    if(!("geolocation" in navigator)||!window.isSecureContext){setStatus("unavailable");return}
    setStatus("locating")
    navigator.geolocation.getCurrentPosition(({coords:c})=>{
      if(ticket!==generation.current)return
      const point=parsePoint(new URLSearchParams({lat:String(c.latitude),lng:String(c.longitude)}))
      if(!point){setStatus("unavailable");return}
      setLocation(point,"Current location")
    },err=>{if(ticket===generation.current)setStatus(err.code===1?"denied":"unavailable")},
    {enableHighAccuracy:false,timeout:10000,maximumAge:0})
  },[setLocation])
  const search=async (event:React.FormEvent<HTMLFormElement>)=>{
    event.preventDefault()
    const ticket=++searchGeneration.current
    const value=query.trim()
    setResults([]);setSearchError("")
    if(value.length<2){setSearchError("Enter a town, city or full UK postcode.");return}
    setSearching(true)
    try {
      const response=await fetch("/api/location?q="+encodeURIComponent(value),{signal:AbortSignal.timeout(10000)})
      const data=await response.json()
      if(ticket!==searchGeneration.current)return
      if(!response.ok)throw new Error(data.error||"Location lookup unavailable. Please try again.")
      const matches=Array.isArray(data.results)?data.results.filter((p:Coords & {label:string})=>typeof p.label==="string"&&parsePoint(new URLSearchParams({lat:String(p.lat),lng:String(p.lng)}))):[]
      if(!matches.length){setSearchError("Location not found. Try another town or postcode.");return}
      if(matches.length===1)setLocation(matches[0],matches[0].label)
      else setResults(matches)
    }catch(error){if(ticket===searchGeneration.current)setSearchError(error instanceof Error&&error.name!=="TimeoutError"?error.message:"Location lookup unavailable. Please try again.")}
    finally{if(ticket===searchGeneration.current)setSearching(false)}
  }
  useEffect(()=>{
    try {
      const saved=JSON.parse(sessionStorage.getItem(KEY)||"null")
      if(saved?.authorized&&typeof saved.label==="string"){
        const point=parsePoint(new URLSearchParams({lat:String(saved.point?.lat),lng:String(saved.point?.lng)}))
        if(point){setAuthorized(true);setCoords(point);setLabel(saved.label);setStatus("ready")}
      }
    }catch{}
    return ()=>{generation.current++;searchGeneration.current++}
  },[request])
  return <LocationContext.Provider value={{coords,status,label,request,setLocation,browseAll:false}}>
    {authorized ? children : <main className="flex min-h-dvh items-center justify-center px-4 py-10">
      <section aria-labelledby="location-title" className="w-full max-w-md rounded-2xl border bg-card p-6 shadow-sm">
        <p className="mb-3 text-sm font-semibold text-primary">Dadspace</p>
        <h1 id="location-title" className="text-2xl font-bold">Find your starting location</h1>
        <p className="mt-3 text-muted-foreground">Find activities and days out near you. Use your device location or enter a town, city or UK postcode to continue.</p>
        <p className="mt-3 text-sm text-muted-foreground">You can search manually without sharing your device location.</p>
        <div aria-live="polite" className="mt-4 text-sm">
          {status==="locating"&&<p>Finding your location…</p>}
          {status==="denied"&&<p>Location access is blocked. Enter a town or postcode below to continue, or allow location in your browser’s site settings and try again.</p>}
          {status==="unavailable"&&<p>Your device location is unavailable. Enter a town or postcode below to continue.</p>}
        </div>
        <button type="button" onClick={request} disabled={status==="locating"} className="mt-5 w-full rounded-full bg-primary px-4 py-3 font-semibold text-primary-foreground disabled:opacity-50">{status==="locating"?"Finding location…":status==="denied"||status==="unavailable"?"Try again":"Allow location and continue"}</button>
        <div className="my-5 text-center text-sm text-muted-foreground">or enter a location manually</div>
        <form onSubmit={search} className="space-y-3">
          <label htmlFor="starting-location" className="block text-sm font-semibold">Town, city or UK postcode</label>
          <input id="starting-location" value={query} maxLength={100} onChange={event=>{searchGeneration.current++;setSearching(false);setQuery(event.target.value);setResults([]);setSearchError("")}} placeholder="e.g. Manchester or SW1A 1AA" autoComplete="postal-code" aria-describedby={searchError?"location-search-error":undefined} aria-invalid={!!searchError} className="w-full rounded-lg border bg-background px-3 py-3 text-base" />
          <button type="submit" disabled={searching} className="w-full rounded-full border px-4 py-3 font-semibold disabled:opacity-50">{searching?"Searching…":"Find location and continue"}</button>
          <div aria-live="polite">
            {searchError&&<p id="location-search-error" role="alert" className="text-sm text-destructive">{searchError}</p>}
            {!!results.length&&<div className="space-y-2"><p className="text-sm">Choose your location:</p>{results.map((place,index)=><button key={`${place.lat}-${place.lng}-${index}`} type="button" onClick={()=>setLocation(place,place.label)} className="block w-full rounded-lg border p-3 text-left text-sm hover:bg-muted">{place.label}</button>)}</div>}
          </div>
        </form>
      </section>
    </main>}
  </LocationContext.Provider>
}
export const useLocation=()=>useContext(LocationContext)
