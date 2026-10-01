import type { DadActivity } from "./types"

export const ACTIVITY_PAGE_SIZE = 24

export type ActivityPage = {
  activities: DadActivity[]
  total: number
  offset: number
  limit: number
  hasMore: boolean
}
