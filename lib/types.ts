export type DadEvent = {
  id: string
  title: string
  description: string | null
  start_date: string
  end_date: string | null
  time_text: string | null
  location: string | null
  event_url: string | null
  cost_text: string | null
  age_range: string | null
  family_relevance: number | null
  source_url: string | null
}

export type ForumThread = {
  id: string
  title: string
  category: string | null
  author: string | null
  comments: number
}

export type Article = {
  id: string
  title: string
  source: string | null
}

export type Deal = {
  id: string
  title: string
  retailer: string
  price: number
  oldPrice: number
  image: string
  category: string
  url: string
}

export type Sourced<T> = { items: T; isSample: boolean }

export type HomeData = {
  greeting: string
  sleepsToWeekend: number
  weekendLabel: string
  events: Sourced<DadEvent[]> & { isWeekend: boolean }
  threads: Sourced<ForumThread[]>
  articles: Sourced<Article[]>
  deal: Sourced<Deal>
}
