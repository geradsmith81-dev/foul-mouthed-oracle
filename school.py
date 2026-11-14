"""Whose reading: William Lilly (Christian Astrology, 1647) or Ptolemy (Tetrabiblos, 2nd century).

The sidebar switch "Whose reading?" (app.py calls switch() once per run, before the page runs): William Lilly,
Ptolemy or John Dee. The Chart page reads the chart with the chosen author's rules; the Auspicious dates page keeps
Lilly's election rules in every reading, because neither the Tetrabiblos nor Dee's angelic tables give rules for
choosing times (user decision), and says so.

John Dee's reading is the user's Sidereal Enochian Chart app (package enochian/): the Heptarchic King and Prince of
the day, the ministering angels of the hour, the zodiac Kings of Liber Scientiae and the Part of the Earth, from
J. H. Peterson's edition of John Dee's Five Books of Mystery and G. James's The Enochian Evocation of Dr John Dee.

Ptolemy is quoted from F. E. Robbins's translation (Loeb Classical Library, 1940; public domain in the United States,
copyright not renewed), as transcribed on LacusCurtius. Its tables are the CSV files data/ptolemy_*.csv.
"""
import streamlit as st

KEY = 'reading_school'
LILLY, PTOLEMY, DEE = 'Lilly', 'Ptolemy', 'Dee'
OPTIONS = (LILLY, PTOLEMY, DEE)
LABELS = {LILLY: 'William Lilly (1647)', PTOLEMY: 'Ptolemy (Tetrabiblos)', DEE: 'John Dee'}
HELP = ("Whose rules read the chart. William Lilly: Christian Astrology (1647), with his dignity points, his "
        "considerations before judgment and Regiomontanus houses. Ptolemy: the Tetrabiblos (2nd century, tr. "
        "F. E. Robbins, 1940), with his dignities, sect, places of authority and his pictures of each planet. "
        "John Dee: the angelic reading of the Sidereal Enochian Chart - the day's Heptarchic King and Prince, the "
        "ministering angels of the hour, the zodiac Kings and the Part of the Earth for the place. All three read "
        "the real sidereal sky. The Auspicious dates page always uses Lilly's election rules, because the others "
        "give none.")
ROBBINS = 'https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Ptolemy/Tetrabiblos/home.html'


def current():
    try:
        v = st.session_state.get(KEY, LILLY)
    except Exception:
        v = LILLY
    return v if v in OPTIONS else LILLY


def is_ptolemy():
    return current() == PTOLEMY


def is_dee():
    return current() == DEE


def is_lilly():
    return current() == LILLY


def author():
    """'Lilly', 'Ptolemy' or 'Dee'."""
    return current()


def authors():
    """"Lilly's", "Ptolemy's" or "Dee's"."""
    return current() + "'s"


def book():
    return {PTOLEMY: 'the Tetrabiblos', DEE: "Dee's angelic tables"}.get(current(), 'Christian Astrology (1647)')


def switch():
    """The sidebar switch. Call once per run, from app.py, before the page runs."""
    if st.session_state.get(KEY) not in OPTIONS:
        st.session_state[KEY] = LILLY
    st.sidebar.radio('Whose reading?', OPTIONS, key=KEY, format_func=LABELS.get, help=HELP)
