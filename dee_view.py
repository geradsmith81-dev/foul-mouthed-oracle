"""The Chart page in John Dee's reading (sidebar 'Whose reading?' > John Dee).

This is the user's Sidereal Enochian Chart app (package enochian/) run on this app's own engine: the Heptarchic
King and Prince who govern the day, the ministering angels of the six parts of the day, the zodiac Kings of
Liber Scientiae for each body's real IAU constellation, and the Part of the Earth for the place. Sources:
J. H. Peterson (ed.), John Dee's Five Books of Mystery; G. James, The Enochian Evocation of Dr John Dee. The
strengths and weaknesses are the Enochian app's own interpretive rules (enochian/data/forecast_rules.csv), not Dee's.
Dee's system has no houses, no dignity points and no aspects, so the wheel shows none.
"""
import datetime as dt

import pandas as pd
import streamlit as st

import sidereal_engine as se
import glossary
import device
from enochian import layer as en
from enochian import forecast as efc

CLASSICAL = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']
CORR = en.H.set_index('weekday')
DISCLAIMER = ("This reading applies fixed rules from Dee's angelic tables to the real sky. It is offered for "
              "reflection and study, as a structured prompt for thinking about the day, not as a prediction; "
              "there is no scientific evidence that it foretells events.")


def _v(x):
    return None if x is None or (isinstance(x, float) and x != x) else x


def compute(utc, lat, lon, elev, convention='sunrise'):
    """Same return shape as the Chart page's other readings:
    rows, bands, cusps (None: no houses), R, ph, fc, asc, mc, stars, cusps_l (Lilly's, for the four undertakings)."""
    t, rows = se.chart(utc, lat, lon, elev)
    bands = se.ecliptic_constellation_bands(t, step=0.05)
    if bands[0][1] == bands[-1][1]:
        bands = bands[1:]
    cusps_l = se.regiomontanus_cusps(t, lat, lon)
    stars = se.fixed_stars(t)
    sun_up = [r for r in rows if r['body'] == 'Sun'][0]['alt'] > -0.8333
    _, summary, tab = en.interpret(utc, lat, lon, elev, convention, t=t, rows=rows)
    fc = efc.build(summary, tab)
    ph = se.planetary_hour(t, lat, lon, elev)
    asc, mc = se.angles(t, lat, lon)
    T = tab.set_index('body')
    asc_c = T.loc['Ascendant', 'iau_constellation'] if 'Ascendant' in T.index else ''
    asc_k = _v(T.loc['Ascendant', 'zodiac_king']) if 'Ascendant' in T.index else None
    R = dict(school='Dee', sun_up=sun_up, planets=[], aspects=[], cusps=None, lord_of_asc=None,
             asc=dict(constellation=asc_c, has_sign=bool(asc_k), zodiac_king=asc_k),
             summary=summary, tab=[{k: _v(v) for k, v in r.items()} for r in tab.to_dict('records')])
    return rows, bands, None, R, ph, fc, asc, mc, stars, cusps_l


def part_window(summary, utc_dt, lon, tz_hours):
    """Local clock times (start, end) of the current part of the Heptarchic day, and the day's start."""
    if summary.get('day_start_utc') and summary.get('next_day_start_utc'):
        start = dt.datetime.fromisoformat(summary['day_start_utc'].replace('Z', '+00:00')).replace(tzinfo=None)
        end = dt.datetime.fromisoformat(summary['next_day_start_utc'].replace('Z', '+00:00')).replace(tzinfo=None)
    else:                                         # midnight convention: Local Mean Time midnight to midnight
        lmt = utc_dt + dt.timedelta(hours=lon / 15.0)
        start = dt.datetime.combine(lmt.date(), dt.time()) - dt.timedelta(hours=lon / 15.0)
        end = start + dt.timedelta(days=1)
    n = int(summary['part_of_day'])
    step = (end - start) / 6
    a, b = start + step * (n - 1), start + step * n
    shift = dt.timedelta(hours=tz_hours)
    return a + shift, b + shift, start + shift


def the(p):
    return f'the {p}' if p in ('Sun', 'Moon') else p


# ---------------------------------------------------------------- right-hand column
def right_column(R, utc_dt, lon, tz):
    s = R['summary']
    m = s['ministers']
    st.subheader(f"Heptarchic day: {s['weekday']}")
    a, b, day0 = part_window(s, utc_dt, lon, tz)
    if s.get('day_start_utc'):
        st.caption(f"Counted from local sunrise ({day0:%H:%M} local), as chosen for this app; Dee was never told when "
                   f"the day begins.")
    else:
        st.caption(f"Counted from local mean midnight. {s['convention']}.")
    c1, c2, c3 = st.columns(3)
    c1.metric('King', s['day_king'], help=glossary.TERMS['d_heptarchy'][1])
    c2.metric('Prince', s['day_prince'], help=glossary.TERMS['d_heptarchy'][1])
    c3.metric('Part of the day', f"{s['part_of_day']} of 6", help=glossary.TERMS['d_ministers'][1])
    st.markdown(f"**Realm:** {s['day_realm']}")
    with st.container(border=True):
        st.markdown(f"**Ministers of part {s['part_of_day']}** (about {a:%H:%M}–{b:%H:%M} local)")
        part = m.get('part') or {}
        if part.get('names_dee_letters'):
            st.markdown(f"Dee's letters: `{part['names_dee_letters']}`  \nJames's names: {part['names_james_rotation']}")
        else:
            st.markdown('The source does not record the ministers for this part.')
        if m.get('whole_day') and m['whole_day'].get('names_dee_letters'):
            st.markdown(f"Whole-day six (Peterson): `{m['whole_day']['names_dee_letters']}`")
    pe = s['part_of_the_earth']
    st.markdown('**Part of the Earth (this place)**')
    if pe['parts']:
        for p in pe['parts']:
            st.markdown(f"**{p['angel']}**, {p['country']} ({p['modern_identification']}) · Aethyr **{p['aire']}** · "
                        f"{p['ministers']:,} ministers · King {p['zodiac_king']} ({p['sign']}) · tribe of "
                        f"{p['tribe']} · facing {p['quarter']}")
    st.caption(pe['status'])
    glossary.chips(['d_heptarchy', 'd_ministers', 'd_day_start', 'd_part_earth', 'd_aethyr'], 'dee_day')


# ---------------------------------------------------------------- Full view
def bodies_table(R):
    tab = pd.DataFrame(R['tab'])
    show = tab.rename(columns={'body': 'Body', 'ecl_lon': 'Ecl. long. (°)', 'iau_constellation': 'IAU constellation',
                               'above_horizon': 'Above horizon', 'heptarchic_king': 'Heptarchic King',
                               'heptarchic_prince': 'Prince', 'king_planet': 'Planet (Dee table)',
                               'zodiac_king': 'Zodiac King', 'tribe': 'Tribe', 'quarter': 'Face'})
    cols = [c for c in ['Body', 'Ecl. long. (°)', 'IAU constellation', 'Above horizon', 'Heptarchic King', 'Prince',
                        'Planet (Dee table)', 'Zodiac King', 'Tribe', 'Face'] if c in show]
    return show[cols]


def full_sections(R, rows, glyph):
    s = R['summary']
    T = {r['body']: r for r in R['tab']}
    st.subheader("The planets in Dee's tables")
    st.caption("Each of the seven planets belongs to one of the seven Heptarchic Kings (from Dee's Table of the 49 "
               "Good Angels, as read by James), and each body takes the zodiac King of the IAU constellation it "
               "actually stands in. Ophiuchus and the constellations off the zodiac have no King. Dee's system has "
               "no dignity points, houses or aspects.")
    told, notes_told = {}, {}

    def once(text, who):
        """A note shared by several planets is written in full once, then pointed back to (no repeats on a page)."""
        if text in notes_told:
            return f"as noted under {notes_told[text]} above"
        notes_told[text] = who
        return text

    for b in CLASSICAL:
        r = T.get(b)
        if not r:
            continue
        zk = r.get('zodiac_king')
        head = (f"{glyph.get(b, '')} {b} in {r['iau_constellation']} · King {r.get('heptarchic_king') or '—'}"
                + (f" · zodiac King {zk}" if zk else ' · no zodiac King') + (' · above the horizon' if r.get('above_horizon') else ''))
        with st.expander(head):
            c = CORR[CORR['planet_trad'] == b]
            if not c.empty:
                c = c.iloc[0]
                if c['king'] == s['day_king']:
                    st.markdown(f"**King {c['king']}** (the King of this day) and **Prince {c['prince']}**, ruling on "
                                f"{c.name}. Their realm is given at the top of the page.")
                else:
                    st.markdown(f"**King {c['king']}** and **Prince {c['prince']}**, ruling on {c.name}.  \n"
                                f"**Realm:** {c['realm']}  \nIn everyday words: {c['realm_plain']}.")
                st.caption(f"Planet in Dee's table: King {c['king_planet']}, Prince {c['prince_planet']}. "
                           f"Basis: {once(c['planet_basis'], b)} · {c['cites']}")
                if isinstance(c.get('ensign'), str) and c['ensign'].strip():
                    st.caption(f"Ensign: {once(c['ensign'], b)}")
            if zk:
                key = zk
                if key in told:
                    st.markdown(f"**Zodiac King {zk}**: as told under {told[key]} above.")
                else:
                    told[key] = b
                    st.markdown(f"**Zodiac King {zk}** ({r.get('zodiac_sign')}), of the tribe of {r.get('tribe')}, "
                                f"facing {r.get('quarter')} (Liber Scientiae; sign attribution after James).")
            else:
                st.markdown(f"**No zodiac King:** {r['iau_constellation']} "
                            + ("is the IAU's thirteenth ecliptic constellation, which has none in Dee's twelve."
                               if r['iau_constellation'] == 'Ophiuchus' else 'lies outside the zodiac constellations.'))
    glossary.chips(['d_heptarchy', 'd_zodiac_king'], 'dee_planets')

    st.subheader(f"The ministers of {s['weekday']}")
    mins = en.MIN[en.MIN.weekday == s['weekday']].copy()
    mins['now'] = mins['part_of_day'].astype(str) == str(s['part_of_day'])
    tbl = pd.DataFrame({'Part of the day': mins['part_of_day'], "Dee's letters": mins['angels'],
                        "James's names": mins['james_rotation_names'].fillna(''),
                        'Now': mins['now'].map({True: '◀ now', False: ''}), 'Status': mins['status']})
    device.table(tbl, ['Part of the day', "Dee's letters", 'Now'])
    st.caption("Each letter is one angel: \"The Letters onely ... are theyr names\" (Peterson, PDF p157). James's "
               "seven-letter rotations are shown beside them, as chosen for this app.")

    st.subheader('Bodies')
    device.table(bodies_table(R), ['Body', 'IAU constellation', 'Zodiac King'])

    with st.expander('Sources and certainty'):
        st.markdown('Each statement is tagged **sourced**, **inferred** or **app design rule**. Sources: J. H. Peterson '
                    "(ed.), *John Dee's Five Books of Mystery*; G. James, *The Enochian Evocation of Dr John Dee*; "
                    "Skinner's introduction to *Dr John Dee's Spiritual Diaries*. The strengths and weaknesses of the "
                    "Forecast are this app's interpretive rules, not Dee's. The tables are in the folder enochian/data.")
        device.table(pd.read_csv(en.D('uncertainty_log.csv'), encoding='utf-8'))


# ---------------------------------------------------------------- the plain-English window
def plain_sections(R, utc_dt, lon, tz):
    """[(heading, markdown)] for 'What does this mean?' in Dee's reading (the Enochian app's own wording)."""
    s = R['summary']
    wd = s['weekday']
    row = CORR.loc[wd]
    out = []
    a, b, day0 = part_window(s, utc_dt, lon, tz)
    start_word = 'sunrise' if s.get('day_start_utc') else 'midnight'
    out.append(('Who is in charge today',
                f"In Dee's angelic week this is **{wd}**, counted from {start_word} ({day0:%H:%M} local time). "
                f"It is overseen by **King {s['day_king']}** and his **Prince {s['day_prince']}**, linked with "
                f"{the(row['planet_trad'])}. In everyday words, their area is **{row['realm_plain']}**."))
    m = s['ministers']
    part = m.get('part') or {}
    txt = (f"The angelic day is split into six equal parts, and this is **part {s['part_of_day']}**, "
           f"about **{a:%H:%M}–{b:%H:%M}** local time.")
    if part.get('names_dee_letters'):
        txt += (f" Seven ministering angels serve in this part. Dee wrote each one as a single letter: "
                f"**{part['names_dee_letters']}**; James reads them as the names {part['names_james_rotation']}.")
    else:
        txt += ' The source does not record the names of the ministering angels for this part.'
    if m.get('whole_day') and m['whole_day'].get('names_dee_letters'):
        txt += f" Six more, **{m['whole_day']['names_dee_letters']}**, stand by the King for the whole day."
    out.append(('Right now', txt))
    pe = s['part_of_the_earth']
    if pe.get('parts'):
        p = pe['parts'][0]
        out.append(('Where you are',
                    f"Dee divided the world known in his day into 91 regions, each with a guardian angel. This place "
                    f"falls in **{p['country']}** (roughly {p['modern_identification']}), guarded by **{p['angel']}**, "
                    f"under the sign-angel {p['zodiac_king']} ({p['sign']}). The match is made by distance to the "
                    f"region's approximate centre, so treat it as a guide."))
    else:
        out.append(('Where you are', "Dee's 91 regions cover only the world known in his day; this place is outside "
                                     "them, so no regional guardian applies."))
    return out
