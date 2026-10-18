"""Validate and generate an atomic, immutable reference import. No DB connection."""
import argparse
import copy
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
POSTCODE = re.compile(r'^([A-Z]{1,2})([0-9][A-Z0-9]?) ([0-9])[A-Z]{2}$')
KINDS = {'nation':0,'region':1,'county':2,'council':3,'postal_area':0,'postal_district':1,'postal_sector':2}


def normalize(value):
    compact = re.sub(r'\s+', '', str(value)).upper()
    formatted = compact[:-3]+' '+compact[-3:]
    if not POSTCODE.fullmatch(formatted) or formatted.startswith('BT'):
        raise ValueError('Invalid or licence-blocked postcode')
    return formatted


def month(value):
    if not value: return None
    if not re.fullmatch(r'\d{6}', str(value)): raise ValueError('Invalid reference month')
    return dt.date(int(value[:4]), int(value[4:]), 1).isoformat()


def postal_nodes(postcode):
    match = POSTCODE.fullmatch(postcode)
    area, district, sector = match[1], match[1]+match[2], postcode[:-2]
    return [(f'P:{area}', area, 'postal_area'), (f'P:{district}', district, 'postal_district'),
            (f'P:{sector}', sector, 'postal_sector')]


def validate(reference):
    areas = {a['code']: a for a in reference['areas']}
    if len(areas) != len(reference['areas']): raise ValueError('Duplicate area code')
    for area in areas.values():
        if area['kind'] not in KINDS or not area['name'].strip(): raise ValueError('Invalid area')
    parents = {}
    for edge in reference['relationships']:
        child, parent = areas.get(edge['child']), areas.get(edge['parent'])
        if not child or not parent or child['kind']!='council' and child['kind'] not in ('region','county') or parent['kind'] not in ('nation','region','county') or KINDS[child['kind']]<=KINDS[parent['kind']]:
            raise ValueError('Invalid administrative relationship')
        if edge['child'] in parents: raise ValueError('Ambiguous administrative parent')
        parents[edge['child']] = edge['parent']
    for area in areas.values():
        if area['kind']!='nation' and area['code'] not in parents: raise ValueError('Missing administrative parent')
    seen = set()
    for row in reference['postcodes']:
        postcode = normalize(row['postcode'])
        if postcode in seen: raise ValueError('Duplicate postcode')
        seen.add(postcode)
        if areas.get(row['council_code'],{}).get('kind')!='council' or areas.get(row['nation_code'],{}).get('kind')!='nation': raise ValueError('Unknown postcode mapping')
        ancestor = row['council_code']
        while ancestor in parents: ancestor = parents[ancestor]
        if ancestor != row['nation_code']: raise ValueError('Postcode nation mismatch')
        if not isinstance(row['latitude'],(int,float)) or not isinstance(row['longitude'],(int,float)) or not 49<=row['latitude']<=61.5 or not -9<=row['longitude']<=2.5: raise ValueError('Invalid postcode point')
        month(row.get('introduced')); month(row.get('terminated'))
        if row.get('introduced') and row.get('terminated') and row['introduced']>row['terminated']: raise ValueError('Invalid termination chronology')
    return reference


def literal(value):
    return 'null' if value is None else "'"+str(value).replace("'", "''")+"'"


def insert(table, columns, values):
    return 'insert into public.'+table+'('+','.join(columns)+') values ('+','.join(map(literal,values))+');\n'


def emit_seed(reference, output):
    validate(reference)
    reference=copy.deepcopy(reference)
    for postcode in reference['postcodes']: postcode['postcode']=normalize(postcode['postcode'])
    canonical = json.dumps(reference, sort_keys=True, separators=(',',':'),ensure_ascii=False).encode()
    digest = hashlib.sha256(canonical).hexdigest()
    release = reference['release_id']
    output.write('begin;\nset local standard_conforming_strings=on;\n')
    # Serialize same release imports; a changed artefact cannot masquerade as an idempotent re-run.
    output.write('select pg_advisory_xact_lock(hashtextextended('+literal('geography:'+release)+',0));\n')
    output.write('do $guard$ begin if exists(select 1 from geography_releases where id='+literal(release)+' and content_sha256<>'+literal(digest)+") then raise exception 'Release content changed; choose a new release ID'; end if; end $guard$;\n")
    output.write('create temporary table geography_import_new as select not exists(select 1 from geography_releases where id='+literal(release)+') as yes;\n')
    def row(table, columns, values):
        output.write('insert into public.'+table+'('+','.join(columns)+') select '+','.join(map(literal,values))+' where (select yes from geography_import_new);\n')
    source=reference['administrative']
    row('geography_releases',['id','content_sha256','edition','source_url','licence','scope','observed_at','provenance'],
        [release,digest,source['edition'],source['source'],source['licence']+'; '+reference['postal']['licence'],reference['postal']['scope'],reference['captured_at'],json.dumps(dict(administrative=source,postal=reference['postal']),ensure_ascii=False)])
    nodes={a['code']:(a['name'],a['kind']) for a in reference['areas']}
    edges={(e['child'],e['parent'],e['kind']) for e in reference['relationships']}
    for postcode in reference['postcodes']:
        postal = postal_nodes(postcode['postcode'])
        for code,name,kind in postal: nodes[code]=(name,kind)
        edges.update([(postal[1][0],postal[0][0],'postal'),(postal[2][0],postal[1][0],'postal')])
    for code,(name,kind) in sorted(nodes.items()): row('geography_areas',['release_id','code','name','kind'],[release,code,name,kind])
    for child,parent,kind in sorted(edges): row('geography_relationships',['release_id','child_code','parent_code','kind'],[release,child,parent,kind])
    for p in reference['postcodes']:
        row('geography_postcodes',['release_id','postcode','sector_code','council_code','nation_code','latitude','longitude','introduced','terminated','coordinate_method'],
            [release,p['postcode'],postal_nodes(p['postcode'])[-1][0],p['council_code'],p['nation_code'],p['latitude'],p['longitude'],month(p.get('introduced')),month(p.get('terminated')),p['coordinate_method']])
    output.write('drop table geography_import_new;\ncommit;\n')
    return digest


def read_onspd(path):
    """Yield a filtered, licensed GB ONSPD file; reject NI rather than silently import it."""
    with open(path, newline='', encoding='utf-8-sig') as handle:
        reader=csv.DictReader(handle)
        required={'pcds','lat','long','lad','ctry','dointr','doterm'}
        if not required.issubset(reader.fieldnames or []): raise ValueError('Missing ONSPD columns')
        for item in reader:
            yield dict(postcode=normalize(item['pcds']),latitude=float(item['lat']),longitude=float(item['long']),
                       council_code=item['lad'],nation_code=item['ctry'],introduced=item['dointr'] or None,
                       terminated=item['doterm'] or None,coordinate_method='ONSPD postcode representative point')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,default=ROOT/'geography/reference.json')
    parser.add_argument('--output',type=Path,default=ROOT/'review/geography-seed.sql')
    args=parser.parse_args()
    reference=json.loads(args.reference.read_text(encoding='utf-8'))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    # Write to a sibling temporary file; invalid inputs never replace a valid seed.
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=args.output.parent,delete=False,suffix='.sql') as output:
        temporary=Path(output.name)
        try: digest=emit_seed(reference,output)
        except Exception:
            output.close();temporary.unlink();raise
    temporary.replace(args.output)
    print(json.dumps(dict(release=reference['release_id'],sha256=digest,output=str(args.output),database_writes=0)))


if __name__=='__main__': main()
