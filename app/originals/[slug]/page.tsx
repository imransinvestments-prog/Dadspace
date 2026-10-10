import Link from "next/link"
import { notFound } from "next/navigation"
import { getOriginal, originalDate } from "@/lib/originals"
import { pageMetadata, siteUrl } from "@/lib/seo"

export const dynamic = "force-dynamic"
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const post = await getOriginal(slug)
  return post ? pageMetadata(post.title, `/originals/${post.slug}`, post.summary) : pageMetadata("Original not found", "/originals", "Dadspace Originals", { noIndex: true })
}
export default async function OriginalPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const post = await getOriginal(slug)
  if (!post) notFound()
  const jsonLd = { "@context": "https://schema.org", "@type": "Article", headline: post.title, description: post.summary, datePublished: post.published_at, author: { "@type": "Organization", name: "Dadspace" }, mainEntityOfPage: `${siteUrl}/originals/${post.slug}` }
  return <article className="mx-auto w-full max-w-3xl space-y-7 pb-8">
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />
    <Link href="/originals" className="inline-block font-semibold text-accent">← All originals</Link>
    <header className="space-y-4">
      <p className="text-sm font-semibold text-accent">{post.cadence === "daily" ? "Daily tip" : "Weekend guide"} · <time dateTime={post.published_at}>{originalDate(post.published_at)}</time></p>
      <h1 className="font-heading text-4xl font-bold sm:text-5xl">{post.title}</h1>
      <p className="text-xl text-muted-foreground">{post.summary}</p>
      <p className="text-sm text-muted-foreground">By Dadspace · Created with AI assistance</p>
    </header>
    {post.sections.map((section, index) => <section key={index} className="space-y-4">
      <h2 className="font-heading text-2xl font-bold">{section.heading}</h2>
      {section.paragraphs.map((paragraph, i) => <p key={i} className="text-lg leading-relaxed">{paragraph}</p>)}
    </section>)}
    <aside className="rounded-2xl border bg-card p-6"><p className="font-semibold">Make it your own</p><p className="mt-2 text-muted-foreground">Adapt these ideas to your child’s age, interests and needs.</p><Link href="/activities" className="mt-4 inline-block font-semibold text-accent">Find family activities →</Link></aside>
  </article>
}
