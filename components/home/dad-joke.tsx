"use client"

import { useEffect, useState } from "react"
import { MessageCircleMore, Shuffle } from "lucide-react"
import { DAD_JOKES, randomJokeIndex } from "@/lib/dad-jokes"

export function DadJoke() {
  const [index, setIndex] = useState(0)
  // Keep server and first client render identical, then randomise on arrival.
  useEffect(() => { setIndex(Math.floor(Math.random() * DAD_JOKES.length)) }, [])
  const joke = DAD_JOKES[index]

  return (
    <section aria-labelledby="dad-joke-title" className="flex min-w-0 flex-col gap-5 rounded-xl border border-highlight/40 bg-highlight/10 p-6 text-foreground dark:border-border dark:bg-card">
      <div className="flex items-center gap-3">
        <MessageCircleMore className="size-8 shrink-0 text-primary" aria-hidden />
        <p className="text-xs font-bold tracking-wide text-muted-foreground uppercase">Dad joke break</p>
      </div>
      <h2 id="dad-joke-title" className="font-heading text-2xl leading-tight font-extrabold tracking-tight">Certified groan-worthy.</h2>
      <div role="status" aria-live="polite" aria-atomic="true" className="flex min-h-32 flex-1 flex-col gap-4">
        <p className="text-base leading-relaxed">{joke.question}</p>
        <p className="font-heading text-xl leading-snug font-bold">{joke.punchline}</p>
      </div>
      <div className="mt-auto flex flex-col gap-4">
        <p className="text-sm text-muted-foreground">Fresh jokes. Familiar eye-rolls.</p>
        <button type="button" onClick={() => setIndex((current) => randomJokeIndex(current))} className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-full bg-navy px-4 py-3 text-sm font-bold text-navy-foreground transition hover:bg-navy/85 dark:bg-primary dark:text-primary-foreground dark:hover:bg-primary/90">
          <Shuffle className="size-4 shrink-0" aria-hidden />
          Another dad joke
        </button>
      </div>
    </section>
  )
}
