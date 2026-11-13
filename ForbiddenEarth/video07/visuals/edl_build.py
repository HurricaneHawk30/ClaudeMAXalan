"""Edit decision list for video07 "Towns Abandoned Almost Overnight" (11:41.8).
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 13 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 701.8

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

# ---------------- 00_hook (0:00-0:31.8) ----------------
shots += [
    shot("tyn_01",   0.00,  2.70, IN(1.0, 1.08), 0.3, xin=0),     # most towns die slowly
    shot("ken_13",   2.70,  7.70, IN(1.0, 1.10), 0.3),            # grass grows back over decades
    shot("has_04",   7.70, 10.20, IN(1.0, 1.10), 0.3),            # some died almost overnight
    shot("hal_02",  10.20, 12.00, IN(1.0, 1.08), 0.25),           # a storm
    shot("epe_13",  12.00, 13.20, IN(1.0, 1.08), 0.25),           # a flood
    shot("chn_14",  13.20, 14.40, IN(1.0, 1.08), 0.25),           # a volcano
    shot("tyn_09",  14.40, 15.50, IN(1.0, 1.08), 0.25),           # an order from the army
    shot("pri_02",  15.50, 17.80, IN(1.0, 1.08), 0.25),           # an invisible poison
    shot("pri_19",  17.80, 21.50, IN(1.0, 1.10), 0.3),            # plates left on tables
    shot("pri_11",  21.50, 24.50, IN(1.0, 1.10), 0.3),            # ten towns abandoned overnight
    shot("pri_10",  24.50, 32.575, IN(1.0, 1.08), 0.3, xout=0.5), # back in three days
]
overlays.append({"type": "brand", "t0": 28.40, "t1": 32.30, "fin": 0.9, "fout": 0.5})

# ---------------- 01_kennecott ----------------
place("#10", "KENNECOTT", "ALASKA, USA", "frames_kennecott", 32.575, 35.70, 39.20, 92.325, [
    shot("ken_07", 39.20, 46.20, PAN(0.35, 0.65, 1.1)),            # Wrangell-St. Elias, red buildings
    shot("ken_04", 46.20, 52.80, TILT(0.3, 0.6, 1.05)),            # one of the richest copper deposits
    inset("ken_14", 52.80, 60.70, max_up=1.0),                     # a railway nearly 200 miles long
    shot("ken_02", 60.70, 64.30, IN(1.0, 1.10)),                   # a busy company town, 1911
    shot("ken_09", 64.30, 67.10, IN(1.0, 1.08)),                   # hospital, school, store
    shot("ken_01", 67.10, 70.10, IN(1.0, 1.10)),                   # a giant mill on the mountain
    shot("ken_05", 70.10, 73.60, IN(1.0, 1.10)),                   # by 1938 the ore was gone
    shot("ken_15", 73.60, 78.20, IN(1.0, 1.10)),                   # the last train left
    shot("ken_12", 78.20, 81.20, PAN(0.4, 0.6, 1.1)),              # simply left behind
    shot("ken_03", 81.20, 85.20, IN(1.0, 1.10)),                   # empty in the cold
    shot("ken_06", 85.20, 88.60, IN(1.0, 1.08)),                   # the National Park Service
    shot("ken_16", 88.60, 93.125, OUT(1.1, 1.0)),                  # still painted red
], badge="ABANDONED 1938")

# ---------------- 02_pyramiden ----------------
place("#9", "PYRAMIDEN", "SVALBARD, NORWAY", "frames_pyramiden", 93.125, 96.25, 99.75, 159.175, [
    shot("pyr_01", 99.75, 105.50, IN(1.0, 1.10)),                  # a Soviet town on Svalbard
    shot("pyr_15", 105.50, 112.40, PAN(0.4, 0.6, 1.1)),            # founded by Sweden, sold 1927
    shot("pyr_02", 112.40, 116.30, IN(1.0, 1.10)),                 # a model mining settlement
    shot("pyr_16", 116.30, 120.30, IN(1.0, 1.08)),                 # cultural centre, pool
    shot("pyr_05", 120.30, 123.20, TILT(0.3, 0.45, 1.0)),          # Lenin
    shot("pyr_03", 123.20, 126.80, IN(1.0, 1.10)),                 # staring across the square
    shot("pyr_13", 126.80, 131.20, IN(1.0, 1.08)),                 # the coal mine, 1998
    shot("pyr_10", 131.20, 134.60, IN(1.0, 1.10)),                 # last coal, March 31st
    shot("pyr_12", 134.60, 137.90, PAN(0.4, 0.6, 1.1)),            # last resident gone
    shot("pyr_08", 137.90, 142.30, IN(1.0, 1.12)),                 # pictures left behind
    shot("pyr_07", 142.30, 147.00, IN(1.0, 1.10)),                 # preserved by the cold
    shot("pyr_11", 147.00, 150.40, IN(1.0, 1.10)),                 # completely empty
    shot("pyr_14", 150.40, 154.00, IN(1.0, 1.08)),                 # a handful of workers
    shot("pyr_09", 154.00, 159.975, OUT(1.1, 1.0)),                # frozen in 1998
], badge="EMPTY SINCE 1998")

# ---------------- 03_hashima ----------------
place("#8", "HASHIMA ISLAND", "NAGASAKI, JAPAN", "frames_hashima", 159.975, 163.10, 166.60, 227.425, [
    shot("has_01", 166.60, 169.70, IN(1.0, 1.10)),                 # looks like a warship
    shot("has_09", 169.70, 175.00, PAN(0.35, 0.65, 1.1)),          # apartment blocks, sea wall
    shot("has_10", 175.00, 179.60, IN(1.0, 1.10)),                 # Battleship Island
    inset("has_18", 179.60, 183.60, max_up=1.4),                   # an undersea coal mine
    inset("has_17", 183.60, 189.30, max_up=1.0),                   # 1959: 5,000 people (old postcard)
    shot("has_11", 189.30, 194.70, IN(1.0, 1.10)),                 # most densely populated
    shot("has_07", 194.70, 205.70, IN(1.0, 1.06)),                 # a dark side to its history
    shot("has_13", 205.70, 211.90, IN(1.0, 1.10)),                 # January 1974, mine closed
    shot("has_05", 211.90, 214.70, IN(1.0, 1.08)),                 # every resident had left
    shot("has_06", 214.70, 219.20, PAN(0.4, 0.6, 1.1)),            # sealed and empty
    shot("has_12", 219.20, 223.00, IN(1.0, 1.10)),                 # tourists back in 2009
    shot("has_02", 223.00, 228.225, OUT(1.1, 1.0)),                # UNESCO, 2015
], badge="LEFT IN 1974")

# ---------------- 04_hallsands ----------------
place("#7", "HALLSANDS", "DEVON, ENGLAND", "frames_hallsands", 228.225, 231.35, 234.85, 289.825, [
    shot("hal_01", 234.85, 238.80, IN(1.0, 1.10)),                 # a village on a rock ledge
    shot("hal_14", 238.80, 245.20, PAN(0.35, 0.65, 1.1)),          # a bank of shingle
    shot("hal_15", 245.20, 252.00, IN(1.0, 1.10)),                 # Devonport dockyard
    inset("hal_12", 252.00, 256.10, max_up=1.0),                   # dredging the bay (chart)
    shot("hal_06", 256.10, 259.90, IN(1.0, 1.08)),                 # the beach began to drop
    shot("hal_13", 259.90, 264.40, IN(1.0, 1.08)),                 # January 26th, 1917
    shot("hal_02", 264.40, 272.00, TILT(0.3, 0.6, 1.08)),          # waves smashed through walls
    shot("hal_03", 272.00, 278.60, IN(1.0, 1.10)),                 # the village was destroyed
    shot("hal_04", 278.60, 280.90, IN(1.0, 1.08)),                 # never rebuilt
    shot("hal_09", 280.90, 285.70, IN(1.0, 1.08)),                 # a viewing platform
    shot("hal_10", 285.70, 290.625, OUT(1.1, 1.0)),                # the sea that took them
], badge="ONE NIGHT · 1917")

# ---------------- 05_tyneham ----------------
place("#6", "TYNEHAM", "DORSET, ENGLAND", "frames_tyneham", 290.625, 293.75, 297.25, 350.05, [
    shot("tyn_14", 297.25, 300.40, IN(1.0, 1.08)),                 # a quiet valley
    shot("tyn_03", 300.40, 302.80, IN(1.0, 1.08)),                 # a church, a school
    shot("tyn_10", 302.80, 309.10, PAN(0.4, 0.6, 1.1)),            # the army needed land, 1943
    shot("tyn_01", 309.10, 315.30, IN(1.0, 1.10)),                 # 225 people told to leave
    shot("tyn_04", 315.30, 324.20, IN(1.0, 1.10)),                 # a note on the church door
    shot("tyn_07", 324.20, 328.60, IN(1.0, 1.08)),                 # they never did
    shot("tyn_12", 328.60, 334.10, IN(1.0, 1.08)),                 # bought for good, 1948
    shot("tyn_09", 334.10, 337.80, IN(1.0, 1.08)),                 # a military firing range
    shot("tyn_13", 337.80, 342.20, IN(1.0, 1.08)),                 # roofless shells
    shot("tyn_06", 342.20, 345.80, IN(1.0, 1.10)),                 # the school preserved
    shot("tyn_11", 345.80, 350.85, OUT(1.1, 1.0)),                 # time stopped in 1943
], badge="LEFT IN 1943")

# ---------------- 06_chaiten ----------------
place("#5", "CHAITÉN", "LOS LAGOS, CHILE", "frames_chaiten", 350.85, 353.975, 357.475, 410.925, [
    shot("chn_09", 357.475, 362.60, IN(1.0, 1.08)),                # a small port town
    shot("chn_02", 362.60, 367.70, IN(1.0, 1.10)),                 # May 2nd, 2008
    shot("chn_10", 367.70, 370.50, IN(1.0, 1.10)),                 # ash poured out of the sky
    shot("cha_n_3", 370.50, 378.10, IN(1.0, 1.10)),                # evacuated, mostly by sea (ISS)
    shot("chn_03", 378.10, 380.50, IN(1.0, 1.08)),                 # the second disaster
    shot("chn_11", 380.50, 386.70, IN(1.0, 1.10)),                 # ash washed down
    shot("chn_05", 386.70, 392.50, IN(1.0, 1.12)),                 # the river through town
    shot("chn_08", 392.50, 396.80, IN(1.0, 1.10)),                 # buried in grey mud
    shot("chn_04", 396.80, 402.40, IN(1.0, 1.08)),                 # finished?
    shot("chn_06", 402.40, 408.30, IN(1.0, 1.08)),                 # they came back
    shot("chn_14", 408.30, 411.725, OUT(1.1, 1.0)),                # a volcano still watched
], badge="EVACUATED 2008")

# ---------------- 07_times_beach ----------------
place("#4", "TIMES BEACH", "MISSOURI, USA", "frames_times_beach", 411.725, 414.85, 418.35, 480.50, [
    shot("tim_04", 418.35, 422.70, IN(1.0, 1.08)),            # by the Meramec River
    shot("tim_06", 422.70, 431.20, IN(1.0, 1.10)),                 # dirt roads sprayed with oil
    shot("tim_05", 431.20, 439.10, IN(1.12, 1.2, (0.6,0.5))),       # dioxin
    shot("tim_13", 439.10, 445.70, IN(1.0, 1.08)),                 # the river flooded (Meramec flood, 2008)
    shot("tim_01", 445.70, 455.90, IN(1.0, 1.08)),                 # EPA: the whole town bought out
    shot("tim_11", 455.90, 458.80, IN(1.0, 1.08)),                 # $30 million
    shot("tim_02", 458.80, 464.90, IN(1.0, 1.08)),                 # 1985: stopped existing
    shot("tim_08", 464.90, 470.20, IN(1.12, 1.2)),                  # demolished and buried
    shot("tim_07", 470.20, 474.60, IN(1.0, 1.08)),                 # Route 66 State Park
    shot("tim_09", 474.60, 481.30, OUT(1.1, 1.0)),                 # walk and cycle; nothing shows a town
], badge="GONE 1985")

# ---------------- 08_epecuen ----------------
place("#3", "VILLA EPECUÉN", "BUENOS AIRES, ARGENTINA", "frames_epecuen", 481.30, 484.425, 487.925, 549.425, [
    shot("epe_16", 487.925, 492.70, IN(1.0, 1.08)),                # a very salty lake
    shot("epe_10", 492.70, 499.80, IN(1.0, 1.12)),                 # tourists every summer
    shot("epe_15", 499.80, 505.80, IN(1.0, 1.10)),                 # hotels, shops, restaurants
    shot("epe_04", 505.80, 513.50, IN(1.0, 1.10)),                 # November 1985, the dam broke
    shot("epe_13", 513.50, 520.50, IN(1.0, 1.08)),                 # the water kept rising
    shot("epe_03", 520.50, 526.70, PAN(0.4, 0.6, 1.1)),            # ten metres of salt water
    shot("epe_12", 526.70, 534.40, IN(1.0, 1.08)),                 # underwater for 20 years
    shot("epe_02", 534.40, 537.40, IN(1.0, 1.08)),                 # a grey, ghostly town
    shot("epe_14", 537.40, 540.10, IN(1.0, 1.08)),                 # dead trees bleached white
    shot("epe_08", 540.10, 543.70, IN(1.0, 1.10)),                 # broken walls
    shot("epe_05", 543.70, 550.225, OUT(1.1, 1.0)),                # one man among the ruins
], badge="FLOODED 1985")

# ---------------- 09_futaba ----------------
place("#2", "FUTABA", "FUKUSHIMA, JAPAN", "frames_futaba", 550.225, 553.35, 556.85, 611.625, [
    shot("fut_12", 556.85, 565.20, IN(1.0, 1.10)),                 # Fukushima Daiichi meltdown
    shot("fut_13", 565.20, 568.20, IN(1.0, 1.08)),                 # part of the plant in Futaba
    inset("fut_17", 568.20, 573.40, max_up=1.0),                   # 7,000 residents told to leave (station, 2010)
    shot("fut_06", 573.40, 576.30, IN(1.0, 1.08)),                 # gone for a few days
    shot("fut_09", 576.30, 579.80, IN(1.0, 1.08)),                 # frozen for years
    shot("fut_03", 579.80, 583.20, IN(1.0, 1.08)),                 # shop shelves, bicycles
    shot("fut_01", 583.20, 592.30, IN(1.0, 1.25, (0.5, 0.5), (0.47, 0.52))), # the slogan sign
    shot("fut_15", 592.30, 595.30, IN(1.0, 1.08)),                 # it was taken down
    shot("fut_07", 595.30, 600.40, IN(1.0, 1.08)),                 # eleven years
    shot("fut_02", 600.40, 606.30, IN(1.0, 1.08)),                 # 2022, evacuation lifted
    shot("fut_10", 606.30, 612.425, OUT(1.1, 1.0)),                # only a few came back
], badge="EVACUATED 2011")

# ---------------- 10_pripyat ----------------
place("#1", "PRIPYAT", "KYIV OBLAST, UKRAINE", "frames_pripyat", 612.425, 615.55, 619.05, 680.95, [
    shot("pri_01", 619.05, 625.20, IN(1.0, 1.10)),                 # a model Soviet city, 1970
    shot("pri_04", 625.20, 627.40, IN(1.0, 1.08)),                 # young and modern
    shot("pri_05", 627.40, 634.10, PAN(0.4, 0.6, 1.1)),            # 50,000 people
    shot("pri_06", 634.10, 638.40, IN(1.0, 1.10)),                 # schools, cinema, pool
    shot("pri_17", 638.40, 644.90, IN(1.0, 1.10)),                 # reactor number four exploded
    shot("pri_03", 644.90, 648.40, IN(1.0, 1.08)),                 # life went on as normal
    shot("pri_n_1", 648.40, 655.10, IN(1.0, 1.10)),                # April 27th, buses (from space)
    shot("pri_18", 655.10, 660.90, IN(1.0, 1.10)),                 # back in three days
    shot("pri_15", 660.90, 665.70, IN(1.0, 1.10)),                 # empty in three and a half hours
    shot("pri_14", 665.70, 668.40, IN(1.0, 1.08)),                 # nobody came back
    shot("pri_09", 668.40, 671.90, IN(1.0, 1.10)),                 # a yellow Ferris wheel
    shot("pri_16", 671.90, 675.70, IN(1.0, 1.08)),                 # supposed to open on May 1st
    shot("pri_08", 675.70, 681.75, OUT(1.1, 1.0)),                 # waiting for a crowd
], badge="EMPTIED IN 3.5 HOURS")

# ---------------- 11_outro ----------------
shots.append(shot("epe_11", 681.75, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 682.3, "t1": DURATION, "fin": 1.2, "fout": 0.6})

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
