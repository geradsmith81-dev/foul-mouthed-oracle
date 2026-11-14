"""
Ptolemy interpretation layer.

Source: Claudius Ptolemy, Tetrabiblos (2nd century), tr. F. E. Robbins (Loeb Classical Library, 1940; public domain
in the United States), as transcribed on LacusCurtius. Every table it uses is a CSV in data/ with chapter and Loeb page:
  ptolemy_dignities.csv    I.17 houses, I.18 triangles (by sect), I.19 exaltations and depressions,
                           I.21 "terms according to Ptolemy", I.11-I.12 sign qualities and genders
  ptolemy_planets.csv      I.4 natures, I.5 beneficent/maleficent, I.6 genders, I.7 sects,
                           III.13 the planet ruling the soul "in an honourable position" / "in the opposite position"
  ptolemy_places.csv       III.10 places of authority, I.24 power by position, and what Ptolemy reads from each place
  ptolemy_testimonies.csv  the testimonies counted for each planet, with app weights (Ptolemy gives no numbers)
  ptolemy_uncertainty.csv  every place where the app adapts or departs from the text

APP ADAPTATIONS (user decisions): the signs are the real IAU constellations on the ecliptic at their true widths (Ptolemy
himself counts them from the equinoxes, I.22), and the places are constellation places: place 1 is the whole
constellation that holds the point 5 degrees above the Ascendant (III.10), places 2-12 the constellations that follow,
with Ophiuchus joined to Scorpius's place. Degree rules (terms) are stretched across each constellation's width.

The result has the same shape as lilly_layer.interpret(), so the pages can show either; each item carries a tag:
'Ptolemy' (sourced) or 'app rule'.
"""
import os
import pandas as pd

import lilly_layer as ll
import sidereal_engine as se

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda f: os.path.join(HERE, 'data', f)
PDG = pd.read_csv(D('ptolemy_dignities.csv'), encoding='utf-8').fillna('')
PN = pd.read_csv(D('ptolemy_planets.csv'), encoding='utf-8').fillna('').set_index('planet')
PL = pd.read_csv(D('ptolemy_places.csv'), encoding='utf-8').fillna('').set_index('place')
TW = pd.read_csv(D('ptolemy_testimonies.csv'), encoding='utf-8').set_index('rule_id')
BY_SIGN = PDG.set_index('sign')
BY_IAU = PDG.set_index('iau_constellation')
PLANETS = ll.PLANETS
BENEFIC, MALEFIC = ('Jupiter', 'Venus'), ('Saturn', 'Mars')
SECT = {'Sun': 'diurnal', 'Jupiter': 'diurnal', 'Saturn': 'diurnal', 'Moon': 'nocturnal', 'Venus': 'nocturnal',
        'Mars': 'nocturnal', 'Mercury': 'common'}                     # I.7
FACE_K = {'Mercury': 1, 'Venus': 2, 'Mars': 3, 'Jupiter': 4, 'Saturn': 5}   # signs from the luminaries' houses (I.17)
FACE_ORB, RAYS, NODE_ORB = 3.0, 15.0, 6.0                            # app rules (ptolemy_uncertainty.csv)
AUTHORITY = [10, 1, 11, 7, 9]                                        # III.10: the order of the places of authority
ANGLES = (1, 4, 7, 10)
NO_ASPECT = (2, 6, 8, 12)                                            # places that bear no aspect to the orient (I.24)
ROBBINS = 'https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Ptolemy/Tetrabiblos/'
CH_FILE = {'I': {**{n: '1A' for n in (1, 2, 3)}, **{n: '1B' for n in range(4, 25)}},
           'II': {**{n: '2A' for n in (1, 2, 3)}, **{n: '2B' for n in range(4, 10)}, **{n: '2C' for n in range(10, 14)}},
           'III': {**{n: '3A' for n in range(1, 10)}, 10: '3B', 11: '3C', 12: '3C', 13: '3D', 14: '3D'},
           'IV': {**{n: '4A' for n in (1, 2, 3, 4)}, **{n: '4B' for n in (5, 6, 7)}, **{n: '4C' for n in (8, 9, 10)}}}
sep = ll.sep
_ord = ll._ord


def text_url(chapter, page=None):
    """LacusCurtius page of a chapter ('III.13'), at the Loeb page if given."""
    b, n = chapter.split('.')
    f = CH_FILE.get(b, {}).get(int(n))
    if not f:
        return ROBBINS + 'home.html'
    return f"{ROBBINS}{f}*.html" + (f'#p{int(page)}' if page else f'#{int(n)}')


def P(rule):
    return int(TW.loc[rule, 'points'])


def W(rule):
    return TW.loc[rule, 'wording']


def place_name(n):
    return PL.loc[int(n), 'name']


def place_points(n):
    return int(PL.loc[int(n), 'points'])


# ---------------------------------------------------------------- signs and places
def placement(lon, bands):
    """Sign (= IAU zodiac constellation) and equivalent degree 0-30 (rescaled, app rule)."""
    name, s, w, f = ll.band_of(lon, bands)
    if name in BY_IAU.index:
        return dict(constellation=name, sign=BY_IAU.loc[name, 'sign'], sign_deg=30.0 * f, band_start=s, band_width=w,
                    has_sign=True)
    return dict(constellation=name, sign=None, sign_deg=None, band_start=s, band_width=w, has_sign=False)


def zodiac_places(bands):
    """The twelve constellation bands that make the places: Ophiuchus joined to Scorpius (app rule).
    Returns [(start_lon, name)] in zodiacal order."""
    zs = []
    for s, _abbr, name in bands:
        if name == 'Ophiuchus' or (zs and zs[-1][1] == name):
            continue
        zs.append((s, name))
    if len(zs) > 1 and zs[0][1] == zs[-1][1]:          # Pisces split at 0 degrees: keep its real start
        zs = zs[1:]
    return zs


def places(asc_lon, bands):
    """Constellation places (user decision, after III.10): place 1 is the constellation holding the point 5 degrees
    above the Ascendant; the others follow in zodiacal order. Returns (12 cusps, 12 constellation names)."""
    zs = zodiac_places(bands)
    n = len(zs)
    point = (asc_lon - 5.0) % 360
    k = 0
    for i, (s, _) in enumerate(zs):
        w = (zs[(i + 1) % n][0] - s) % 360 or 360
        if (point - s) % 360 < w:
            k = i
            break
    order = [zs[(k + j) % n] for j in range(n)]
    return [s for s, _ in order], [nm for _, nm in order]


def place_of(lon, cusps):
    return se.house_of(lon, cusps, five_degree_rule=False)


def term_ruler(sign, deg):
    r = BY_SIGN.loc[sign]
    for i in range(1, 6):
        if deg < float(r[f'term{i}_end']):
            return r[f'term{i}']
    return r['term5']


def planet_sect(planet, b):
    """I.7: Mercury is diurnal as a morning star, nocturnal as an evening star."""
    if planet == 'Mercury':
        return 'diurnal' if b['elong'] < 0 else 'nocturnal'
    return SECT[planet]


def sign_sect(sign):
    return SECT[BY_SIGN.loc[sign, 'domicile']]


def _trip(r, is_day):
    return (r['triplicity_day'], r['co_ruler_day']) if is_day else (r['triplicity_night'], r['co_ruler_night'])


# ---------------------------------------------------------------- essential familiarity (Book I)
def essential(planet, pl, is_day, b, lons):
    items = []
    if not pl['has_sign']:
        items.append(('no_sign', W('no_sign'), P('no_sign'), 'app rule'))
        return items
    r = BY_SIGN.loc[pl['sign']]
    deg = pl['sign_deg']
    fam = 0
    if r['domicile'] == planet:
        items.append(('domicile', W('domicile'), P('domicile'), 'Ptolemy I.17')); fam += 1
    if r['exaltation'] == planet:
        items.append(('exaltation', W('exaltation'), P('exaltation'), 'Ptolemy I.19')); fam += 1
    trip, co = _trip(r, is_day)
    when = 'by day' if is_day else 'by night'
    if trip == planet:
        items.append(('triplicity', f"{W('triplicity')} ({when})", P('triplicity'), 'Ptolemy I.18')); fam += 1
    elif co == planet:
        items.append(('co_triplicity', f"{W('co_triplicity')} ({when}, with Mars)", P('co_triplicity'), 'Ptolemy I.18')); fam += 1
    if term_ruler(pl['sign'], deg) == planet:
        items.append(('term', W('term'), P('term'), 'Ptolemy I.21 + app rescaling')); fam += 1
    if fam >= 2:
        items.append(('chariot', W('chariot'), P('chariot'), 'Ptolemy I.23'))
    face = proper_face(planet, lons)
    if face:
        items.append(('proper_face', f"{W('proper_face')} ({face})", P('proper_face'), 'Ptolemy I.23 (orb: app rule)'))
    if r['depression'] == planet:
        items.append(('depression', W('depression'), P('depression'), 'Ptolemy I.19'))
    if fam == 0:
        ss, ps = sign_sect(pl['sign']), planet_sect(planet, b)
        if ss == ps:
            items.append(('rejoice', W('rejoice'), P('rejoice'), 'Ptolemy I.23'))
        elif ss == 'common':
            items.append(('no_familiarity', W('no_familiarity'), P('no_familiarity'), 'app rule'))
        else:
            items.append(('alien', W('alien'), P('alien'), 'Ptolemy I.23'))
    return items


def proper_face(planet, lons):
    """I.23: the planet keeps to the Sun or Moon the aspect its house has to their houses (Venus: 60 degrees east of the
    Sun, or 60 degrees west of the Moon). Returns a short description or ''."""
    k = FACE_K.get(planet)
    if not k:
        return ''
    ang = 30 * k
    if abs((lons[planet] - lons['Sun']) % 360 - ang) <= FACE_ORB:
        return f"{ang}° east of the Sun"
    if abs((lons['Moon'] - lons[planet]) % 360 - ang) <= FACE_ORB:
        return f"{ang}° west of the Moon"
    return ''


# ---------------------------------------------------------------- position and phase (I.24, I.7, III.13)
def accidental(planet, b, place, is_day, aspects, lons):
    it = []
    it.append((f'place_{place}', f"In {place_name(place)} (place {place})", place_points(place),
               'Ptolemy I.24, III.10 (points: app weight)'))
    e = b['elong']
    if planet not in ('Sun', 'Moon'):
        it.append(('oriental', W('oriental'), P('oriental'), 'Ptolemy I.24') if e < 0
                  else ('occidental', W('occidental'), P('occidental'), 'Ptolemy I.24'))
        mean = ll.OM.loc[planet, 'mean_motion_arcmin_per_day'] / 60.0
        sp = b['speed']
        if sp > 0 and sp > mean:
            it.append(('adding_motion', f"{W('adding_motion')} ({sp * 60:.0f}' a day; mean {ll.OM.loc[planet, 'mean_motion_text']})",
                       P('adding_motion'), 'Ptolemy I.24 (app rule: direct and faster than mean)'))
        else:
            how = 'retrograde' if sp < 0 else 'slower than its mean'
            it.append(('diminishing_motion', f"{W('diminishing_motion')} ({how}, {abs(sp) * 60:.0f}' a day)",
                       P('diminishing_motion'), 'Ptolemy I.24 (app rule)'))
    if planet == 'Moon':
        it.append(('moon_waxing', W('moon_waxing'), P('moon_waxing'), 'Ptolemy III.13') if e > 0
                  else ('moon_waning', W('moon_waning'), P('moon_waning'), 'Ptolemy III.13'))
    if planet != 'Sun' and b['sun_dist'] <= RAYS:
        it.append(('under_rays', f"{W('under_rays')} ({b['sun_dist']:.1f}° from the Sun)", P('under_rays'),
                   'Ptolemy III.13 (15°: app rule)'))
    fig = 'diurnal' if is_day else 'nocturnal'
    ps = planet_sect(planet, b)
    it.append(('in_sect', f"{W('in_sect')} ({fig})", P('in_sect'), 'Ptolemy I.7') if ps == fig
              else ('out_of_sect', f"{W('out_of_sect')} ({ps}, in a {fig} figure)", P('out_of_sect'), 'Ptolemy I.7'))
    good, bad, ov_good, ov_bad = [], [], [], []
    for a in aspects:
        if planet not in (a['a'], a['b']):
            continue
        other = a['b'] if a['a'] == planet else a['a']
        dexter = a['aspect'] == 'square' and abs((lons[planet] - lons[other]) % 360 - 90) <= a['moiety']
        if other in BENEFIC:
            if dexter:
                ov_good.append(other)
            elif a['aspect'] in ('conjunction', 'sextile', 'trine'):
                good.append(f"{other} ({a['aspect']})")
        if other in MALEFIC:
            if dexter:
                ov_bad.append(other)
            elif a['aspect'] in ('conjunction', 'square', 'opposition'):
                bad.append(f"{other} ({a['aspect']})")
    join = lambda xs: ' and '.join(xs)
    if good:
        it.append(('benefic_aspect', f"In familiarity with {join(good)}", P('benefic_aspect'), 'Ptolemy III.13 (orbs: app rule)'))
    if ov_good:
        it.append(('overcome_benefic', f"Overcome by {join(ov_good)} (dexter square)", P('overcome_benefic'), 'Ptolemy IV.4 (orbs: app rule)'))
    if bad:
        it.append(('malefic_aspect', f"Afflicted by {join(bad)}", P('malefic_aspect'), 'Ptolemy III.13 (orbs: app rule)'))
    if ov_bad:
        it.append(('overcome_malefic', f"Overcome by {join(ov_bad)} (dexter square)", P('overcome_malefic'), 'Ptolemy III.13 (orbs: app rule)'))
    return it


# ---------------------------------------------------------------- domination: the five ways (III.2-III.3)
def ways_to(lon, pl, is_day, lons, orb_col='orb_lilly'):
    """{planet: [ways]} for a degree: house, triangle, exaltation, terms, and aspect ('phase or aspect', read as an
    aspect to the degree within the planet's moiety - app rule). A degree in Ophiuchus has no sign, so no ruler."""
    if not pl['has_sign']:
        return {}
    r = BY_SIGN.loc[pl['sign']]
    out = {p: [] for p in PLANETS}
    out[r['domicile']].append('house')
    trip, co = _trip(r, is_day)
    out[trip].append('triangle')
    if co:
        out[co].append('co-rulership of the triangle')
    if r['exaltation']:
        out[r['exaltation']].append('exaltation')
    out[term_ruler(pl['sign'], pl['sign_deg'])].append('terms')
    for p in PLANETS:
        orb = ll.OM.loc[p, orb_col] / 2
        s = sep(lons[p], lon)
        if s > 0.01 and any(abs(s - ang) <= orb for _, ang in ll.ASPECTS):
            out[p].append('aspect')
    return {p: w for p, w in out.items() if w}


def choose(ways, info, is_day):
    """The planet with most ways; ties: the place of greater authority (III.10), then the sect, then the net score."""
    if not ways:
        return None, []
    fig = 'diurnal' if is_day else 'nocturnal'
    rank = lambda p: AUTHORITY.index(info[p]['house']) if info[p]['house'] in AUTHORITY else 9
    best = sorted(ways, key=lambda p: (-len(ways[p]), rank(p), info[p]['sect'] != fig, -info[p]['net']))[0]
    return best, ways[best]


def ways_text(ws):
    ws = list(ws)
    return ws[0] if len(ws) == 1 else ', '.join(ws[:-1]) + ' and ' + ws[-1]


# ---------------------------------------------------------------- main entry
def interpret(rows, bands, stars, sun_up, orb_col='orb_lilly'):
    """rows: engine chart rows; bands: ecliptic bands; stars: unused (kept for the same call as Lilly's layer);
    sun_up: True for a day chart."""
    by = {r['body']: r for r in rows}
    asc_lon = by['Ascendant']['ecl_lon']
    cusps, names = places(asc_lon, bands)
    lons = {p: by[p]['ecl_lon'] for p in PLANETS}
    pl = {p: placement(lons[p], bands) for p in PLANETS}
    asp = ll.aspects(by, orb_col)
    out = []
    for p in PLANETS:
        b = by[p]
        h = place_of(b['ecl_lon'], cusps)
        ess = essential(p, pl[p], sun_up, b, lons)
        acc = accidental(p, b, h, sun_up, asp, lons)
        ef, edb, en = ll.score(ess)
        f, d, n = ll.score(ess + acc)
        cond = 'well dignified' if n > 0 else 'ill dignified' if n < 0 else 'neither well nor ill dignified'
        honour = 'in an honourable position' if n > 0 else 'in a position of the opposite kind' if n < 0 else \
            'neither honourable nor the opposite'
        out.append(dict(planet=p, constellation=pl[p]['constellation'], sign=pl[p]['sign'], sign_deg=pl[p]['sign_deg'],
                        true_constellation=b['constellation'], house=h, essential=ess, accidental=acc,
                        essential_score=en, fortitudes=f, debilities=d, net=n, condition=cond, honour=honour,
                        sect=planet_sect(p, b), retrograde=b['speed'] < 0, speed=b['speed'], ecl_lon=b['ecl_lon'],
                        elong=b['elong']))
    info = {x['planet']: x for x in out}
    asc_pl = placement(asc_lon, bands)
    lord, lord_ways = choose(ways_to(asc_lon, asc_pl, sun_up, lons, orb_col), info, sun_up)
    # the governor of the soul: the planet that dominates both Mercury and the Moon (III.13)
    soul = {}
    for k in ('Mercury', 'Moon'):
        for p, w in ways_to(lons[k], pl[k], sun_up, lons, orb_col).items():
            if p != k:
                soul.setdefault(p, []).extend(f"{x} ({k})" for x in w)
    governor, governor_ways = choose(soul, info, sun_up)
    pof = by['Part of Fortune']
    pof_pl = placement(pof['ecl_lon'], bands)
    fortune_ruler = BY_SIGN.loc[pof_pl['sign'], 'domicile'] if pof_pl['has_sign'] else None
    mc_pl = placement(by['Midheaven']['ecl_lon'], bands)
    return dict(school='Ptolemy', planets=out, asc=asc_pl, mc=mc_pl, lord_of_asc=lord, lord_ways=lord_ways,
                soul_governor=governor, soul_ways=governor_ways, sun_up=sun_up, sect='diurnal' if sun_up else 'nocturnal',
                part_of_fortune=dict(ecl_lon=pof['ecl_lon'], house=place_of(pof['ecl_lon'], cusps), **pof_pl),
                fortune_ruler=fortune_ruler, aspects=asp, cusps=cusps, place_constellations=names,
                cusp_signs=[placement(c, bands) for c in cusps])


# ---------------------------------------------------------------- Ptolemy's words
def _ellipsis(text):
    """A quotation that starts inside Ptolemy's sentence begins with an ellipsis."""
    return ('… ' + text) if text[:1].islower() else text


def the(planet):
    """'the Sun', 'the Moon', 'Venus'."""
    return f'the {planet}' if planet in ('Sun', 'Moon') else planet


def reading(planet, condition, R=None, rows=None):
    """Ptolemy's picture of the planet as ruler of the soul (III.13): 'in an honourable position' or 'in the opposite
    position'. The Moon is read by her phase (and the nodes when she is near one), the Sun by his position.
    Returns (text, cite, label)."""
    r = PN.loc[planet]
    if planet == 'Moon':
        P_ = {p['planet']: p for p in (R or {}).get('planets', [])}
        waxing = P_.get('Moon', {}).get('elong', 1) > 0
        text, cite = (r['honourable'], r['honourable_cite']) if waxing else (r['opposite'], r['opposite_cite'])
        label = 'increasing in light' if waxing else 'waning'
        if rows is not None:
            by = {x['body']: x for x in rows}
            if min(sep(by['Moon']['ecl_lon'], by['North Node']['ecl_lon']),
                   sep(by['Moon']['ecl_lon'], by['South Node']['ecl_lon'])) <= NODE_ORB:
                text = text.rstrip('.') + ' ... at the nodes, in the direction of greater keenness, activity, and excitability.'
                label += ', near a node'
        return _ellipsis(text), cite, label
    if condition == 'ill dignified':
        return _ellipsis(r['opposite']), r['opposite_cite'], 'in the opposite position'
    return _ellipsis(r['honourable']), r['honourable_cite'], 'in an honourable position'


def nature(planet):
    r = PN.loc[planet]
    return r['nature'], r['nature_cite']


def house_meaning(n, maxlen=240):
    s = PL.loc[int(n), 'meaning']
    return (s[:maxlen].rsplit(' ', 1)[0] + ' ...') if len(s) > maxlen else s


def place_cite(n):
    return PL.loc[int(n), 'cite']
