"""Edit decision list for video17 "10 Places Disappearing Before Our Eyes".
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 23 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 629.85

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

# ---------------- 00_hook (0:00-0:23.5) ----------------
shots += [
    shot("dea_05",  0.00,  3.60, IN(1.0, 1.08), 0.3, xin=0),     # won't be here much longer
    shot("dea_09",  3.60,  6.70, IN(1.0, 1.10), 0.25),           # a sea that drops a metre a year
    shot("jak_14",  6.70, 11.60, IN(1.0, 1.10), 0.25),           # a capital city sinking
    shot("bla_04", 11.60, 16.00, IN(1.0, 1.10), 0.25),           # a village that vanished
    shot("tuv_26", 16.00, 23.50, IN(1.0, 1.12), 0.3, xout=0.5),  # a whole country
]
overlays.append({"type": "brand", "t0": 18.50, "t1": 23.10, "fin": 0.9, "fout": 0.5})

M = lambda f, t0, t1: {"frames": f"maps/{f}", "t0": t0, "t1": t1, "f0": 104, "xin": 0.6, "xout": 0.6}

# ---------------- 01_glacier_np ----------------
place("#10", "GLACIER NATIONAL PARK", "USA", "frames_glacier_np", 23.5, 26.625, 30.125, 79.525, [
    shot("gla_06", 30.125, 35.50, IN(1.0, 1.08)),                 # Montana
    shot("gla_12", 35.50, 41.10, PAN(0.35, 0.65, 1.12)),          # 150 glaciers in the high valleys
    shot("gla_01", 41.10, 46.00, IN(1.0, 1.10)),                  # USGS measured them
    shot("gla_15", 46.00, 50.60, IN(1.0, 1.08)),
    shot("gla_05", 50.60, 56.10, IN(1.0, 1.10)),                  # only 26 left
    shot("gla_11", 56.10, 61.90, IN(1.0, 1.08)),                  # shrunk by 80 %
    shot("gla_07", 61.90, 66.00, IN(1.0, 1.08)),                  # hike to Grinnell Glacier
    shot("gla_02", 66.00, 69.50, TILT(0.3, 0.6, 1.1)),            # 1938 (USGS repeat photo)
    shot("gla_10", 69.50, 72.50, IN(1.0, 1.08)),                  # 2009
    shot("gla_16", 72.50, 75.50, IN(1.0, 1.08)),                  # 2019
    shot("gla_09", 75.50, 80.325, OUT(1.12, 1.0)),                # within our lifetime
], badge="150 TO 26 GLACIERS")

# ---------------- 02_kilimanjaro ----------------
place("#9", "KILIMANJARO", "TANZANIA", "frames_kilimanjaro", 80.325, 83.45, 86.95, 132.375, [
    shot("kil_04", 86.95, 92.00, IN(1.0, 1.10)),                  # highest mountain in Africa
    shot("kil_14", 92.00, 98.20, PAN(0.35, 0.65, 1.12)),          # ice above the savanna
    shot("kil_n3", 98.20, 100.60, IN(1.0, 1.08)),                 # going fast
    shot("kil_01", 100.60, 106.00, IN(1.0, 1.08)),                # 1993 (NASA)
    shot("kil_06", 106.00, 110.60, IN(1.0, 1.08)),                # 2000 (NASA)
    shot("kil_02", 110.60, 115.00, IN(1.0, 1.10)),                # walls of ice
    shot("kil_07", 115.00, 119.80, IN(1.0, 1.08)),                # melting in the sun
    shot("kil_10", 119.80, 123.50, IN(1.0, 1.08)),                # gone around 2040
    shot("kil_n2", 123.50, 126.30, IN(1.0, 1.08)),
    shot("kil_03", 126.30, 133.175, OUT(1.12, 1.0)),              # bare rock
], badge="85% OF THE ICE GONE")

# ---------------- 03_aral_sea ----------------
place("#8", "ARAL SEA", "CENTRAL ASIA", "frames_aral_sea", 133.175, 136.30, 139.80, 190.5, [
    shot("ara_02", 139.80, 144.90, IN(1.0, 1.10)),                # one of the four biggest lakes
    shot("ara_16", 144.90, 147.30, IN(1.0, 1.08)),                # fishing towns
    shot("ara_08", 147.30, 154.20, IN(1.0, 1.10)),                # rivers diverted for cotton
    shot("ara_n1", 154.20, 160.40, IN(1.0, 1.06)),                # lost 90 % (NASA then/now)
    shot("ara_15", 160.40, 163.90, IN(1.0, 1.08)),                # broke apart
    shot("ara_13", 163.90, 167.50, IN(1.0, 1.08)),                # Aralkum desert
    shot("ara_07", 167.50, 171.30, IN(1.0, 1.08)),                # salt and chemicals
    shot("ara_10", 171.30, 176.20, IN(1.0, 1.08)),                # kilometres from any water
    shot("ara_14", 176.20, 181.00, IN(1.0, 1.10)),                # 2005 dam
    shot("ara_17", 181.00, 184.20, IN(1.0, 1.08)),
    shot("ara_n2", 184.20, 187.50, IN(1.0, 1.08)),                # water rose, fish came back
    shot("ara_04", 187.50, 191.30, OUT(1.12, 1.0)),               # the rest is gone
], badge="90% OF THE WATER GONE")

# ---------------- 04_dead_sea ----------------
place("#7", "DEAD SEA", "MIDDLE EAST", "frames_dead_sea", 191.3, 194.425, 197.925, 249.25, [
    shot("dea_12", 197.925, 203.40, IN(1.0, 1.10)),               # lowest point on dry land
    shot("dea_01", 203.40, 208.70, IN(1.0, 1.08)),                # so salty you float
    shot("dea_n3", 208.70, 214.00, IN(1.0, 1.10)),                # shrinking
    shot("dea_15", 214.00, 218.60, IN(1.0, 1.08)),                # the Jordan River's water
    shot("dea_03", 218.60, 221.90, IN(1.0, 1.08)),                # more than a metre a year
    shot("dea_n2", 221.90, 228.30, IN(1.0, 1.08)),                # lost a third of its surface
    shot("dea_07", 228.30, 232.00, PAN(0.35, 0.65, 1.12)),        # something dangerous
    shot("dea_13", 232.00, 237.70, IN(1.0, 1.08)),                # fresh water dissolves the salt
    shot("dea_02", 237.70, 242.10, IN(1.0, 1.10)),                # 100 sinkholes in 1990
    shot("dea_04", 242.10, 245.00, IN(1.0, 1.08)),                # more than 6,000
    shot("dea_08", 245.00, 250.05, OUT(1.12, 1.0)),               # beaches abandoned
], badge="6,000+ SINKHOLES")

# ---------------- 05_venice ----------------
place("#6", "VENICE", "ITALY", "frames_venice", 250.05, 253.175, 256.675, 309.175, [
    shot("ven_12", 256.675, 261.00, IN(1.0, 1.08)),               # piles in a lagoon
    shot("ven_04", 261.00, 265.00, PAN(0.35, 0.65, 1.12)),        # slowly sinking
    shot("ven_05", 265.00, 270.00, IN(1.0, 1.10)),                # floods are part of life
    shot("ven_01", 270.00, 273.80, TILT(0.3, 0.6, 1.1)),          # November 2019
    shot("ven_17", 273.80, 279.60, IN(1.0, 1.08)),                # St Mark's Basilica
    shot("ven_06", 279.60, 284.50, IN(1.0, 1.08)),                # MOSE gates
    shot("ven_14", 284.50, 289.40, IN(1.0, 1.08)),
    shot("ven_18", 289.40, 293.20, IN(1.0, 1.08)),                # another flood: people
    shot("ven_16", 293.20, 298.50, IN(1.0, 1.08)),                # entry fee
    shot("ven_n1", 298.50, 302.50, IN(1.0, 1.08)),                # 60 days in 2026
    shot("ven_n2", 302.50, 306.00, IN(1.0, 1.08)),
    shot("ven_11", 306.00, 309.975, OUT(1.12, 1.0)),              # visitors outnumber residents
], badge="78 FLOOD GATES")

# ---------------- 06_great_barrier_reef ----------------
place("#5", "GREAT BARRIER REEF", "AUSTRALIA", "frames_great_barrier_reef", 309.975, 313.10, 316.60, 371.775, [
    shot("gbr_06", 316.60, 322.40, IN(1.0, 1.10)),                # largest living structure
    shot("gbr_n2", 322.40, 325.30, IN(1.0, 1.08)),                # visible from space
    shot("gbr_05", 325.30, 330.00, IN(1.0, 1.10)),                # coral is fragile
    shot("gbr_08", 330.00, 334.70, IN(1.0, 1.08)),                # push out the algae, turn white
    shot("gbr_03", 334.70, 339.00, IN(1.0, 1.08)),                # bleaching
    shot("gbr_13", 339.00, 344.00, IN(1.0, 1.08)),                # 1998 ... 2025
    shot("gbr_02", 344.00, 349.70, IN(1.0, 1.08)),
    shot("gbr_17", 349.70, 354.50, IN(1.0, 1.08)),                # biggest one-year loss
    shot("gbr_n3", 354.50, 359.50, IN(1.0, 1.08)),
    shot("gbr_15", 359.50, 362.70, IN(1.0, 1.08)),                # first signs of recovery
    shot("gbr_09", 362.70, 367.50, IN(1.0, 1.10)),                # reefs can bounce back
    shot("gbr_11", 367.50, 372.575, OUT(1.12, 1.0)),              # calm years getting shorter
], badge="8 MASS BLEACHINGS")

# ---------------- 07_isle_de_jean_charles ----------------
place("#4", "ISLE DE JEAN CHARLES", "USA", "frames_isle_de_jean_charles", 372.575, 375.70, 379.20, 435.75, [
    shot("ijc_30", 379.20, 385.00, IN(1.0, 1.10)),                # Louisiana bayou
    shot("ijc_03", 385.00, 389.00, IN(1.0, 1.08)),                # families who fished and farmed
    shot("ijc_07", 389.00, 392.40, IN(1.0, 1.08)),
    shot("ijc_12", 392.40, 397.70, IN(1.0, 1.10)),                # lost 98 % of its land
    shot("ijc_08", 397.70, 402.00, IN(1.0, 1.08)),                # canals, sinking ground
    shot("ijc_28", 402.00, 404.80, IN(1.0, 1.08)),
    shot("ijc_29", 404.80, 410.80, TILT(0.4, 0.6, 1.1)),          # thin strip, single road
    shot("ijc_09", 410.80, 415.00, IN(1.0, 1.08)),                # 2016: 48 million dollars
    shot("ijc_24", 415.00, 420.00, IN(1.0, 1.08)),
    shot("ijc_26", 420.00, 425.40, IN(1.0, 1.08)),                # first federal relocation
    shot("ijc_11", 425.40, 432.20, IN(1.0, 1.08)),                # families moved north
    shot("ijc_23", 432.20, 436.55, OUT(1.12, 1.0)),               # slipping into the Gulf
], badge="98% OF THE LAND GONE")

# ---------------- 08_jakarta ----------------
place("#3", "JAKARTA", "INDONESIA", "frames_jakarta", 436.55, 439.675, 443.175, 492.025, [
    shot("jak_04", 443.175, 446.20, IN(1.0, 1.08)),               # one of the biggest cities
    shot("jak_16", 446.20, 450.00, IN(1.0, 1.08)),                # pumping groundwater
    shot("jak_08", 450.00, 453.60, IN(1.0, 1.08)),
    shot("jak_n2", 453.60, 458.00, IN(1.0, 1.08)),                # 3.5 cm a year
    shot("jak_01", 458.00, 463.10, IN(1.0, 1.08)),                # northern districts
    shot("jak_10", 463.10, 469.00, IN(1.0, 1.08)),                # dropped by up to 4 m
    shot("jak_06", 469.00, 473.00, IN(1.0, 1.08)),                # below sea level, walls
    shot("jak_02", 473.00, 477.20, IN(1.0, 1.08)),
    shot("jak_20", 477.20, 481.00, IN(1.0, 1.08)),                # a new capital
    M("frames_jakarta", 481.00, 485.00),                          # Nusantara, Borneo
    shot("jak_14", 485.00, 489.00, IN(1.0, 1.08)),                # flood at every high tide
    shot("jak_18", 489.00, 492.825, OUT(1.1, 1.0)),
], badge="4 M LOWER")

# ---------------- 09_blatten ----------------
place("#2", "BLATTEN", "SWITZERLAND", "frames_blatten", 492.825, 495.95, 499.45, 550.4, [
    shot("bla_05", 499.45, 503.00, IN(1.0, 1.08)),                # a small quiet village
    shot("bla_10", 503.00, 506.00, IN(1.0, 1.08)),                # wooden houses, a church
    shot("bla_03", 506.00, 510.50, IN(1.0, 1.08)),                # the mountain began to crack
    shot("bla_02", 510.50, 514.80, IN(1.0, 1.10)),                # Birch Glacier
    shot("bla_11", 514.80, 517.30, IN(1.0, 1.08)),                # glacier sped up
    shot("bla_01", 517.30, 521.10, IN(1.0, 1.08)),                # evacuated on May 19
    shot("bla_09", 521.10, 525.50, IN(1.0, 1.08)),                # cows and sheep flown out
    shot("bla_04", 525.50, 531.00, IN(1.0, 1.10)),                # May 28: glacier collapsed (NASA)
    shot("bla_06", 531.00, 534.50, IN(1.0, 1.08)),                # buried most of Blatten
    shot("bla_08", 534.50, 538.00, PAN(0.35, 0.65, 1.12)),
    shot("bla_13", 538.00, 542.30, IN(1.0, 1.08)),                # almost everyone was safe
    shot("bla_15", 542.30, 546.50, IN(1.0, 1.08)),                # other alpine villages
    shot("bla_16", 546.50, 551.20, OUT(1.12, 1.0)),
], badge="300 PEOPLE EVACUATED")

# ---------------- 10_tuvalu ----------------
place("#1", "TUVALU", "PACIFIC OCEAN", "frames_tuvalu", 551.2, 554.325, 557.825, 615.15, [
    shot("tuv_26", 557.825, 563.80, IN(1.0, 1.10)),               # nine islands of coral and sand
    shot("tuv_01", 563.80, 567.00, IN(1.0, 1.08)),                # two or three metres above the sea
    shot("tuv_06", 567.00, 570.10, IN(1.0, 1.08)),
    shot("tuv_20", 570.10, 575.00, IN(1.0, 1.08)),                # high tides flood homes
    shot("tuv_22", 575.00, 579.00, IN(1.0, 1.08)),
    shot("tuv_11", 579.00, 583.00, IN(1.0, 1.10)),                # Funafuti under water
    M("frames_tuvalu", 583.00, 586.30),                           # treaty with Australia
    shot("tuv_02", 586.30, 590.00, IN(1.0, 1.08)),
    shot("tuv_17", 590.00, 595.90, IN(1.0, 1.08)),                # 280 visas a year
    shot("tuv_07", 595.90, 599.50, IN(1.0, 1.08)),                # half the country entered
    shot("tuv_05", 599.50, 603.30, IN(1.0, 1.08)),
    shot("tuv_24", 603.30, 606.80, IN(1.0, 1.08)),                # building new land
    shot("tuv_n2", 606.80, 611.00, IN(1.0, 1.08)),
    shot("tuv_14", 611.00, 615.95, OUT(1.12, 1.0)),               # stay a nation
], badge="280 VISAS A YEAR")

# ---------------- 11_outro ----------------
shots.append(shot("ven_15", 615.95, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 616.45, "t1": DURATION, "fin": 1.2, "fout": 0.6})
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
