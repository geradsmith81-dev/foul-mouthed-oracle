"""Page 1: the sidereal chart read through William Lilly's Christian Astrology (1647)."""
import calendar
import datetime as dt
import os
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use('Agg')

import sidereal_engine as se
import lilly_layer as ll
import chart_wheel as cw
import places
import inputs
import user_profile
import forecast
import glossary
import plain_forecast
import theme
import device
import school
import ptolemy_layer as pt
import ptolemy_forecast
import dee_view
import voice

HERE = os.path.dirname(os.path.abspath(__file__))
ORD = ll._ord


@st.cache_data(show_spinner=False, max_entries=16, ttl=3600)      # the spinner is shown at the call, in the app's voice
def run(utc, lat, lon, elev, beams_rule, orb_col):
    t, rows = se.chart(utc, lat, lon, elev)
    bands = se.ecliptic_constellation_bands(t, step=0.05)
    if bands[0][1] == bands[-1][1]:
        bands = bands[1:]
    cusps = se.regiomontanus_cusps(t, lat, lon)
    stars = se.fixed_stars(t)
    sun_up = [r for r in rows if r['body'] == 'Sun'][0]['alt'] > -0.8333
    R = ll.interpret(rows, bands, cusps, stars, sun_up, beams_rule=beams_rule, orb_col=orb_col)
    ph = se.planetary_hour(t, lat, lon, elev)
    fc = forecast.build(R, rows, bands, ph)
    asc, mc = se.angles(t, lat, lon)
    return rows, bands, cusps, R, ph, fc, asc, mc, stars


@st.cache_data(show_spinner=False, max_entries=16, ttl=3600)
def run_dee(utc, lat, lon, elev, convention):
    """The same moment read by John Dee's angelic tables (the Sidereal Enochian Chart). No houses (cusps None);
    cusps_l = Lilly's Regiomontanus cusps, still used for the four undertakings (Lilly's election rules)."""
    return dee_view.compute(utc, lat, lon, elev, convention)


@st.cache_data(show_spinner=False, max_entries=16, ttl=3600)
def run_ptolemy(utc, lat, lon, elev, orb_col):
    """The same chart read by Ptolemy's rules (Tetrabiblos). cusps = the constellation places; cusps_l = Lilly's
    Regiomontanus cusps, still used for the four undertakings (Lilly's election rules, in both modes)."""
    t, rows = se.chart(utc, lat, lon, elev)
    bands = se.ecliptic_constellation_bands(t, step=0.05)
    if bands[0][1] == bands[-1][1]:
        bands = bands[1:]
    cusps_l = se.regiomontanus_cusps(t, lat, lon)
    stars = se.fixed_stars(t)
    sun_up = [r for r in rows if r['body'] == 'Sun'][0]['alt'] > -0.8333
    R = pt.interpret(rows, bands, stars, sun_up, orb_col=orb_col)
    ph = se.planetary_hour(t, lat, lon, elev)
    fc = ptolemy_forecast.build(R, rows, bands, ph)
    asc, mc = se.angles(t, lat, lon)
    return rows, bands, R['cusps'], R, ph, fc, asc, mc, stars, cusps_l


user_profile.title('The Foul-Mouthed Oracle', 'The Foul-Mouthed Oracle')      # home page title (not personalised)
# subtitle under the title: The Sidereal Oracle's wording, plus the attitude
SUBTITLE = ('Horoscope readings of the real sky for any moment and place. Powerfully calculated using NASA JPL '
            'planet movements, and the actual constellation positions.')  # user's wording
st.markdown('<p class="lilly-subtitle" style="font-size:1.12rem; line-height:1.45; margin:-0.4rem 0 0.9rem 0; '
            'color:#f7f1ea;">' + voice.say(SUBTITLE + " No sugar-coating, no bullshit, and it doesn't give a damn "
                                           'about your feelings.', SUBTITLE) + '</p>', unsafe_allow_html=True)
PHONE = device.phone()
FULL = device.full_view()          # Simple view: the chart, the sky and the forecast; Full view: also the tables
PT = school.is_ptolemy()          # whose reading: Ptolemy (Tetrabiblos) or Lilly (Christian Astrology)
DEE = school.is_dee()             # ... or John Dee (the Sidereal Enochian Chart's angelic tables)

# Forecast rules -> the terms that explain them (the "i" buttons under the Forecast)
RULE_TERMS = {'radical': ['radical'], 'not_radical': ['radical', 'hours'], 'asc_early': ['considerations', 'ascendant'],
              'asc_late': ['considerations', 'ascendant'], 'asc_ophiuchus': ['sidereal'], 'moon_void': ['void'],
              'moon_via_combusta': ['via_combusta'], 'moon_late': ['considerations'], 'saturn_asc': ['considerations'],
              'saturn_7': ['considerations', 'houses'], 'lord_asc_combust': ['combust', 'lord_asc'],
              'lord_7_afflicted': ['considerations', 'retrograde'], 'testimonies_equal': ['fortitudes'],
              'lord_asc_strong': ['lord_asc', 'fortitudes'], 'lord_asc_weak': ['lord_asc', 'fortitudes'],
              'lord_asc_angular': ['angles'], 'lord_asc_cadent': ['angles'], 'moon_apply_benefic': ['applying', 'fortunes'],
              'moon_apply_malefic': ['applying', 'fortunes'], 'cazimi': ['cazimi'], 'reception': ['reception'],
              'fortune_angular': ['fortune', 'angles'], 'fortune_cadent': ['fortune', 'angles'],
              'ophiuchus_planet': ['sidereal'], 'polar': ['hours']}
# the same for the Enochian rules (John Dee's reading)
RULE_TERMS_DEE = {'day_planet_up': ['d_heptarchy'], 'day_planet_down': ['d_heptarchy'],
                  'day_planet_offzodiac': ['d_heptarchy', 'd_zodiac_king'], 'day_place_concord': ['d_zodiac_king', 'd_part_earth'],
                  'concentration': ['d_zodiac_king'], 'planet_offzodiac': ['d_zodiac_king'], 'planet_ophiuchus': ['d_zodiac_king', 'sidereal'],
                  'rising_place_concord': ['d_zodiac_king', 'd_part_earth'], 'place_clear': ['d_part_earth', 'd_aethyr'],
                  'place_approximate': ['d_part_earth'], 'place_none': ['d_part_earth'], 'no_sunrise': ['d_day_start']}
# the same for Ptolemy's rules (Ptolemy mode)
RULE_TERMS_PT = {'sect_light_authority': ['p_sect', 'p_places'], 'lights_masculine_angular': ['p_lights', 'p_gender'],
                 'light_benefic_attended': ['p_lights', 'p_benefic'], 'benefic_angular': ['p_benefic', 'p_places'],
                 'ruler_asc_strong': ['p_ruler', 'p_honour'], 'ruler_asc_weak': ['p_ruler', 'p_honour'],
                 'ruler_asc_powerless': ['p_ruler', 'p_places'], 'fortune_ruler_strong': ['p_fortune'],
                 'fortune_ruler_weak': ['p_fortune'], 'moon_waxing': ['p_moon'], 'moon_waning': ['p_moon'],
                 'malefic_angular': ['p_benefic', 'p_sect'], 'light_afflicted': ['p_lights', 'p_benefic'],
                 'lights_not_angular': ['p_lights', 'p_places'], 'evil_daemon': ['p_places'],
                 'asc_ophiuchus': ['sidereal'], 'ophiuchus_planet': ['sidereal']}


def _span(days):
    h = days * 24
    return 'under an hour' if h < 1 else f'about {h:.0f} h' if h < 36 else f'about {days:.1f} days'


def sky_card(rows, bands, local):
    """The sky at this moment: the Moon's phase and light, retrograde planets, the Moon's next contact or void of
    course, and when she leaves her constellation."""
    s = forecast.sky(rows, bands)
    leave = local + dt.timedelta(days=s['exit_days'])
    with st.container(border=True):
        st.markdown('**The sky at this moment**')
        if school.is_dee():
            st.markdown(f"{s['symbol']} **{s['phase']}**, {s['lit']}% lit: the Moon is "
                        f"{'increasing' if s['waxing'] else 'decreasing'} in light.")
        else:
          st.markdown(f"{s['symbol']} **{s['phase']}**, {s['lit']}% lit: the Moon is "
                    f"{'increasing' if s['waxing'] else 'decreasing'} in light ({'+2' if s['waxing'] else '-2'} for her in "
                    + ("Ptolemy's testimonies, after III.13)." if school.is_ptolemy() else "Lilly's table)."))
        st.markdown('**Retrograde:** ' + (', '.join(s['retrograde']) if s['retrograde'] else 'no planet') + '.')
        if s['void']:
            st.markdown(f"**The Moon is void of course** until she leaves {s['band']} ({_span(s['exit_days'])}, "
                        f"{leave:%a %H:%M} local). " + ("Void of course is Lilly's term (a time when things begun go on "
                                                         "with difficulty); the Tetrabiblos does not use it."
                                                         if school.is_ptolemy() else
                                                         "Void of course is Lilly's term (a time when things begun go on "
                                                         "with difficulty); Dee's angelic tables do not use it."
                                                         if school.is_dee() else
                                                         "Lilly: a time when things begun go on with difficulty."))
        else:
            p, asp, days = s['next']
            st.markdown(f"**The Moon's next contact:** {asp} with {p}, in {_span(days)}. She leaves {s['band']} in "
                        f"{_span(s['exit_days'])} ({leave:%a %H:%M} local).")
        glossary.chips((['p_moon', 'p_retrograde'] if school.is_ptolemy() else [] if school.is_dee()
                        else ['moon_light', 'retrograde']) + ['void'] + ([] if school.is_dee() else ['aspects']), 'sky')

def set_now(tzkey):
    """Put the present moment (local clock time in tzkey) into the date and time boxes."""
    n = inputs.now_local(tzkey)
    st.session_state['c_year'] = min(max(n.year, 1850), 2149)
    st.session_state['c_month'] = n.month
    st.session_state['day_value'] = n.day
    st.session_state['c_time'] = dt.time(n.hour, n.minute)
    st.session_state['c_now_tz'] = tzkey


if 'c_time' not in st.session_state:              # the page opens at the present moment (user request)
    set_now(inputs.start_timezone())

# ---------------- inputs (same as the first app; a fold-out panel at the top on a phone) ----------------
with device.input_panel('Chart input: date, time and place'):
    if not PHONE:
        st.header('Chart input')
    dh, nb = st.columns([2.2, 1], vertical_alignment='bottom')
    dh.markdown('**Date**')
    if nb.button('Now', key='c_now', icon=':material/schedule:', width='stretch',
                 help='Set the date and time to the present moment, in the local time of the chosen place.'):
        set_now(st.session_state.get('c_last_tz') or inputs.start_timezone())
    yc, mc_, dc = st.columns([1.3, 1.4, 1])
    year = yc.number_input('Year', min_value=1850, max_value=2149, step=1, key='c_year',
                           help='Type any year from 1850 to 2149 (range of the NASA JPL DE440s data).')
    month = mc_.selectbox('Month', range(1, 13), format_func=lambda m: calendar.month_abbr[m], key='c_month')
    ndays = calendar.monthrange(int(year), int(month))[1]
    if st.session_state.get('day_value', 1) > ndays:          # e.g. 31 Jan -> Feb keeps the last day
        st.session_state['day_value'] = ndays
    day = dc.number_input('Day', min_value=1, max_value=ndays, step=1, key='day_value')
    d = dt.date(int(year), int(month), int(day))
    tm = st.time_input('Local clock time (24-hour clock)', step=60, key='c_time')
    st.caption(f"The page opens at the present moment (local time, {st.session_state.get('c_now_tz', '')}). "
               'Press Now to return to the present.')
    place, lat, lon, tzname, elev = inputs.place_picker('c')
    local_naive = dt.datetime.combine(d, tm)
    override = False
    if tzname:
        auto_off, tz_note = places.utc_offset_hours(tzname, local_naive)
        override = st.checkbox(f'Override UTC offset (automatic: {auto_off:+.2f} h)', value=False)
        tz = st.number_input('UTC offset (hours)', -12.0, 14.0, float(auto_off), 0.25) if override else auto_off
        if tz_note:
            st.info(tz_note)
    else:
        tz = st.number_input('UTC offset of that clock (hours)', -12.0, 14.0, 0.0, 0.25)
    st.session_state['c_last_tz'] = tzname if (tzname and not override) else f'UTC{tz:+.2f}'   # for the Now button
    st.subheader('Options (John Dee)' if DEE else 'Options (Ptolemy)' if PT else 'Options (Lilly)')
    if DEE:
        dee_start = st.radio('Heptarchic day begins at', ['sunrise', 'midnight'], index=0, key='dee_day_start',
                             format_func={'sunrise': 'Local sunrise', 'midnight': 'Local mean midnight'}.get,
                             help='Dee was never told when the angelic day begins (Peterson, PDF p160, p260). Local '
                                  'sunrise is this app\'s default, as in the Sidereal Enochian Chart.')
        st.caption("Dee's angelic tables have no houses, dignity points or aspect orbs, so Lilly's options are not used "
                   "in this reading (his own rules still apply to the four undertakings).")
    else:
        dee_start = 'sunrise'
    if PT:
        st.caption("Ptolemy gives no orbs for the aspects, so the medieval moieties are used (Lilly p.107). Lilly's "
                   'Sun-beams option is not used in Ptolemy mode (his own rule applies to the four undertakings).')
    beams = 'As in Lilly\'s table (p.113, p.115)' if (PT or DEE) else st.radio('Sun-beams rule', ['As in Lilly\'s table (p.113, p.115)', 'As in Lilly\'s worked example (pp.178-180)'],
                     index=0, help='Lilly\'s table counts a planet within 17° of the Sun as "under the Sun-beams" (-4). '
                                   'In his own worked example he does not apply this, and counts only combustion (8°30\').')
    orbs = 'Lilly\'s own' if DEE else st.radio('Orbs of the planets (p.107)', ['Lilly\'s own (Saturn 10, Jupiter 12 ...)', '"According to others" (Saturn 9, Jupiter 9 ...)'],
                    index=0)
    st.caption('Valid dates 1850–2149 (JPL DE440s). Place data: GeoNames (CC BY 4.0); time zones: IANA tz database. '
               + ("Text: J. H. Peterson (ed.), John Dee's Five Books of Mystery; G. James, The Enochian Evocation of Dr John "
                  'Dee (tables transcribed in the Sidereal Enochian Chart).' if DEE else
                  'Text: Ptolemy, Tetrabiblos, tr. F. E. Robbins (Loeb, 1940; public domain in the US), via LacusCurtius.'
                  if PT else 'Text: W. Lilly, Christian Astrology (1647), Wellcome Library copy (public domain).'))

beams_rule = 'table' if beams.startswith('As in Lilly\'s table') else 'example'
orb_col = 'orb_lilly' if orbs.startswith('Lilly') else 'orb_others'
local = dt.datetime.combine(d, tm)
utc_dt = local - dt.timedelta(hours=tz)
utc = (utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute, 0)
with st.spinner(voice.loading('Computing the chart ...')):
    if DEE:
        rows, bands, cusps, R, ph, fc, asc, mc, stars, cusps_l = run_dee(utc, lat, lon, elev, dee_start)
    elif PT:
        rows, bands, cusps, R, ph, fc, asc, mc, stars, cusps_l = run_ptolemy(utc, lat, lon, elev, orb_col)
    else:
        rows, bands, cusps, R, ph, fc, asc, mc, stars = run(utc, lat, lon, elev, beams_rule, orb_col)
        cusps_l = cusps
P = {p['planet']: p for p in R['planets']}

# ---------------- header ----------------
st.caption(f'{place} · {local:%d %b %Y %H:%M} local (UTC{tz:+.2f}) = {utc_dt:%Y-%m-%d %H:%M} UTC · '
           'positions: NASA JPL DE440s via Skyfield (IAU standards) · '
           + ('no houses (Dee\'s angelic tables use none) · ' if DEE else
              'places: whole constellations, from the one 5° above the Ascendant (after Tetrabiblos III.10) · '
              if PT else 'houses: Regiomontanus, as Lilly · ')
           + 'signs: the real IAU constellations on the ecliptic (13, at their true widths)')


# ---------------- the punchline: one big, rude line about this chart (not in Polite) ----------------
def _next_punchline():
    st.session_state['punch_shift'] = st.session_state.get('punch_shift', 0) + 1


if not voice.polite():
    seed = f"{utc_dt:%Y%m%d%H%M}|{lat:.3f}|{lon:.3f}"
    if st.session_state.get('punch_seed') != seed:         # a new moment or place starts again from its own line
        st.session_state['punch_seed'] = seed
        st.session_state['punch_shift'] = 0
    line = voice.punchline(fc, seed, rows, st.session_state.get('punch_shift', 0), R=R)
    if line:
        plain_mode = bool(st.session_state.get('punch_straight', False))      # 'Say it straight' (CARROT's idea)
        shown = voice.straight(fc) if plain_mode else line
        st.markdown(f"<div class='foul-punch{' foul-straight' if plain_mode else ''}'>{shown}</div>",
                    unsafe_allow_html=True)
        pc1, pc2 = st.columns([1, 1])
        pc1.button(voice.filter_text('Give me another one, damn it'), key='punch_next', icon=':material/refresh:',
                   on_click=_next_punchline, width='stretch', disabled=plain_mode)
        with pc2:
            voice.speak_button(shown)
        st.toggle('Say it straight', key='punch_straight',
                  help='Swap the joke for a plain sentence with the same facts, and back.')

left, right = st.columns([1.15, 1])
with left:
    fig = cw.draw_wheel(rows, bands, f'{place}, {local:%d %b %Y %H:%M}', asc, mc, cusps=cusps,
                        scores=None if DEE else {p['planet']: p['net'] for p in R['planets']},
                        aspects=None if DEE else R['aspects'],
                        theme=theme.WHEEL_THEME_PHONE if PHONE else theme.WHEEL_THEME, compact=PHONE)
    st.pyplot(fig, width='stretch')
    if PHONE:
        st.caption('  \n'.join(cw.legend_lines(theme.WHEEL_THEME_PHONE)))

with right:
  if DEE:
    dee_view.right_column(R, utc_dt, lon, tz)
    sky_card(rows, bands, local)
  elif PT:
    _light = 'Sun' if R['sun_up'] else 'Moon'
    st.subheader(f"{'Diurnal' if R['sun_up'] else 'Nocturnal'} figure: the {_light} leads the sect")
    st.caption(f"Ptolemy reads the chart by its sect: by day the Sun, Jupiter and Saturn are of the sect, by night the "
               f"Moon, Venus and Mars; Mercury goes with the side he rises on (Tetrabiblos I.7). Planetary hours are not "
               f"in the Tetrabiblos (this is the day of {ph['day_ruler']}, hour of {ph['hour_ruler']}, by Lilly's reckoning).")
  else:
    st.subheader(f"Day of {ph['day_ruler']}, hour of {ph['hour_ruler']}")
  if not (PT or DEE):
    if ph['sunrise']:
        sr = ph['sunrise'] + dt.timedelta(hours=tz); ss = ph['sunset'] + dt.timedelta(hours=tz)
        st.caption(f"{ph['weekday']} planetary day, from local sunrise {sr:%H:%M} (sunset {ss:%H:%M}, local clock). "
                   f"This is hour {ph['hour_number']} of 24, in unequal hours. Lilly: the day's planet rules the first hour and the eighth.")
    else:
        st.caption('No sunrise or sunset here today (polar). Equal hours from local mean midnight are used.')
  if not DEE:
   with right:
    c1, c2, c3 = st.columns(3)
    a_ = R['asc']
    c1.metric('Rising', a_['constellation'], help=glossary.TERMS['p_horoscope' if PT else 'ascendant'][1])
    if PT:
        c2.metric('Ruler of the horoscope', R['lord_of_asc'] or '—', help=glossary.TERMS['p_ruler'][1])
    else:
        c2.metric('Lord of the Ascendant', R['lord_of_asc'] or '—', help=glossary.TERMS['lord_asc'][1])
    if R['lord_of_asc']:
        c3.metric(f"{R['lord_of_asc']}: net score", f"{P[R['lord_of_asc']]['net']:+d}",
                  help=glossary.TERMS['p_testimonies' if PT else 'fortitudes'][1])
    sky_card(rows, bands, local)
    if FULL and PT:
      st.write(f"**Figure:** {'diurnal (Sun above the horizon)' if R['sun_up'] else 'nocturnal (Sun below the horizon)'} · "
               f"**Lot of Fortune:** {R['part_of_fortune']['constellation']}, place {R['part_of_fortune']['house']}"
               + (f" · **Governor of the soul:** {R['soul_governor']}" if R.get('soul_governor') else ''))
      st.markdown("**Strength of the planets** (Ptolemy's testimonies, [I.23-I.24](" + pt.text_url('I.24', 115)
                  + ') and [III.10](' + pt.text_url('III.10', 273) + '); the points are app weights)')
      sc = pd.DataFrame([dict(Planet=p['planet'], Constellation=p['constellation'] + (' R' if p['retrograde'] else ''),
                              Place=p['house'], For=p['fortitudes'], Against=p['debilities'], Net=p['net'],
                              Position=p['honour'].replace('in an ', '').replace('in a ', '')) for p in R['planets']])
      device.table(sc, ['Planet', 'Place', 'Net', 'Position'])
      found = [glossary.item_term(k) for p in R['planets'] for k, *_ in p['essential'] + p['accidental']]
      glossary.chips(['p_testimonies', 'p_familiarity'] + [k for k in found if k] + ['p_places'], 'table')
    elif FULL:
      st.write(f"**Figure:** {'diurnal (Sun above the horizon)' if R['sun_up'] else 'nocturnal (Sun below the horizon)'} · "
             f"**Part of Fortune:** {R['part_of_fortune']['constellation']}, {ORD(R['part_of_fortune']['house'])} house")
      st.markdown('**Strength of the planets** (Lilly\'s table, [p.115](' + glossary.scan_url(115) + '))')
      sc = pd.DataFrame([dict(Planet=p['planet'], Constellation=p['constellation'] + (' R' if p['retrograde'] else ''),
                              House=p['house'], Fortitudes=p['fortitudes'], Debilities=p['debilities'], Net=p['net'],
                              Essentially=p['condition']) for p in R['planets']])
      device.table(sc, ['Planet', 'House', 'Net', 'Essentially'])
      found = [glossary.item_term(k) for p in R['planets'] for k, *_ in p['essential'] + p['accidental']]
      glossary.chips(['fortitudes', 'essential'] + [k for k in found if k] + ['angles'], 'table')

st.subheader('Forecast')
with st.container(border=True):
    st.markdown(fc['summary'] if FULL else plain_forecast.overview(fc, R))
    # the plain-English summary first and most prominent (user request), then the Strengths and the Weaknesses;
    # each opens in its own window
    if st.button(voice.say('What the hell does this mean?', 'What does this mean?'), type='primary', icon=':material/lightbulb:', key='plain_btn',
                 width='stretch', help='A summary of the Forecast without the technical terms, with this moment judged '
                                       'for the four undertakings of the Auspicious dates page.'):
        tzkey = tzname if (tzname and not override) else f'UTC{tz:+.2f}'
        plain_forecast.show(fc, R, rows, bands, cusps_l, stars, ph, lat, lon, elev, tzkey, local, beams_rule, place)
    b0, b1_ = st.columns(2)
    if b0.button(f"Strengths ({len(fc['strengths'])})", icon=':material/thumb_up:', key='strengths_btn', width='stretch',
                 help=f"{school.authors()} rules that favour this moment, with the page references."):
        plain_forecast.show_strengths(fc, place, local)
    if b1_.button(f"Weaknesses ({len(fc['weaknesses'])})", icon=':material/report:', key='weaknesses_btn', width='stretch',
                  help=f"{school.authors()} rules that count against this moment, with the page references."):
        plain_forecast.show_weaknesses(fc, place, local)
    fired = [x.get('id') for x in fc['strengths'] + fc['weaknesses']]
    glossary.chips([g for rid in fired for g in (RULE_TERMS_DEE if DEE else RULE_TERMS_PT if PT else RULE_TERMS).get(rid, [])], 'fc')
    st.caption(fc['note'] if voice.polite() else
               voice.filter_text("The summary restates Dee's angelic tables (Peterson; James). The strengths and "
                                 "weaknesses are this app's own rules built on them, not Dee's: he never judged a "
                                 "damn chart this way. " if DEE else
                                 "The strengths and weaknesses are Ptolemy's own testimonies (Tetrabiblos, tr. Robbins "
                                 "1940), mainly III.10, III.13 and IV.2-IV.3, slapped onto the real IAU sky. He wrote "
                                 "no rules for questions, so the moment is read like a birth chart. Where the app had "
                                 "to bend a rule, the line says so. " if PT else
                                 "The strengths and weaknesses are Lilly's own rules (Christian Astrology, 1647), "
                                 "mainly his 'Considerations before Judgment' (pp.121-123), slapped onto the real IAU "
                                 "sky. Where the app had to bend a rule, the line says so. ")
               + voice.pick('disclaimer', seed='chart'))
    st.download_button('Download forecast (.txt)',
                       (dee_view.efc if DEE else ptolemy_forecast if PT else forecast).as_text(fc, header=(f"Prepared for {user_profile.get()['name']}\n" if user_profile.get()['name'] else '')
                                       + f"{place} · {local:%d %b %Y %H:%M} local (UTC{tz:+.2f})"),
                       file_name=f"forecast_{local:%Y%m%d_%H%M}.txt", mime='text/plain', icon=':material/download:')

if not FULL:
    st.caption(("Simple view. Switch on **Full view** in the sidebar for the planets in Dee's tables, the day's "
                "ministers, the bodies and the sources." if DEE else
                f"Simple view. Switch on **Full view** in the sidebar for {school.authors()} tables of points, the "
                'planets in his words, the aspects and the sources.') + (' (On a phone, open the sidebar with the arrow at the top left.)'
                                                         if PHONE else ''))
    st.stop()

if DEE:
    dee_view.full_sections(R, rows, cw.GLYPH)
    st.stop()

if PT:
    st.subheader("The planets in Ptolemy's words")
    st.caption('For each planet: the testimonies for and against it and the net score. Ptolemy ranks the testimonies '
               '(I.23-I.24, III.10) but gives no numbers; the points are app weights. His pictures of each planet come '
               'from III.13, where the planet rules the soul "in an honourable position" or "in the opposite position".')
    _place_told = {}
    _place_seen = []
    _POINTERS_PT = ['what Ptolemy reads from it is quoted under {who} above', 'see {who} above for this place',
                    'quoted already, with {who}', 'as told under {who}', 'its meaning appears with {who}',
                    "Ptolemy's words for it are given under {who}"]
    for p in R['planets']:
        gov = ' · governor of the soul' if R.get('soul_governor') == p['planet'] else ''
        head = (f"{cw.GLYPH[p['planet']]} {p['planet']} in {p['constellation']}"
                + (f" (≈ {p['sign']} {p['sign_deg']:.0f}°)" if p['sign'] else '') + f" · place {p['house']} · net {p['net']:+d}{gov}")
        with st.expander(head):
            text, cite, label = pt.reading(p['planet'], p['condition'], R, rows)
            ch, pg = cite.replace('Tetrabiblos ', '').split(', Loeb ')
            link = f"[{cite}]({pt.text_url(ch, pg.split('.')[-1].split('-')[0])})"
            pos = p['honour'][0].upper() + p['honour'][1:]
            if p['net'] == 0 and p['planet'] != 'Moon':
                pos += ' (a net of zero is read with the honourable text)'
            if p['planet'] == 'Moon':
                st.markdown(f"**{pos}** (net {p['net']:+d}). Ptolemy on the Moon, *{label}*:")
            elif p['planet'] == 'Sun':
                st.markdown(f"**{pos}.** Ptolemy on the Sun, which aids the planet that governs the soul, *{label}*:")
            else:
                st.markdown(f"**{pos}.** Ptolemy on {p['planet']} as ruler of the soul, *{label}*:")
            st.markdown(f"> {text}  \n> <small>{link}</small>", unsafe_allow_html=True)
            nat, ncite = pt.nature(p['planet'])
            st.caption(f"Nature ({ncite.replace('Tetrabiblos ', '')}): {nat}")
            if p['true_constellation'] != p['constellation']:
                st.caption(f"Its actual position (RA/Dec) lies in {p['true_constellation']}, off the ecliptic band. "
                           f"It is read by the ecliptic band ({p['constellation']}).")
            if p['house'] in _place_told:
                _n = sum(1 for q_ in _place_seen if q_ == p['house'])
                _place_seen.append(p['house'])
                st.markdown(f"**Place {p['house']}, {pt.place_name(p['house'])}**: " + _POINTERS_PT[_n % len(_POINTERS_PT)].format(
                    who=_place_told[p['house']]) + '.')
            else:
                _place_told[p['house']] = p['planet']
                st.markdown(f"**Place {p['house']}, {pt.place_name(p['house'])}** (Ptolemy): {pt.house_meaning(p['house'], 600)}  \n"
                            f"<small>{pt.place_cite(p['house'])}</small>", unsafe_allow_html=True)
            e1, e2 = st.columns(2)
            e1.markdown('**Familiarity with the sign**  \n' + '  \n'.join(f"{'+' if v > 0 else ''}{v} {txt} <small>({tag})</small>"
                                                                       for _, txt, v, tag in p['essential']), unsafe_allow_html=True)
            e2.markdown('**Position and phase**  \n' + '  \n'.join(f"{'+' if v > 0 else ''}{v} {txt} <small>({tag})</small>"
                                                                  for _, txt, v, tag in p['accidental']), unsafe_allow_html=True)
            st.caption(f"{p['planet']}: for {p['fortitudes']} · against {p['debilities']} · net {p['net']:+d} · "
                       f"sect: {p['sect']}")
            glossary.chips([glossary.item_term(k) for k, *_ in p['essential'] + p['accidental']], 'pl_' + p['planet'])
else:
    st.subheader("The planets in Lilly's words")
    st.caption('For each planet: fortitudes, debilities and the net score. Lilly: subtract the lesser number from the '
               f'greater, "and so judge" ([p.181]({glossary.scan_url(181)})).')
    _house_told = {}                       # each house's meaning is quoted once on the page; later planets point back
    _house_seen = []                       # ... each time in a different wording
    _POINTERS = ['its meaning is quoted under {who} above', "Lilly's words for it are given under {who}", 'see {who} above for what it signifies', 'described already, with {who}', 'as told under {who}', 'its signification appears with {who}']
    for p in R['planets']:
        head = (f"{cw.GLYPH[p['planet']]} {p['planet']} in {p['constellation']}"
                + (f" (≈ {p['sign']} {p['sign_deg']:.0f}°)" if p['sign'] else '') + f" · {ORD(p['house'])} house · net {p['net']:+d}")
        with st.expander(head):
            text, cite = ll.reading(p['planet'], p['condition'])
            label = 'when ill dignified' if p['condition'] == 'ill dignified' else 'when well dignified'
            st.markdown(f"**Essentially {p['condition']}.** Lilly on {p['planet']} *{label}*:")
            st.markdown(f"> {text}  \n> <small>{cite}</small>", unsafe_allow_html=True)
            if p['true_constellation'] != p['constellation']:
                st.caption(f"Its actual position (RA/Dec) lies in {p['true_constellation']}, off the ecliptic band. "
                           f"It is read by the ecliptic band ({p['constellation']}).")
            if p['house'] in _house_told:
                _n = sum(1 for q_ in _house_seen if q_ == p['house'])
                _house_seen.append(p['house'])
                st.markdown(f"**The {ORD(p['house'])} house**: " + _POINTERS[_n % len(_POINTERS)].format(
                    who=_house_told[p['house']]) + '.')
            else:
                _house_told[p['house']] = p['planet']
                st.markdown(f"**The {ORD(p['house'])} house** (Lilly): {ll.house_meaning(p['house'], 400)}")
            e1, e2 = st.columns(2)
            e1.markdown('**Essential dignities**  \n' + '  \n'.join(f"{'+' if v > 0 else ''}{v} {txt} <small>({tag})</small>"
                                                                       for _, txt, v, tag in p['essential']), unsafe_allow_html=True)
            e2.markdown('**Accidental**  \n' + '  \n'.join(f"{'+' if v > 0 else ''}{v} {txt} <small>({tag})</small>"
                                                             for _, txt, v, tag in p['accidental']), unsafe_allow_html=True)
            st.caption(f"{p['planet']}: fortitudes {p['fortitudes']} · debilities {p['debilities']} · net {p['net']:+d}")
            glossary.chips([glossary.item_term(k) for k, *_ in p['essential'] + p['accidental']], 'pl_' + p['planet'])

st.subheader('Aspects (moieties of orbs from Lilly p.107; Ptolemy gives none)' if PT else 'Aspects (Lilly\'s moieties of orbs, p.107)')
if R['aspects']:
    device.table(pd.DataFrame([dict(Between=f"{a['a']} – {a['b']}", Aspect=a['aspect'], **{'From exact (°)': round(a['deviation'], 2)},
                                    **{'Allowed (°)': a['moiety']}, Partile=a['partile'],
                                    Motion='applying' if a['applying'] else 'separating') for a in R['aspects']]),
                 ['Between', 'Aspect', 'Motion'])
else:
    st.caption('No aspects within the planets\' moieties.')
glossary.chips(['aspects', 'orbs', 'applying', 'partile'], 'asp')

st.subheader('Bodies')
tab = pd.DataFrame([dict(Body=r['body'], **{'Ecl. long. (°)': round(r['ecl_lon'], 2)}, **{'Ecliptic band': r['band']},
                         **{'IAU constellation (RA/Dec)': r['constellation']},
                         **{'Daily motion (°)': round(r['speed'], 3) if 'speed' in r else None},
                         **{'Above horizon': (r['alt'] > 0) if 'alt' in r else None},
                         **{('Place' if PT else 'House'): (pt.place_of(r['ecl_lon'], cusps) if PT else se.house_of(r['ecl_lon'], cusps))})
                    for r in rows])
device.table(tab, ['Body', 'Ecliptic band', 'Place' if PT else 'House'])
if PHONE:
    st.caption('Phone layout shows the main columns of each table. To see them all, switch off "Phone layout" '
               'in the sidebar (open it with the arrow at the top left).')
glossary.chips(['sidereal', 'p_places'] if PT else ['sidereal', 'houses', 'five_degree'], 'bodies')
if PT:
    st.caption('Places (whole constellations, Ophiuchus with Scorpius): '
               + ' · '.join(f"{i + 1}: {c}" for i, c in enumerate(R['place_constellations'])))
else:
    st.caption('House cusps (Regiomontanus): ' + ' · '.join(f"{i + 1}: {c['constellation']}" for i, c in enumerate(R['cusp_signs'])))

with st.expander('Sources and certainty'):
  if PT:
    st.markdown('Each statement carries a tag: **Ptolemy** (from the *Tetrabiblos*, tr. F. E. Robbins, Loeb 1940, with '
                'book and chapter) or **app rule** (where the app had to adapt Ptolemy to the sidereal IAU sky). Note that '
                'Ptolemy himself counts the signs from the equinoxes (I.22); reading them as the real constellations is '
                'this app\'s choice. The tables are in the *data* folder as CSV files (ptolemy_*.csv).')
    device.table(pd.read_csv(os.path.join(HERE, 'data', 'ptolemy_uncertainty.csv'), encoding='utf-8'))
  else:
    st.markdown('Each statement carries a tag: **Lilly** (from *Christian Astrology*, 1647, with page) or **app rule** '
                '(where the app had to adapt Lilly to the sidereal IAU sky). The tables are in the *data* folder as CSV files.')
    device.table(pd.read_csv(os.path.join(HERE, 'data', 'uncertainty_log.csv'), encoding='utf-8'))
  device.table(pd.read_csv(os.path.join(HERE, 'data', 'sources.csv'), encoding='utf-8'))
