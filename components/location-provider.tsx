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
  const authorizedRef=useRef(false)
  const generation=useRef(0)
  const setLocation=useCallback((p:Coords,name="Selected destination")=>{
    if(!authorizedRef.current)return
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
      authorizedRef.current=true;setAuthorized(true);setLocation(point,"Current location")
    },err=>{if(ticket===generation.current)setStatus(err.code===1?"denied":"unavailable")},
    {enableHighAccuracy:false,timeout:10000,maximumAge:0})
  },[setLocation])
  useEffect(()=>{
    try {
      const saved=JSON.parse(sessionStorage.getItem(KEY)||"null")
      if(saved?.authorized&&typeof saved.label==="string"){
        const point=parsePoint(new URLSearchParams({lat:String(saved.point?.lat),lng:String(saved.point?.lng)}))
        if(point){authorizedRef.current=true;setAuthorized(true);setCoords(point);setLabel(saved.label);setStatus("ready")}
      }
    }catch{}
    return ()=>{generation.current++}
  },[request])
  return <LocationContext.Provider value={{coords,status,label,request,setLocation,browseAll:false}}>
    {authorized ? children : <main className="flex min-h-dvh items-center justify-center px-4 py-10">
      <section aria-labelledby="location-title" className="w-full max-w-md rounded-2xl border bg-card p-6 shadow-sm">
        <p className="mb-3 text-sm font-semibold text-primary">Dadspace</p>
        <h1 id="location-title" className="text-2xl font-bold">Find your starting location</h1>
        <p className="mt-3 text-muted-foreground">Allow location access to find activities and days out near you. Once inside, you can search another town or postcode you plan to visit.</p>
        <p className="mt-3 text-sm text-muted-foreground">Location access is required to begin each browser session. We use an approximate location for nearby results.</p>
        <div aria-live="polite" className="mt-4 text-sm">
          {status==="locating"&&<p>Finding your location…</p>}
          {status==="denied"&&<p>Location access is blocked. Allow location for Dadspace in your browser’s site settings, then try again.</p>}
          {status==="unavailable"&&<p>Your device location is unavailable. Check location services and your connection, then try again.</p>}
        </div>
        <button type="button" onClick={request} disabled={status==="locating"} className="mt-5 w-full rounded-full bg-primary px-4 py-3 font-semibold text-primary-foreground disabled:opacity-50">{status==="locating"?"Finding location…":status==="denied"||status==="unavailable"?"Try again":"Allow location and continue"}</button>
      </section>
    </main>}
  </LocationContext.Provider>
}
export const useLocation=()=>useContext(LocationContext)
