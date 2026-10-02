"use client"
import { useState } from 'react'
import { useLocation } from '@/components/location-provider'

export function LocationControls() {
  const {coords,status,request,setLocation,browseAll,showAll} = useLocation()
  const [postcode,setPostcode]=useState('')
  const [error,setError]=useState('')
  const [busy,setBusy]=useState(false)
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setError('')
    try {
      const r=await fetch('/api/location?postcode='+encodeURIComponent(postcode.trim()), {cache:'no-store'})
      if (!r.ok) throw new Error('Enter a valid UK postcode, or try again shortly.')
      const point=await r.json(); setLocation(point)
    } catch(e) {setError((e as Error).message)} finally {setBusy(false)}
  }
  return <div className="flex flex-col gap-3 rounded-xl border bg-card p-4">
    <p className="text-sm font-semibold" role="status">{coords ? 'Nearest first · approximate straight-line distances' : browseAll ? 'Browsing all UK listings. Set a location to see the nearest first.' : status==='idle'||status==='locating' ? 'Finding your location… You can also enter a postcode.' : 'Set your location to see nearby results first.'}</p>
    {(status==='denied'||status==='unavailable')&&!coords&&<p className="text-sm text-muted-foreground">{status==='denied' ? 'Location access is blocked. Enter a postcode, or allow location in your browser settings.' : 'Your device location is unavailable. Enter a postcode instead.'}</p>}
    <form onSubmit={submit} className="flex flex-wrap items-center gap-2">
      <button type="button" onClick={request} disabled={status==='locating'} className="rounded-full border px-3 py-2 text-sm font-semibold disabled:opacity-50">Use my location</button>
      <label className="sr-only" htmlFor="nearby-postcode">Your UK postcode</label>
      <input id="nearby-postcode" value={postcode} onChange={e=>setPostcode(e.target.value)} placeholder="Enter UK postcode" autoComplete="postal-code" maxLength={10} className="w-44 rounded-lg border bg-background px-3 py-2 text-sm" />
      <button disabled={busy||!postcode.trim()} className="rounded-full bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50">{busy?'Finding…':'Set location'}</button>
      <button type="button" onClick={showAll} className="px-2 py-2 text-sm underline">Browse all UK</button>
    </form>
    {error&&<p role="alert" className="text-sm text-destructive">{error}</p>}
  </div>
}
