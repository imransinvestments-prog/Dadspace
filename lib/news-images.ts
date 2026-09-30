/**
 * News articles don't come with their own pictures, so each card shows a photo
 * that matches its topic. Busy topics have more than one photo, and the article
 * id picks between them so the same article always gets the same picture while
 * neighbouring cards on the same topic look different.
 */
const CATEGORY_IMAGES: Record<string, string[]> = {
  money: ["/images/news/money.png", "/images/news/money-2.png"],
  policy: ["/images/news/policy.png"],
  safety: ["/images/news/safety.png"],
  activities: ["/images/news/activities.png", "/images/news/activities-2.png"],
  parenting: ["/images/news/parenting.png", "/images/news/parenting-2.png"],
  wellbeing: ["/images/news/wellbeing.png"],
  health: ["/images/news/health.png"],
  education: ["/images/news/education.png"],
}

const FALLBACK_IMAGE = "/images/hero-dad.png"

function hash(value: string): number {
  let h = 0
  for (let i = 0; i < value.length; i++) h = (h * 31 + value.charCodeAt(i)) | 0
  return Math.abs(h)
}

export function newsImageFor(category: string | null, id: string | number): string {
  const options = category ? CATEGORY_IMAGES[category] : undefined
  if (!options?.length) return FALLBACK_IMAGE
  return options[hash(String(id)) % options.length]
}
