"""Bounded canonical lookup. Discovery never creates or publishes a place."""
import re


def normalise(value):
    return re.sub(r'[^a-z0-9]+', ' ', (value or '').lower().replace('&', ' and ')).strip()


def resolve(db, name, postcode):
    if not name or not postcode:
        return None, 'missing_place_evidence'
    # Equality uses venues_postcode_idx. Non-canonical stored postcode formats
    # remain unresolved rather than prompting a table-wide fuzzy scan.
    rows = db.table('venues').select('id,venue_name,postcode,public_visible,merged_into').eq('postcode', postcode).limit(21).execute().data or []
    if len(rows) > 20:
        return None, 'candidate_limit'
    exact = [r for r in rows if normalise(r.get('venue_name')) == normalise(name)]
    targets = set()
    for row in exact:
        seen = set()
        for _ in range(20):
            rid = str(row['id'])
            if rid in seen:
                return None, 'invalid_alias_chain'
            seen.add(rid)
            target = row.get('merged_into')
            if not target:
                if not row.get('public_visible'):
                    return None, 'unreviewed_place'
                targets.add(rid)
                break
            matches = db.table('venues').select('id,venue_name,postcode,public_visible,merged_into').eq('id', str(target)).limit(2).execute().data or []
            if len(matches) != 1:
                return None, 'missing_alias_target'
            row = matches[0]
        else:
            return None, 'invalid_alias_chain'
    if len(targets) == 1:
        return targets.pop(), 'canonical_exact_or_reviewed_alias'
    return None, 'ambiguous_place' if targets else 'unmatched_place'
