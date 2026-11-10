"""The Foul-Mouthed Oracle's voice: the same readings as The Sidereal Oracle, said rudely.

The idea comes from joke weather apps such as WTForecast, which pair an accurate forecast with one big, blunt and often
profane line, and let the user turn the swearing up or down. Every line here is new: none is copied from such apps.

Four levels (sidebar 'How rude?'), like the ON / SOME / MINIMAL / OFF settings of those apps:
  Full   - the crude wording with the swear words as written;
  Some   - the same wording with the strong swear words masked (f*ck, sh*t);
  Clean  - the same wording with the swear words swapped for tame ones (frick, crap, heck);
  Polite - the original Sidereal Oracle wording (no punchline).

The crude wording lives in the column 'crude' of data/forecast_rules.csv and data/election_rules.csv (same
placeholders as the 'plain' column) and the punchlines in data/punchlines.csv. Lilly's own words (column 'text') are
never changed: they are shown under Strengths/Weaknesses, in Full view and in "Show the working".
"""
import os
import random
import re
import zlib

import json

import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
LEVELS = ('Full', 'Some', 'Clean', 'Polite')
DEFAULT = 'Full'
KEY = 'voice_level'
HELP = ("How rude the Oracle is. Full: swearing as written. Some: the worst words masked (f*ck). "
        "Clean: tame stand-ins (frick, crap, heck). Polite: The Sidereal Oracle's original wording, no punchline. "
        "Lilly's own 1647 words are never changed.")

# ------------------------------------------------------------------ the swear filter
# whole idioms first (so they stay idiomatic when cleaned), then single words; matched as whole words, any case
_IDIOMS_CLEAN = [
    (r'weak as piss', 'weak as dishwater'), (r'fuck all', 'diddly squat'), (r'bugger all', 'diddly squat'),
    (r"for fuck's sake", 'for crying out loud'), (r'give a shit', 'give a hoot'), (r'give a damn', 'give a hoot'),
    (r'talking out of its ass', 'talking nonsense'), (r'talking out of their ass', 'talking nonsense'),
    (r'kick(s)? ass', r'rock\1'), (r'half-assed', 'half-baked'), (r'tough shit', 'tough luck'),
    (r'shit hits the fan', 'muck hits the fan'), (r'holy shit', 'holy moly'), (r'pissed themselves laughing', 'nearly wet themselves laughing'), (r'piss off', 'buzz off'),
    (r'arse-end', 'tail end'), (r'ass-end', 'tail end'), (r'pain in the ass', 'pain in the neck'),
    (r'hell yes', 'heck yes'), (r'hell no', 'heck no'), (r'what the hell', 'what the heck'),
    (r'shitshow', 'circus'), (r'(get|start|this|that|new) shit', r'\1 stuff'),
]
_WORDS_CLEAN = [
    ('motherfucking', 'mother-flipping'), ('fucking', 'flipping'), ('fucked', 'fricked'), ('fuckery', 'foolery'),
    ('fucker', 'jerk'), ('fucks', 'fricks'), ('fuck', 'frick'),
    ('bullshit', 'baloney'), ('shitty', 'crappy'), ('shit', 'crap'),
    ('asshole', 'jerk'), ('assholes', 'jerks'), ('badass', 'champ'), ('smartass', 'smarty-pants'),
    ('dumbass', 'dummy'), ('ass', 'butt'), ('arse', 'bum'),
    ('bastards', 'so-and-sos'), ('bastard', 'so-and-so'), ('bollocks', 'nonsense'), ('bugger', 'blighter'),
    ('pissed', 'ticked off'), ('pissing', 'peeing'), ('piss', 'pee'),
    ('bloody', 'flipping'), ('damned', 'darned'), ('damn', 'darn'), ('goddamn', 'gosh-darn'), ('hell', 'heck'), ('dick', 'jerk'),
]
# 'Some': mask the strong words only; damn, hell, crap and ass stay as they are
_WORDS_SOME = [
    ('motherfucking', 'motherf*cking'), ('fucking', 'f*cking'), ('fucked', 'f*cked'), ('fuckery', 'f*ckery'),
    ('fucker', 'f*cker'), ('fucks', 'f*cks'), ('fuck', 'f*ck'), ('bullshit', 'bullsh*t'), ('shitty', 'sh*tty'),
    ('shitshow', 'sh*tshow'), ('shit', 'sh*t'), ('asshole', 'a**hole'), ('assholes', 'a**holes'),
    ('bastards', 'b*stards'), ('bastard', 'b*stard'), ('bollocks', 'b*llocks'), ('pissed', 'p*ssed'),
    ('pissing', 'p*ssing'), ('piss', 'p*ss'), ('dick', 'd*ck'),
]


def _case_like(src, new):
    if src.isupper() and len(src) > 1:
        return new.upper()
    if src[:1].isupper():
        return new[:1].upper() + new[1:]
    return new


def _sub_all(text, pairs, is_regex=False):
    for old, new in pairs:
        # whole words only; '*' counts as a word character only inside a word (f*ck), not in **bold** marks
        pat = re.compile(r'(?<![\w])(?<!\w\*)' + (old if is_regex else re.escape(old)) + r'(?![\w])(?!\*\w)',
                         re.IGNORECASE)
        text = pat.sub(lambda m: _case_like(m.group(0), m.expand(new)), text)
    return text


def filter_text(text, lvl=None):
    """Apply the profanity level to a crude line ('Polite' is treated like 'Clean' here)."""
    lvl = lvl or level()
    if not isinstance(text, str) or lvl == 'Full':
        return text
    if lvl == 'Some':
        return _sub_all(text, _WORDS_SOME)
    return _sub_all(_sub_all(text, _IDIOMS_CLEAN, is_regex=True), _WORDS_CLEAN)


# ------------------------------------------------------------------ the level
def level():
    try:
        v = st.session_state.get(KEY, DEFAULT)
    except Exception:            # outside a Streamlit run (tests, scripts)
        v = DEFAULT
    return v if v in LEVELS else DEFAULT


def polite():
    return level() == 'Polite'


def switch():
    """The sidebar control. Rendered by app.py on every page."""
    if KEY not in st.session_state:
        st.session_state[KEY] = DEFAULT
    try:
        st.sidebar.segmented_control('How rude?', LEVELS, key=KEY, help=HELP, required=True, width='stretch')
    except TypeError:            # an older Streamlit without 'required'
        st.sidebar.radio('How rude?', LEVELS, key=KEY, help=HELP, horizontal=True)


def say(crude, polite_text):
    """Pick the wording for the current level: the crude line (filtered) or the original polite one."""
    if polite() or not isinstance(crude, str) or not crude.strip():
        return polite_text
    return filter_text(crude)


def item(x):
    """A Forecast line (dict with 'plain' and 'crude') in the current voice."""
    return say(x.get('crude'), x.get('plain') or x.get('text'))


def items(result):
    """Election items of one judged moment, with the text swapped for the current voice (same 5-tuple shape)."""
    its = result.get('items') or []
    cr = result.get('crude')
    if polite() or not cr or len(cr) > len(its):
        return its
    # the election rules come first; natal points added for a birth chart (natal.personalise) follow, unchanged
    n = len(cr)
    return ([(rid, filter_text(c) if c else t, p, s, k) for (rid, t, p, s, k), c in zip(its[:n], cr)]
            + list(its[n:]))


def plain(j):
    """j['plain'] of electional.judge in the current voice: (rule_id, text, points, kind)."""
    cr = j.get('crude')
    if polite() or not cr or len(cr) != len(j['plain']):
        return j['plain']
    return [(rid, filter_text(c) if c else t, p, k) for (rid, t, p, k), c in zip(j['plain'], cr)]


# ------------------------------------------------------------------ grades
GRADE_POLITE = {'best': 'Best', 'good': 'Good', 'fair': 'Fair', 'avoid': 'Avoid'}
GRADE_CRUDE = {'best': 'Hell yes', 'good': 'Not bad', 'fair': 'Meh', 'avoid': 'Nope'}


class GradeText(dict):
    """Acts like the old {'best': 'Best', ...} dict, but answers in the current voice."""
    def __init__(self):
        super().__init__(GRADE_POLITE)

    def __getitem__(self, g):
        return GRADE_POLITE[g] if polite() else filter_text(GRADE_CRUDE[g])

    def get(self, g, default=None):
        return self[g] if g in GRADE_POLITE else default


GRADE_TXT = GradeText()


# ------------------------------------------------------------------ punchlines (the big line on top of the Forecast)
@st.cache_data(show_spinner=False)
def _punchlines(mtime):
    df = pd.read_csv(os.path.join(HERE, 'data', 'punchlines.csv'), encoding='utf-8')
    return {k: g['text'].tolist() for k, g in df.groupby('trigger')}


def _bank():
    path = os.path.join(HERE, 'data', 'punchlines.csv')
    return _punchlines(os.path.getmtime(path))


# Forecast rules (and two extra sky conditions) that get their own punchlines
TRIGGERS = ('moon_void', 'not_radical', 'saturn_asc', 'cazimi', 'asc_ophiuchus', 'lord_asc_combust',
            'moon_via_combusta', 'mercury_retro', 'reception')


def verdict(fc):
    s, w = len(fc['strengths']), len(fc['weaknesses'])
    return 'good' if s > w + 1 else 'bad' if w > s + 1 else 'mixed'


def candidates(fc, rows=None):
    """Every punchline that fits this chart: lines for the special conditions first, then the overall verdict."""
    bank = _bank()
    fired = {x.get('id') for x in fc['strengths'] + fc['weaknesses']}
    if rows is not None and any(r['body'] == 'Mercury' and r.get('speed', 0) < 0 for r in rows):
        fired.add('mercury_retro')
    special = [t for k in TRIGGERS if k in fired for t in bank.get(k, [])]
    return special, bank.get('verdict_' + verdict(fc), [])


def punchline(fc, seed, rows=None, shift=0):
    """One line for this chart. The same moment and place always give the same line; 'shift' moves to the next."""
    special, general = candidates(fc, rows)
    rng = random.Random(zlib.crc32(str(seed).encode()))
    special, general = special[:], general[:]
    rng.shuffle(special)
    rng.shuffle(general)
    # alternate: a line about a special condition, then a line about the overall verdict, and so on
    order = []
    while special or general:
        if special:
            order.append(special.pop())
        if general:
            order.append(general.pop())
    if not order:
        return ''
    return filter_text(order[shift % len(order)])


# ------------------------------------------------------------------ loading messages
LOADING = [
    'Shoving the planets into place ...', 'Asking the Moon what the hell she is doing ...',
    'Waking up Saturn. He is a grumpy old bastard in the mornings ...', 'Digging William Lilly out of 1647 ...',
    'Untangling the damn constellations ...', 'Pestering NASA for the planet positions ...',
    'Hold your horses, the sky is big ...', 'Counting the planets. Still seven. Still a pain in the ass ...',
    'Polishing the crystal ball. Someone sneezed on it ...', 'Bribing Mercury to stop going backwards ...',
]


def loading(polite_text):
    if polite():
        return polite_text
    return filter_text(random.choice(LOADING))


# ------------------------------------------------------------------ reading the punchline out loud
def speak_button(line):
    """A 'Say it out loud' button using the browser's own speech (no sound files, nothing sent anywhere).
    At 'Some' the clean wording is spoken, so the voice does not read out asterisks."""
    spoken = line if level() == 'Full' else filter_text(line, 'Clean')
    label = filter_text('Say it out loud, damn it') if level() != 'Polite' else 'Say it out loud'
    html = f"""<!doctype html><html><body style="margin:0;background:transparent">
<button id="b" style="width:100%;height:40px;border-radius:0.5rem;border:1px solid #4f6789;background:#111927;
 color:#f7f1ea;font:600 15px 'Source Sans Pro','Segoe UI',sans-serif;cursor:pointer">&#128266; {label}</button>
<script>
const t = {json.dumps(spoken)};
document.getElementById('b').onclick = () => {{
  try {{ speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(t); u.rate = 1.0; speechSynthesis.speak(u); }}
  catch (e) {{ document.getElementById('b').textContent = 'This browser cannot speak'; }}
}};
if (!('speechSynthesis' in window)) {{ document.getElementById('b').style.display = 'none'; }}
</script></body></html>"""
    if hasattr(st, 'iframe'):
        st.iframe(html, height=44)
    else:                                           # an older Streamlit
        import streamlit.components.v1 as components
        components.html(html, height=44)


# ------------------------------------------------------------------ styling of the punchline (added by app.py)
CSS = """<style>
.foul-punch { font-size: 1.65rem; line-height: 1.3; font-weight: 700; color: #ffffff; margin: 0.2rem 0 0.7rem 0;
  padding: 0.9rem 1.1rem; border-left: 6px solid #f2994a; border-radius: 0.6rem;
  background: rgba(17, 25, 39, 0.82); text-shadow: 0 1px 2px rgba(0,0,0,0.6); }
@media (max-width: 640px) { .foul-punch { font-size: 1.3rem; padding: 0.7rem 0.85rem; } }
</style>"""


def rules_table(df):
    """A rules CSV for display: the 'crude' column filtered to the current level, or dropped in Polite."""
    if 'crude' not in df.columns:
        return df
    if polite():
        return df.drop(columns=['crude'])
    df = df.copy()
    df['crude'] = df['crude'].map(filter_text)
    return df
