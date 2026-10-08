/** Round one is each category's nearest place, round two its next nearest, etc. */
export function interleavePlaces<T extends { id: string }>(groups: T[][]): T[] {
  const places: T[] = []
  const seen = new Set<string>()
  const rounds = Math.max(0, ...groups.map((group) => group.length))
  for (let round = 0; round < rounds; round++) {
    for (const group of groups) {
      const place = group[round]
      if (place && !seen.has(place.id)) {
        seen.add(place.id)
        places.push(place)
      }
    }
  }
  return places
}
