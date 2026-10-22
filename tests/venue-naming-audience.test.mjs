import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { PGlite } from '@electric-sql/pglite'

// Runs the exact owner-run files against a venues stand-in that keeps production's rule:
// reviewed rows keep their publication decision unless a review write is in progress.
const schema = `
  create table public.venues(id uuid primary key default gen_random_uuid(), venue_name text, venue_label text, category text,
    nearby_settlement text, notes text, source_url text, public_visible boolean, review_reason text, ops_reviewed_at timestamptz);
  create function public.preserve_review() returns trigger language plpgsql as $$ begin
    if old.ops_reviewed_at is not null then new.public_visible := old.public_visible; new.review_reason := old.review_reason; new.venue_name := old.venue_name; end if;
    return new; end $$;
  create trigger venues_preserve_operations_review before update on public.venues for each row execute function public.preserve_review();`
const migration = fs.readFileSync('supabase/migrations/20261022170000_venue_adult_only.sql', 'utf8')
const arcades = fs.readFileSync('supabase/arcade-audience-2026-10-22.sql', 'utf8')
const playgrounds = fs.readFileSync('supabase/unnamed-playground-labels-2026-10-22.sql', 'utf8')
const review = JSON.parse(fs.readFileSync('artefacts/data/venue-publication-review-2026-10-14.json', 'utf8')).decisions
const evidence = JSON.parse(fs.readFileSync('artefacts/data/unnamed-playground-labels-2026-10-22.json', 'utf8')).playgrounds

async function database() {
  const db = new PGlite()
  await db.exec(schema)
  await db.exec(migration)
  return db
}

test('arcades are listed only when confirmed family-friendly; reviewed decisions are untouched', async () => {
  const db = await database()
  try {
    // Production state before the change: hidden decisions were reviewed, the rest public and unreviewed.
    // One adult-flagged arcade escaped the 14 Oct hide (it matched exact names only) and is still public.
    const escaped = review.find(d => d.decision === 'hide').source_url
    for (const d of review) {
      const hidden = d.decision.startsWith('hide') && d.source_url !== escaped
      // PGlite rejects null text parameters, so empty strings stand in for NULL here.
      await db.query(`insert into public.venues(venue_name, category, source_url, public_visible, review_reason, ops_reviewed_at)
        values (nullif($1, ''), 'Amusement arcade', $2, $3, nullif($4, ''), nullif($5, '')::timestamptz)`,
        [d.venue_name ?? '', d.source_url, !hidden, hidden ? d.reason : '', hidden ? '2026-10-14T20:00:00Z' : ''])
    }
    await db.query("insert into public.venues(venue_name, category, source_url, public_visible) values ('Church Lane Playground', 'Children’s playground', 'x', true)")
    await db.exec(arcades)
    const count = async sql => (await db.query(sql)).rows[0].n
    const families = review.filter(d => d.decision === 'retain-family').length
    assert.equal(await count("select count(*)::int n from public.venues where category = 'Amusement arcade' and public_visible"), families)
    assert.equal(await count("select count(*)::int n from public.venues where category = 'Amusement arcade' and public_visible and adult_only = false"), families)
    assert.equal(await count("select count(*)::int n from public.venues where adult_only"), review.filter(d => d.decision === 'hide').length)
    // Casino-named quarantines are not asserted to be adult-only.
    assert.equal(await count("select count(*)::int n from public.venues v where adult_only is null and review_reason like '%quarantined%'"), 2)
    // Reviewed rows keep their original reason; newly hidden rows say why and are not called adult.
    assert.equal(await count("select count(*)::int n from public.venues where ops_reviewed_at is not null and review_reason like '%2026-10-22%'"), 0)
    const rule = (await db.query("select review_reason from public.venues where category = 'Amusement arcade' and adult_only is null and ops_reviewed_at is null limit 1")).rows[0].review_reason
    assert.match(rule, /owner rule: amusement arcades are listed only when confirmed family-friendly/)
    assert.match(rule, /not asserted to be adult-only/)
    const adult = (await db.query('select public_visible, review_reason from public.venues where source_url = $1', [escaped])).rows[0]
    assert.equal(adult.public_visible, false)
    assert.match(adult.review_reason, /Adult evidence from the 2026-10-14 review/)
    assert.doesNotMatch(adult.review_reason, /not asserted to be adult-only/)
    assert.equal(await count("select count(*)::int n from public.venues where category <> 'Amusement arcade' and public_visible"), 1, 'other categories untouched')
    // Every flag records its evidence.
    assert.equal(await count("select count(*)::int n from public.venues where category = 'Amusement arcade' and adult_only_evidence is null"), 0)
    // The documented rollback restores the publication rule's hides only.
    const rollback = arcades.split('-- Rollback of the publication rule only')[1].split('\n').slice(1).map(l => l.replace(/^-- ?/, '')).join('\n')
    await db.exec(rollback)
    assert.equal(await count("select count(*)::int n from public.venues where category = 'Amusement arcade' and public_visible"),
      review.filter(d => !d.decision.startsWith('hide')).length + 1, 'the escaped adult arcade returns too: rollback undoes this change only')
    assert.equal(await count("select count(*)::int n from public.venues where review_reason like '%2026-10-22%'"), 0)
  } finally { await db.close() }
})

test('unnamed playgrounds get "<road> Playground" or "Playground near <town>"; named or renamed rows are left alone', async () => {
  const db = await database()
  try {
    for (const [i, p] of evidence.entries()) {
      await db.query(`insert into public.venues(id, venue_label, category, nearby_settlement, notes, source_url, public_visible)
        values ($1, $2, 'Children’s playground', 'Mill Hill', 'Name missing in source.', $3, true)`,
        [p.id, `Unnamed children’s playground (way/${1000 + i})`, `https://www.openstreetmap.org/way/${1000 + i}`])
    }
    // A playground that gained a real name since the lookup must keep it.
    const named = evidence[0].id
    await db.query("update public.venues set venue_name = 'Okemoor Play Park' where id = $1", [named])
    const result = await db.exec(playgrounds)
    assert.equal(result.at(-2).rows[0].still_unnamed, 0, 'the named row is excluded from the unnamed check')
    const rows = (await db.query('select id, venue_label, notes from public.venues')).rows
    const byId = new Map(rows.map(r => [r.id, r]))
    for (const p of evidence.slice(1)) {
      const row = byId.get(p.id)
      assert.equal(row.venue_label, p.road ? `${p.road} Playground` : 'Playground near Mill Hill')
      assert.match(row.notes, /^Name missing in source\. Display label derived 2026-10-22 from the (nearest named road in OpenStreetMap|nearby settlement); not an official name\.$/)
    }
    assert.match(byId.get(named).venue_label, /^Unnamed/, 'a real name since the lookup is never overwritten')
    assert.ok(evidence.every(p => !p.road || !/^[ABM]\d+[A-Z]?$/i.test(p.road)), 'no bare road numbers used as names')
    const streets = /^highway\/(motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street|pedestrian|road)$/
    assert.ok(evidence.every(p => !p.road || streets.test(p.matched_kind)), 'only public streets name a playground')
    assert.ok(evidence.some(p => p.address_road === 'Lower Lacon Caravan Park' && p.road === null), 'site names on service roads fall back')
    // The documented rollback restores the previous label and note exactly.
    const rollback = playgrounds.split('-- Rollback:')[1].split('\n').slice(2).map(l => l.replace(/^-- ?/, '')).join('\n')
    await db.exec(rollback)
    const restored = (await db.query("select count(*)::int n from public.venues where venue_label ~ '^Unnamed children’s playground \\(way/[0-9]+\\)$' and notes = 'Name missing in source.'")).rows[0].n
    assert.equal(restored, evidence.length)
  } finally { await db.close() }
})
