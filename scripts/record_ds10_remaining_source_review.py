"""Attach reviewed decisions as evidence, never mark owner decisions approved."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REVIEWS={
 'Curiosity Club':('exclude from family supply','Current Curiosity Club is for adults 50+/55+, not evidenced child/family supply. Old route returns 404.',['Owner review before withdrawal from family activities; retain adult-programme evidence separately.'],[('Current adult programme','https://www.oxfordshire.gov.uk/events/workshops-oxfordshire-museum/curiosity-club-3')]),
 'Wildlings at Milton Country Park':('route recovered; currentness unresolved','Primary forest-activities route and Wildlings booking route recovered. Programme page gives Fridays 12:00–13:30 for non-walking babies, but its listed next dates are May 2026.',['Confirm current dated availability before restoring verification; do not substitute fully booked Wild Beginnings or unrelated Wildlings operators.'],[('Current forest activities','https://www.miltoncountrypark.org/wild-place'),('Wildlings booking calendar','https://www.miltoncountrypark.org/booking-calendar/wildlings')]),
 'BAYSE Multi-Sports':('current timetable unresolved','Original route now returns 404. Cached October 6 occurrence describes weekly Tuesday 18:00–19:30 at Brookhouse, excluding bank holidays/festive period.',['Find current provider timetable; cached past date does not qualify current supply or prove closure.'],[('Provider','https://salfordcommunityleisure.co.uk/')]),
 'Baby Gym':('recovered; split into sessions','Current operator table yields seven weekly Baby Gym sessions for ages 9 months+. Select the split action to review the generated rows.',['Match actual venue addresses before application; resolve £4.50 primary-page versus £4.10 old-product pricing.'],[('Current Baby Gym timetable','https://salfordcommunityleisure.co.uk/active-communities/active-gymnastics/')]),
 'Bampton: Rhymetime - Poetry Special':('expired occasion; withdrawal proposed','Published occasion was 30 September 2026, 10:30–11:00; original page now returns 404. This was a Poetry Special, not evidence of a weekly recurring programme.',['Owner review of expiry before withdrawal; keep branch directory as discovery evidence rather than substituting another activity.'],[('Current Bampton Library','https://www.oxfordshire.gov.uk/oxfordshire-libraries/find-library/bampton-library')]),
 'Didcot: Rhymetime':('expired old route; current branch discovered','Old occurrence was 17 July 2026 and now returns 404. Current branch page lists Cantonese Rhymetime and other programmes.',['Do not overwrite English Rhymetime with another language/programme; collect newly evidenced future occurrences separately.'],[('Current Didcot Library','https://www.oxfordshire.gov.uk/oxfordshire-libraries/find-library/didcot-library')]),
 'Marble Triceratops Skull public sculpture':('place conversion proposed','Primary gallery evidence locates the public sculpture in Berkeley Square, Mayfair. Hoop daily occurrence and 23:00–22:59 range are not an actionable activity timetable.',['Match/create an appropriate venue candidate before withdrawing the activity alias; preserve independent place value.'],[('Primary sculpture evidence','https://www.davidaaron.com/event-details/50334')]),
 'Total Ballers 1-2-1 Sessions Football':('mobile service; appointment required','Provider site and booking hub recovered. Mobile coaching is arranged with the family; Hoop daily 17:00 slot and SW11 map pin do not establish a fixed venue or daily availability.',['Confirm service area, session age eligibility and appointment through actual booking; £35/hour primary versus £40/monthly-paid aggregator pricing needs review.'],[('Primary operator','https://www.totalballers.co.uk/'),('Provider booking hub','https://linktr.ee/totalballers')])}

def main():
    path=ROOT/'artefacts/data/ds10-action-console-19-2026-10-12.json'
    cohort=json.loads(path.read_text(encoding='utf8'));ledger=[]
    for row in cohort['records']:
        if row['title'] not in REVIEWS:continue
        status,recommendation,remaining,links=REVIEWS[row['title']]
        review=dict(checked_on='2026-10-12',status=status,recommendation=recommendation,remaining=remaining,links=[dict(label=l,url=u) for l,u in links],owner='Imran Tajuddin',approved=False)
        row['source_review']=review
        known={x['url'] for x in row['links']}
        row['links'].extend(x for x in review['links'] if x['url'] not in known)
        ledger.append(dict(record_id=row['id'],title=row['title'],**review))
    assert len(ledger)==8
    path.write_text(json.dumps(cohort,ensure_ascii=False,indent=2),encoding='utf8')
    (ROOT/'artefacts/data/ds10-remaining-source-review-2026-10-12.json').write_text(json.dumps(dict(records=ledger,database_writes=0,source_activations=0,notes='Read-only evidence; provider pages and cached historical dates are distinguished. Recommendations are not applied decisions.'),ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()
