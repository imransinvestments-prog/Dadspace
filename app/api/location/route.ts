import { NextResponse } from "next/server"
import { parsePoint } from "@/lib/distance"
export const dynamic="force-dynamic"
const headers={"Cache-Control":"private, no-store"}
export async function GET(request:Request) {
  const params=new URL(request.url).searchParams
  const query=(params.get("q")||params.get("postcode")||"").trim()
  if (query.length<2||query.length>100) return NextResponse.json({error:"Enter a town, city or full UK postcode."},{status:400,headers})
  const postcode=query.replace(/\s/g,"").toUpperCase()
  const isPostcode=/^[A-Z]{1,2}\d[A-Z\d]?\d[A-Z]{2}$/.test(postcode)
  const legacyPostcode=!params.has("q")&&params.has("postcode")
  if(legacyPostcode&&!isPostcode)return NextResponse.json({error:"Invalid postcode"},{status:400,headers})
  try {
    const url=isPostcode ? "https://api.postcodes.io/postcodes/"+encodeURIComponent(postcode) : "https://api.postcodes.io/places?q="+encodeURIComponent(query)+"&limit=10"
    const response=await fetch(url,{cache:"no-store",signal:AbortSignal.timeout(5000)})
    if (!response.ok) return NextResponse.json({error:response.status===404?"Location not found. Try another town or postcode.":"Location lookup unavailable. Try again shortly."},{status:response.status===404?404:503,headers})
    const data=await response.json()
    const entries=isPostcode ? [data.result] : data.result
    if (!Array.isArray(entries)) throw new Error("Invalid lookup response")
    const results=entries.flatMap((p)=>{
      if (!p || typeof p.latitude!=="number" || typeof p.longitude!=="number") return []
      const point=parsePoint(new URLSearchParams({lat:String(p.latitude),lng:String(p.longitude)}))
      const name=isPostcode?p.postcode:p.name_1
      if (!point||typeof name!=="string") return []
      return [{...point,label:isPostcode?name:[name,p.county_unitary||p.district_borough,p.country].filter(Boolean).join(", ")}]
    })
    // Keep the legacy postcode response compatible with older callers.
    if (legacyPostcode) {
      if (!results.length) return NextResponse.json({error:"Postcode not found"},{status:404,headers})
      return NextResponse.json({lat:results[0].lat,lng:results[0].lng},{headers})
    }
    return NextResponse.json({results},{headers})
  } catch {return NextResponse.json({error:"Location lookup unavailable. Try again shortly."},{status:503,headers})}
}
