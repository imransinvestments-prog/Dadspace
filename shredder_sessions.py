"""Coach/day review drafts from public pages; enquiry-only times stay unknown."""
import re
from bs4 import BeautifulSoup
from session_proposals import proposal

VENUES={'book-burwell':('Burwell Skatepark','Burwell, Cambridgeshire'),'book-trumpington':('Trumpington Skatepark','Trumpington, Cambridge'),'book-jesus-green':('Jesus Green Skatepark','Cambridge'),'book-haslingfield':('Haslingfield Skatepark','Haslingfield, Cambridgeshire'),'book-cottenham':('Cottenham Skatepark','Cottenham, Cambridgeshire'),'book-orchard-park':('Orchard Park Skatepark','Orchard Park, Cambridge')}

def parse_shredder(document,url,venue,town,home):
    age=re.search(r'Lessons are suitable for ages (\d+) and above',BeautifulSoup(home,'html.parser').get_text(' ',strip=True))
    if not age:raise ValueError('Operator minimum age not evidenced')
    soup=BeautifulSoup(document,'html.parser');items=[];issues=[];seen=set()
    for a in soup.select('a[href]'):
        if a.get_text(' ',strip=True)!='GROUP':continue
        if not a['href'].startswith('mailto:'):raise ValueError('Group booking mechanism changed; needs qualification')
        card=next((p for p in a.parents if p.name=='div' and 'Coach /' in p.get_text(' ',strip=True) and re.search(r'Saturday|Sunday',p.get_text(' ',strip=True))),None)
        if card is None:issues.append('Group coach card lacks a supported published weekday');continue
        body=card.get_text(' ',strip=True)
        coach=re.split(r'(?:Head|Senior) Coach /',body)[0].strip()
        if coach in seen:continue
        seen.add(coach)
        # Ignore the separate adult Monday class on the Trumpington card.
        days=list(dict.fromkeys(re.findall(r'\b(Saturday|Sunday)s?\b',body)))
        sport='Scooter' if 'Coach / SCOOT' in body else 'Skateboard'
        for day in days:
            notes='Enquiry-only draft: exact session clock time and availability are unpublished; confirm before application. Coach: '+coach+'. Operator age '+age[1]+'+ supersedes directory age 3+. Street address/postcode and canonical venue require confirmation. No occurrence dates generated. Recurring Activity. Published group rate £12.50 per hour; block-payment terms apply.'
            items.append(proposal(sport+' group lesson — '+coach,venue,venue+', '+town,age[1]+'+',day+'; time to confirm with coach',url,dates='',notes=notes))
        issues.append(coach+': weekday evidenced; exact time, place details and availability require enquiry')
    if not items:issues.append('No actionable group timetable: private/enquiry-only or holiday offering without published session times')
    if re.search(r'Holiday Clubs\s+SKATE',soup.get_text(' ',strip=True)):issues.append('Holiday Clubs: no exact dates/times published; no occurrences created')
    return items,issues
