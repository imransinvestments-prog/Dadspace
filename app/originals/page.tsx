import Link from "next/link"
import { getOriginals, originalDate } from "@/lib/originals"
import { pageMetadata } from "@/lib/seo"

export const metadata = pageMetadata("Originals", "/originals", "Fresh ideas for family life: a small daily tip and a longer Friday weekend guide from Dadspace.")
export const dynamic = "force-dynamic"

export default async function OriginalsPage({ searchParams }: { searchParams: Promise<{ type?: string }> }) {
  const { type } = await searchParams
  const cadence = type === "daily" || type === "weekly" ? type : undefined
  let posts: Awaited<ReturnType<typeof getOriginals>> = []
  let unavailable = false
  try { posts = await getOriginals(cadence) } catch { unavailable = true }
  return <div className="space-y-8">
    <header className="rounded-3xl bg-primary p-6 text-primary-foreground sm:p-10">
      <p className="text-sm font-semibold uppercase tracking-widest">Dadspace Originals</p>
      <h1 className="mt-3 font-heading text-4xl font-bold sm:text-5xl">Small ideas. More family time.</h1>
      <p className="mt-4 max-w-2xl text-lg">A useful idea for today, and a little inspiration for the weekend. Written for the everyday adventures of being a dad.</p>
      <p className="mt-5 text-sm">Daily tips · Friday weekend guides</p>
    </header>
    <nav aria-label="Original content filters" className="flex flex-wrap gap-2">
      {[[undefined, "All originals"], ["daily", "Daily tips"], ["weekly", "Weekend guides"]].map(([value, label]) => <Link key={label} href={value ? `/originals?type=${value}` : "/originals"} aria-current={cadence === value ? "page" : undefined} className={`rounded-full border px-5 py-3 font-semibold ${cadence === value ? "bg-primary text-primary-foreground" : "bg-card hover:bg-muted"}`}>{label}</Link>)}
    </nav>
    {unavailable ? <div role="status" className="rounded-2xl border bg-card p-6"><p>Originals are temporarily unavailable.</p><Link href={cadence ? `/originals?type=${cadence}` : "/originals"} className="mt-3 inline-block underline">Try again</Link></div> : !posts.length ? <p className="rounded-2xl border bg-card p-6">Fresh originals are on their way. Check back soon.</p> : <div className="grid gap-5 md:grid-cols-2">
      {posts.map(post => <article key={post.slug} className="flex flex-col rounded-3xl border bg-card p-6 sm:p-8">
        <p className="text-sm font-semibold text-accent">{post.cadence === "daily" ? "Daily tip" : "Weekend guide"} · <time dateTime={post.published_at}>{originalDate(post.published_at)}</time></p>
        <h2 className="mt-3 font-heading text-2xl font-bold"><Link href={`/originals/${post.slug}`} className="hover:underline">{post.title}</Link></h2>
        <p className="mt-3 text-muted-foreground">{post.summary}</p>
        <Link href={`/originals/${post.slug}`} className="mt-auto pt-6 font-semibold text-accent">Read {post.cadence === "daily" ? "the tip" : "the guide"}<span className="sr-only">: {post.title}</span> →</Link>
      </article>)}
    </div>}
    <p className="text-sm text-muted-foreground">Original content created for Dadspace with AI assistance. Practical inspiration for families; choose what suits your children.</p>
  </div>
}
