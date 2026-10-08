"use client"
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react"
import { parsePoint } from "@/lib/distance"
export type Coords = { lat: number; lng: number }
export type LocationStatus = "idle" | "locating" | "ready" | "denied" | "unavailable"
type Value = { coords: Coords | null; status: LocationStatus; label: string; request: () => void; setLocation: (p: Coords, label?: string) => void; browseAll: boolean }
const LocationContext=createContext<Value>({coords:null,status:"idle",label:"Current location",request:()=>{},setLocation:()=>{},browseAll:false})
const KEY="dadspace-location-v2"
export const DEFAULT_LOCATION: Coords = {lat:51.5074,lng:-0.1278}
export function LocationProvider({children}:{children:React.ReactNode}) {
  const [coords,setCoords]=useState<Coords|null>(DEFAULT_LOCATION)
  const [status,setStatus]=useState<LocationStatus>("ready")
  const [label,setLabel]=useState("Central London")
  const [query,setQuery]=useState("")
  const [searching,setSearching]=useState(false)
  const [searchError,setSearchError]=useState("")
  const [results,setResults]=useState<(Coords & {label:string})[]>([])
  const searchGeneration=useRef(0)
  const generation=useRef(0)
  const setLocation=useCallback((p:Coords,name="Selected destination")=>{
    const point=parsePoint(new URLSearchParams({lat:String(p.lat),lng:String(p.lng)}))
    if(!point)return
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
        if(point){setCoords(point);setLabel(saved.label);setStatus("ready");return ()=>{generation.current++;searchGeneration.current++}}
      }
    }catch{}
    const ticket=++generation.current
    const controller=new AbortController()
    const timeout=setTimeout(()=>controller.abort(),5000)
    fetch("/api/location?estimate=1",{cache:"no-store",signal:controller.signal})
      .then(async response=>{
        if(!response.ok)return
        const data=await response.json()
        if(ticket!==generation.current||controller.signal.aborted)return
        const guess=data.location
        if(!guess||typeof guess.label!=="string")return
        const point=parsePoint(new URLSearchParams({lat:String(guess.lat),lng:String(guess.lng)}))
        if(point){setCoords(point);setLabel(guess.label);setStatus("ready")}
      })
      .catch(()=>{}) // Missing or failed estimates leave the London fallback usable.
      .finally(()=>clearTimeout(timeout))
    return ()=>{controller.abort();clearTimeout(timeout);generation.current++;searchGeneration.current++}
  },[request])
  return <LocationContext.Provider value={{coords,status,label,request,setLocation,browseAll:false}}>
    <div className="mx-auto w-full max-w-6xl px-4 pt-4 lg:pl-72">
      <section aria-label="Search location" className="rounded-xl border bg-card p-4">
        <p role="status" className="mb-3 text-sm text-muted-foreground">Showing nearby results for <strong className="text-foreground">{label}</strong>. Search a town or postcode to change area.</p>
        <form onSubmit={search} className="space-y-3">
          <label htmlFor="starting-location" className="sr-only">Town, city or UK postcode</label>
          <div className="flex flex-col gap-2 sm:flex-row">
            <input id="starting-location" type="search" value={query} maxLength={100} onChange={event=>{searchGeneration.current++;setSearching(false);setQuery(event.target.value);setResults([]);setSearchError("")}} placeholder="Search a town, city or UK postcode" autoComplete="postal-code" aria-describedby={searchError?"location-search-error":undefined} aria-invalid={!!searchError} className="min-w-0 flex-1 rounded-lg border bg-background px-3 py-3 text-base" />
            <button type="submit" disabled={searching} className="rounded-full bg-primary px-5 py-3 font-semibold text-primary-foreground disabled:opacity-50">{searching?"Searching…":"Search location"}</button>
            <button type="button" onClick={()=>{searchGeneration.current++;setSearching(false);setResults([]);setSearchError("");request()}} disabled={status==="locating"} className="rounded-full border px-4 py-3 text-sm font-semibold disabled:opacity-50">{status==="locating"?"Finding location…":"Use my location"}</button>
          </div>
          <div aria-live="polite">
            {searchError&&<p id="location-search-error" role="alert" className="text-sm text-destructive">{searchError}</p>}
            {!!results.length&&<div className="space-y-2"><p className="text-sm">Choose your location:</p>{results.map((place,index)=><button key={`${place.lat}-${place.lng}-${index}`} type="button" onClick={()=>{setLocation(place,place.label);setResults([])}} className="block w-full rounded-lg border p-3 text-left text-sm hover:bg-muted">{place.label}</button>)}</div>}
            {(status==="denied"||status==="unavailable")&&<p className="text-sm text-muted-foreground">Could not use your device location. Still showing results for {label}; search a town or postcode to change area.</p>}
          </div>
        </form>
      </section>
    </div>
    {children}
  </LocationContext.Provider>
}
export const useLocation=()=>useContext(LocationContext)
