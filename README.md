# The Foul-Mouthed Oracle

The Sidereal Oracle with a potty mouth. It draws an accurate chart of the real sky for any moment and place (NASA JPL
DE440s planet positions via Skyfield, the real IAU constellations at their true widths) and reads it with the rules of
William Lilly's *Christian Astrology* (London, 1647), then says what it means rudely. The idea comes from joke
weather apps such as WTForecast; every line was written for this app.

**How rude?** (sidebar): Full, Some (masked), Clean (tame stand-ins) or Polite (the original Sidereal Oracle wording).
Lilly's own words, page references and scores are never changed.

- Run online on Streamlit Community Cloud: see `DEPLOY GUIDE.txt`.
- The rude wording: column `crude` of `data/forecast_rules.csv` and `data/election_rules.csv`, and
  `data/punchlines.csv`.
- The NASA JPL file `ephem/de440s.bsp` (32 MB) is not in this repository; the app downloads it on first start.
- Profile: online, profiles and friends are kept only while the app is open, unless *Remember me on this device* is
  ticked (then in this browser only). Nothing about visitors is stored on the server.
- Background: Hubble's image of the Lagoon Nebula (heic1808a), credit NASA, ESA, STScI, CC BY 4.0.
- Astrology has not been found to predict events in controlled studies. This app is for fun and reflection.
