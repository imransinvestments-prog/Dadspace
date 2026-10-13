"""Read the primary Baby Gym table, avoiding duplicate RISE timetable rows."""
from bs4 import BeautifulSoup
from session_proposals import proposal
URL='https://salfordcommunityleisure.co.uk/active-communities/active-gymnastics/'
def parse_baby_gym(document,url=URL):
    soup=BeautifulSoup(document,'html.parser');body=soup.get_text(' ',strip=True)
    if '9 months' not in body:raise ValueError('Baby Gym eligibility missing')
    table=next((t for t in soup.select('table') if [x.get_text(' ',strip=True) for x in t.select('tr')[0].select('th,td')]==['Day','Venue','Time']),None)
    if not table:raise ValueError('Baby Gym timetable structure changed')
    out=[]
    for row in table.select('tr')[1:]:
        cells=[x.get_text(' ',strip=True) for x in row.select('td')]
        if len(cells)!=3:raise ValueError('Incomplete Baby Gym row')
        day,venue,time=cells
        notes='Parent-led Baby Gym; no pre-booking required; pay at reception. Primary page price £4.50 per child; older product pages quote £4.10, verify price. Match venue/address before application. No dated occurrences generated.'
        schedule=day+' '+time
        if '*' in time:schedule+='; term-time only'
        out.append(proposal('Baby Gym',venue,venue+', Salford','9 months+',schedule,url,notes=notes))
    return out
