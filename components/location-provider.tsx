"use client"
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react"
import { parsePoint } from "@/lib/distance"
export type Coords = { lat: number; lng: number }
export type LocationStatus = "idle" | "locating" | "ready" | "denied" | "unavailable"
type Value = { coords: Coords | null; status: LocationStatus; request: () => void; setLocation: (p: Coords) => void; browseAll: boolean; showAll: () => void }
const LocationContext=createContext<Value>({coords:null,status:"idle",request:()=>{},setLocation:()=>{},browseAll:false,showAll:()=>{}})
const KEY="dadspace-location-v1"
export function LocationProvider({children}:{children:React.ReactNode}) {
  const [coords,setCoords]=useState<Coords|null>(null)
  const [status,setStatus]=useState<LocationStatus>("idle")
  const [browseAll,setBrowseAll]=useState(false)
  const generation=useRef(0)
  const setLocation=useCallback((p:Coords)=>{
    const point=parsePoint(new URLSearchParams({lat:String(p.lat),lng:String(p.lng)}))
    if(!point)return
    generation.current++;setCoords(point);setStatus("ready");setBrowseAll(false)
    try {sessionStorage.setItem(KEY,JSON.stringify({point,at:Date.now()}))} catch {}
  },[])
  const showAll=useCallback(()=>{
    generation.current++;setCoords(null);setStatus("idle");setBrowseAll(true)
    try{sessionStorage.setItem(KEY,JSON.stringify({all:true,at:Date.now()}))}catch{}
  },[])
  const request=useCallback(()=>{
    const ticket=++generation.current
    setBrowseAll(false)
    if(!("geolocation" in navigator)||!window.isSecureContext){setStatus("unavailable");return}
    setStatus("locating")
    navigator.geolocation.getCurrentPosition(({coords:c})=>{
      if(ticket===generation.current)setLocation({lat:c.latitude,lng:c.longitude})
    },err=>{if(ticket===generation.current)setStatus(err.code===1?"denied":"unavailable")},
    {enableHighAccuracy:false,timeout:8000,maximumAge:30*60*1000})
  },[setLocation])
  useEffect(()=>{
    try {
      const saved=JSON.parse(sessionStorage.getItem(KEY)||"null")
      if(saved&&Date.now()-saved.at>=0&&Date.now()-saved.at<30*60*1000){
        if(saved.all){setBrowseAll(true);return}
        const point=parsePoint(new URLSearchParams({lat:String(saved.point?.lat),lng:String(saved.point?.lng)}))
        if(point){setCoords(point);setStatus("ready");return}
      }
    }catch{}
    request()
    return ()=>{generation.current++}
  },[request])
  return <LocationContext.Provider value={{coords,status,request,setLocation,browseAll,showAll}}>{children}</LocationContext.Provider>
}
export const useLocation=()=>useContext(LocationContext)
