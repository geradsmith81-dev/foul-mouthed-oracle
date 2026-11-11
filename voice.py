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
    (r'shitshow', 'circus'), (r'good shit', 'good stuff'), (r'watch your ass', 'watch your back'),
    (r'full of shit', 'full of baloney'), (r'(get|start|this|that|new) shit', r'\1 stuff'),
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


# ------------------------------------------------------------------ variety: no swear expression twice on a page
# (user request: reduce repeated foul language). The first use of an expression on a page stays as written; each
# later use is swapped for a colourful idiom, a different one each time. The idioms are common English expressions,
# most of them listed in Wiktionary's "Category:English idioms" (headwords only; no definitions were copied). They are
# clean, so the variety also thins out the swearing. Works on text already filtered to the 'How rude?' level.
_VREG = '_voice_variety'
VARIETY = [
    ('give', r"\bgive a (?:damn|hoot|shit|sh\*t)\b", ["give a monkey's", 'give two hoots', 'give a fig']),
    ('as_hell', r"\bas (?:hell|heck)\b", ['as all get-out', 'as they come', 'as anything', 'as an ox', 'to the nines']),
    ('wh_hell', r"\b(what|who|where|why|how) the (?:hell|heck)\b", [r'\1 on earth', r'\1 in blazes', r'\1 the dickens']),
    ('hell_yes', r"\b(?:hell|heck) yes\b", ['you bet', 'and how', 'too right', "that's the ticket", 'bang on']),
    ('tough', r"\btough (?:shit|sh\*t|luck)\b", ['hard cheese', 'tough cookies', 'tough beans']),
    ('holy', r"\bholy (?:shit|sh\*t|moly)\b", ['holy cow', 'holy mackerel', 'holy smoke']),
    ('nothing', r"\b(?:fuck|f\*ck|bugger) all\b|\bdiddly squat\b", ['precious little', 'zilch', 'next to nothing']),
    ('sake', r"\bfor (?:fuck's|f\*ck's) sake\b|\bfor crying out loud\b",
     ["for heaven's sake", "for Pete's sake", 'for the love of Mike']),
    ('get_done', r"\bget (?:shit|sh\*t|stuff) done\b",
     ['get the show on the road', 'get down to brass tacks', 'get a wiggle on']),
    ('new_stuff', r"\bnew (?:shit|sh\*t|stuff)\b", ['new can of worms', 'new song and dance', 'new caper']),
    ('stuff', r"\b(this|that) (?:shit|sh\*t|stuff)\b",
     [r'\1 kettle of fish', r'\1 song and dance', r'\1 whole shebang', r'\1 malarkey']),
    ('kicks', r"\bkicks ass\b|\brocks\b(?=[.!])", ["is the bee's knees", "is the cat's pyjamas", 'is top drawer']),
    ('talking', r"\btalking (?:out of (?:its|their) (?:ass|butt)|nonsense)\b",
     ['talking through its hat', 'blowing hot air', 'full of hot air']),
    ('move', r"\bmove your (?:ass|arse|butt|bum)\b", ['shake a leg', 'get a wiggle on', 'look lively']),
    ('watch', r"\bwatch your (?:ass|arse|butt|back)\b", ['watch your step', 'mind your step', 'keep your eyes peeled']),
    ('piss_off', r"\b(?:piss|p\*ss|buzz) off\b", ['take a hike', 'go fly a kite', 'sling your hook']),
    ('go_hell', r"\bgo to (?:hell|heck)\b", ['go pear-shaped', 'go south', 'go to the dogs']),
    ('mess', r"\b(?:shitshow|sh\*tshow|dumpster fire)\b|(?<=of a )circus\b",
     ["dog's breakfast", 'three-ring circus', 'train wreck', 'dog and pony show']),
    ('nonsense', r"\b(?:bullshit|bullsh\*t|baloney)\b", ['hot air', 'codswallop', 'tommyrot', 'hogwash']),
    ('bastards', r"\b(?:bastards|b\*stards|so-and-sos)\b", ['blighters', 'rascals', 'old devils']),
    ('bastard', r"\b(?:bastard|b\*stard|so-and-so)\b", ['blighter', 'rascal', 'old devil']),
    ('crap', r"\bcrap\b", ['tosh', 'guff', 'twaddle']),
    # plain intensifiers last ('a damn thing', 'too damn early', 'absolutely fucking nowhere')
    ('mod', r"(?<!give a )\b(?:damn|darn|bloody|flipping|fucking|f\*cking)\b(?=\s+[a-z])",
     ['ruddy', 'blooming', 'blinking', 'dashed', 'deuced', 'flaming', 'thundering', 'perishing']),
]
_VARIETY_RX = [(n, re.compile(rx, re.IGNORECASE), alts) for n, rx, alts in VARIETY]


def vary(text):
    """Swap the second and later uses of a swear expression on this page for idioms (see VARIETY)."""
    if polite() or not isinstance(text, str):
        return text
    try:
        state = st.session_state.setdefault(_VREG, {})
    except Exception:
        return text
    memo = state.setdefault('_memo', {})
    if text in memo:                 # the same line again on this page (e.g. shared by undertakings): same wording
        return memo[text]
    src = text
    used_alts = state.setdefault('_alts', set())
    for name, rx, alts in _VARIETY_RX:
        def repl(m, name=name, alts=alts):
            n = state.get(name, 0)
            state[name] = n + 1
            if n == 0:
                return m.group(0)
            k = (n - 1) % len(alts)
            for a in alts[k:] + alts[:k]:
                out = m.expand(a)
                if out.lower() not in used_alts:
                    used_alts.add(out.lower())
                    return _case_like(m.group(0), out)
            return m.group(0)
        text = rx.sub(repl, text)
    memo[src] = text
    return text


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
    """The sidebar controls 'How rude?' (profanity) and 'Who's talking?' (personality). Rendered by app.py."""
    if KEY not in st.session_state:
        st.session_state[KEY] = DEFAULT
    if PKEY not in st.session_state:
        st.session_state[PKEY] = PDEFAULT
    try:
        st.sidebar.segmented_control('How rude?', LEVELS, key=KEY, help=HELP, required=True, width='stretch')
        st.sidebar.segmented_control("Who's talking?", PERSONAS, key=PKEY, help=PHELP, required=True,
                                     width='stretch', disabled=polite())
    except TypeError:            # an older Streamlit without 'required'
        st.sidebar.radio('How rude?', LEVELS, key=KEY, help=HELP, horizontal=True)
        st.sidebar.radio("Who's talking?", PERSONAS, key=PKEY, help=PHELP, horizontal=True, disabled=polite())


# ------------------------------------------------------------------ personality (an idea from CARROT Weather)
# Separate from the swearing: the same facts said by three characters. Polite switches the personality off.
PERSONAS = ('Friendly', 'Snarky', 'Doom-monger')
PDEFAULT = 'Snarky'
PKEY = 'voice_persona'
PHELP = ("Who delivers the reading. Friendly: warm teasing. Snarky: sarcastic. Doom-monger: theatrical cosmic dread "
         "about the sky (never aimed at you). The swearing is set separately under 'How rude?'. Off in Polite.")


def persona():
    try:
        v = st.session_state.get(PKEY, PDEFAULT)
    except Exception:
        v = PDEFAULT
    return v if v in PERSONAS else PDEFAULT


# ------------------------------------------------------------------ no phrase twice on one page (user request)
# Every run of a page starts a fresh register (app.py calls new_page()). Each box that says something takes a
# wording nobody else on the page has used yet; repeated slots (grade meanings, headings, labels, disclaimers) have
# several variants for that reason.
_REG = '_voice_page_used'


def new_page():
    try:
        st.session_state[_REG] = set()
        st.session_state[_VREG] = {}
    except Exception:
        pass
    try:
        import glossary
        getattr(glossary, 'new_page', lambda: None)()
    except Exception:
        pass


def _norm(t):
    t = re.sub(r'<[^>]+>', ' ', str(t)).replace('*', '')
    return re.sub(r'[^a-z0-9 ]+', '', re.sub(r'\s+', ' ', t.lower())).strip()


def _register():
    try:
        return st.session_state.setdefault(_REG, set())
    except Exception:
        return set()


def mark_used(text):
    _register().add(_norm(text))
    return text


def is_used(text):
    return _norm(text) in _register()


def pick(slot, polite_options=None, seed=0, **fmt):
    """A wording for `slot` that is not yet used on this page, in the current voice and personality."""
    if polite():
        opts = list(polite_options or POLITE_PHRASES.get(slot, []))
    else:
        opts = list(PHRASES[slot][persona()])
    if not opts:
        return ''
    k = zlib.crc32(str(seed).encode()) % len(opts)
    order = opts[k:] + opts[:k]
    reg = _register()
    for o in order:
        txt = o.format(**fmt) if fmt else o
        out = txt if polite() else filter_text(txt)
        if _norm(out) not in reg:
            reg.add(_norm(out))
            return out if polite() else vary(out)
    out = order[0].format(**fmt) if fmt else order[0]
    return out if polite() else filter_text(out)


def say(crude, polite_text):
    """Pick the wording for the current level: the crude line (filtered) or the original polite one."""
    if polite() or not isinstance(crude, str) or not crude.strip():
        return polite_text
    return vary(filter_text(crude))


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


# ------------------------------------------------------------------ variant wordings for repeated slots
# One list per personality; at least four variants where a page can show the slot four times (the four undertakings).
# No sentence is shared between variants, so no two boxes on a page say the same thing.
PHRASES = {
    'grade_best': {
        'Snarky': ["Hell yes. This hour sits in the top tenth of the week, so stop dithering.",
                   "Top-tier hour. The week barely gets better than this, so move your ass.",
                   "One of the finest hours of the whole damn week. Go.",
                   "Prime time: hardly any hour this week beats it."],
        'Friendly': ["Oh, this is a lovely hour, right up with the best tenth of the week.",
                     "Gold star! Few hours this week can touch this one.",
                     "What a cracking time, near the very top of the week.",
                     "Treat yourself: this hour ranks among the week's finest."],
        'Doom-monger': ["Rejoice, briefly: this hour stands among the week's finest, and such mercy is rare.",
                        "The heavens relent. Few hours this week will be kinder.",
                        "A window of grace, in the top tenth of the week. It will not last.",
                        "Even this doom-laden sky smiles on the hour. Seize it before it remembers itself."]},
    'grade_good': {
        'Snarky': ["Not bad. Better than most hours this week.",
                   "Decent. Most of the week is worse than this.",
                   "A respectable hour, comfortably above the week's usual crap.",
                   "Good enough to get on with it, which most hours this week can't claim."],
        'Friendly': ["Nice! This hour beats most of the week.",
                     "A good one, comfortably nicer than the usual hour.",
                     "Pretty pleasant, as hours go: well above average this week.",
                     "Solid choice. Most of this week's hours fall short of it."],
        'Doom-monger': ["A tolerable hour. Most of the week is bleaker.",
                        "Better than most hours ahead, which is not saying much.",
                        "The gloom lifts a little here: an above-average hour.",
                        "Of the many grim hours this week, this is one of the less grim."]},
    'grade_fair': {
        'Snarky': ["Meh. No warning, nothing special: a beige sort of hour.",
                   "An ordinary hour. Nobody will write songs about it.",
                   "Middling. It won't hurt, it won't help.",
                   "Perfectly average, like supermarket bread."],
        'Friendly': ["An everyday hour: no warnings, no fireworks.",
                     "Fine and ordinary, with nothing against it and nothing special for it.",
                     "A plain, gentle hour. Nothing wrong with that.",
                     "Middle of the road, with no red flags."],
        'Doom-monger': ["A grey hour, neither cursed nor blessed.",
                        "The void shrugs. Nothing marks this hour for good or ill.",
                        "Ordinary, as most hours are before the end.",
                        "No omen either way. The sky simply waits."]},
    'grade_avoid': {
        'Snarky': ["Nope. One of Lilly's cautions applies, so he'd sit on his hands.",
                   "Hard pass: a Lilly warning is in force right now.",
                   "Don't. Lilly flagged this hour with one of his cautions.",
                   "Lilly would refuse this one outright. Pick another hour, genius."],
        'Friendly': ["Maybe not this one: one of Lilly's cautions applies.",
                     "Best to wait, sweetheart. Lilly has a warning out for this hour.",
                     "Let this hour pass; Lilly would have advised against it.",
                     "Not ideal. One of Lilly's warnings is in play."],
        'Doom-monger': ["Forbidden. One of Lilly's dread cautions hangs over this hour.",
                        "The omens forbid it: Lilly's warnings are upon this moment.",
                        "Turn back. Lilly himself would have bolted the door.",
                        "Ill-starred. A caution from Lilly darkens this hour."]},
    'best_label': {
        'Snarky': ['Best damn time this week', 'Your best shot this week', 'When to actually do it',
                   "The week's sweet spot"],
        'Friendly': ['Your best time this week', 'The loveliest time this week', 'Pencil this in',
                     "The week's happy hour"],
        'Doom-monger': ["The week's one mercy", 'The least doomed hour', 'When the stars relent',
                        'Your narrow window']},
    'best_none': {
        'Snarky': ["Every single hour this week has a Lilly warning on it. Tough luck.",
                   "Not one clean hour all week for this. Try next week.",
                   "The whole week is flagged for this one. Sit tight.",
                   "Zero usable hours this week. The sky says wait."],
        'Friendly': ["No luck this week, I'm afraid: every hour carries a warning.",
                     "This week isn't the one for it, as every hour has a caution.",
                     "Let this one wait for another week, since no hour is clear.",
                     "Every hour this week has a little warning attached. Sorry!"],
        'Doom-monger': ["The whole week lies under Lilly's shadow for this.",
                        "No hour escapes the warnings. Not one.",
                        "Seven days, and all of them marked. Wait.",
                        "Every hour this week is cursed for this undertaking."]},
    'helping': {
        'Snarky': ['Going for it:', 'The good shit:', 'Points in its favour:', "What's working:"],
        'Friendly': ['Cheering you on:', "What's on your side:", 'Good news:', 'Helping hands:'],
        'Doom-monger': ['Faint hope:', 'What little helps:', 'Scant comfort:', 'A glimmer:']},
    'take_care': {
        'Snarky': ['The catch:', 'Watch your ass:', 'What could screw it up:', 'The fine print:'],
        'Friendly': ['Gently does it:', 'A little caution:', 'Mind these:', 'Keep an eye on:'],
        'Doom-monger': ['The shadows:', 'What lurks:', 'Ill omens:', 'Beware:']},
    'shared_title': {
        'Snarky': ['Goes for all four, like it or not'], 'Friendly': ['True for all four'],
        'Doom-monger': ['Hangs over all four']},
    'shared_intro': {
        'Snarky': ["These apply to the whole chart, so they're listed once here instead of four bloody times below."],
        'Friendly': ["These are about the whole sky right now, so you'll find them once here rather than in every box."],
        'Doom-monger': ["These omens hang over the entire sky, so they are spoken once, here, and not again below."]},
    'disclaimer': {
        'Snarky': ["Reality check: this is a 1647 astrology book with a potty mouth, for fun and reflection. Controlled "
                   "studies have never found astrology to predict a damn thing, so don't make important decisions with it.",
                   "Fine print: astrology has flunked every controlled test going, so treat this as a laugh, not a plan.",
                   "Reminder: nothing here has passed a scientific test. Don't bet anything that matters on it."],
        'Friendly': ["Just so you know: astrology hasn't held up in controlled studies, so enjoy this for fun and "
                     "reflection, not decisions.",
                     "A friendly reminder: these readings come from a 1647 book. Science hasn't found astrology "
                     "predictive, so keep it light.",
                     "Please don't base big decisions on this; studies haven't found that astrology works."],
        'Doom-monger': ["Heed this above all: no controlled study has found astrology to foretell anything. Decide "
                        "nothing grave by it.",
                        "The only certain prophecy here: science has never found astrology predictive. Treat this "
                        "as theatre.",
                        "Be warned: these omens come from a 1647 book, and controlled studies have not found such "
                        "omens to work."]},
}
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

# Overview of the Forecast box and of 'In short' (two wordings, so both can be on one page)
OVERVIEW = {
    'Snarky': dict(
        word=('strong as hell', 'pretty solid', 'neither here nor there', 'a bit wobbly', 'weak as piss'),
        lord=["**{con}** is rising, so **{lord}** is the planet standing in for you. By Lilly's points it's "
              "**{word}** (net {n:+d}), in the {house} house.",
              "Your stand-in tonight is **{lord}**, because **{con}** is coming up over the horizon. It scores "
              "{n:+d} on Lilly's table, which makes it **{word}**, and it's parked in the {house} house."],
        nolord=["**{con}** is rising. It has no sign in Lilly, so no planet stands for you and half his tests go "
                "straight out the damn window.",
                "With **{con}** on the horizon there's no Lilly sign and so no planet for you; a good chunk of his "
                "tests simply can't be run."],
        tally=["The Forecast found **{s} good sign{ss}** and **{w} bit{ws} of bad news**.",
               "Count: **{s} point{ss} in your favour**, **{w} against**."],
        good=[" On balance: **pretty damn good**.", " Net result: **the sky is on your side**."],
        bad=[" On balance: **a bit of a shitshow**. Prepare, wait or go easy; this is not the moment to push your luck.",
             " Net result: **rough**. Keep your head down and don't force anything."],
        mixed=[" On balance: **meh, mixed**.", " Net result: **a coin toss**."],
        caution=["{c} of the bad bits {isare} among Lilly's *considerations before judgment* (marked ⚠). They don't "
                 "say things will go to hell; they say this chart might be full of shit, so take the rest of it "
                 "with a pinch of salt.",
                 "Watch the ⚠ marks: {c} of them {isare} Lilly's *considerations before judgment*, his way of saying "
                 "the chart itself may be unreliable, not that doom is coming."]),
    'Friendly': dict(
        word=('wonderfully strong', 'doing nicely', 'perfectly balanced', 'a little tired', 'having a rough day'),
        lord=["**{con}** is rising, which makes **{lord}** your planet for this moment. On Lilly's points it's "
              "**{word}** (net {n:+d}), sitting in the {house} house.",
              "With **{con}** coming up, your planet is **{lord}**. Lilly's table gives it {n:+d}, so it's **{word}**, "
              "and you'll find it in the {house} house."],
        nolord=["**{con}** is rising, and Lilly's book has no sign for it, so there's no planet for you this time "
                "and several of his tests can't be made.",
                "Rising now is **{con}**, a constellation Lilly never gave a sign, so no planet speaks for you and "
                "some tests have to sit this one out."],
        tally=["The Forecast found **{s} encouraging sign{ss}** and **{w} thing{ws} to watch**.",
               "Tally: **{s} hopeful sign{ss}**, **{w} gentle warning{ws}**."],
        good=[" Overall it's **really rather lovely**.", " All in all, **things look bright**."],
        bad=[" Overall it **asks for care**: a time to rest, prepare or go gently.",
             " All in all, **go easy on yourself** and save big moves for later."],
        mixed=[" Overall it's **a mixed bag**.", " All in all, **a bit of both**."],
        caution=["{c} of the warnings {isare} among Lilly's *considerations before judgment* (marked ⚠). They don't "
                 "mean things will go wrong, just that the chart may not be safe to read, so hold the rest lightly.",
                 "The ⚠ marks ({c}) are Lilly's *considerations before judgment*: a gentle note that the chart "
                 "itself may be hard to read, rather than a bad sign."]),
    'Doom-monger': dict(
        word=('terrifyingly strong', 'holding firm', 'suspended between fates', 'faltering', 'all but extinguished'),
        lord=["**{con}** ascends, and so **{lord}** answers for you. By Lilly's reckoning it is **{word}** (net "
              "{n:+d}), lodged in the {house} house.",
              "As **{con}** climbs the eastern sky, **{lord}** is bound to your fate. Lilly's tally reads {n:+d}: "
              "**{word}**, from the {house} house."],
        nolord=["**{con}** ascends, a constellation without a sign in Lilly's book. No planet answers for you, and "
                "his surest tests fall silent.",
                "The horizon brings **{con}**, unknown to Lilly's signs: you stand unrepresented, and many of his "
                "tests cannot be made."],
        tally=["The Forecast found **{s} sign{ss} of hope** and **{w} omen{ws} of trouble**.",
               "The reckoning: **{s} mercy{ss}**, **{w} portent{ws}**."],
        good=[" On balance: **a rare reprieve**.", " Verdict: **the heavens are, for now, merciful**."],
        bad=[" On balance: **dark days**. Prepare, wait, and do not tempt the sky.",
             " Verdict: **the omens gather**. Hold back."],
        mixed=[" On balance: **the scales hang level**.", " Verdict: **fate undecided**."],
        caution=["{c} of the portents {isare} among Lilly's *considerations before judgment* (marked ⚠). They do not "
                 "foretell ruin; they warn that this chart may deceive, so trust the rest of it less.",
                 "Mark the ⚠ signs, {c} in number: Lilly's *considerations before judgment*, warnings that the chart "
                 "itself may lie rather than that disaster comes."]),
}

# Loading messages, one set per personality (worded unlike any punchline)
LOADING_BY = {
    'Snarky': ['Shoving the planets into place ...', 'Asking the Moon what the hell she is doing ...',
               'Digging William Lilly out of 1647 ...', 'Untangling the damn constellations ...',
               'Pestering NASA for the planet positions ...', 'Hold your horses, the sky is big ...',
               'Counting the planets. Still seven. Still a pain in the ass ...',
               'Polishing the crystal ball. Someone sneezed on it ...'],
    'Friendly': ['Warming up the telescope ...', 'Fetching the planets, gently ...',
                 'Asking the Moon nicely where she has got to ...', 'Plumping the cushions on the zodiac ...',
                 'Making Saturn a cup of tea ...', 'Tidying the constellations ...',
                 "Checking NASA's planet tables ...", "Dusting off William Lilly's book ..."],
    'Doom-monger': ['Consulting the abyss ...', 'Unsealing the tome of 1647 ...',
                    "Reading the sky's last will and testament ...", 'Counting the omens. There are many ...',
                    'The planets assemble in silence ...', 'Peering into the dark between the stars ...',
                    "Summoning NASA's ephemeris from the deep ...", 'Waiting for the heavens to pronounce ...'],
}


# ------------------------------------------------------------------ grades
GRADE_POLITE = {'best': 'Best', 'good': 'Good', 'fair': 'Fair', 'avoid': 'Avoid'}
GRADE_CRUDE = {'best': 'Top notch', 'good': 'Not bad', 'fair': 'Meh', 'avoid': 'Nope'}   # labels: no swearing, since they repeat


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
    if 'persona' not in df.columns:
        df['persona'] = PDEFAULT
    return {(t, p): g['text'].tolist() for (t, p), g in df.groupby(['trigger', 'persona'])}


def _bank():
    path = os.path.join(HERE, 'data', 'punchlines.csv')
    return _punchlines(os.path.getmtime(path))


# Conditions with their own punchlines: Forecast rules, plus conditions read straight from the sky
TRIGGERS = ('moon_void', 'not_radical', 'saturn_asc', 'cazimi', 'asc_ophiuchus', 'lord_asc_combust',
            'moon_via_combusta', 'reception', 'full_moon', 'new_moon', 'mercury_retro', 'venus_retro', 'mars_retro',
            'jupiter_retro', 'saturn_retro', 'many_retro', 'lord_strong', 'lord_weak')
_CLASSICAL = ('Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn')


def verdict(fc):
    s, w = len(fc['strengths']), len(fc['weaknesses'])
    return 'good' if s > w + 1 else 'bad' if w > s + 1 else 'mixed'


def conditions(fc, rows=None, R=None):
    """The special conditions of this chart that have punchlines."""
    fired = {x.get('id') for x in fc['strengths'] + fc['weaknesses']}
    if rows is not None:
        by = {r['body']: r for r in rows}
        retro = [p for p in _CLASSICAL if p in by and by[p].get('speed', 0) < 0]
        fired |= {p.lower() + '_retro' for p in retro}
        if len(retro) >= 3:
            fired.add('many_retro')
        if 'Sun' in by and 'Moon' in by and 'ecl_lon' in by['Sun'] and 'ecl_lon' in by['Moon']:
            e = (by['Moon']['ecl_lon'] - by['Sun']['ecl_lon']) % 360
            if e < 15 or e > 345:
                fired.add('new_moon')
            elif abs(e - 180) < 15:
                fired.add('full_moon')
    if R is not None and R.get('lord_of_asc'):
        n = {p['planet']: p['net'] for p in R['planets']}.get(R['lord_of_asc'], 0)
        if n >= 10:
            fired.add('lord_strong')
        elif n <= -10:
            fired.add('lord_weak')
    return [k for k in TRIGGERS if k in fired]


def candidates(fc, rows=None, R=None, who=None):
    """Every punchline that fits this chart for this personality: special conditions, then the overall verdict."""
    bank, who = _bank(), who or persona()
    special = [t for k in conditions(fc, rows, R) for t in bank.get((k, who), [])]
    return special, bank.get(('verdict_' + verdict(fc), who), [])


def _order(fc, seed, rows, R, who):
    special, general = candidates(fc, rows, R, who)
    rng = random.Random(zlib.crc32(f'{seed}|{who}'.encode()))
    special, general = special[:], general[:]
    rng.shuffle(special)
    rng.shuffle(general)
    order = []                     # alternate: a line about a special condition, then one about the verdict
    while special or general:
        if special:
            order.append(special.pop())
        if general:
            order.append(general.pop())
    return order


RECENT_MAX = 40


def punchline(fc, seed, rows=None, shift=0, R=None):
    """One line for this chart. The same moment, place, personality and 'shift' give the same line within a visit;
    lines already shown recently in this visit are skipped (no joke on repeat, the main complaint about Dirty
    Weather), as long as there are others left."""
    who = persona()
    order = _order(fc, seed, rows, R, who)
    if not order:
        return ''
    try:
        cache = st.session_state.setdefault('_punch_pick', {})
        recent = st.session_state.setdefault('_punch_recent', [])
    except Exception:
        cache, recent = {}, []
    key = (str(seed), int(shift), who)
    line = cache.get(key)
    if line not in order:
        k = shift % len(order)
        rot = order[k:] + order[:k]
        fresh = [t for t in rot if t not in recent and not is_used(filter_text(t))]
        line = (fresh or rot)[0]
        cache[key] = line
        recent.append(line)
        del recent[:-RECENT_MAX]
    return mark_used(vary(filter_text(line)))


def straight(fc):
    """'Say it straight' (an idea from CARROT Weather): the punchline's facts in one plain sentence."""
    s, w = len(fc['strengths']), len(fc['weaknesses'])
    word = {'good': 'encouraging', 'bad': 'one that calls for care', 'mixed': 'mixed'}[verdict(fc)]
    return mark_used(f"Straight answer: Lilly's rules give this moment {s} point{'s' if s != 1 else ''} for and "
                     f"{w} against, so the overall picture is {word}.")


# ------------------------------------------------------------------ loading messages
LOADING = LOADING_BY['Snarky']


def loading(polite_text):
    if polite():
        return polite_text
    return filter_text(random.choice(LOADING_BY[persona()]))


# ------------------------------------------------------------------ reading the punchline out loud
def speak_button(line):
    """A 'Say it out loud' button using the browser's own speech (no sound files, nothing sent anywhere).
    At 'Some' the clean wording is spoken, so the voice does not read out asterisks."""
    spoken = line if level() == 'Full' else filter_text(line, 'Clean')
    label = 'Say it out loud!'                     # the user's wording
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
.foul-punch.foul-straight { font-size: 1.2rem; font-weight: 600; border-left-color: #6fd0dc; }
@media (max-width: 640px) { .foul-punch { font-size: 1.3rem; padding: 0.7rem 0.85rem; }
  .foul-punch.foul-straight { font-size: 1.05rem; } }
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
