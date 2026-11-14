"""Tap-to-explain: short definitions of the terms the app uses, each with the page of Lilly's Christian Astrology
(1647) it comes from and a link to that page of the scanned book (Wellcome Library copy, Internet Archive b30338724).

Page references are the ones the app's data tables already cite. In the scan, printed page N is image N + 35
(checked at pp.57-115), which the Internet Archive viewer numbers n(N + 34).
"""
import inspect
import re

import streamlit as st

SCAN = 'https://archive.org/details/b30338724'
BOOK = "Lilly, *Christian Astrology* (1647)"

# key: (title, plain definition, [pages] or None for an app rule)
TERMS = {
    'ascendant': ('Rising sign (Ascendant)',
                  'The constellation coming up over the eastern horizon at this moment. It begins the 1st house, which '
                  'Lilly says "hath signification of the life of man": it stands for you, or for whoever asks.', [50]),
    'lord_asc': ('Lord of the Ascendant',
                 'The planet that rules the rising sign. It stands for you in the chart: its strength and its place '
                 'describe your part in the matter.', None),
    'hours': ('Planetary day and hour',
              'Each day and each of its 24 unequal hours (12 from sunrise to sunset, 12 from sunset to sunrise) '
              'belongs to one of the seven planets, in a fixed order. The planet of the day rules its first hour.', [61, 65]),
    'radical': ('Radical',
                "Lilly's first test of whether a chart is fit to be judged: the planet of the hour and the Lord of the "
                'Ascendant must agree (be the same planet, share a triplicity, or share a nature).', [121]),
    'considerations': ('Considerations before judgment',
                       "Lilly's list of signs that a chart may not be safe to judge at all: for example the rising sign "
                       'in its first or last degrees, the Moon void of course or on the Via Combusta, or Saturn in the '
                       '1st or 7th house. They are cautions about the reading, not predictions of misfortune.', [121]),
    'fortitudes': ('Fortitudes and debilities',
                   "Lilly's table of points for (fortitudes) and against (debilities) each planet. The net score is "
                   'one minus the other: "subtract the lesser number from the greater, and so judge".', [115, 181]),
    'essential': ('Essential dignity',
                  "A planet's strength from where it stands among the signs: in its own house +5, exaltation +4, "
                  'triplicity +3, terms +2, face +1. The app reads each IAU constellation as the sign of that name, '
                  'rescaled to 30 degrees.', [104, 115]),
    'detriment': ('Detriment', 'A planet in the sign opposite its own house: ill at ease and weakened (-5).', [104, 115]),
    'fall': ('Fall', 'A planet in the sign opposite its exaltation (-4).', [104, 115]),
    'peregrine': ('Peregrine', 'A "wandering" planet, with no essential dignity at all in its degree (-5).', [112, 115]),
    'reception': ('Reception',
                  'Two planets each standing in a sign (or exaltation) of the other: mutual reception, which Lilly '
                  'reads as cooperation between the two.', [112]),
    'angles': ('Angular, succedent and cadent houses',
               'The four angles (1st, 10th, 7th, 4th) are the strongest places in the chart; the succedent houses '
               '(11th, 5th, 2nd, 8th) come next; the cadent ones (9th, 3rd, 12th, 6th) are the weakest. Lilly scores '
               'each house in his table.', [115]),
    'houses': ('Houses',
               'Twelve divisions of the sky, each standing for a part of life: the 7th for partners and love, the 11th '
               'for friends and hopes, the 4th for home and endings, the 10th for work and reputation. The app uses '
               "Regiomontanus houses, as Lilly did.", [50]),
    'five_degree': ('Five-degree rule',
                    'A planet within five degrees before the next house cusp is counted in that next house.', [33]),
    'retrograde': ('Retrograde and direct',
                   'Seen from Earth, a planet sometimes appears to move backwards against the stars (retrograde, -5); '
                   'moving forwards it is direct (+4).', [115]),
    'speed': ('Swift and slow', 'A planet moving faster than its average daily motion is swift (+2); slower, it is '
                                'slow (-2).', [115]),
    'oriental': ('Oriental and occidental',
                 'Rising before the Sun (oriental) or setting after it (occidental). Lilly counts oriental as good for '
                 'Saturn, Jupiter and Mars, and occidental as good for Venus, Mercury and the Moon.', [115]),
    'moon_light': ('Moon increasing or decreasing in light',
                   'From New to Full Moon she is increasing in light (+2); from Full to New, decreasing (-2).', [115]),
    'combust': ('Combust and free from combustion',
                'A planet within 8°30\' of the Sun is combust, lost in its glare and badly weakened (-5). Well clear '
                'of the Sun it is "free from combustion" (+5).', [113, 115]),
    'cazimi': ('Cazimi', 'Within 17 arc-minutes of the Sun\'s centre: "in the heart of the Sun", and strengthened '
                         'instead (+5).', [113, 115]),
    'beams': ('Under the Sun-beams',
              "Within 17° of the Sun but not combust (-4 in Lilly's table; his own worked example does not count it).",
              [113, 115]),
    'aspects': ('Aspects',
                'Set angles between two planets. Sextile (60°) and trine (120°) are friendly; square (90°) and '
                'opposition (180°) are hard (Lilly: "imperfect" and "perfect" enmity); a conjunction (0°) is a meeting.',
                [106]),
    'orbs': ('Orbs and moieties',
             'Each planet has an orb, a reach of influence. Two planets are in aspect when they are within half the '
             'sum of their orbs (their "moieties").', [107]),
    'partile': ('Partile', 'An aspect exact to the degree. Partile contacts with Jupiter or Venus count for a planet; '
                           'with Saturn or Mars, against it.', [115]),
    'applying': ('Applying and separating',
                 'Applying: the faster planet is moving towards the exact aspect. Separating: moving away from it. '
                 'Lilly judges what is to come by applying aspects.', [124]),
    'perfection': ('Perfection and translation of light',
                   'How a matter "comes about" in Lilly: by an applying aspect between the two planets concerned, or '
                   'by a third planet (often the Moon) carrying the light from one to the other.', [124]),
    'void': ('Void of course',
             'The Moon makes no further aspect before she leaves the sign she is in (here: the constellation band). '
             'Lilly says matters then go on with difficulty.', [112]),
    'via_combusta': ('Via Combusta', 'The "burnt road", the second half of Libra and the first half of Scorpio, '
                                     'which Lilly thought unsafe for the Moon.', [121]),
    'fortune': ('Part of Fortune', 'A calculated point (Ascendant + Moon - Sun) standing for wealth and well-being.',
                [143]),
    'fortunes': ('Fortunes and infortunes', 'Jupiter and Venus are the fortunes (helpful); Saturn and Mars the '
                                            'infortunes (difficult).', [106]),
    'stars': ('Regulus, Spica and Algol', 'A planet with the royal star Regulus (+6) or with Spica (+5) is '
                                          'strengthened; with Algol (-5), weakened.', [115]),
    'besieged': ('Besieged', 'A planet between Saturn and Mars (-5).', [115]),
    'nodes': ("Dragon's Head and Tail", "The Moon's nodes: exactly with the North Node (Dragon's Head) +4; with the "
                                        "South Node (Dragon's Tail) -4.", [115]),
    # ---- Ptolemy mode (Tetrabiblos, tr. F. E. Robbins, Loeb 1940): the 'pages' slot holds (chapter, Loeb page)
    'p_sect': ('Sect (day and night)',
               'Ptolemy divides the planets into a day party (the Sun, Jupiter, Saturn) and a night party (the Moon, '
               'Venus, Mars); Mercury joins the side he rises on. A planet of the chart\'s own sect is the stronger, and '
               'a harsh planet of the right sect is tempered.', ('I.7', 43)),
    'p_places': ('Places of authority',
                 'Ptolemy ranks the parts of the sky: the mid-heaven first, then the rising place, the Good Daemon (11th), '
                 'the Occident (7th) and the House of the God (9th). Places that cannot "see" the rising place (2nd, 6th, '
                 '8th, 12th) leave a planet powerless. In this app each place is a whole IAU constellation, starting from '
                 'the one 5 degrees above the Ascendant.', ('III.10', 273)),
    'p_lights': ('The luminaries',
                 'The Sun and the Moon. Ptolemy reads rank and security from whether they are on the angles, in '
                 '"masculine" signs, and attended by kindly or harsh planets.', ('IV.3', 377)),
    'p_gender': ('Masculine and feminine signs',
                 'Six signs are masculine and six feminine, alternating from Aries (masculine).', ('I.12', 69)),
    'p_benefic': ('Beneficent and maleficent planets',
                  'Jupiter, Venus and the Moon are beneficent (warm and moist); Saturn and Mars maleficent (too cold, too '
                  'dry); the Sun and Mercury take on the nature of the planets they join.', ('I.5', 39)),
    'p_ruler': ('Ruler of the horoscope',
                'The planet with the most claims on the rising degree, by Ptolemy\'s five ways: its triangle, its house, '
                'its exaltation, its terms, and an aspect to it. It stands for the person or moment the chart is cast for.',
                ('III.2', 233)),
    'p_honour': ('Honourable position',
                 'Ptolemy describes each planet twice: "in an honourable position" and "in the opposite position". The '
                 'app calls a planet honourable when its testimonies add up to more for than against.', ('III.13', 339)),
    'p_fortune': ('Lot of Fortune',
                  'A point as far from the rising degree as the Moon is from the Sun, by day and by night alike. Its '
                  'lord shows material fortune: strong, it makes for riches.', ('IV.2', 373)),
    'p_moon': ("The Moon's light",
               'Ptolemy: a Moon increasing in light makes for natural gifts, renown and firmness; a waning Moon for '
               'sluggishness and caution.', ('III.13', 361)),
    'p_testimonies': ('Testimonies and net score',
                      "Ptolemy's reasons for and against a planet's power: its familiarity with the sign, its place, "
                      'its phase toward the Sun, its sect and its aspects. Ptolemy gives no numbers; the app weighs them '
                      'on the same scale as Lilly\'s table, and the net score is the difference.', ('I.24', 115)),
    'p_familiarity': ('Familiarity with the sign',
                      'A planet is at home in a sign by its house, its exaltation, its triangle and its terms; in two '
                      'or more of these it is in its "chariot". Without any, it rejoices in a sign of its own sect, but '
                      'in one of the opposite sect "a great part of their proper power is paralysed".', ('I.23', 111)),
    'p_face': ('Proper face',
               'A planet keeps to the Sun or the Moon the angle its own house has to theirs: Venus 60 degrees from them, '
               'Mars 90, Jupiter 120, Saturn 150, Mercury 30.', ('I.23', 111)),
    'p_oriental': ('Oriental and adding to its motion',
                   'A planet rising before the Sun (a morning star) and speeding up is at its most powerful; one setting '
                   'after the Sun (an evening star) and slowing down is weaker.', ('I.24', 115)),
    'p_rays': ("Under the Sun's rays",
               'A planet close to the Sun is setting into his light and cannot be seen; Ptolemy says such "settings" make '
               'it weak. The app counts within 15 degrees.', ('III.13', 335)),
    'p_overcome': ('Overcoming',
                   'A planet in the square on the right-hand side of another (90 degrees before it in the zodiac) '
                   '"overcomes" it: a kindly planet so placed lifts it, a harsh one oppresses it.', ('III.13', 339)),
    # ---- John Dee's reading (Sidereal Enochian Chart): the 'pages' slot holds a text reference
    'd_heptarchy': ('Heptarchic King and Prince',
                    'In Dee\'s Heptarchia each day of the week is governed by one angelic King and his Prince, "for the '
                    'whole daye"; each King belongs to one of the seven planets.',
                    "Peterson, John Dee's Five Books of Mystery, Book 4 (PDF p160); planets: James, App. A"),
    'd_ministers': ('Ministering angels',
                    'The day is split into six equal parts; in each part a set of angels serves under the King. Dee '
                    'wrote each angel as a single letter ("The Letters onely ... are theyr names").',
                    "Peterson, Five Books, PDF p157, p259-260; James's Table of the 42 Ministers"),
    'd_day_start': ('When the angelic day begins',
                    'Dee was never told. This app counts the day from local sunrise (or, as an option, local mean '
                    'midnight).', "Peterson, Five Books, PDF p160 and p260 (an app decision)"),
    'd_part_earth': ('Parts of the Earth',
                     'Dee\'s 91 regions of the world as known in his day, each with a governing angel, an Aethyr, a '
                     'number of ministers and a zodiac King. The app finds the nearest region to the place, by an '
                     'approximate centre of its own.', "James, Book Four (the 91 Parts); centres: app gazetteer"),
    'd_aethyr': ('Aethyr', 'One of the thirty "Aires" (heavens) to which Dee\'s Parts of the Earth belong.',
                 "James, Book Four"),
    'd_zodiac_king': ('Zodiac King (Liber Scientiae)',
                      'Twelve angelic Kings, one for each sign, each with a tribe of Israel and a quarter of the '
                      'world. A body takes the King of the IAU constellation it stands in; Ophiuchus and the '
                      'constellations off the zodiac have none (an app rule).', "James, App. A; Book Four table"),
    'sidereal': ('Sidereal sky and the IAU constellations',
                 'This app places the planets against the real constellations as the International Astronomical Union '
                 'draws them: 13 on the ecliptic, of unequal widths, rather than twelve equal signs. Each is rescaled to '
                 "30 degrees so that the old tables (Lilly's or Ptolemy's) can be applied (an app rule). Ptolemy "
                 'himself counted the signs from the equinoxes (Tetrabiblos I.22); reading them as the real '
                 "constellations is this app's choice.", None),
    'p_horoscope': ('Horoscope (the rising degree)',
                    'The degree of the zodiac rising on the eastern horizon at this moment. Ptolemy\'s first place is '
                    'the twelfth part of the zodiac around it, starting 5 degrees above the horizon; here that place '
                    'is the whole constellation holding that point.', ('III.10', 273)),
    'p_retrograde': ('Retrograde (in Ptolemy)',
                     'A planet seeming to move backwards against the stars. Ptolemy counts a planet slowing down or '
                     'going back as "diminishing in speed", when "their energy is weaker".', ('I.24', 117)),
}

# names used inside the dignity tables -> the term that explains them
_ITEM = {'house': 'essential', 'exaltation': 'essential', 'triplicity': 'essential', 'term': 'essential',
         'face': 'essential', 'detriment': 'detriment', 'fall': 'fall', 'peregrine': 'peregrine',
         'reception_house': 'reception', 'reception_exalt': 'reception', 'retrograde': 'retrograde',
         'direct': 'retrograde', 'swift': 'speed', 'slow': 'speed', 'combust': 'combust', 'free_combustion': 'combust',
         'cazimi': 'cazimi', 'under_beams': 'beams', 'besieged': 'besieged', 'moon_increasing': 'moon_light',
         'moon_decreasing': 'moon_light', 'conj_regulus': 'stars', 'conj_spica': 'stars', 'conj_algol': 'stars',
         'partile_conj_north_node': 'nodes', 'partile_conj_south_node': 'nodes'}


_ITEM_PT = {'domicile': 'p_familiarity', 'exaltation': 'p_familiarity', 'triplicity': 'p_familiarity',
            'co_triplicity': 'p_familiarity', 'term': 'p_familiarity', 'chariot': 'p_familiarity',
            'rejoice': 'p_familiarity', 'alien': 'p_familiarity', 'no_familiarity': 'p_familiarity', 'no_sign': 'sidereal',
            'depression': 'p_familiarity', 'proper_face': 'p_face', 'oriental': 'p_oriental', 'occidental': 'p_oriental',
            'adding_motion': 'p_oriental', 'diminishing_motion': 'p_oriental', 'moon_waxing': 'p_moon',
            'moon_waning': 'p_moon', 'under_rays': 'p_rays', 'in_sect': 'p_sect', 'out_of_sect': 'p_sect',
            'benefic_aspect': 'p_benefic', 'malefic_aspect': 'p_benefic', 'overcome_benefic': 'p_overcome',
            'overcome_malefic': 'p_overcome'}


def _ptolemy_mode():
    try:
        import school
        return school.is_ptolemy()
    except Exception:
        return False


def _dee_mode():
    try:
        import school
        return school.is_dee()
    except Exception:
        return False


def item_term(k):
    if _dee_mode():
        return None
    if _ptolemy_mode():
        return _ITEM_PT.get(k) or ('p_places' if k.startswith('place_') else None)
    if k in _ITEM:
        return _ITEM[k]
    if k.startswith('house_'):
        return 'angles'
    if 'oriental' in k or 'occidental' in k:
        return 'oriental'
    if k.startswith('partile'):
        return 'partile'
    return None


# Ptolemy: LacusCurtius pages of Robbins's translation, with an anchor for each Loeb page
PT_BASE = 'https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Ptolemy/Tetrabiblos/'
_PT_FILE = {'I': [(3, '1A'), (24, '1B')], 'II': [(3, '2A'), (9, '2B'), (13, '2C')],
            'III': [(9, '3A'), (10, '3B'), (12, '3C'), (14, '3D')], 'IV': [(4, '4A'), (7, '4B'), (10, '4C')]}


def pt_url(chapter, page=None):
    """'III.13', 341 -> the LacusCurtius page of that chapter, at Loeb page 341."""
    try:
        b, n = chapter.split('.')
        f = next(f for last, f in _PT_FILE[b] if int(n) <= last)
    except Exception:
        return PT_BASE + 'home.html'
    return f'{PT_BASE}{f}*.html' + (f'#p{int(page)}' if page else f'#{int(n)}')


def scan_url(page):
    return f'{SCAN}/page/n{int(page) + 34}/mode/1up'


def page_links(pages):
    return ', '.join(f'[p.{p}]({scan_url(p)})' for p in pages)


def cite_links(source):
    """'Lilly pp.121-123; p.112' -> the same text with each page linked to the scan. Ptolemy's references
    ('Tetrabiblos IV.3, Loeb p.377') link to the LacusCurtius text instead."""
    s = str(source or '')
    if any(w in s for w in ('Peterson', 'James', "Dee's", 'Enochian')):   # Dee's sources: no scan to link to
        return s
    if 'Loeb' in s or 'Tetrabiblos' in s:
        return re.sub(r'\b((?:IV|III|II|I)\.\d{1,2})(?:-(?:IV|III|II|I)\.\d{1,2})?(?:, Loeb pp?\.(\d{1,3})(?:-\d{1,3})?)?',
                      lambda m: f'[{m.group(0)}]({pt_url(m.group(1), m.group(2))})', s)
    return re.sub(r'\b(pp?\.)\s?(\d{1,3})((?:\s?[-–]\s?\d{1,3})?)',
                  lambda m: f'[{m.group(1)}{m.group(2)}{m.group(3)}]({scan_url(m.group(2))})', s)


def explain_md(key):
    title, text, pages = TERMS[key]
    if isinstance(pages, tuple):                                          # a Ptolemy term: (chapter, Loeb page)
        cite = f'Ptolemy, Tetrabiblos [{pages[0]}]({pt_url(*pages)})'
    elif isinstance(pages, str):                                          # a Dee term: a text reference
        cite = pages
    else:
        cite = ('Lilly, ' + page_links(pages)) if pages else 'An app rule.'   # short, so it never repeats as a phrase
    return f'**{title}**  \n{text}  \n\n<small>{cite}</small>'


_POP_KEY = 'key' in inspect.signature(st.popover).parameters


# Each term is explained once per page (user request: no phrasing twice on one page). app.py calls new_page() at the
# start of every run; without that call (an older app.py) nothing is held back.
_SEEN = '_gloss_page_seen'


def new_page():
    try:
        st.session_state[_SEEN] = set()
    except Exception:
        pass


def _seen():
    try:
        return st.session_state.get(_SEEN)
    except Exception:
        return None


def unseen(keys):
    """The terms not yet explained on this page (all of them if the page register is not in use)."""
    seen = _seen()
    keys = [k for k in dict.fromkeys(keys) if k in TERMS]
    return keys if seen is None else [k for k in keys if k not in seen]


def mark_seen(keys):
    seen = _seen()
    if seen is not None:
        seen.update(keys)


def chips(keys, where):
    """A row of small buttons; each opens a short explanation of one term. where: a unique prefix for this row.
    Terms already explained elsewhere on the page are left out."""
    keys = unseen(keys)
    mark_seen(keys)
    if not keys:
        return
    try:
        row = st.container(horizontal=True, gap='small')
    except TypeError:                     # an older Streamlit: one under another
        row = st.container()
    with row:
        for k in keys:
            kw = dict(key=f'gl_{where}_{k}') if _POP_KEY else {}
            with st.popover(TERMS[k][0], icon=':material/info:', **kw):
                st.markdown(explain_md(k), unsafe_allow_html=True)


def full_list():
    """Every term, for the About page."""
    for k, (title, text, pages) in sorted(TERMS.items(), key=lambda kv: kv[1][0].lower()):
        cite = (f'Ptolemy, Tetrabiblos [{pages[0]}]({pt_url(*pages)})' if isinstance(pages, tuple)
                else pages if isinstance(pages, str) else page_links(pages) if pages else 'app rule')
        st.markdown(f'**{title}**: {text} <small>({cite})</small>', unsafe_allow_html=True)
