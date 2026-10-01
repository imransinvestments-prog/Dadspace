import Image from "next/image"

export function AuthLayout({
  eyebrow,
  title,
  intro,
  children,
}: {
  eyebrow: string
  title: string
  intro: string
  children: React.ReactNode
}) {
  return (
    <section className="animate-rise grid overflow-hidden rounded-xl border bg-card lg:grid-cols-2">
      <div className="relative hidden lg:block">
        <Image
          src="/images/hero-dad.png"
          alt=""
          fill
          sizes="(min-width: 1024px) 40vw, 0px"
          className="object-cover"
          priority
        />
        <div className="absolute inset-x-0 bottom-0 bg-navy/85 p-8 text-navy-foreground">
          <p className="font-heading text-2xl font-extrabold text-balance">The group chat your mates&apos; wives warned you about.</p>
          <p className="mt-2 text-sm leading-relaxed opacity-80">Days out, deals and dad chat, all in one place.</p>
        </div>
      </div>
      <div className="flex flex-col gap-6 p-6 sm:p-10">
        <header className="flex flex-col gap-2">
          <p className="text-sm font-semibold tracking-wide text-accent uppercase">{eyebrow}</p>
          <h1 className="font-heading text-3xl font-extrabold tracking-tight text-balance sm:text-4xl">{title}</h1>
          <p className="leading-relaxed text-pretty text-muted-foreground">{intro}</p>
        </header>
        {children}
      </div>
    </section>
  )
}
