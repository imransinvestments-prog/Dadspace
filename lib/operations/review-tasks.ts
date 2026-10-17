export const REVIEW_TASKS = [
  { id: 123, title: "Pilot quality thresholds", need: "Agree remaining numeric thresholds and accepted/rejected examples.", dependencies: [122], route: "/ops" },
  { id: 34, title: "Pilot venue quality", need: "Review the 50-venue cohort: identity, location, access, facts and photo rights.", dependencies: [122, 33], route: "/ops/review?kind=venues" },
  { id: 126, title: "News quality", need: "Score 50 news items for relevance, attribution and working destinations.", dependencies: [122, 123], route: "/news" },
  { id: 128, title: "Originals editorial acceptance", need: "Review daily tips, Friday guides and rejected drafts for claims, tone and usefulness.", dependencies: [], route: "/originals" },
  { id: 130, title: "Published deals and ranking", need: "Review the published pool and top 20 for usefulness, accuracy, terms and redemption.", dependencies: [122, 123], route: "/deals" },
  { id: 135, title: "Historical programme corrections", need: "Decide unresolved schedule, eligibility and session proposals; guarded application remains separate.", dependencies: [33, 40], route: "/ops/review?kind=activities" },
  { id: 136, title: "Pilot activity coverage", need: "Score 100 activities and assess local breadth against agreed thresholds.", dependencies: [122, 123, 120, 125, 40], route: "/ops/review?kind=activities" },
  { id: 145, title: "Provider quality and rollout", need: "Review representative quality and actual cost evidence before a provider rollout decision. Engineering evidence remains outstanding.", dependencies: [], route: "/ops#editorial" },
  { id: 149, title: "Operations coverage and usability", need: "Review the upkeep inventory and demonstrate usable maintenance and recovery paths. Engineering work remains outstanding.", dependencies: [33, 40, 146, 147, 148], route: "/ops#processes" },
] as const
export const REVIEW_DECISIONS = ["Approved for stated scope", "Changes requested", "Blocked — more evidence needed"] as const
export function reviewTask(id: number) { return REVIEW_TASKS.find(task => task.id === id) }
