import "server-only"
import { getMonthlyNews } from "./news-monthly"
import { selectNewsCards } from "./home-selection"
import { getDeals } from "./deals"
import { getSupabase } from "./supabase"
import { londonHour, londonToday, upcomingWeekend, formatEventDate } from "./dates"
import { sampleArticles, sampleEvents, sampleThreads } from "./sample-data"
import { distanceKm, geocodeLocations, kmToMiles, locationKey, type Point } from "./geo"
import type { Article, DadEvent, ForumThread, HomeData } from "./types"

const EVENT_COLUMNS =
  "id,title,description,start_date,end_date,time_text,location,event_url,cost_text,age_range,family_relevance,source_url"

function greetingFor(hour: number) {
  if (hour < 5) return "Up with the baby, Dad?"
  if (hour < 12) return "Morning, Dad."
  if (hour < 17) return "Afternoon, Dad."
  if (hour < 21) return "Evening, Dad."
  return "Night shift, Dad?"
}

const NEARBY_RADIUS_MILES = 30
const HOME_EVENT_COUNT = 3

type EventsResult = HomeData["events"]

function locationBucket(event: DadEvent) {
  const parts = (event.location ?? "")
    .split(",")
    .map((part) => part.trim().toLowerCase())
    .filter(Boolean)
  return parts[parts.length - 1] || String(event.id)
}

function pickLocationMix(events: DadEvent[], count = HOME_EVENT_COUNT) {
  const selected: DadEvent[] = []
  const seen = new Set<string>()

  for (const event of events) {
    const bucket = locationBucket(event)
    if (seen.has(bucket)) continue
    selected.push(event)
    seen.add(bucket)
    if (selected.length === count) return selected
  }

  for (const event of events) {
    if (selected.some((item) => item.id === event.id)) continue
    selected.push(event)
    if (selected.length === count) break
  }

  return selected
}

async function getNearbyEvents(user: Point, saturday: string, sunday: string, today: string): Promise<EventsResult | null> {
  const db = getSupabase()
  if (!db) return null

  const { data, error } = await db
    .from("upcoming_events")
    .select(`${EVENT_COLUMNS},source_id`)
    .gte("end_date", today)
    .order("start_date", { ascending: true })
    .limit(500)
  if (error || !data?.length) return null

  const rows = data as DadEvent[]
  const places = await geocodeLocations(rows)
  const located = rows
    .map((event) => {
      const point = places.get(locationKey(event))
      return point ? { ...event, distance_miles: Math.round(kmToMiles(distanceKm(user, point)) * 10) / 10 } : null
    })
    .filter((e): e is DadEvent & { distance_miles: number } => e !== null)
  if (!located.length) return null

  const byDistance = (a: DadEvent, b: DadEvent) =>
    (a.distance_miles ?? 0) - (b.distance_miles ?? 0) || (b.family_relevance ?? 0) …7661 tokens truncated…generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }
    if THINKING_LEVEL != "off":
        body["generationConfig"]["thinkingConfig"] = {"thinkingLevel": THINKING_LEVEL.upper()}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    last_error = None
    for attempt in range(2):
        try:
            r = requests.post(url, headers={"x-goog-api-key": GEMINI_API_KEY},
                              json=body, timeout=GEMINI_TIMEOUT)
            r.raise_for_status()
            reply = r.json()
            usage = reply.get("usageMetadata", {})
            TOKENS["in"] += usage.get("promptTokenCount", 0)
            # "thinking" tokens are billed as output, so they are counted too
            TOKENS["out"] += usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0)
            TOKENS["think"] += usage.get("thoughtsTokenCount", 0)
            TOKENS["calls"] += 1
            text = reply["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(text)
            if isinstance(data, dict):
                data = data.get("articles") or data.get("results") or data.get("stories") or [data]
            return data
        except Exception as exc:
            last_error = exc
            time.sleep(3)
    raise RuntimeError(f"Gemini failed: {last_error}")


def gemini_score(batch):
    """batch: list of {"i", "title", "source", "snippet"}. Returns list of dicts."""
    lines = []
    for item in batch:
        parts = [str(item["i"]), item["source"], item["title"], item.get("snippet", "")]
        lines.append(" | ".join(p.replace("|", "/") for p in parts).rstrip(" |"))
    return gemini_json(PROMPT + "\n".join(lines))


# ----------------------------------------------------------------------
# STORY GROUPING (one card per story, other outlets listed underneath)
# ----------------------------------------------------------------------
def clean_key(key):
    key = re.sub(r"[^a-z0-9]+", "-", str(key).lower()).strip("-")
    return key[:60] or None


def official_source(row):
    return "gov" in (row.get("source_name") or "").lower()


def load_existing_stories():
    """Stories already showing in the feed (one row per story), so new articles
    about the same story are merged into them instead of appearing again."""
    cutoff = iso(now_utc() - timedelta(days=14))
    r = sb("GET", "news_items", params={
        "select": "story_key,title", "is_primary": "eq.true",
        "story_key": "not.is.null", "relevance": f"gte.{MIN_RELEVANCE}",
        "created_at": f"gte.{cutoff}", "order": "id.desc", "limit": "150"})
    return r.json()


def assign_stories(rows, existing):
    """Fills in story_key and is_primary on each kept row.
    Returns {story_key: {"members": [rows], "existing": bool}} for the report."""
    kept = [r for r in rows if r["relevance"] >= MIN_RELEVANCE][:MAX_GROUP_ITEMS]
    if not kept:
        return {}
    existing_keys = {e["story_key"] for e in existing}
    existing_lines = "\n".join(
        f"{e['story_key']} | {e['title'][:110].replace('|', '/')}" for e in existing) or "(none)"
    new_lines = "\n".join(
        f"{n} | {r['title'][:110].replace('|', '/')} | {r['source_name']}"
        for n, r in enumerate(kept))
    answer = gemini_json(GROUP_PROMPT.replace("{existing}", existing_lines)
                                     .replace("{new}", new_lines))
    keys = {}
    for item in answer:
        try:
            n, key = int(item["id"]), clean_key(item["story"])
        except Exception:
            continue
        if key and 0 <= n < len(kept):
            keys[n] = key

    groups = {}
    for n, r in enumerate(kept):
        if keys.get(n):
            groups.setdefault(keys[n], []).append(r)

    report = {}
    for key, members in groups.items():
        if key in existing_keys:
            # Story already has a card in the feed: these are extra outlets.
            for r in members:
                r["story_key"], r["is_primary"] = key, False
        else:
            # New story: the highest-scoring article (official sources win ties) gets the card.
            members.sort(key=lambda r: (-r["relevance"], 0 if official_source(r) else 1))
            for i, r in enumerate(members):
                r["story_key"], r["is_primary"] = key, (i == 0)
        report[key] = {"members": members, "existing": key in existing_keys}
    return report


# ----------------------------------------------------------------------
# SELF-TEST
# ----------------------------------------------------------------------
def self_test():
    problems = []
    for name in ("SUPABASE_URL", "SUPABASE_SERVICE_KEY", "GEMINI_API_KEY"):
        if not os.environ.get(name):
            problems.append(f"missing setting: {name}")
    if problems:
        print("SELF-TEST FAILED:\n  " + "\n  ".join(problems))
        return 1
    try:
        sb("GET", "news_sources", params={"select": "id", "limit": "1"})
        print("Supabase: OK")
        try:
            sb("GET", "news_items", params={"select": "region", "limit": "1"})
            print("news_items.region column: OK")
        except Exception:
            problems.append("news_items has no 'region' column yet. Run the region SQL in Supabase first.")
        try:
            sb("GET", "news_items", params={"select": "story_key,is_primary", "limit": "1"})
            print("news_items story columns: OK")
        except Exception:
            problems.append("news_items has no 'story_key'/'is_primary' columns yet. Run story_grouping.sql in Supabase first.")
        try:
            sb("GET", "pipeline_runs", params={"select": "id", "limit": "1"})
            print("pipeline_runs table: OK")
        except Exception:
            problems.append("pipeline_runs table is missing. Run pipeline_runs.sql in Supabase first.")
    except Exception as exc:
        problems.append(f"Supabase: {exc}")
    try:
        result = gemini_score([{"i": 0, "title": "Changes to paternity leave rules announced",
                                "source": "test", "snippet": ""}])
        print(f"Gemini ({GEMINI_MODEL}): OK ({len(result)} result)")
    except Exception as exc:
        problems.append(f"Gemini: {exc}")
        try:
            r = requests.get("https://generativelanguage.googleapis.com/v1beta/models",
                             headers={"x-goog-api-key": GEMINI_API_KEY},
                             params={"pageSize": 100}, timeout=30)
            names = [m["name"].replace("models/", "") for m in r.json().get("models", [])
                     if "generateContent" in m.get("supportedGenerationMethods", [])
                     and "flash" in m["name"]]
            print("Flash models your key can use right now:\n  " + "\n  ".join(names))
        except Exception as exc2:
            print(f"(could not list models: {exc2})")
    if TOKENS["calls"]:
        log_run({"scored": 0}, worker="news-selftest", dry_run=True)
    if problems:
        print("SELF-TEST FAILED:\n  " + "\n  ".join(problems))
        return 1
    print("SELF-TEST PASSED")
    return 0


# ----------------------------------------------------------------------
# RUN LOG (one row per run in the pipeline_runs table)
# ----------------------------------------------------------------------
def log_run(stats, worker="news", dry_run=None):
    skipped = sum(v for k, v in stats.items() if k.startswith("skipped_"))
    row = {
        "worker": worker,
        "dry_run": DRY_RUN if dry_run is None else dry_run,
        "input_tokens": TOKENS["in"],
        "output_tokens": TOKENS["out"],
        "gemini_calls": TOKENS["calls"],
        "articles_scored": stats["scored"],
        "skipped_prefilter": skipped,
    }
    try:
        sb("POST", "pipeline_runs", json_body=row,
           extra_headers={"Prefer": "return=minimal"})
        print("Run logged to pipeline_runs.")
    except Exception as exc:  # logging must never break the run
        print(f"(could not log this run: {exc})")


# ----------------------------------------------------------------------
# MAIN RUN
# ----------------------------------------------------------------------
def run():
    stats = {"sources_ok": 0, "sources_failed": 0, "new_articles": 0,
             "scored": 0, "kept": 0, "low_relevance": 0,
             "saved": 0, "batches_failed": 0,
             "duplicates_merged": 0, "stories_shown": 0,
             "skipped_blocked_word": 0, "skipped_no_family_word": 0,
             "skipped_near_duplicate": 0}
    failed_sources = []
    kept_lines, rejected_lines = [], []
    per_source = {}  # feed name -> [scored, kept]
    skipped_lines = []  # what the free pre-filter removed (shown in dry run)
    story_lines = []  # duplicate stories that were merged (shown in dry run)
    all_rows = []  # every scored article, saved together after grouping

    print(f"Dadspace news worker | dry_run={DRY_RUN} | model={GEMINI_MODEL} | thinking={THINKING_LEVEL}")

    try:
        sources = load_sources()
        print(f"Active sources: {len(sources)}")
        seen_urls, seen_titles, known_sets = load_existing()

        # ---- 1) collect new articles from every feed
        candidates = []
        for src in sources:
            if out_of_time() or len(candidates) >= MAX_NEW_PER_RUN:
                print("Stopping collection early (time or article limit reached).")
                break
            t0 = time.time()
            try:
                entries = fetch_feed(src)
            except Exception as exc:
                stats["sources_failed"] += 1
                failed_sources.append(f"{src['name']}: {str(exc)[:100]}")
                mark_source(src, ok=False, error=exc)
                print(f"  FAIL  {src['name']}: {str(exc)[:100]}")
                continue

            mark_source(src, ok=True)
            stats["sources_ok"] += 1
            added = too_old = already = 0
            for e in entries:
                title = clean_text(e.get("title"), 300)
                link = clean_url(e.get("link", "")) if e.get("link") else ""
                if not title or not link:
                    continue
                published = entry_date(e)
                if published and published < now_utc() - timedelta(days=MAX_ARTICLE_AGE_DAYS):
                    too_old += 1
                    continue
                key = title_key(title)
                if link in seen_urls or key in seen_titles:
                    already += 1
                    continue
                seen_urls.add(link)
                seen_titles.add(key)
                publisher = (e.get("source") or {}).get("title") or src["name"]

                # Snippet: short, and dropped when it only repeats the headline
                # (Google News snippets are just the headline again = wasted tokens).
                snippet = clean_text(e.get("summary"), SNIPPET_CHARS)
                if "news.google.com" in src["feed_url"] or title_key(title)[:30] in title_key(snippet):
                    snippet = ""

                # Free checks before spending any Gemini tokens
                reason = prefilter(title, snippet, src.get("filter_mode") or "none")
                if reason:
                    stats[f"skipped_{reason}"] += 1
                    skipped_lines.append(f"({reason}) {title}  [{publisher}]")
                    continue
                words = word_set(title)
                if is_near_duplicate(words, known_sets):
                    stats["skipped_near_duplicate"] += 1
                    skipped_lines.append(f"(near_duplicate) {title}  [{publisher}]")
                    continue
                known_sets.append(words)

                candidates.append({
                    "src": src, "title": title, "url": link, "published": published,
                    "publisher": publisher, "snippet": snippet,
                })
                added += 1
            print(f"  ok    {src['name']}: {added} new, {len(entries)} in feed, "
                  f"{too_old} too old, {already} already seen ({time.time() - t0:.1f}s)")

        stats["new_articles"] = len(candidates)
        print(f"New articles to score: {len(candidates)}")

        # ---- 2) score with Gemini in batches, then save
        for start in range(0, len(candidates), BATCH_SIZE):
            if out_of_time():
                print("Stopping scoring early (time limit reached).")
                break
            chunk = candidates[start:start + BATCH_SIZE]
            payload = [{"i": n, "title": c["title"], "source": c["publisher"],
                        "snippet": c["snippet"]} for n, c in enumerate(chunk)]
            try:
                results = gemini_score(payload)
            except Exception as exc:
                stats["batches_failed"] += 1
                print(f"  Batch failed (will retry next run): {exc}")
                continue

            rows = []
            for res in results:
                try:
                    c = chunk[int(res["i"])]
                    relevance = max(0, min(5, int(res.get("relevance", 0))))
                except Exception:
                    continue
                category = res.get("category") if res.get("category") in CATEGORIES else "other"
                region = str(res.get("region", "uk")).strip().lower().replace(" ", "_")
                if region not in REGIONS:
                    region = "uk"
                summary = clean_text(res.get("summary"), 300)
                why = clean_text(res.get("why_it_matters"), 150)
                stats["scored"] += 1
                counts = per_source.setdefault(c["src"]["name"], [0, 0])
                counts[0] += 1
                line = f"[{relevance}] ({region}) {c['title']}  ({c['publisher']})"
                if relevance >= MIN_RELEVANCE:
                    counts[1] += 1
                    stats["kept"] += 1
                    kept_lines.append(f"{line}\n      -> {why}")
                else:
                    stats["low_relevance"] += 1
                    rejected_lines.append(line)
                rows.append({
                    "source_id": c["src"]["id"], "source_name": c["publisher"],
                    "title": c["title"], "url": c["url"],
                    "published_at": iso(c["published"]) if c["published"] else None,
                    "summary": summary, "why_it_matters": why,
                    "category": category, "relevance": relevance,
                    "region": region,
                })
            all_rows.extend(rows)

        # ---- 2b) group articles that are the same story
        for r in all_rows:
            r["story_key"], r["is_primary"] = None, True
        if all_rows and not out_of_time():
            try:
                story_groups = assign_stories(all_rows, load_existing_stories())
                stats["duplicates_merged"] = sum(1 for r in all_rows if not r["is_primary"])
                for key, info in story_groups.items():
                    members = info["members"]
                    if len(members) < 2 and not info["existing"]:
                        continue
                    tag = " [already in feed]" if info["existing"] else ""
                    story_lines.append(f"{key} ({len(members)} articles){tag}")
                    for r in members:
                        mark = "SHOWN " if r["is_primary"] else "merged"
                        story_lines.append(f"    {mark} [{r['relevance']}] {r['title'][:100]}  ({r['source_name']})")
            except Exception as exc:
                print(f"  Story grouping failed, saving without grouping: {exc}")
                for r in all_rows:
                    r["story_key"], r["is_primary"] = None, True
        stats["stories_shown"] = stats["kept"] - stats["duplicates_merged"]

        # Resolve only relevant articles, after scoring and grouping.
        kept = [row for row in all_rows if row["relevance"] >= MIN_RELEVANCE]
        destinations = resolve_article_urls([row["url"] for row in kept])
        for row, destination in zip(kept, destinations):
            row["url"] = clean_url(destination)

        if all_rows and not DRY_RUN:
            save_items(all_rows)
            stats["saved"] = len(all_rows)

        # ---- 3) tidy up
        if not DRY_RUN:
            delete_old()

    except Exception:
        print("UNEXPECTED ERROR:")
        traceback.print_exc()
    finally:
        print("\n" + "=" * 60)
        if DRY_RUN:
            print("DRY RUN: nothing was saved.")
            print(f"\nWould KEEP ({len(kept_lines)}):")
            for line in kept_lines[:200]:
                print("  " + line)
            # Spread the rejected sample evenly so every source is represented
            step = max(1, len(rejected_lines) // 40)
            sample = rejected_lines[::step][:40]
            print(f"\nSample of REJECTED ({len(rejected_lines)} total, showing {len(sample)}):")
            for line in sample:
                print("  " + line)
        if DRY_RUN and story_lines:
            print(f"\nSTORY GROUPS: same story from several outlets ({stats['duplicates_merged']} "
                  f"merged, so the feed would show {stats['stories_shown']} cards):")
            for line in story_lines:
                print("  " + line)
        if DRY_RUN and skipped_lines:
            step = max(1, len(skipped_lines) // 40)
            print(f"\nSKIPPED BEFORE GEMINI, free ({len(skipped_lines)} total, "
                  f"showing {len(skipped_lines[::step][:40])}). Check nothing good is in here:")
            for line in skipped_lines[::step][:40]:
                print("  " + line)
        print("\nPER-SOURCE RESULTS (kept / scored)")
        for name, (scored, kept) in per_source.items():
            print(f"  {kept:>3} / {scored:<3}  {name}")
        print("\nSUMMARY")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        print(f"  gemini_calls: {TOKENS['calls']}")
        print(f"  input_tokens: {TOKENS['in']:,}")
        print(f"  output_tokens: {TOKENS['out']:,}  (of which thinking: {TOKENS['think']:,})")
        print(f"  thinking_level: {THINKING_LEVEL}")
        if failed_sources:
            print("  failing feeds:")
            for f in failed_sources:
                print("    - " + f)
        print(f"  minutes: {(time.time() - START) / 60:.1f}")
        print("=" * 60)
        log_run(stats)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(self_test())
    if not (SUPABASE_URL and SUPABASE_SERVICE_KEY and GEMINI_API_KEY):
        print("Missing SUPABASE_URL, SUPABASE_SERVICE_KEY or GEMINI_API_KEY")
        sys.exit(1)
    run()
