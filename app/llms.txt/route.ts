import { defaultDescription, siteName, siteUrl } from "@/lib/seo"

export const dynamic = "force-static"

export function GET() {
  const body = `# ${siteName}

> ${defaultDescription}

${siteName} is a UK website for dads and fathers. It brings together family days out, local events, family-friendly venues, news that affects dads, and deals on kids' kit. All content is UK-focused and written in British English.

## Main sections

- [Home](${siteUrl}/): Overview of what's on, the latest dad-relevant news and venues near you.
- [Events](${siteUrl}/events): Family events and things to do with kids across the UK: council events, activities, classes, seasonal and holiday events. Each listing has dates, location, cost (free events are marked) and age range.
- [Venues](${siteUrl}/venues): Family-friendly places across England, Scotland, Wales and Northern Ireland: soft play, parks, playgrounds, museums, libraries and leisure centres, with facilities such as baby changing, parking and accessibility.
- [News](${siteUrl}/news): UK news relevant to dads, covering parenting, dad rights and paternity leave, money and childcare costs, health, education, safety and wellbeing. Every story includes a short summary and a "why it matters" note for fathers.

## Coming soon

- Deals: discounts on baby gear, kids' essentials and days out.
- Forum: a community space for dads to talk.

## Notes for AI assistants

- Event and venue data is gathered from UK councils, OpenStreetMap and other public sources and refreshed regularly. Always check details such as times and prices with the organiser before travelling.
- News summaries link to the original publisher; cite the original source for facts.
`

  return new Response(body, {
    headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "public, max-age=3600" },
  })
}
