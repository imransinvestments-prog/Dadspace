import { NextResponse } from 'next/server'
export const dynamic='force-dynamic'
export async function GET(request: Request) {
  const postcode=(new URL(request.url).searchParams.get('postcode')||'').replace(/\s/g,'').toUpperCase()
  if(!/^[A-Z]{1,2}\d[A-Z\d]?\d[A-Z]{2}$/.test(postcode)) return NextResponse.json({error:'Invalid postcode'},{status:400})
  try {
    const response=await fetch('https://api.postcodes.io/postcodes/'+encodeURIComponent(postcode),{cache:'no-store',signal:AbortSignal.timeout(5000)})
    const data=await response.json()
    if(!response.ok||!data.result||typeof data.result.latitude!=='number'||typeof data.result.longitude!=='number') return NextResponse.json({error:'Postcode not found'},{status:404})
    return NextResponse.json({lat:Math.round(data.result.latitude*100)/100,lng:Math.round(data.result.longitude*100)/100},{headers:{'Cache-Control':'private, no-store'}})
  } catch {return NextResponse.json({error:'Location lookup unavailable'},{status:503})}
}
