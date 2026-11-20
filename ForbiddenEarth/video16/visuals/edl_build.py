"""Edit decision list for video16 "10 Places That Were Erased From Maps".
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 22 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 773.8

FILES = {os.path.splitext(os.path.basename(p))[0]: os.path.relpath(p, HERE)
         for p in glob.glob(os.path.join(HERE, "src", "*", "*")) if not p.endswith(".json")}

IN = lambda s0=1.0, s1=1.10, c0=(0.5, 0.5), c1=None: {"s0": s0, "s1": s1, "c0": list(c0), "c1": list(c1 or c0)}
OUT = lambda s0=1.12, s1=1.0, c0=(0.5, 0.5), c1=None: {"s0": s0, "s1": s1, "c0": list(c0), "c1": list(c1 or c0)}
PAN = lambda a, b, s=1.15, y=0.5: {"s0": s, "s1": s, "c0": [a, y], "c1": [b, y]}
TILT = lambda a, b, s=1.15, x=0.5: {"s0": s, "s1": s, "c0": [x, a], "c1": [x, b]}

def shot(key, t0, t1, move=None, x=0.6, **kw):
    return {"src": FILES.get(key, f"src/MISSING/{key}"), "t0": t0, "t1": t1, "move": move or IN(), "xin": x, "xout": x, **kw}

def inset(key, t0, t1, **kw):
    return shot(key, t0, t1, None, inset=True, **kw)

shots, overlays = [], []

def place(num, name, sub, frames, t_card, t_map, t_lower, t_end, items, lower=None, badge=None):
    if badge:   # age plate, bottom-left: appears with "Number ...", holds ~6 s (ends before the lower third)
        overlays.append({"type": "badge", "text": badge, "t0": t_card + 0.4, "t1": t_lower - 0.1, "fin": 0.5, "fout": 0.5})
    shots.append({"card": True, "bg_map": f"maps/{frames}", "num": num, "name": name, "sub": sub,
                  "t0": t_card, "t1": t_map, "xin": 0.5, "xout": 0.5})
    shots.append({"frames": f"maps/{frames}", "t0": t_map, "t1": t_lower, "xin": 0.5, "xout": 0.6})
    shots.extend(items)
    overlays.append({"type": "lower", "num": num, "text": lower or f"{name}, {sub}", "t0": t_lower + 0.1, "t1": t_end})

# ---------------- 00_hook (0:00-0:31.675) ----------------
shots += [
    shot("hyb_21",  0.00,  3.00, IN(1.0, 1.08), 0.3, xin=0),     # maps are supposed to tell the truth
    shot("hyb_n1",  3.00,  5.50, IN(1.0, 1.08), 0.25),           # these ten prove they don't
    shot("hyb_20",  5.50,  9.50, IN(1.0, 1.12), 0.25),           # never existed, stayed for centuries
    shot("sdy_17",  9.50, 14.10, IN(1.0, 1.10), 0.25),           # an island fooled sailors and Google
    shot("agl_05", 14.10, 18.10, IN(1.0, 1.10), 0.25),           # a town invented to catch thieves
    shot("dug_05", 18.10, 23.10, TILT(0.6, 0.35, 1.12), 0.25),   # very real, hidden
    shot("a51_09", 23.10, 31.675, IN(1.0, 1.12), 0.3, xout=0.5), # number one: a secret base
]
overlays.append({"type": "brand", "t0": 26.40, "t1": 31.30, "fin": 0.9, "fout": 0.5})

# ---------------- 01_argleton ----------------
place("#10", "ARGLETON", "ENGLAND", "frames_argleton", 31.675, 34.80, 38.30, 91.725, [
    shot("arg_17", 38.30, 41.50, IN(1.0, 1.08)),                   # West Lancashire, 2008
    shot("arg_dia", 41.50, 47.60, IN(1.0, 1.05)),    # between Aughton and Ormskirk (own sketch)
    shot("arg_12", 47.60, 52.00, IN(1.0, 1.08)),                   # jobs, homes, weather
    shot("arg_02", 52.00, 56.40, PAN(0.35, 0.65, 1.12)),
    shot("arg_14", 56.40, 60.10, IN(1.0, 1.08)),                   # Argleton didn't exist
    shot("arg_01", 60.10, 66.20, PAN(0.3, 0.7, 1.15)),             # an empty field
    shot("arg_09", 66.20, 70.00, IN(1.0, 1.08)),                   # people drove out to visit
    shot("arg_06", 70.00, 72.70, IN(1.0, 1.06)),
    shot("arg_03", 72.70, 77.30, IN(1.0, 1.08)),                   # typing mistake? a trap?
    shot("arg_11", 77.30, 82.00, IN(1.0, 1.10)),                   # NOT LARGE, NOT REAL
    shot("arg_16", 82.00, 86.70, TILT(0.35, 0.6, 1.1)),
    shot("arg_07", 86.70, 89.50, IN(1.0, 1.06)),                   # vanished in May 2010
    shot("arg_10", 89.50, 92.525, OUT(1.1, 1.0)),
], badge="NEVER EXISTED")

# ---------------- 02_agloe ----------------
place("#9", "AGLOE", "USA", "frames_agloe", 92.525, 95.65, 99.15, 163.525, [
    shot("agl_01", 99.15, 103.30, IN(1.0, 1.10)),                  # two mapmakers in New York
    shot("agl_14", 103.30, 108.50, IN(1.0, 1.08)),                 # rivals kept copying
    shot("agl_02", 108.50, 114.00, PAN(0.3, 0.7, 1.15)),           # a dirt road crossing in the Catskills
    shot("agl_08", 114.00, 119.10, IN(1.0, 1.08)),                 # named from their initials
    shot("agl_16", 119.10, 124.00, IN(1.0, 1.10)),                 # if Agloe showed up elsewhere
    shot("agl_03", 124.00, 132.50, TILT(0.3, 0.65, 1.12)),         # Rand McNally
    shot("agl_15", 132.50, 135.80, IN(1.0, 1.08)),                 # case closed? not quite
    shot("agl_10", 135.80, 140.90, IN(1.0, 1.08)),                 # a general store at the crossing
    shot("agl_05", 140.90, 145.80, IN(1.0, 1.08)),                 # the name on an Esso road map
    shot("agl_04", 145.80, 151.00, IN(1.0, 1.08)),                 # the fake town came to life
    {"frames": "maps/frames_agloe", "t0": 151.00, "t1": 157.90, "f0": 104, "xin": 0.6, "xout": 0.6},  # even on Google Maps
    shot("agl_09", 157.90, 164.325, OUT(1.12, 1.0)),               # removed in 2014
], badge="COPYRIGHT TRAP")

# ---------------- 03_hy_brasil ----------------
place("#8", "HY-BRASIL", "ATLANTIC OCEAN", "frames_hy_brasil", 164.325, 167.45, 170.95, 224.9, [
    shot("hyb_20", 170.95, 178.50, PAN(0.25, 0.45, 1.6, 0.4)),     # a round island west of Ireland (Ortelius 1572)
    shot("hyb_04", 178.50, 181.90, IN(1.0, 1.08)),                 # Brasil, Hy-Brasil
    shot("hyb_21", 181.90, 186.50, PAN(0.3, 0.6, 1.25)),           # 1325, for 500 years
    shot("hyb_08", 186.50, 190.80, IN(1.3, 1.5, (0.28, 0.4))),
    shot("hyb_06", 190.80, 195.00, IN(1.0, 1.08)),                 # hidden by mist
    shot("hyb_n2", 195.00, 198.00, IN(1.0, 1.08)),                 # once every seven years
    shot("hyb_12", 198.00, 203.50, PAN(0.35, 0.65, 1.12)),         # 1480, a ship from Bristol
    shot("hyb_02", 203.50, 207.50, IN(1.0, 1.10)),                 # never found
    {"frames": "maps/frames_hy_brasil", "t0": 207.50, "t1": 213.00, "f0": 104, "xin": 0.6, "xout": 0.6},  # it simply shrank
    shot("hyb_n1", 213.00, 219.00, IN(1.0, 1.10)),                 # Brasil Rock in the 1800s
    shot("hyb_16", 219.00, 225.70, OUT(1.12, 1.0)),                # gone by the 1870s
], badge="ON MAPS FOR 500 YEARS")

# ---------------- 04_sannikov_land ----------------
place("#7", "SANNIKOV LAND", "ARCTIC", "frames_sannikov_land", 225.7, 228.825, 232.325, 298.65, [
    shot("san_07", 232.325, 237.00, IN(1.0, 1.10)),                # 1811, New Siberian Islands
    shot("san_04", 237.00, 243.10, PAN(0.3, 0.7, 1.15)),           # high land far to the north
    shot("san_13", 243.10, 251.00, IN(1.0, 1.10, (0.5, 0.4))),     # a dashed line waiting to be found
    shot("san_06", 251.00, 256.00, IN(1.0, 1.08)),                 # 1886, Eduard Toll
    shot("san_14", 256.00, 261.70, IN(1.0, 1.08)),                 # obsessed
    shot("san_18", 261.70, 266.80, IN(1.0, 1.08)),                 # 1900 expedition
    shot("san_02", 266.80, 271.00, IN(1.0, 1.10)),                 # towards Bennett Island
    shot("san_17", 271.00, 274.40, IN(1.0, 1.08)),                 # never seen again
    {"frames": "maps/frames_sannikov_land", "t0": 274.40, "t1": 277.20, "f0": 104, "xin": 0.6, "xout": 0.6},
    shot("san_10", 277.20, 284.60, IN(1.0, 1.10)),                 # 1937-38 icebreakers (Sadko)
    shot("san_16", 284.60, 290.60, IN(1.0, 1.08)),                 # only frozen ocean
    shot("san_11", 290.60, 299.45, OUT(1.12, 1.0)),                # a mirage?
], badge="NEVER FOUND")

# ---------------- 05_sandy_island ----------------
place("#6", "SANDY ISLAND", "CORAL SEA", "frames_sandy_island", 299.45, 302.575, 306.075, 366.65, [
    shot("sdy_n2", 306.075, 314.80, IN(1.0, 1.10)),                # bigger than Manhattan
    shot("sdy_16", 314.80, 320.50, IN(1.0, 1.08)),                 # atlases, databases, Google Earth
    shot("sdy_06", 320.50, 326.10, IN(1.0, 1.10)),
    shot("sdy_03", 326.10, 333.00, IN(1.0, 1.08)),                 # November 2012, Southern Surveyor
    shot("sdy_08", 333.00, 337.20, IN(1.0, 1.10)),                 # 1,400 m of water
    shot("sdy_01", 337.20, 341.30, IN(1.0, 1.08)),                 # there was no island
    shot("sdy_15", 341.30, 345.10, IN(1.0, 1.10)),                 # un-discovered it
    shot("sdy_05", 345.10, 351.90, IN(1.0, 1.10)),                 # deleted from Google's maps
    shot("sdy_n1", 351.90, 356.50, IN(1.0, 1.08)),                 # a whaling ship, floating pumice
    shot("sdy_17", 356.50, 361.80, IN(1.0, 1.08)),
    {"frames": "maps/frames_sandy_island", "t0": 361.80, "t1": 367.45, "f0": 104, "xin": 0.6, "xout": 0.6},  # copied chart to chart
], badge="1,400 M OF WATER")

# ---------------- 06_bermeja ----------------
place("#5", "BERMEJA", "GULF OF MEXICO", "frames_bermeja", 367.45, 370.575, 374.075, 439.75, [
    shot("ber_18", 374.075, 381.50, PAN(0.25, 0.6, 1.3)),          # Spanish mapmakers, 1500s
    shot("ber_08", 381.50, 384.80, IN(1.0, 1.08)),                 # stayed on the maps
    shot("ber_n1", 384.80, 389.50, IN(1.0, 1.10)),                 # worth a fortune
    shot("ber_06", 389.50, 396.80, IN(1.0, 1.10)),                 # oil, borders at sea
    shot("ber_14", 396.80, 401.50, TILT(0.3, 0.7, 1.15)),          # Mexico's waters
    shot("ber_01", 401.50, 406.20, IN(1.0, 1.08)),
    shot("ber_n3", 406.20, 410.80, IN(1.0, 1.08)),                 # billions of barrels
    shot("ber_03", 410.80, 415.30, IN(1.0, 1.08)),                 # Mexico went looking, 1997
    shot("ber_02", 415.30, 420.00, IN(1.0, 1.10)),                 # 2009 survey
    shot("ber_07", 420.00, 424.00, IN(1.0, 1.08)),                 # no island
    shot("ber_17", 424.00, 430.20, IN(1.0, 1.08)),                 # rumours it was blown up
    shot("ber_n2", 430.20, 435.00, IN(1.0, 1.08)),                 # never there at all
    {"frames": "maps/frames_bermeja", "t0": 435.00, "t1": 440.55, "f0": 104, "xin": 0.6, "xout": 0.6},
], badge="BILLIONS IN OIL")

# ---------------- 07_camp_century ----------------
place("#4", "CAMP CENTURY", "GREENLAND", "frames_camp_century", 440.55, 443.675, 447.175, 520.7, [
    shot("cmp_17", 447.175, 453.60, IN(1.0, 1.10)),               # a town inside the ice sheet
    shot("cmp_05", 453.60, 459.00, TILT(0.3, 0.7, 1.2)),           # 21 tunnels (layout plan)
    shot("cmp_07", 459.00, 464.00, IN(1.0, 1.08)),                 # living quarters, labs
    shot("cmp_03", 464.00, 471.90, IN(1.0, 1.10)),                 # portable nuclear reactor
    shot("cmp_n4", 471.90, 476.00, IN(1.0, 1.08)),                 # missiles under the ice
    shot("cmp_n5", 476.00, 479.90, IN(1.0, 1.08)),
    shot("cmp_n3", 479.90, 484.80, IN(1.0, 1.10)),                 # Denmark was never told
    shot("cmp_01", 484.80, 490.30, IN(1.0, 1.08)),                 # the ice crushed the tunnels
    shot("cmp_09", 490.30, 494.20, IN(1.0, 1.08)),                 # abandoned in 1967
    shot("cmp_04", 494.20, 500.00, IN(1.0, 1.08)),                 # fuel, waste water, radioactive waste
    shot("cmp_14", 500.00, 506.80, IN(1.0, 1.08)),
    shot("cmp_n2", 506.80, 514.00, IN(1.0, 1.10)),                 # 1997; NASA radar 2024
    {"frames": "maps/frames_camp_century", "t0": 514.00, "t1": 521.50, "f0": 104, "xin": 0.6, "xout": 0.6},  # 30 m under the ice
], badge="30 M UNDER ICE")

# ---------------- 08_duga ----------------
place("#3", "DUGA RADAR", "UKRAINE", "frames_duga", 521.5, 524.625, 528.125, 599.425, [
    shot("dug_14", 528.125, 533.00, IN(1.0, 1.08)),                # 1976, a strange sound
    shot("dug_18", 533.00, 537.90, IN(1.0, 1.08)),                 # the Russian woodpecker
    shot("dug_n1", 537.90, 543.00, IN(1.0, 1.10)),                 # drowned out radio stations
    shot("dug_12", 543.00, 548.20, IN(1.0, 1.10)),                 # a forest near Chernobyl
    {"frames": "maps/frames_duga", "t0": 548.20, "t1": 553.50, "f0": 104, "xin": 0.6, "xout": 0.6},
    shot("dug_01", 553.50, 558.00, PAN(0.3, 0.7, 1.15)),           # Duga, over-the-horizon radar
    shot("dug_06", 558.00, 562.90, IN(1.0, 1.08)),
    shot("dug_11", 562.90, 567.50, TILT(0.7, 0.3, 1.1)),           # 150 m high, 700 m long
    shot("dug_05", 567.50, 571.80, IN(1.0, 1.10)),
    shot("dug_15", 571.80, 576.10, IN(1.0, 1.08)),                 # to hide something that huge
    shot("dug_16", 576.10, 580.70, IN(1.0, 1.08)),                 # marked as a children's summer camp
    shot("dug_03", 580.70, 586.10, IN(1.0, 1.08)),                 # switched off in 1989
    shot("dug_02", 586.10, 592.30, IN(1.0, 1.10)),                 # the nuclear disaster nearby
    shot("dug_10", 592.30, 600.225, OUT(1.12, 1.0)),               # still stands, forest growing back
], badge='"CHILDREN\'S CAMP"')

# ---------------- 09_sarov ----------------
place("#2", "SAROV", "RUSSIA", "frames_sarov", 600.225, 603.35, 606.85, 672.3, [
    shot("sar_20", 606.85, 613.70, IN(1.0, 1.10)),                 # a famous monastery in the forests (1903, PD)
    shot("sar_06", 613.70, 618.70, TILT(0.3, 0.55, 1.15)),         # 1946: removed from all maps
    {"frames": "maps/frames_sarov", "t0": 618.70, "t1": 623.50, "f0": 104, "xin": 0.6, "xout": 0.6},  # Arzamas-16, Moscow -> Sarov
    shot("sar_04", 623.50, 627.80, IN(1.1, 1.25, (0.45, 0.4))),    # a town dozens of km away
    shot("sar_03", 627.80, 633.30, IN(1.0, 1.10)),                 # the first Soviet atomic bomb (museum mock-up)
    shot("sar_07", 633.30, 639.00, IN(1.0, 1.08)),                 # tested in 1949
    shot("sar_n1", 639.00, 643.50, IN(1.0, 1.08)),                 # the hydrogen bomb
    shot("sar_22", 643.50, 648.40, PAN(0.35, 0.65, 1.12)),         # not allowed to talk about it
    shot("sar_24", 648.40, 654.20, PAN(0.25, 0.75, 1.5)),
    shot("sar_02", 654.20, 660.00, TILT(0.25, 0.55, 1.12)),        # old name back in 1995, still closed
    shot("sar_n2", 660.00, 666.10, IN(1.0, 1.10)),                 # nuclear weapons research centre
    {"frames": "maps/frames_sarov", "t0": 666.10, "t1": 673.10, "f0": 104, "xin": 0.6, "xout": 0.6},  # 90,000 people, special pass
], badge="ARZAMAS-16")

# ---------------- 10_area_51 ----------------
place("#1", "AREA 51", "USA", "frames_area_51", 673.1, 676.225, 679.725, 758.6, [
    shot("a51_n1", 679.725, 683.50, IN(1.0, 1.10)),               # 130 km north-west of Las Vegas
    shot("a51_09", 683.50, 690.50, IN(1.0, 1.12)),                 # Groom Lake, the most famous secret base
    shot("a51_11", 690.50, 695.50, IN(1.0, 1.08)),                 # 1955, the U-2
    shot("a51_12", 695.50, 700.00, IN(1.0, 1.08)),
    shot("a51_05", 700.00, 703.50, IN(1.0, 1.08)),                 # the A-12 Oxcart
    shot("a51_06", 703.50, 706.70, IN(1.0, 1.08)),                 # the F-117
    shot("a51_13", 706.70, 713.50, IN(1.0, 1.08)),                 # strange lights in the sky
    shot("a51_10", 713.50, 718.50, PAN(0.35, 0.65, 1.12)),         # the CIA later admitted
    shot("a51_17", 718.50, 723.10, IN(1.0, 1.08)),
    shot("a51_07", 723.10, 727.80, IN(1.0, 1.08)),                 # wouldn't even confirm it existed
    shot("a51_02", 727.80, 730.90, IN(1.0, 1.10)),                 # maps showed empty desert
    shot("a51_21", 730.90, 736.80, IN(1.0, 1.08)),                 # guards and warning signs
    shot("a51_14", 736.80, 746.70, IN(1.0, 1.12)),                 # 2013, Freedom of Information Act
    {"frames": "maps/frames_area_51", "t0": 746.70, "t1": 751.70, "f0": 104, "xin": 0.6, "xout": 0.6},  # named it and showed it on a map
    shot("a51_20", 751.70, 759.40, OUT(1.12, 1.0)),                # still secret
], badge="ADMITTED IN 2013")

# ---------------- 11_outro ----------------
shots.append(shot("hyb_04", 759.40, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 759.90, "t1": DURATION, "fin": 1.2, "fout": 0.6})
# ---------------- checks ----------------
errors, last = [], {}
for s in sorted(shots, key=lambda s: s["t0"]):
    src = s.get("src") if not s.get("card") else None
    if not src: continue
    if not os.path.exists(os.path.join(HERE, src)): errors.append(f"missing {src}")
    if src in last and s["t0"] - last[src] < MIN_GAP:
        errors.append(f"repeat {src}: {last[src]:.1f}s -> {s['t0']:.1f}s")
    last[src] = s["t1"]
for s in shots:
    if "frames" in s and not os.path.isdir(os.path.join(HERE, s["frames"])): errors.append(f"missing {s['frames']}")
if errors and "--force" not in sys.argv:
    print("\n".join(errors), file=sys.stderr); sys.exit(1)
print(json.dumps({"duration": DURATION, "audio": "../voice/full.mp3", "shots": shots, "overlays": overlays}, indent=1))
