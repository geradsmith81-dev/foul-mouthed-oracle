"""Whose reading: William Lilly (Christian Astrology, 1647) or Ptolemy (Tetrabiblos, 2nd century).

The sidebar switch "Whose reading?" (app.py calls switch() once per run, before the page runs). The Chart page
reads the chart with the chosen author's rules; the Auspicious dates page keeps Lilly's election rules in both modes,
because the Tetrabiblos has no rules for choosing times (user decision), and says so.

Ptolemy is quoted from F. E. Robbins's translation (Loeb Classical Library, 1940; public domain in the United States,
copyright not renewed), as transcribed on LacusCurtius. Its tables are the CSV files data/ptolemy_*.csv.
"""
import streamlit as st

KEY = 'reading_school'
LILLY, PTOLEMY = 'Lilly', 'Ptolemy'
OPTIONS = (LILLY, PTOLEMY)
LABELS = {LILLY: 'William Lilly (1647)', PTOLEMY: 'Ptolemy (Tetrabiblos)'}
HELP = ("Whose rules read the chart. William Lilly: Christian Astrology (1647), with his dignity points, his "
        "considerations before judgment and Regiomontanus houses. Ptolemy: the Tetrabiblos (2nd century, tr. "
        "F. E. Robbins, 1940), with his dignities, sect, places of authority and his pictures of each planet. "
        "Both read the real sidereal sky. The Auspicious dates page always uses Lilly's election rules, because "
        "Ptolemy wrote none.")
ROBBINS = 'https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Ptolemy/Tetrabiblos/home.html'


def current():
    try:
        v = st.session_state.get(KEY, LILLY)
    except Exception:
        v = LILLY
    return v if v in OPTIONS else LILLY


def is_ptolemy():
    return current() == PTOLEMY


def author():
    """'Ptolemy' or 'Lilly'."""
    return current()


def authors():
    """"Ptolemy's" or "Lilly's"."""
    return current() + "'s"


def book():
    return 'the Tetrabiblos' if is_ptolemy() else 'Christian Astrology (1647)'


def switch():
    """The sidebar switch. Call once per run, from app.py, before the page runs."""
    if st.session_state.get(KEY) not in OPTIONS:
        st.session_state[KEY] = LILLY
    st.sidebar.radio('Whose reading?', OPTIONS, key=KEY, format_func=LABELS.get, help=HELP)
