"""
Enochian interpretation layer - step 3.

Source: J. H. Peterson (ed.), John Dee's Five Books of Mystery, Book 4 (Nov. 1582).
Data: heptarchia_correspondences.csv (King/Prince/day) and heptarchia_ministers.csv
(minister letter-angels). Every row cites PDF pages/endnotes and states its basis.

Day rule: "The King and prince gouern for the whole daye ... The rest according to
the six partes of the day" (PDF p160). Dee was never told when the day begins: p160 "Thow shalt be towght the rest"; on
5 May 1583 (p260) Uriel declined to answer, calling it "most easy, and perfectly deliuered".
DEFAULT (user decision, confirmed after reading James) = 'sunrise': the planetary day runs from local sunrise to the next local
sunrise, computed for the chart's latitude, longitude and elevation (Sun's upper limb
on the horizon, standard refraction -0.8333 deg, minus horizon dip 0.0293*sqrt(h_m) deg).
The day is split into six equal parts. If there is no sunrise (polar day or night),
the code falls back to local-mean-time midnight and flags it.
Alternative: convention='midnight' (Local Mean Time from longitude).

Planet to King: SOURCED from Dee's Table of the 49 Good Angels as read by G. James,
The Enochian Evocation of Dr John Dee (App. A); the Kings' planets match the weekday rulers.
Ministers: James's Table of the 42 Ministers (from Sloane 3191), with row n serving part n
of the day. Peterson's Sunday whole-day six (LEE+BLN) is also reported.
Zodiac Kings (Liber Scientiae): 12 angelic Kings, one per sign (James App. A p186), each with
a tribe of Israel and a quarter of the earth (Book Four table). APP DESIGN RULE: a body in
an IAU zodiacal constellation gets that sign's King. Ophiuchus and non-zodiacal
constellations (e.g. Cetus, Orion) get none.
Part of the Earth: the chart location's governing Part(s) from the 91 Parts (James Book Four),
found through an approximate app gazetteer of Ptolemaic regions (see part_of_earth).
"""
import os
from datetime import timedelta
from math import sqrt
import pandas as pd
from skyfield import almanac
from skyfield.api import wgs84
import sidereal_engine as se          # the host app's engine (same DE440s positions, IAU constellations by RA/Dec)

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda f: os.path.join(HERE, 'data', f)
# the bodies the Enochian app reads (the host engine also gives the nodes and the Part of Fortune, which Dee has not)
DEE_BODIES = ('Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto',
              'Ascendant', 'Midheaven')

WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
H = pd.read_csv(D('heptarchia_correspondences.csv'), encoding='utf-8')
MIN = pd.read_csv(D('heptarchia_ministers.csv'), encoding='utf-8', dtype=str)
BY_DAY = H.set_index('weekday')
BY_PLANET = H.set_index('planet_trad')
ZK = pd.read_csv(D('zodiac_kings.csv'), encoding='utf-8').set_index('iau_constellation')
PARTS = pd.read_csv(D('parts_of_the_earth.csv'), encoding='utf-8')


def part_of_earth(lat, lon, max_km=1000.0):
    """Part(s) of the Earth (Liber Scientiae, 91 Parts) governing a location.
    Uses the APP GAZETTEER: an approximate centre for each identifiable Ptolemaic region,
    my identification, not in any source. Takes the nearest region within max_km and
    returns every Part sharing that region (Dee lists some regions twice, e.g. Assyria 25/85).
    27 Parts are not yet placed and can never be returned."""
    from math import radians, sin, cos, asin, sqrt
    loc = PARTS.dropna(subset=['lat_approx']).copy()
    def hav(a, b, c, d):
        a, b, c, d = map(radians, (a, b, c, d))
        return 2 * 6371.0 * asin(sqrt(sin((c - a) / 2) ** 2 + cos(a) * cos(c) * sin((d - b) / 2) ** 2))
    loc['dist_km'] = [hav(lat, lon, la, lo) for la, lo in zip(loc.lat_approx, loc.lon_approx)]
    dmin = loc.dist_km.min()
    if dmin > max_km:
        return dict(status=f'outside Dee\'s 91 Parts (nearest identified region {dmin:.0f} km away)', parts=[],
                    dist_km=int(round(dmin)))
    hit = loc[loc.dist_km <= dmin + 1.0]
    cols = ['no', 'country', 'angel', 'aire', 'ministers', 'zodiac_king', 'sign', 'tribe', 'quarter', 'modern_identification']
    return dict(dist_km=int(round(dmin)),
                status=f'nearest identified region, {dmin:.0f} km from its approximate centre (gazetteer is approximate)',
                parts=[{k: (v.item() if hasattr(v, 'item') else v) for k, v in r.items()} for r in hit[cols].to_dict('records')])


def _lmt(t, lon_deg):
    return t.utc_datetime() + timedelta(hours=lon_deg / 15.0)


def _midnight(t, lon, note=''):
    lmt = _lmt(t, lon)
    frac = (lmt.hour + lmt.minute / 60 + lmt.second / 3600) / 24
    return dict(convention='midnight (LMT)' + note, weekday=WEEKDAYS[lmt.weekday()],
                day_start_utc=None, next_day_start_utc=None, horizon_deg=None,
                part_of_day=int(frac * 6) + 1)


def day_governance(t, lat, lon, elev_m=0.0, convention='sunrise'):
    if convention != 'sunrise':
        return _midnight(t, lon)
    observer = se.eph['earth'] + wgs84.latlon(lat, lon, elevation_m=elev_m)
    horizon = -0.8333 - (0.0293 * sqrt(elev_m) if elev_m > 0 else 0.0)
    tr, ok = almanac.find_risings(observer, se.eph['sun'], t - 1.5, t + 1.5,
                                  horizon_degrees=horizon)
    rises = [ti for ti, o in zip(tr, ok) if o]
    before = [r for r in rises if r.tt <= t.tt]
    after = [r for r in rises if r.tt > t.tt]
    if not (before and after):
        return _midnight(t, lon, ' - FALLBACK: no sunrise at this latitude/date')
    start, end = before[-1], after[0]
    frac = (t.tt - start.tt) / (end.tt - start.tt)
    return dict(convention='sunrise (local)', weekday=WEEKDAYS[_lmt(start, lon).weekday()],
                day_start_utc=start.utc_iso(), next_day_start_utc=end.utc_iso(),
                horizon_deg=round(horizon, 4), part_of_day=int(frac * 6) + 1)


def ministers_for(weekday, part):
    m = MIN[MIN.weekday == weekday]
    whole = m[m.part_of_day == 'whole day']
    part_row = m[m.part_of_day == str(part)]
    if part_row.empty:
        part_row = m[m.part_of_day == 'all']
    def pick(d):
        if d.empty:
            return None
        r = d.iloc[0]
        val = lambda x: None if pd.isna(x) else x
        return dict(names_dee_letters=val(r['angels']),            # Dee (Peterson p157): the letters are the names
                    names_james_rotation=val(r['james_rotation_names']),  # James App. A p184: 7-letter rotations
                    group_label=val(r['group_label']), status=r['status'], basis=r['basis'], cites=r['cites'])
    return dict(whole_day=pick(whole), part=pick(part_row))


def interpret(utc, lat, lon, elev_m=0.0, convention='sunrise', t=None, rows=None):
    """As in the Enochian app. t, rows: an already computed host-engine chart (saves computing it twice)."""
    if t is None or rows is None:
        t, rows = se.chart(utc, lat, lon, elev_m)
    gov = day_governance(t, lat, lon, elev_m, convention)
    g = BY_DAY.loc[gov['weekday']]
    out = []
    for r in [x for x in rows if x['body'] in DEE_BODIES]:
        b = r['body']
        alt = r.get('alt')
        rec = dict(body=b, ecl_lon=round(r['ecl_lon'], 4), iau_constellation=r['constellation'],
                   above_horizon=None if alt is None or alt != alt else bool(alt > 0))
        if b in BY_PLANET.index:
            h = BY_PLANET.loc[b]
            rec.update(heptarchic_king=h['king'], heptarchic_prince=h['prince'], realm=h['realm'],
                       king_planet=h['king_planet'],
                       link_basis="sourced: Dee's Table of 49 Good Angels (via James)", cites=h['cites'])
        elif b in ('Uranus', 'Neptune', 'Pluto'):
            rec.update(link_basis='none: body unknown to Dee')
        else:
            rec.update(link_basis='chart angle: no Heptarchic link in source')
        c = r['constellation']
        if c in ZK.index:
            z = ZK.loc[c]
            rec.update(zodiac_king=z['zodiac_king'], zodiac_sign=z['sign'], tribe=z['tribe'], quarter=z['quarter'])
        else:
            rec.update(zodiac_king=None, zodiac_note='constellation has no Liber Scientiae King')
        out.append(rec)
    summary = dict(**gov, day_king=g['king'], day_prince=g['prince'], day_realm=g['realm'],
                   day_basis=g['day_basis'], day_cites=g['cites'],
                   ministers=ministers_for(gov['weekday'], gov['part_of_day']),
                   part_of_the_earth=part_of_earth(lat, lon))
    return t, summary, pd.DataFrame(out)
