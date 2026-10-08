import type { LiveDeal } from "./deals-selection"

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
  source_id?: string | null
  recurrence?: string | null
  category?: string | null
  is_holiday_camp?: boolean
  venue_name?: string | null
  venue_address?: string | null
  postcode?: string | null
  venue_id?: string | null
  distance_miles?: number | null
  image_url?: string | null
}

export type DadActivity = {
  distance_miles?: number | null
  id: string
  title: string
  description: string | null
  schedule_text: string | null
  time_text: string | null
  location: string | null
  event_url: string | null
  cost_text: string | null
  age_range: string | null
  family_relevance: number | null
  source_url: string | null
  source_id?: string | null
  category?: string | null
  venue_name?: string | null
  venue_address?: string | null
  postcode?: string | null
  venue_id?: string | null
  last_seen_at?: string | null
}

/** How the Home events were picked when the user's location is known. */
export type NearbyScope = "weekend" | "soon" | "nearest"

export type ForumThread = {
  id: string
  title: string
  category: string | null
  author: string | null
  comments: number
}

export type Article = {
  summary?: string | null
  why_it_matters?: string | null
  published_at?: string | null
  id: string
  title: string
  source: string | null
  url?: string | null
  category?: string | null
  relevance?: number | null
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
  events: Sourced<DadEvent[]> & { isWeekend: boolean; nearby: NearbyScope | null; radiusMiles: number }
  threads: Sourced<ForumThread[]>
  /** `pool[i]` holds the newest articles for the category shown in card `i`, newest first. */
  articles: Sourced<Article[]> & { pool?: Article[][] }
  deal: Sourced<LiveDeal | null> & { loadFailed: boolean }
}
