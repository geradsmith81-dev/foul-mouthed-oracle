# Third-party notices

The MIT License in `LICENSE` covers the program code of The Foul-Mouthed Oracle and the wording written for it
(including the rude wording, the punchlines and the plain-English texts). It does **not** cover the material below,
which keeps its own terms. Full references are in `data/sources.csv` (shown on the About page) and, for the
Astrosophy Birth Chart page, in `astrosophy/data/sources.csv`.

## Texts quoted or tabulated

- **William Lilly, *Christian Astrology* (London, 1647).** Public domain. Quoted from the Wellcome Library copy
  (Internet Archive item b30338724, Public Domain Mark).
- **Ptolemy, *Tetrabiblos*, translated by F. E. Robbins (Loeb Classical Library, 1940).** In the public domain in the
  United States (copyright not renewed); it may still be protected in other countries. Quoted from the transcription
  by Bill Thayer on LacusCurtius.
- **John Dee reading (folder `enochian/data`).** The tables of angel names, correspondences and Parts of the Earth
  were transcribed from Joseph H. Peterson (ed.), *John Dee's Five Books of Mystery* (Weiser Books, 2003), and
  Geoffrey James, *The Enochian Evocation of Dr John Dee*. Dee's own sixteenth-century words are in the public
  domain; the editors' editions are still under copyright, and any rights in them remain with their holders. These
  tables are not licensed under the MIT License.
- **Astrosophy Birth Chart page (folder `astrosophy`).** Readings after Rudolf Steiner, Elisabeth Vreede and
  Willi Sucher, and the life chart after George and Gisela O'Neil, *The Human Life* (ed. Florin Lowndes, Mercury
  Press, 1990), drawn afresh. See `astrosophy/data/sources.csv`.

## Data and images

- **NASA JPL DE440s ephemeris** (downloaded on first start, not stored in this repository), used through the
  Skyfield library.
- **GeoNames** place names (via the geonamescache package): Creative Commons Attribution 4.0 (CC BY 4.0).
- **Elevation:** Terrain Tiles on the AWS Registry of Open Data (Mapzen/Tilezen), and the Open-Meteo Elevation API
  (CC BY 4.0; Copernicus DEM GLO-90, © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018, provided
  under COPERNICUS by the European Union and ESA).
- **Background image:** Hubble's image of the Lagoon Nebula (heic1808a). Credit: NASA, ESA, STScI. Creative Commons
  Attribution 4.0 International (CC BY 4.0).
- **Enochian letters (font `assets/fonts/OracleEnochian.ttf`, used by the "Enochian script" switch).** The glyph
  drawings are "Enochian - <letter>.svg" (22 files, Wikimedia Commons, Category:Enochian letters) by Лорд Алекс
  (Lord Alex), 2018, licensed Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0),
  https://creativecommons.org/licenses/by-sa/4.0/. They were converted into a font (scaled, set on a baseline,
  mapped to A-Z, W made from two Vans) by Gerad Smith, 2026; the font is shared under the same CC BY-SA 4.0 license,
  not the MIT License. Details: `assets/fonts/OracleEnochian-LICENSE.txt`. The letter forms follow John Dee's table
  of 6 May 1583 (British Library, Sloane MS 3188, f. 104), which is in the public domain.
- **Wiktionary**, Category:English idioms (CC BY-SA 4.0): headwords only were used as a check; no definitions were
  copied.

## Inspiration

The idea of a rude reading comes from joke weather apps such as WTForecast, CARROT Weather and Dirty Weather; every
line was written for this app. Not affiliated with or endorsed by the makers of these apps.

## Software

The app runs on open-source packages listed in `requirements.txt` (among them Streamlit, Skyfield, NumPy, pandas
and Matplotlib), each under its own license.
