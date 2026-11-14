"""Chart page: the dialog 'The forecast in plain English'.

It restates the Forecast box without the technical terms, in three parts:
  1. In short: the overall picture (how many good signs and warning signs, and whether Lilly's
     cautions before judgment apply);
  2. the same lines in plain English (column 'plain' of data/forecast_rules.csv);
  3. the four undertakings of the Auspicious dates page (romance, friendship, life transition, project),
     judged for this exact moment with the same rules (electional.judge) and graded against the other
     hours of the surrounding week, as the Auspicious dates page grades against its period.
"""
import datetime as dt
import re
from zoneinfo import ZoneInfo

import streamlit as st

import electional as el
import glossary
import lilly_layer as ll
import theme
import user_profile
try:
    import school
except ModuleNotFoundError:          # an older app without the Lilly / Ptolemy switch
    school = None
try:
    import voice
except ModuleNotFoundError:
    # The Sidereal Oracle has no rude voice (voice.py belongs to The Foul-Mouthed Oracle). This polite stand-in
    # gives the same page register, so no wording repeats on a page there either; app.py calls new_page() each run.
    import re as _re
    import zlib as _zlib

    class _PoliteVoice:
        # the same polite variants as voice.POLITE_PHRASES in The Foul-Mouthed Oracle
        POLITE_PHRASES = {
            'grade_best': ["This moment is one of the best tenth of hours this week.",
                           "Few hours this week score higher than this one.",
                           "A strong moment, in the top tenth of the week.",
                           "Among the most favourable hours of the week."],
            'grade_good': ["This moment is better than most hours this week.", "Above average for the week.",
                           "A favourable hour, ahead of the usual hour this week.",
                           "More promising than most of this week's hours."],
            'grade_fair': ["This is an ordinary hour: no warning, but nothing special.",
                           "An average hour, with no cautions against it.",
                           "Neither favoured nor warned against.", "A middling hour for this undertaking."],
            'grade_avoid': ["Lilly would wait: one of his cautions applies at this moment.",
                            "One of Lilly's cautions applies, so he would not begin now.",
                            "Lilly's warnings rule this moment out.",
                            "A caution from Lilly applies; another hour would be wiser."],
            'best_label': ['Best time this week', 'Most favourable time this week', 'Recommended time this week',
                           "The week's strongest time"],
            'best_none': ["Every hour this week has one of Lilly's warnings for this undertaking.",
                          "No hour this week is free of Lilly's cautions for this.",
                          "Lilly's cautions cover the whole week for this undertaking.",
                          "This week offers no hour without a warning for this."],
            'helping': ['Helping:', 'In its favour:', 'Working for it:', 'On the plus side:'],
            'take_care': ['Take care:', 'Against it:', 'Watch out for:', 'On the minus side:'],
            'shared_title': ['Applies to all four'],
            'shared_intro': ["These signs concern the whole chart, so they are listed once here and not repeated in each "
                             "undertaking below."],
        }
        GRADE_TXT = {'best': 'Best', 'good': 'Good', 'fair': 'Fair', 'avoid': 'Avoid'}
        _REG = '_pf_page_used'

        def polite(self):
            return True

        def persona(self):
            return ''

        def say(self, crude, polite_text):
            return polite_text

        def filter_text(self, text, lvl=None):
            return text

        def item(self, x):
            return x.get('plain') or x['text']

        def plain(self, j):
            return j['plain']

        def loading(self, polite_text):
            return polite_text

        def new_page(self):
            st.session_state[self._REG] = set()

        def _register(self):
            return st.session_state.setdefault(self._REG, set())

        @staticmethod
        def _norm(t):
            t = _re.sub(r'<[^>]+>', ' ', str(t)).replace('*', '')
            return _re.sub(r'[^a-z0-9 ]+', '', _re.sub(r'\s+', ' ', t.lower())).strip()

        def is_used(self, text):
            return self._norm(text) in self._register()

        def mark_used(self, text):
            self._register().add(self._norm(text))
            return text

        def pick(self, slot, polite_options=None, seed=0, **fmt):
            opts = list(polite_options or self.POLITE_PHRASES.get(slot, []))
            if not opts:
                return ''
            k = _zlib.crc32(str(seed).encode()) % len(opts)
            for o in opts[k:] + opts[:k]:
                txt = o.format(**fmt) if fmt else o
                if not self.is_used(txt):
                    return self.mark_used(txt)
            return opts[k]

    voice = _PoliteVoice()


def _dee():
    """True when the chart is read by John Dee's angelic tables (the sidebar switch 'Whose reading?')."""
    try:
        return bool(school and school.is_dee())
    except Exception:
        return False


def _pt():
    """True when the chart is read by Ptolemy's rules (the sidebar switch 'Whose reading?')."""
    try:
        return bool(school and school.is_ptolemy())
    except Exception:
        return False


def new_page():
    """Called by app.py at the start of every run: a fresh register of the wordings used on this page."""
    getattr(voice, 'new_page', lambda: None)()

ORDER = ('romance', 'friendship', 'transition', 'project')
SHORT = {'romance': 'Romance', 'friendship': 'Friendship', 'transition': 'Life transition', 'project': 'Project'}
GRADE_TXT = voice.GRADE_TXT
GRADE_MEANING_POLITE = {
    'best': 'This moment is one of the best tenth of hours this week.',
    'good': 'This moment is better than most hours this week.',
    'fair': 'This is an ordinary hour: no warning, but nothing special.',
    'avoid': "Lilly would wait: one of his cautions applies at this moment. The best time this week is shown below.",
}
GRADE_MEANING_CRUDE = {
    'best': 'Hell yes. This is one of the best tenth of hours this week. Go.',
    'good': 'Better than most hours this week. Not bad at all.',
    'fair': 'Meh. No warning, nothing special: a beige sort of hour.',
    'avoid': "Nope. One of Lilly's cautions applies, so he'd sit on his hands. The best time this week is below.",
}


def grade_meaning(g, seed=0):
    """What a grade means, in a wording not yet used on this page (each grade has several variants)."""
    return voice.pick('grade_' + g, seed=seed)


WORKING_LABELS = ('Show the working', 'How it was scored', 'The sums behind it', "Lilly's rules behind it",
                  'Where the points came from', 'Workings')
# Lilly's "Considerations before Judgment" (pp.121-123): signs that the chart may not be safe to read at all.
CAUTIONS = {'not_radical', 'asc_early', 'asc_late', 'asc_ophiuchus', 'moon_via_combusta', 'moon_late',
            'saturn_7', 'lord_7_afflicted', 'testimonies_equal'}
def _is_caution(x):
    """One of Lilly's considerations before judgment (marked ⚠). Ptolemy has no such warnings about the chart itself."""
    return not (_pt() or _dee()) and x.get('id') in CAUTIONS


GLOSSARY_KEYS_PT = ['p_horoscope', 'p_ruler', 'p_sect', 'p_places', 'p_lights', 'p_benefic', 'p_fortune', 'p_moon',
                    'p_testimonies', 'hours', 'considerations', 'fortunes', 'aspects', 'applying']
GLOSSARY_KEYS_DEE = ['d_heptarchy', 'd_ministers', 'd_day_start', 'd_part_earth', 'd_aethyr', 'd_zodiac_king',
                     'hours', 'considerations', 'fortunes', 'aspects', 'applying']
GLOSSARY_KEYS = ['ascendant', 'lord_asc', 'hours', 'radical', 'considerations', 'fortitudes', 'houses', 'angles',
                 'fortunes', 'aspects', 'applying', 'combust', 'cazimi', 'void', 'via_combusta', 'reception', 'fortune']


DISCLAIMER_CRUDE = ("Reality check: this is a 1647 astrology book with a potty mouth, for fun and reflection. "
                    "Controlled studies have never found astrology to predict a damn thing, so don't make important "
                    "decisions with it.")


def tz_from_key(tzkey):
    return ZoneInfo(tzkey) if not tzkey.startswith('UTC') else dt.timezone(dt.timedelta(hours=float(tzkey[3:])))


@st.cache_data(show_spinner=False, max_entries=8, ttl=3600)
def week(lat, lon, elev, tzkey, start, beams_rule):
    """The four undertakings over 7 days from `start`, every hour of the day (00:00-23:00 local).
    Returns, per undertaking, the grade thresholds and the best window of the week."""
    res, _ = el.scan_many(ORDER, lat, lon, elev, tz_from_key(tzkey), start, 7, 0, 24, 60, beams_rule)
    out = {}
    for k in ORDER:
        q = el.grade(res[k])
        wins = el.windows(res[k])
        best = None
        if wins:
            w = wins[0]
            best = dict(date=w['date'], start=w['start'], end=w['end'] + dt.timedelta(minutes=60), grade=w['grade'])
        out[k] = dict(q=q, best=best, n=len(res[k]), n_avoid=sum(r['grade'] == 'avoid' for r in res[k]))
    return out


def week_start(d):
    """Three days before to three days after the chart date, kept inside the ephemeris range (1850-2149)."""
    s = d - dt.timedelta(days=3)
    return min(max(s, dt.date(1850, 1, 1)), dt.date(2149, 12, 25))


def grade_moment(j, q):
    if j['avoid']:
        return 'avoid'
    if q is None:                     # every hour of the week has a warning; this moment has none
        return 'good'
    q90, q65 = q
    return 'best' if j['score'] >= q90 else 'good' if j['score'] >= q65 else 'fair'


def badge(g):
    fg = theme.PALETTE['void'] if g in ('good', 'best') else theme.PALETTE['starlight']
    return (f"<span class='lilly-badge' data-g='{g}' style='background:{theme.GRADE_COLOURS[g]};color:{fg};padding:0.1rem 0.55rem;border-radius:0.6rem;"
            f"font-weight:600;border:1px solid {theme.PALETTE['orbit']}'>{GRADE_TXT[g]}</span>")


def best_box(b, seed=0):
    """'Best time this week' as a highlighted box (user request: make it stand out): a gold-edged panel with a star,
    the day and hours in large white type and the grade badge."""
    label = voice.pick('best_label', seed=seed)
    return (f"<div class='lilly-best' style='margin:0.6rem 0 0.25rem; padding:0.6rem 0.8rem; border-radius:0.65rem; "
            f"border:1px solid {theme.PALETTE['brass']}; border-left:6px solid {theme.PALETTE['brass']}; "
            f"background:{theme.rgba(theme.PALETTE['brass'], 0.18)}; color:#ffffff; line-height:1.45; "
            f"box-shadow:0 0 14px {theme.rgba(theme.PALETTE['brass'], 0.30)};'>"
            f"<span style='color:{theme.PALETTE['brass_pale']}; font-weight:700; font-size:0.95rem; "
            f"letter-spacing:0.03em;'>&#9733; {label}</span><br>"
            f"<span style='color:#ffffff; font-weight:700; font-size:1.15rem;'>{b['start']:%a %d %b}, "
            f"{b['start']:%H:%M}–{b['end']:%H:%M}</span>&nbsp; {badge(b['grade'])}</div>")


OVERVIEW_POLITE = dict(
    word=('strong', 'fairly strong', 'neither strong nor weak', 'fairly weak', 'weak'),
    lord=["**{con}** is rising, so **{lord}** is the planet that stands for you. By Lilly's points it is **{word}** "
          "(net {n:+d}), in the {house} house.",
          "The planet that stands for you is **{lord}**, because **{con}** is rising. Lilly's table gives it "
          "{n:+d}, which makes it **{word}**; it is in the {house} house."],
    nolord=["**{con}** is rising. It has no sign in Lilly, so no planet stands for you, and several of his tests "
            "cannot be made.",
            "With **{con}** on the horizon there is no sign in Lilly's scheme, and so no planet for you; some of his "
            "tests have to be left out."],
    tally=["The Forecast found **{s} encouraging sign{ss}** and **{w} caution{ws}**.",
           "In all, **{s} sign{ss} in favour** and **{w} against**."],
    good=[" On balance the picture is **encouraging**.", " Taken together, the signs are **favourable**."],
    bad=[" On balance it **calls for care**: a time to prepare, wait or go gently rather than push.",
         " Taken together, they **advise patience** rather than bold steps."],
    mixed=[" On balance the picture is **mixed**.", " Taken together, the signs are **evenly balanced**."],
    caution=["{c} of the cautions {isare} among Lilly's *considerations before judgment* (marked ⚠). For Lilly these "
             "do not say that things will go badly; they say that this chart may not be safe to read at all, so he "
             "would hold its other signs more lightly.",
             "The ⚠ marks ({c}) are Lilly's *considerations before judgment*: warnings about the chart itself rather "
             "than about the outcome, which is why its other signs deserve less weight."])


OVERVIEW_POLITE_PT = dict(
    word=('strong', 'fairly strong', 'neither strong nor weak', 'fairly weak', 'weak'),
    lord=["The rising degree is in **{con}**, and the planet with most claims on it is **{lord}**, the ruler that "
          "stands for you. By Ptolemy's testimonies it is **{word}** (net {n:+d}), in place {place}.",
          "**{lord}** rules the horoscope (the rising degree, in **{con}**), so it is the planet that stands for you. "
          "Its testimonies come to {n:+d}, which makes it **{word}**; it is in place {place}."],
    nolord=["**{con}** is rising. It is not one of Ptolemy's twelve signs, so no planet rules the horoscope and "
            "several of his tests cannot be made.",
            "With **{con}** on the horizon there is no sign in Ptolemy's scheme, and so no ruler for you; some of his "
            "tests have to be left out."],
    tally=["Ptolemy's testimonies give **{s} encouraging sign{ss}** and **{w} caution{ws}**.",
           "In all, **{s} sign{ss} in favour** and **{w} against**."],
    good=[" On balance the picture is **encouraging**.", " Taken together, the signs are **favourable**."],
    bad=[" On balance it **calls for care**: a time to prepare, wait or go gently rather than push.",
         " Taken together, they **advise patience** rather than bold steps."],
    mixed=[" On balance the picture is **mixed**.", " Taken together, the signs are **evenly balanced**."],
    caution=['', ''])


OVERVIEW_POLITE_DEE = dict(
    day=["In Dee's angelic week this is **{wd}**, governed by **King {king}** and **Prince {prince}**; their area, "
         "in everyday words, is {realm}.",
         "**{wd}** belongs to **King {king}** and his **Prince {prince}**, whose realm in everyday words is {realm}."],
    tally=["The Forecast found **{s} encouraging sign{ss}** and **{w} caution{ws}** in this moment.",
           "In all, **{s} sign{ss} in favour** and **{w} against**."],
    good=[" On balance the picture is **encouraging**.", " Taken together, the signs are **favourable**."],
    bad=[" On balance it **calls for care**: a time to prepare, wait or go gently rather than push.",
         " Taken together, they **advise patience** rather than bold steps."],
    mixed=[" On balance the picture is **mixed**.", " Taken together, the signs are **evenly balanced**."])


def _overview_dee(fc, R):
    """The overall picture in Dee's reading: the day's King and Prince, then the tally."""
    import dee_view
    T = OVERVIEW_POLITE_DEE if voice.polite() else \
        (getattr(voice, 'OVERVIEW_DEE', {}).get(voice.persona()) or OVERVIEW_POLITE_DEE)
    s_, s, w = R['summary'], fc['strengths'], fc['weaknesses']
    realm = dee_view.CORR.loc[s_['weekday'], 'realm_plain']
    texts = []
    for v in (0, 1):
        lines = [T['day'][v].format(wd=s_['weekday'], king=s_['day_king'], prince=s_['day_prince'], realm=realm)]
        tally = T['tally'][v].format(s=len(s), w=len(w), ss='s' if len(s) != 1 else '', ws='s' if len(w) != 1 else '')
        key = 'good' if len(s) > len(w) + 1 else 'bad' if len(w) > len(s) + 1 else 'mixed'
        lines.append(tally + T[key][v])
        texts.append('\n\n'.join(lines) if voice.polite() else voice.filter_text('\n\n'.join(lines)))
    for t in texts:
        if not voice.is_used(t):
            voice.mark_used(t)
            return t if voice.polite() else getattr(voice, 'vary', lambda x: x)(t)
    return texts[0]


def overview(fc, R):
    """The overall picture. Two wordings exist, so it can appear both in the Forecast box and in the plain-English
    window without repeating itself; the first not yet used on the page is chosen."""
    if _dee() and R.get('school') == 'Dee':
        return _overview_dee(fc, R)
    if _pt():
        T = OVERVIEW_POLITE_PT if voice.polite() else \
            (getattr(voice, 'OVERVIEW_PTOLEMY', {}).get(voice.persona()) or OVERVIEW_POLITE_PT)
    else:
        T = OVERVIEW_POLITE if voice.polite() else voice.OVERVIEW[voice.persona()]
    s, w = fc['strengths'], fc['weaknesses']
    cautions = [x for x in w if _is_caution(x)]
    lord = R['lord_of_asc']
    texts = []
    for v in (0, 1):
        lines = []
        if lord:
            P = {p_['planet']: p_ for p_ in R['planets']}
            n = P[lord]['net']
            i = 0 if n >= 5 else 1 if n > 0 else 2 if n == 0 else 3 if n > -5 else 4
            lines.append(T['lord'][v].format(con=R['asc']['constellation'], lord=lord, word=T['word'][i], n=n,
                                             house=ll._ord(P[lord]['house']), place=P[lord]['house']))
        else:
            lines.append(T['nolord'][v].format(con=R['asc']['constellation']))
        tally = T['tally'][v].format(s=len(s), w=len(w), ss='s' if len(s) != 1 else '', ws='s' if len(w) != 1 else '')
        key = 'good' if len(s) > len(w) + 1 else 'bad' if len(w) > len(s) + 1 else 'mixed'
        lines.append(tally + T[key][v])
        if cautions:
            lines.append(T['caution'][v].format(c=len(cautions), isare='is' if len(cautions) == 1 else 'are'))
        texts.append('\n\n'.join(lines) if voice.polite() else voice.filter_text('\n\n'.join(lines)))
    for t in texts:
        if not voice.is_used(t):
            voice.mark_used(t)
            return t if voice.polite() else getattr(voice, 'vary', lambda x: x)(t)
    return texts[0]


def _v(t):
    """Idiom variety for a line about to be shown (The Foul-Mouthed Oracle only)."""
    return getattr(voice, 'vary', lambda x: x)(t)


def _plain_list(xs, empty):
    if not xs:
        return f'_{empty}_'
    return '\n'.join(f"- {'⚠ ' if _is_caution(x) else ''}{voice.item(x)}" for x in xs)


def _reasons(plain, kinds, n=2):
    xs = [x for x in plain if x[3] in kinds]
    xs.sort(key=lambda x: (x[3] != 'avoid', -abs(x[2])))
    return xs[:n]


@st.dialog('The forecast in plain English', width='large')
def show(fc, R, rows, bands, cusps, stars, ph, lat, lon, elev, tzkey, local, beams_rule, place):
    name = user_profile.get()['name']
    st.caption(f"{place} · {local:%A %d %B %Y, %H:%M} local time"
               + (f" · prepared for {name}" if name else ''))
    if _dee():
        st.markdown("The **Forecast** box reads this moment with John Dee's angelic tables: the King and Prince who "
                    'govern the day, the ministering angels of this part of the day, the zodiac Kings of the '
                    'constellations and the Part of the Earth for the place. Its strengths and weaknesses are this '
                    "app's own rules built on Dee's tables. This window says the same things in everyday words; **Show "
                    'the working** gives each rule as written.')
    elif _pt():
        st.markdown('The **Forecast** box reads the chart of this moment with Ptolemy\'s testimonies from the '
                    '*Tetrabiblos*. Ptolemy wrote no rules for questions, so the moment is read the way he reads a birth '
                    'chart: its sect, the Sun and Moon, the planets on the angles, the ruler of the horoscope and the Lot '
                    'of Fortune. This window says the same things without the technical terms. Under each part, **Show '
                    'the working** gives the rule, the chapter of his book and how the app applies it.')
    else:
        st.markdown('The **Forecast** box reads the chart of this moment the way William Lilly read a chart cast for a '
                    "question put to him. It looks for encouraging signs and cautions in his rules. This window says the "
                    'same things without the technical terms. Under each part, **Show the working** gives the rule, the '
                    'page of his book and how much it counted.')

    st.markdown('#### In short')
    st.markdown(overview(fc, R))
    if _dee() and R.get('school') == 'Dee':
        import dee_view
        tzi = tz_from_key(tzkey)
        off = (tzi.utcoffset(local) if isinstance(tzi, dt.timezone) else local.replace(tzinfo=tzi).utcoffset())
        tz_h = off.total_seconds() / 3600
        for head, text in dee_view.plain_sections(R, local - dt.timedelta(hours=tz_h), lon, tz_h):
            st.markdown(f'#### {head}')
            st.markdown(_v(text) if not voice.polite() else text)

    st.markdown('#### What the Forecast is saying')
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('**Encouraging signs**')
        st.markdown(_plain_list(fc['strengths'], 'None under the current rules.'))
    with c2:
        st.markdown('**Where to take care**')
        st.markdown(_plain_list(fc['weaknesses'], 'None under the current rules.'))
    with st.expander('Show the working', icon=':material/calculate:'):
        working(fc)

    st.markdown('#### If you began something at this moment')
    st.markdown('The **Auspicious dates** page uses the same rules to look for good times to begin four kinds of '
                'undertaking. Here each one is judged for this exact moment. The grade compares this moment with every '
                'hour of the surrounding week, as the Auspicious dates page compares the times in its period.')
    if _pt() or _dee():
        st.caption("These four judgements use Lilly's election rules and his houses, in every reading: neither the "
                   "Tetrabiblos nor Dee's angelic tables give rules for choosing a time to begin something.")
    rules = el.load_rules()
    start = week_start(local.date())
    with st.spinner(voice.loading('Comparing this moment with the rest of the week ...')):
        W = week(lat, lon, elev, tzkey, start, beams_rule)
    judged = {}
    for k in ORDER:
        j = el.judge(rows, bands, cusps, stars, R['sun_up'], k, ph['hour_ruler'], rules, beams_rule)
        judged[k] = (j, grade_moment(j, W[k]['q']), voice.plain(j))
    # signs that come up for two or more undertakings are about the whole chart: said once, in their own box
    from collections import Counter
    count = Counter(t for k in ORDER for t in {t for _, t, _, _ in judged[k][2]})
    shared_txt = {t for t, c in count.items() if c >= 2}
    labels = list(WORKING_LABELS[1:])         # the first one is used by the Forecast's own working above
    if shared_txt:
        shared, seen, shared_items = [], set(), []
        for k in ORDER:
            j, _, pl = judged[k]
            for it, x in zip(j['items'], pl):
                if x[1] in shared_txt and x[1] not in seen:
                    seen.add(x[1])
                    shared.append(x)
                    shared_items.append(it)
        with st.container(border=True):
            st.markdown(f"**{voice.pick('shared_title')}**")
            st.caption(voice.pick('shared_intro'))
            good = [x for x in shared if x[3] == 'good']
            bad = [x for x in shared if x[3] in ('avoid', 'bad')]
            if good:
                st.markdown(f"**{voice.pick('helping', seed='all')}**\n" + '\n'.join(f'- {_v(t)}' for _, t, _, _ in good))
            if bad:
                st.markdown(f"**{voice.pick('take_care', seed='all')}**\n"
                            + '\n'.join(f"- {'⚠ ' if kk == 'avoid' else ''}{_v(t)}" for _, t, _, kk in bad))
            with st.expander(labels.pop(0), icon=':material/calculate:'):
                working_items(shared_items, 'These count in every undertaking they apply to.')
    cols = st.columns(2)
    for i, k in enumerate(ORDER):
        u = el.UNDERTAKINGS[k]
        j, g, pl = judged[k]
        own = [x for x in pl if x[1] not in shared_txt]
        with cols[i % 2].container(border=True):
            st.markdown(f"**{SHORT[k]}** &nbsp; {badge(g)}", unsafe_allow_html=True)
            st.caption(f"{u['label']} · read from the {ll._ord(u['house'])} house and {u['natural']}")
            st.markdown(grade_meaning(g, seed=k))
            good = _reasons(own, ('good',))
            bad = _reasons(own, ('avoid', 'bad'))
            if good:
                st.markdown(f"**{voice.pick('helping', seed=k)}**\n" + '\n'.join(f'- {_v(t)}' for _, t, _, _ in good))
            if bad:
                st.markdown(f"**{voice.pick('take_care', seed=k)}**\n"
                            + '\n'.join(f"- {'⚠ ' if kk == 'avoid' else ''}{_v(t)}" for _, t, _, kk in bad))
            with st.expander(labels.pop(0) if labels else WORKING_LABELS[-1], icon=':material/calculate:'):
                working_undertaking(j, W[k]['q'], skip={ix for ix, x in enumerate(pl) if x[1] in shared_txt},
                                    name=SHORT[k])
            b = W[k]['best']
            if b:
                st.markdown(best_box(b, seed=k), unsafe_allow_html=True)
            else:
                st.caption(voice.pick('best_none', seed=k))
    st.caption(f"Week compared: {start:%d %b} to {start + dt.timedelta(days=6):%d %b %Y}, every hour, at {place}. "
               'For other weeks, other hours or finer time steps, use the Auspicious dates page. '
               'Grades are relative (an app rule): Best is the top tenth of the hours without a warning, Good the next quarter.')

    left = getattr(glossary, 'unseen', lambda ks: ks)(GLOSSARY_KEYS_DEE if _dee() else GLOSSARY_KEYS_PT if _pt()
                                                      else GLOSSARY_KEYS)
    getattr(glossary, 'mark_seen', lambda ks: None)(left)
    with st.expander('Words used in the Forecast'):
        for gk in left:
            st.markdown(glossary.explain_md(gk), unsafe_allow_html=True)
        if not left:
            st.caption('Every term is already explained in the ⓘ buttons on the page.')

    st.info(("This is a reading in the terms of Dee's angelic tables (1582-1583)" if _dee() else
             'This is a reading in the terms of a 2nd-century book' if _pt() else 'This is a reading in the terms of a 1647 book')
            + ', for study and reflection. Controlled studies have not '
            'found astrological charts to predict events, so please do not base important decisions on it.'
            if voice.polite() else voice.pick('disclaimer', seed='dialog'))

# ---------------------------------------------------------------- "Show the working"
def _basis(x):
    b = str(x.get('basis') or '')
    return '' if b == 'nan' else b


def working(fc):
    """Every line of the Forecast: Lilly's rule as he states it, the page (linked to the scan) and how the app
    applies it, grouped by how it counts (so the same explanation is not written under every line)."""
    if not (fc['strengths'] or fc['weaknesses']):
        st.caption('No rule applies at this moment.')
        return
    def entry(x):
        b = _basis(x)
        return (f"- {'⚠ ' if _is_caution(x) else ''}*{_once_sentences(x['text'])}* · "
                f"{_once(glossary.cite_links(x['source']), 'same source as above')}"
                + (f" · app: {b}" if b and b.lower() != 'sourced' else ''))
    parts = []
    if fc['strengths']:
        parts.append('**Each of these counts as one encouraging sign:**\n' + '\n'.join(entry(x) for x in fc['strengths']))
    if fc['weaknesses']:
        parts.append(('**Each of these counts as one caution:**\n' if (_pt() or _dee()) else
                      "**Each of these counts as one caution** (⚠ marks one of Lilly's *considerations before "
                      "judgment* as well):\n") + '\n'.join(entry(x) for x in fc['weaknesses']))
    st.markdown('\n\n'.join(parts))
    st.caption('How the overall picture is decided (an app rule): **encouraging** when the encouraging signs outnumber '
               'the cautions by two or more, **calls for care** when the cautions outnumber them by two or more, '
               'otherwise **mixed**. ' + ("These rules are this app's own, built on Dee's tables, so they have no page "
                                          'of Dee to link to.' if _dee() else
                                          'The links open that chapter of Robbins\'s translation on LacusCurtius.' if _pt()
                                          else 'The page links open that page of the 1647 book on the Internet Archive.'))


def _once(text, short):
    """The full text the first time on a page; afterwards a short pointer back to it (no repeats on a page)."""
    if voice.is_used(text):
        return short
    voice.mark_used(text)
    return text


def _once_sentences(text, short='(quoted above)'):
    """Like _once, sentence by sentence: a sentence of five words or more already shown on the page is replaced
    by a short pointer, so two rules that share a quotation do not repeat it."""
    out = []
    for s in re.split(r'(?<=[.!?])["\u201d]?\s+', str(text)):
        if len(re.findall(r"[A-Za-z0-9']+", s)) >= 5 and voice.is_used(s):
            out.append(short)
        else:
            voice.mark_used(s)
            out.append(s)
    return ' '.join(out)


def _item_line(rid, text, pts, src, kind):
    head = ('⚠ caution: the grade becomes Avoid' if kind == 'avoid' else 'noted, 0 points' if kind == 'info'
            else f'{pts:+.1f} points')
    return (f"- **{head}** · {_once_sentences(text)} · "
            f"{_once(glossary.cite_links(src), 'same source as above')}")


def working_items(items, note=''):
    """Lilly's rules behind the signs shared by several undertakings."""
    st.markdown('\n'.join(_item_line(*it) for it in items) or '_No rule applies._')
    if note:
        st.caption(note)


def working_undertaking(j, q, skip=(), name='Total'):
    """Every rule that scored for one undertaking at this moment, with its points and page. Rules listed in the
    shared box are counted but not written out again."""
    lines = [_item_line(*it) for ix, it in enumerate(j['items']) if ix not in skip]
    st.markdown('\n'.join(lines) or '_No rule of its own; see the shared box._')
    n_skip = len([ix for ix in skip if ix < len(j['items'])])
    st.caption(f"{name}: {j['score']:+.1f} points in all"
               + (f" (including {n_skip} shared sign{'s' if n_skip != 1 else ''} from the box above)" if n_skip else '')
               + '.'
               + (f" This week, Best needs {q[0]:+.1f} or more and Good {q[1]:+.1f} or more (an app rule: the top "
                  'tenth and the next quarter of the hours without a caution).' if q else ''))


# ---------------------------------------------------------------- the Strengths and the Weaknesses, each in its own window
def _rule_items(items):
    for x in items:
        with st.container(border=True):
            st.markdown(('⚠ ' if _is_caution(x) else '') + x['text'])
            src = _once(glossary.cite_links(x['source']), 'Same source as above')
            b = _basis(x)
            st.caption(src + (f' · {b}' if b and b.lower() != 'sourced' else ''))


def _rule_header(place, local):
    name = user_profile.get()['name']
    st.caption(f"{place} · {local:%A %d %B %Y, %H:%M} local time" + (f" · prepared for {name}" if name else ''))


@st.dialog('Strengths', width='large')
def show_strengths(fc, place, local):
    _rule_header(place, local)
    if _dee():
        st.markdown("The rules built on Dee's angelic tables that **favour** this moment. They are this app's own "
                    "interpretive rules (Dee gave no such judgements); the tables behind them come from Peterson's and "
                    "James's editions.")
    elif _pt():
        st.markdown("Ptolemy's testimonies that **favour** this moment, each with its chapter of the *Tetrabiblos* "
                    "(tr. F. E. Robbins, 1940; the links open the text).")
    else:
        st.markdown("Lilly's rules that **favour** this moment, in his words, each with the page of *Christian Astrology* "
                    "(1647) it comes from (the links open the page).")
    if fc['strengths']:
        _rule_items(fc['strengths'])
    else:
        st.info(f"None of the strengths in {'the Enochian' if _dee() else 'Ptolemy' + chr(39) + 's' if _pt() else 'Lilly' + chr(39) + 's'} rules apply at this moment.")
    st.caption('For the same in plain English, close this window and press "What does this mean?".')


@st.dialog('Weaknesses', width='large')
def show_weaknesses(fc, place, local):
    _rule_header(place, local)
    if _dee():
        st.markdown("The rules built on Dee's angelic tables that **count against** this moment. They are this app's "
                    "own interpretive rules (Dee gave no such judgements). Read them as cautions rather than verdicts.")
    elif _pt():
        st.markdown("Ptolemy's testimonies that **count against** this moment, each with its chapter of the "
                    "*Tetrabiblos* (tr. F. E. Robbins, 1940; the links open the text). Read them as cautions rather "
                    "than verdicts.")
    else:
      st.markdown("Lilly's rules that **count against** this moment, in his words, each with the page of *Christian "
                "Astrology* (1647) it comes from (the links open the page). Read them as cautions rather than verdicts. "
                "Lines marked ⚠ are among his *considerations before judgment*: they warn that the chart may not be "
                "safe to read at all, rather than that things will go badly.")
    if fc['weaknesses']:
        _rule_items(fc['weaknesses'])
    else:
        st.info(f"None of the weaknesses in {'the Enochian' if _dee() else 'Ptolemy' + chr(39) + 's' if _pt() else 'Lilly' + chr(39) + 's'} rules apply at this moment.")
    st.caption('For the same in plain English, close this window and press "What does this mean?".')
