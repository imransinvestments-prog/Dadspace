import Link from "next/link"

export function ComingSoon({ title, joke }: { title: string; joke: string }) {
  return (
    <section className="animate-rise flex flex-col items-start gap-4 rounded-xl border bg-card p-8 md:p-12">
      <p className="text-sm font-semibold tracking-wide text-accent uppercase">Under construction</p>
      <h1 className="font-heading text-4xl font-extrabold tracking-tight text-balance">{title}</h1>
      <p className="max-w-prose text-lg leading-relaxed text-muted-foreground">{joke}</p>
      <Link href="/" className="inline-flex h-12 items-center rounded-full bg-primary px-6 font-semibold text-primary-foreground">
        Back to Home
      </Link>
    </section>
  )
}
