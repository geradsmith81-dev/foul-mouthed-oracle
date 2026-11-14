"""Forecast box in Ptolemy mode: the chart of the moment read with the Tetrabiblos's own testimonies.

Ptolemy has no rules for questions (horary) or for choosing times, so this reads the moment as he reads a nativity:
the sect and its light, the luminaries at the angles and in masculine signs and their attendants (IV.3), the
beneficent and maleficent planets at the angles (I.5, I.7, I.24), the ruler of the horoscope by the five ways of
domination (III.2-III.3), the lord of the Lot of Fortune (IV.2), the Moon's light (III.13) and the House of the Evil
Daemon (III.10). The wording of each rule is in data/ptolemy_rules.csv (enabled = False switches one off).
Same result shape as forecast.build().
"""
import os
import pandas as pd

import lilly_layer as ll
import ptolemy_layer as pt
import forecast

HERE = os.path.dirname(os.path.abspath(__file__))
ORD = ll._ord
MASC = set(pt.PDG.loc[pt.PDG['gender'] == 'masculine', 'sign'])


def _join(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' and ' + xs[-1]


def build(R, rows, bands, ph=None, rules_csv=None):
    rules = pd.read_csv(rules_csv or os.path.join(HERE, 'data', 'ptolemy_rules.csv'), encoding='utf-8')
    rules = rules[rules['enabled'].astype(str).str.lower().isin(['true', '1', 'yes'])].set_index('rule_id')
    out = {'strength': [], 'weakness': []}

    def fire(rid, **kw):
        if rid in rules.index:
            r = rules.loc[rid]
            plain = r['plain'] if 'plain' in rules.columns and isinstance(r['plain'], str) and r['plain'].strip() else r['text']
            item = dict(id=rid, text=r['text'].format(**kw), plain=plain.format(**kw), source=r['source'], basis=r['basis'])
            if 'crude' in rules.columns:
                crude = r['crude'] if isinstance(r['crude'], str) and r['crude'].strip() else plain
                item['crude'] = crude.format(**kw)          # the Foul-Mouthed wording (voice.py filters it)
            out[r['kind']].append(item)

    P = {p['planet']: p for p in R['planets']}
    day = R['sun_up']
    daynight = 'day' if day else 'night'
    light, other_light = ('Sun', 'Moon') if day else ('Moon', 'Sun')
    pof = R['part_of_fortune']
    sky = forecast.sky(rows, bands)
    pn = lambda n: pt.place_name(n)

    # ---------------- summary paragraph ----------------
    para = [f"This is a {'diurnal' if day else 'nocturnal'} figure, so the {light} is the light of the sect "
            f"(Tetrabiblos I.7, III.10)."]
    asc = R['asc']
    first = R['place_constellations'][0]
    if first == asc['constellation']:
        para.append(f"The first place is the whole of {first}, the constellation on the Ascendant (III.10, adapted to "
                    f"the real constellations).")
    else:
        para.append(f"The first place is the whole of {first}, the constellation that holds the point 5° above the "
                    f"Ascendant (III.10, adapted to the real constellations); {asc['constellation']} is on the horizon "
                    f"itself.")
    lord = R['lord_of_asc']
    if lord:
        lp = P[lord]
        para.append(f"The ruler of the horoscope, by the five ways of domination (III.2-III.3), is {pt.the(lord)} "
                    f"({pt.ways_text(R['lord_ways'])}). {pt.the(lord)[0].upper() + pt.the(lord)[1:]} stands in {lp['constellation']}, in {pn(lp['house'])} "
                    f"(place {lp['house']}), {lp['honour']}, with {lp['fortitudes']} points for and {lp['debilities']} "
                    f"against (net {lp['net']:+d}).")
    else:
        para.append(f"{asc['constellation']} rises; it has no sign in Ptolemy, so the horoscope has no ruler.")
    if R.get('soul_governor'):
        para.append(f"The planet that dominates Mercury and the Moon, and so governs the quality of the soul (III.13), "
                    f"is {pt.the(R['soul_governor'])}.")
    ranked = sorted(R['planets'], key=lambda p: p['net'], reverse=True)
    para.append(f"The strongest planet is {pt.the(ranked[0]['planet'])} (net {ranked[0]['net']:+d}); "
                f"the weakest is {pt.the(ranked[-1]['planet'])} (net {ranked[-1]['net']:+d}).")
    para.append(f"The Lot of Fortune, reckoned the same way by day and by night (III.10), falls in {pof['constellation']}, "
                f"in place {pof['house']}" + (f"; its lord is {pt.the(R['fortune_ruler'])}." if R.get('fortune_ruler') else '.'))

    # ---------------- rules ----------------
    sl = P[light]
    if sl['house'] in pt.AUTHORITY:
        fire('sect_light_authority', light=light, place=sl['house'], pname=pn(sl['house']), daynight=daynight)
    sun, moon = P['Sun'], P['Moon']
    ang = [x for x in ('Sun', 'Moon') if P[x]['house'] in pt.ANGLES]
    if sun['sign'] in MASC and moon['sign'] in MASC and ang:
        fire('lights_masculine_angular', sun_sign=sun['constellation'], moon_sign=moon['constellation'],
             which='both' if len(ang) == 2 else f"the {ang[0]}",
             which_plain='both stand' if len(ang) == 2 else f"the {ang[0]} stands")
    good, bad = [], []
    for a in R['aspects']:
        if light in (a['a'], a['b']):
            o = a['b'] if a['a'] == light else a['a']
            if o in pt.BENEFIC and a['aspect'] in ('conjunction', 'sextile', 'trine'):
                good.append((o, a['aspect']))
        for L in ('Sun', 'Moon'):
            if L in (a['a'], a['b']):
                o = a['b'] if a['a'] == L else a['a']
                if o in pt.MALEFIC and a['aspect'] in ('conjunction', 'square', 'opposition'):
                    bad.append((L, o, a['aspect'], a['deviation']))
    if good:
        fire('light_benefic_attended', light=light, planets=_join(o for o, _ in good), how=_join(f"{s}" for _, s in good))
    for p in pt.BENEFIC:
        if P[p]['house'] in pt.ANGLES:
            fire('benefic_angular', planet=p, place=P[p]['house'], pname=pn(P[p]['house']))
    if lord:
        lp = P[lord]
        kw = dict(lord=lord, ways=pt.ways_text(R['lord_ways']), n=lp['net'], pname=pn(lp['house']), place=lp['house'])
        if lp['net'] >= 5:
            fire('ruler_asc_strong', **kw)
        elif lp['net'] <= -5:
            fire('ruler_asc_weak', **kw)
        if lp['house'] in pt.NO_ASPECT:
            fire('ruler_asc_powerless', **kw)
    fr = R.get('fortune_ruler')
    if fr:
        n = P[fr]['net']
        if n > 0:
            fire('fortune_ruler_strong', ruler=fr, n=n, fsign=pof['constellation'])
        elif n < 0:
            fire('fortune_ruler_weak', ruler=fr, n=n, fsign=pof['constellation'])
    if moon['elong'] > 0:
        fire('moon_waxing', lit=sky['lit'])
    else:
        fire('moon_waning', lit=sky['lit'])
    for p in pt.MALEFIC:
        if P[p]['house'] in pt.ANGLES:
            own = P[p]['sect'] == ('diurnal' if day else 'nocturnal')
            fire('malefic_angular', planet=p, place=P[p]['house'], pname=pn(P[p]['house']),
                 sect_note=(', though of the sect of the figure, which tempers it: "the greatest part of their injurious '
                            'power is broken"' if own else ', and of the contrary sect, so its harm is not tempered'),
                 sect_plain=(', though it belongs to this chart\'s side (day or night), which softens it' if own
                             else ', and it does not belong to this chart\'s side (day or night), so nothing softens it'))
    for L, o, asp_, dev in bad:
        fire('light_afflicted', light=L, planet=o, aspect=asp_, dev=dev)
    if not ang:
        benef = bool(good) or any(other_light in (a['a'], a['b']) and bool(({a['a'], a['b']} - {other_light}) & set(pt.BENEFIC))
                                  and a['aspect'] in ('conjunction', 'sextile', 'trine') for a in R['aspects'])
        humble = sun['sign'] not in MASC and moon['sign'] not in MASC and not benef
        fire('lights_not_angular',
             extra=('; nor is either in a masculine sign or attended by a beneficent planet, Ptolemy\'s picture of the '
                    'humblest fortune' if humble else ''),
             extra_plain=(', none is in a "masculine" constellation and no kindly planet backs them up' if humble else ''))
    for p in [light, lord] if lord and lord != light else [light]:
        if p and P[p]['house'] == 12:
            fire('evil_daemon', planet=p)
    if not asc['has_sign']:
        fire('asc_ophiuchus', con=asc['constellation'])
    for p in R['planets']:
        if p['constellation'] == 'Ophiuchus':
            fire('ophiuchus_planet', planet=p['planet'])

    return dict(summary=' '.join(para), strengths=out['strength'], weaknesses=out['weakness'],
                note=("The strengths and weaknesses are Ptolemy's own testimonies (Tetrabiblos, tr. F. E. Robbins, 1940), "
                      "chiefly from III.10, III.13 and IV.2-IV.3, applied here to the sidereal IAU sky. Ptolemy wrote no "
                      "rules for questions or for choosing times, so the moment is read as he reads a nativity. Where the "
                      "app had to adapt a rule, the line says so. This is traditional symbolism for study and reflection; "
                      "controlled studies have not found astrological charts to be predictive."))


def as_text(fc, header=''):
    return forecast.as_text(fc, header)
