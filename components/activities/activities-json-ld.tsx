import { JsonLd } from "@/components/seo/json-ld"
import { activitySlug } from "@/lib/activity-slug"
import { siteUrl } from "@/lib/seo"
import type { DadActivity } from "@/lib/types"
export function ActivitiesJsonLd({ activities }: { activities: DadActivity[] }) {
  return <JsonLd data={{ "@context": "https://schema.org", "@type": "CollectionPage", "@id": `${siteUrl}/activities#page`, url: `${siteUrl}/activities`, name: "Activities, classes and clubs", mainEntity: { "@type": "ItemList", numberOfItems: activities.length, itemListElement: activities.map((a,i) => ({ "@type": "ListItem", position: i+1, item: { "@type": "Thing", "@id": `${siteUrl}/activities/${activitySlug(a)}#activity`, name: a.title, url: `${siteUrl}/activities/${activitySlug(a)}` } })) } }} />
}
