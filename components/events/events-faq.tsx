const FAQS = [
  {
    q: "Where do these family events come from?",
    a: "Dadspace collects listings every day from UK council, library and leisure centre websites, plus venues and activity providers. Each card links to the original page so you can check details and book.",
  },
  {
    q: "How do I find free things to do with kids this weekend?",
    a: "Choose “This weekend” and “Free only” in the filters above. Many library story times, rhyme times, parkruns and council family days are free, though some still ask you to book a place.",
  },
  {
    q: "What ages are the events for?",
    a: "Most listings are for babies to under-12s. Where the organiser gives an age range it's shown on the card, and you can search for an age such as “toddler” or “0-5”.",
  },
  {
    q: "How often is the list updated?",
    a: "New events are added daily and past events drop off automatically, so everything shown is today or later.",
  },
]

export function EventsFaq() {
  const schema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: FAQS.map(({ q, a }) => ({ "@type": "Question", name: q, acceptedAnswer: { "@type": "Answer", text: a } })),
  }

  return (
    <section aria-labelledby="events-faq" className="flex flex-col gap-4 rounded-2xl border bg-card p-6 md:p-8">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema).replace(/</g, "\\u003c") }} />
      <h2 id="events-faq" className="font-heading text-2xl font-extrabold">
        Family events: common questions
      </h2>
      <div className="grid gap-x-8 gap-y-5 md:grid-cols-2">
        {FAQS.map(({ q, a }) => (
          <div key={q} className="flex flex-col gap-1.5">
            <h3 className="font-heading font-bold">{q}</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">{a}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
