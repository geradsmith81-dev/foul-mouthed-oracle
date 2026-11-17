"""Enochian script: a sidebar switch that spells the screen in John Dee's Enochian letters (user request; The
Foul-Mouthed Oracle only). The switch itself, with its caption, always stays in English, so it can be found and
switched back.

How it works. Only the look of the letters changes: the words underneath stay English, so copying text, the
downloads, the calendar files and "Say it out loud!" are unchanged. The app's own font, Oracle Enochian
(assets/fonts/OracleEnochian.ttf), puts an Enochian letter in the place of each Latin letter, A-Z and a-z alike
(Enochian has no capitals). Characters the font does not have - digits, punctuation, planet and sign symbols, emoji -
are drawn by the normal font, so dates, degrees and scores stay readable.

Letters, after Dee's table of 6 May 1583 (British Library, Sloane MS 3188, f. 104), where 21 letters stand for 22
English ones: Un A, Pa B, Veh C and K, Gal D, Graph E, Or F, Ged G, Na H, Gon I and J, Ur L, Tal M, Drux N, Med O,
Mals P, Ger Q, Don R, Fam S, Gisg T, Van U and V, Pal X, Ceph Z. W is written as two Vans (VV), and Y as Gon with
a point. Dee wrote Enochian from right to left; the app keeps the English left-to-right order, because the words
are English words.

The glyph drawings are by the Wikimedia Commons user Lord Alex (Лорд Алекс), "Enochian - <letter>.svg", 2018,
licensed CC BY-SA 4.0. The font made from them (scaled, placed on a baseline, W made from two Vans) is
therefore also CC BY-SA 4.0: see assets/fonts/OracleEnochian-LICENSE.txt and THIRD-PARTY-NOTICES.md. It is not
covered by the app's MIT License.

What it reaches: all text on the page (css() below), the tables (drawn as plain tables while the switch is on,
because Streamlit's interactive table paints its letters itself and cannot take a web font), the pictures drawn with
Matplotlib (the chart wheel, the calendars, the Astrosophy charts: install_pyplot() below) and the "Say it out loud!"
button. Left in ordinary letters: this switch, the friend codes (they are typed or pasted back in), the app's icons,
error tracebacks, and Streamlit's own menu at the top right.
"""
import base64
import functools
import os

import streamlit as st

KEY = 'enochian_script'
BOX = 'enochian_switch'          # the keyed container around the switch: Streamlit gives it the class st-key-enochian_switch
FAMILY = 'Oracle Enochian'
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(HERE, 'assets', 'fonts', 'OracleEnochian.ttf')
LETTERS = {'A': 'Un', 'B': 'Pa', 'C': 'Veh', 'D': 'Gal', 'E': 'Graph', 'F': 'Or', 'G': 'Ged', 'H': 'Na', 'I': 'Gon',
           'J': 'Gon', 'K': 'Veh', 'L': 'Ur', 'M': 'Tal', 'N': 'Drux', 'O': 'Med', 'P': 'Mals', 'Q': 'Ger', 'R': 'Don',
           'S': 'Fam', 'T': 'Gisg', 'U': 'Van', 'V': 'Van', 'W': 'Van Van', 'X': 'Pal', 'Y': 'Gon with a point',
           'Z': 'Ceph'}
# the normal fonts behind the Enochian letters (they draw the digits, punctuation and symbols)
TEXT_FALLBACK = '"Source Sans", "Source Sans Pro", "Source Sans 3", "Segoe UI", sans-serif'
HEAD_FALLBACK = "Georgia, 'Palatino Linotype', 'Book Antiqua', serif"
# never re-lettered: this switch, the friend codes and other code, the icons (Material Symbols is a font whose
# "words" draw the pictures), error tracebacks, and Streamlit's own toolbar and menu
KEEP = ('.st-key-' + BOX, '.st-key-' + BOX + ' *', 'code', 'code *', 'pre', 'pre *',
        '[data-testid="stIconMaterial"]', '[data-testid="stToolbar"] *', '[data-testid="stMainMenuPopover"] *',
        '[data-testid="stException"] *')


def available():
    return os.path.exists(FONT_FILE)


def on():
    """True while the switch is on (for this visitor only)."""
    try:
        return bool(st.session_state.get(KEY, False)) and available()
    except Exception:
        return False


def switch():
    """The sidebar switch. Call once per run, from app.py, before the page runs. Always in English."""
    if not available():
        return
    with st.sidebar.container(key=BOX):
        st.toggle('Enochian script', key=KEY)
        st.caption("Spells the screen in John Dee's Enochian letters (1583). This switch always stays in English: "
                   "turn it off to read English again." if on() else
                   "Spells the screen in John Dee's Enochian letters (1583). The words stay English underneath.")


@functools.lru_cache(maxsize=2)
def _font_b64(mtime):
    with open(FONT_FILE, 'rb') as f:
        return base64.b64encode(f.read()).decode()


def font_face():
    """The @font-face rule. The font travels inside the page, so nothing is fetched from anywhere."""
    return ("@font-face { font-family: '" + FAMILY + "'; font-style: normal; font-weight: 100 900; "
            "font-display: block; src: url(data:font/ttf;base64," + _font_b64(os.path.getmtime(FONT_FILE))
            + ") format('truetype'); }")


def css():
    """The page CSS, for st.markdown(..., unsafe_allow_html=True); empty while the switch is off."""
    if not on():
        return ''
    keep = ', '.join(KEEP)
    return ('<style>\n' + font_face() + '\n'
            f"html body *:not({keep}) {{ font-family: '{FAMILY}', {TEXT_FALLBACK} !important; }}\n"
            f"html body :is(h1, h2, h3):not({keep}) {{ font-family: '{FAMILY}', {HEAD_FALLBACK} !important; }}\n"
            # the tables drawn as plain tables on a computer while the switch is on (device.table)
            '.enochian-table { overflow-x: auto; margin: 0.25rem 0 0.9rem; }\n'
            '.enochian-table .lilly-table { border-collapse: collapse; width: 100%; font-size: 0.95rem; }\n'
            '.enochian-table .lilly-table th, .enochian-table .lilly-table td { text-align: left; vertical-align: top; '
            'padding: 0.3rem 0.55rem; border: none; border-bottom: 1px solid rgba(255, 255, 255, 0.18); }\n'
            '.enochian-table .lilly-table th { font-weight: 700; white-space: nowrap; }\n'
            '</style>')


def iframe_css():
    """For the small pages Streamlit puts in frames (the "Say it out loud!" button): the font and a rule that puts
    it in front of the frame's own font. Empty while the switch is off."""
    if not on():
        return ''
    return ('<style>' + font_face() + f" button {{ font-family: '{FAMILY}', 'Source Sans Pro', 'Segoe UI', "
            "sans-serif !important; }</style>")


# ------------------------------------------------------------------ pictures drawn with Matplotlib
_REGISTERED = []


def _register_font():
    if not _REGISTERED:
        from matplotlib import font_manager
        font_manager.fontManager.addfont(FONT_FILE)
        _REGISTERED.append(True)


def letter_figure(fig):
    """Put Oracle Enochian in front of the font of every piece of text in a Matplotlib figure. Matplotlib then
    draws each Latin letter in Enochian and everything else (symbols, digits) in the figure's own font."""
    import matplotlib.text
    _register_font()
    for t in fig.findobj(matplotlib.text.Text):
        fam = list(t.get_fontfamily())
        if fam and fam[0] != FAMILY:
            t.set_fontfamily([FAMILY] + fam)
    return fig


def install_pyplot():
    """st.pyplot is wrapped once per server: while this visitor's switch is on, the figure is re-lettered first.
    The switch is read from the visitor's own session, so other visitors are not affected."""
    if getattr(st.pyplot, '_enochian', False):
        return
    original = st.pyplot

    @functools.wraps(original)
    def pyplot(fig=None, *args, **kwargs):
        if fig is not None and on():
            try:
                letter_figure(fig)
            except Exception:
                pass                     # never lose the picture over its lettering
        return original(fig, *args, **kwargs)

    pyplot._enochian = True
    st.pyplot = pyplot
