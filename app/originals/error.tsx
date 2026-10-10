"use client"
export default function OriginalsError({ reset }: { reset: () => void }) {
  return <div role="alert" className="rounded-2xl border bg-card p-6"><h1 className="text-2xl font-bold">We couldn’t load this original</h1><button onClick={reset} className="mt-4 rounded-full bg-primary px-5 py-3 text-primary-foreground">Try again</button></div>
}
