import type { Article, DadEvent, Deal, ForumThread } from "./types"

export function sampleEvents(saturday: string, sunday: string): DadEvent[] {
  return [
    {
      id: "sample-1",
      title: "Woodland Wellies Nature Trail",
      description: "A self-guided autumn trail with a spotter sheet, mud kitchen and hot chocolate stall.",
      start_date: saturday,
      end_date: sunday,
      time_text: "10am – 3pm",
      location: "Epping Forest Visitor Centre",
      event_url: null,
      cost_text: "Free",
      age_range: "2–10",
      family_relevance: 5,
      source_url: null,
    },
    {
      id: "sample-2",
      title: "Dads & Tots Lego Club",
      description: "Build, trade bricks and pretend you're only helping. Drop-in session at the library.",
      start_date: saturday,
      end_date: saturday,
      time_text: "11am – 12:30pm",
      location: "Central Library, Manchester",
      event_url: null,
      cost_text: "Free",
      age_range: "4–11",
      family_relevance: 5,
      source_url: null,
    },
    {
      id: "sample-3",
      title: "Family Fun Swim with Inflatables",
      description: "The giant pool inflatable is out. Parents must swim too, sorry.",
      start_date: sunday,
      end_date: sunday,
      time_text: "1pm – 3pm",
      location: "Riverside Leisure Centre, Leeds",
      event_url: null,
      cost_text: "£4.50 per child",
      age_range: "3+",
      family_relevance: 4,
      source_url: null,
    },
  ]
}

export const sampleThreads: ForumThread[] = [
  { id: "t1", title: "Survived week one of paternity leave. Is sleep a myth?", category: "New Dads", author: "SleeplessInSheffield", comments: 48 },
  { id: "t2", title: "Best compact buggy that actually fits in a Fiesta boot?", category: "Gear and Recommendations", author: "BootSpaceBarry", comments: 31 },
  { id: "t3", title: "Feeling flat after going back to work. Anyone else?", category: "Mental Health and Support", author: "QuietDadPete", comments: 27 },
  { id: "t4", title: "Rainy day ideas in Bristol that aren't soft play", category: "Days Out", author: "BristolDad88", comments: 22 },
  { id: "t5", title: "Worst dad joke you've told this week. Go.", category: "Banter", author: "PunIntended", comments: 96 },
]

export const sampleArticles: Article[] = [
  { id: "a1", title: "What the new shared parental leave rules mean for working dads", source: "GOV.UK" },
  { id: "a2", title: "Why more fathers are talking openly about postnatal depression", source: "BBC News" },
  { id: "a3", title: "School admissions: key dates for the 2027 intake", source: "Which?" },
  { id: "a4", title: "Five quick, healthy lunchbox ideas kids will actually eat", source: "NHS Better Health" },
]

export const sampleDeal: Deal = {
  id: "d1",
  title: "Compact Fold Travel Buggy",
  retailer: "John Lewis",
  price: 149,
  oldPrice: 229,
  image: "/images/deal-buggy.png",
  category: "Buggies",
  url: "#",
}
