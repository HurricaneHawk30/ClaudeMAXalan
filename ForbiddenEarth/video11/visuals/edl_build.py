"""Edit decision list for video11 "10 Places Sealed Shut" (12:20.6).
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 17 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 740.6

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

# ---------------- 00_hook (0:00-0:30.475) ----------------
shots += [
    shot("see_10",   0.00,  3.60, IN(1.0, 1.08), 0.3, xin=0),     # doors never meant to be opened
    shot("onk_04",   3.60,  7.50, IN(1.0, 1.10), 0.25),           # a room that won't be unlocked
    shot("cha_15",   7.50, 12.10, IN(1.0, 1.10), 0.25),           # a cave sealed off for millions of years
    shot("run_01",  12.10, 17.40, IN(1.0, 1.12), 0.25),           # a concrete dome in the Pacific
    shot("pap_04",  17.40, 22.00, IN(1.0, 1.10), 0.25),           # sealed by people, by nature
    shot("pyr_13",  22.00, 30.475, IN(1.0, 1.12), 0.3, xout=0.5), # the Great Pyramid
]
overlays.append({"type": "brand", "t0": 26.60, "t1": 30.20, "fin": 0.9, "fout": 0.5})

# ---------------- 01_crypt ----------------
place("#10", "CRYPT OF CIVILIZATION", "ATLANTA, GEORGIA, USA", "frames_crypt", 30.475, 33.60, 37.10, 105.50, [
    shot("cry_03", 37.10, 44.10, TILT(0.3, 0.6, 1.1)),             # a university building in Atlanta
    shot("cry_01", 44.10, 54.50, IN(1.0, 1.15)),                   # a room that used to be a pool (1940 photo)
    shot("cry_06", 54.50, 64.00, PAN(0.35, 0.65, 1.12)),           # 1936, Thornwell Jacobs (campus plan)
    shot("pyr_09", 64.00, 72.20, IN(1.0, 1.12)),                   # the ancient Egyptian calendar, 8113
    shot("cry_05", 72.20, 86.80, IN(1.0, 1.15)),                   # filled the room (Lupton Hall, 1940s postcard)
    shot("cry_04", 86.80, 93.50, IN(1.0, 1.10)),                   # steel containers with nitrogen
    shot("cry_10", 93.50, 102.70, TILT(0.3, 0.6, 1.05)),           # May 28, 1940, sealed
    shot("cry_08", 102.70, 106.30, OUT(1.1, 1.0)),                 # nobody goes in
], badge="OPEN IN 8113")

# ---------------- 02_hall_of_records ----------------
place("#9", "HALL OF RECORDS", "MOUNT RUSHMORE, SOUTH DAKOTA", "frames_hall_of_records", 106.30, 109.425, 112.925, 176.90, [
    shot("hal_03", 112.925, 119.30, PAN(0.3, 0.7, 1.12)),          # behind the faces of Mount Rushmore
    shot("hal_01", 119.30, 124.70, TILT(0.3, 0.6, 1.0)),           # a great Hall of Records
    shot("hal_06", 124.70, 133.00, IN(1.0, 1.10)),                 # who these presidents were
    shot("hal_05", 133.00, 138.40, IN(1.0, 1.10)),                 # late 1930s, blasted a tunnel
    shot("hal_07", 138.40, 145.30, IN(1.0, 1.10)),                 # the work stopped
    shot("hal_02", 145.30, 153.80, TILT(0.25, 0.7, 1.0)),          # 1998, finished
    shot("hal_11", 153.80, 160.50, IN(1.0, 1.10)),                 # sixteen panels
    shot("hal_09", 160.50, 164.40, IN(1.0, 1.08)),                 # a teakwood box
    shot("hal_12", 164.40, 171.60, IN(1.0, 1.10)),                 # a titanium vault, a granite slab
    shot("hal_08", 171.60, 174.10, IN(1.0, 1.08)),                 # closed to the public
    shot("hal_13", 174.10, 177.70, OUT(1.1, 1.0)),                 # thousands of years
], badge="SEALED FOR THOUSANDS OF YEARS")

# ---------------- 03_seed_vault ----------------
place("#8", "SEED VAULT", "SVALBARD, NORWAY", "frames_seed_vault", 177.70, 180.825, 184.325, 248.90, [
    shot("see_06", 184.325, 188.20, IN(1.0, 1.08)),                # a frozen island
    shot("see_04", 188.20, 192.00, IN(1.0, 1.10)),                 # a concrete wedge
    shot("see_05", 192.00, 200.90, IN(1.0, 1.12)),                 # a tunnel deep into the rock, -18 C
    shot("see_07", 200.90, 206.60, TILT(0.6, 0.35, 1.0)),          # a million seed samples
    shot("see_09", 206.60, 213.30, IN(1.0, 1.10)),                 # wheat, rice, barley
    shot("see_02", 213.30, 220.20, IN(1.0, 1.10)),                 # a backup
    shot("see_08", 220.20, 223.40, IN(1.0, 1.08)),                 # opens a few times a year
    shot("see_03", 223.40, 227.20, IN(1.0, 1.08)),                 # the war in Syria
    shot("see_11", 227.20, 235.60, IN(1.0, 1.12)),                 # backup seeds out of Svalbard
    shot("see_14", 235.60, 240.30, IN(1.0, 1.08)),                 # 2017, a scare
    shot("see_12", 240.30, 246.10, TILT(0.3, 0.6, 1.0)),           # permafrost melted
    shot("see_01", 246.10, 249.70, OUT(1.1, 1.0)),                 # frozen and safe
], badge="−18°C")

# ---------------- 04_movile ----------------
place("#7", "MOVILE CAVE", "MANGALIA, ROMANIA", "frames_movile", 249.70, 252.825, 256.325, 315.65, [
    shot("mov_03", 256.325, 263.60, PAN(0.35, 0.65, 1.12)),        # drilling near the Black Sea coast
    shot("mov_06", 263.60, 271.20, IN(1.0, 1.10)),                 # broke into a cave (cross-section)
    shot("mov_05", 271.20, 279.70, IN(1.0, 1.12)),                 # sealed 5.5 million years, no sunlight
    shot("mov_02", 279.70, 292.80, PAN(0.3, 0.7, 1.15)),           # poisonous air (schematic)
    shot("mov_01", 292.80, 301.90, TILT(0.2, 0.8, 1.0)),           # spiders, water scorpions, leeches
    shot("mov_04", 301.90, 307.60, IN(1.0, 1.12)),                 # live nowhere else (centipede)
    shot("mov_08", 307.60, 312.20, IN(1.0, 1.08)),                 # bacteria
    shot("mov_07", 312.20, 316.45, OUT(1.1, 1.0)),                 # fewer than a hundred people
], badge="5.5 MILLION YEARS ALONE")

# ---------------- 05_chauvet ----------------
place("#6", "CHAUVET CAVE", "ARDÈCHE, FRANCE", "frames_chauvet", 316.45, 319.575, 323.075, 374.875, [
    shot("cha_07", 323.075, 326.80, PAN(0.35, 0.65, 1.1)),         # cliffs above the Ardèche
    shot("cha_09", 326.80, 330.60, IN(1.0, 1.10)),                 # a small gap in a cliff (cave entrance)
    shot("cha_04", 330.60, 335.80, IN(1.0, 1.12)),                 # horses
    shot("cha_02", 335.80, 340.70, IN(1.0, 1.12)),                 # lions, rhinos, mammoths
    shot("cha_06", 340.70, 348.10, PAN(0.3, 0.7, 1.1)),            # 36,000 years old
    shot("cha_05", 348.10, 352.10, IN(1.0, 1.10)),                 # perfect condition
    shot("cha_13", 352.10, 357.30, IN(1.0, 1.08)),                 # a rockfall sealed the entrance
    shot("cha_11", 357.30, 360.40, IN(1.0, 1.08)),                 # nobody inside since
    shot("cha_01", 360.40, 363.00, IN(1.0, 1.08)),                 # France closed the cave
    shot("cha_14", 363.00, 367.70, IN(1.0, 1.10)),                 # human breath can damage paintings
    shot("cha_10", 367.70, 371.80, IN(1.0, 1.08)),                 # a few researchers
    shot("cha_12", 371.80, 375.675, OUT(1.1, 1.0)),                # a full-size copy
], badge="36,000 YEARS OLD")

# ---------------- 06_runit ----------------
place("#5", "RUNIT DOME", "ENEWETAK ATOLL, MARSHALL ISLANDS", "frames_runit", 375.675, 378.80, 382.30, 445.35, [
    shot("run_02", 382.30, 388.60, IN(1.0, 1.20)),                 # a narrow island in the Pacific
    shot("run_01", 388.60, 399.40, TILT(0.6, 0.35, 1.0)),          # the Tomb
    shot("run_04", 399.40, 404.10, IN(1.0, 1.08)),                 # 1958 test (Hardtack, one wide archival shot)
    shot("run_07", 404.10, 412.50, IN(1.0, 1.12)),                 # crews scraped up contaminated soil (1948 aerial)
    shot("run_05", 412.50, 422.40, PAN(0.3, 0.7, 1.1)),            # covered with a concrete cap
    shot("run_03", 422.40, 430.00, IN(1.0, 1.15)),                 # seawater moves underneath
    shot("run_06", 430.00, 446.15, OUT(1.18, 1.0)),                # 2019 warning; a rising sea
], badge="THE TOMB")

# ---------------- 07_vostok ----------------
place("#4", "LAKE VOSTOK", "ANTARCTICA", "frames_vostok", 446.15, 449.275, 452.775, 515.575, [
    shot("vos_11", 452.775, 459.30, IN(1.0, 1.12)),                # almost 4 km down
    shot("vos_01", 459.30, 465.00, IN(1.0, 1.12)),                 # sealed 15 million years (radar)
    shot("vos_10", 465.00, 468.90, IN(1.0, 1.08)),                 # total darkness
    shot("vos_02", 468.90, 476.70, IN(1.0, 1.12)),                 # heat from below, thick ice
    shot("vos_07", 476.70, 483.90, IN(1.0, 1.10)),                 # cut off from the rest of life
    shot("vos_04", 483.90, 489.30, IN(1.0, 1.08)),                 # Vostok Station
    shot("vos_12", 489.30, 491.30, IN(1.0, 1.08)),                 # one of the coldest places
    shot("vos_09", 491.30, 501.10, IN(1.0, 1.12)),                 # February 2012, drill touched water
    shot("vos_13", 501.10, 505.50, IN(1.0, 1.10)),                 # the water froze
    shot("vos_05", 505.50, 511.70, IN(1.0, 1.08)),                 # kerosene
    shot("vos_08", 511.70, 516.375, OUT(1.1, 1.0)),                # an open question
], badge="4 KM UNDER THE ICE")

# ---------------- 08_onkalo ----------------
place("#3", "ONKALO", "OLKILUOTO, FINLAND", "frames_onkalo", 516.375, 519.50, 523.00, 582.40, [
    shot("onk_05", 523.00, 528.70, PAN(0.35, 0.65, 1.1)),          # an island off the west coast
    shot("onk_02", 528.70, 536.60, IN(1.0, 1.12)),                 # 430 m underground
    shot("onk_01", 536.60, 541.70, IN(1.0, 1.10)),                 # a permanent tomb
    shot("onk_03", 541.70, 549.70, IN(1.0, 1.12)),                 # copper canisters
    shot("onk_06", 549.70, 556.20, IN(1.0, 1.10)),                 # filled in and sealed
    shot("onk_11", 556.20, 565.70, IN(1.0, 1.12)),                 # 100,000 years
    shot("onk_12", 565.70, 571.90, PAN(0.3, 0.7, 1.0)),            # October 2026 license
    shot("onk_09", 571.90, 575.20, IN(1.0, 1.08)),                 # a strange question
    shot("onk_10", 575.20, 579.40, IN(1.0, 1.08)),                 # how do you warn people
    shot("onk_07", 579.40, 583.20, OUT(1.1, 1.0)),                 # no language will last
], badge="100,000 YEARS")

# ---------------- 09_papyri ----------------
place("#2", "VILLA OF THE PAPYRI", "HERCULANEUM, ITALY", "frames_papyri", 583.20, 586.325, 589.825, 655.975, [
    shot("pap_13", 589.825, 597.20, IN(1.0, 1.10)),                # Vesuvius erupted in 79
    shot("pap_01", 597.20, 605.60, PAN(0.3, 0.7, 1.1)),            # a luxury villa
    shot("pap_09", 605.60, 608.50, IN(1.0, 1.08)),                 # a library
    shot("pap_08", 608.50, 613.60, IN(1.0, 1.10)),                 # 1750s tunnels
    shot("pap_03", 613.60, 619.10, IN(1.0, 1.12)),                 # 1,800 burned scrolls
    shot("pap_11", 619.10, 624.30, IN(1.0, 1.10)),                 # unrolling destroyed them
    shot("pap_06", 624.30, 634.60, TILT(0.3, 0.6, 1.0)),           # 2023, X-ray scans and AI
    shot("pap_02", 634.60, 638.60, IN(1.0, 1.08)),                 # words, a title
    shot("pap_12", 638.60, 646.30, IN(1.0, 1.10)),                 # 2026, an entire scroll
    shot("pap_10", 646.30, 649.90, IN(1.0, 1.08)),                 # most of the villa never dug up
    shot("pap_05", 649.90, 654.50, IN(1.0, 1.08)),                 # more library down there
    shot("pap_07", 654.50, 656.775, OUT(1.1, 1.0)),                # waiting (Getty Villa copy)
], badge="1,800 BURNED SCROLLS")

# ---------------- 10_great_pyramid ----------------
place("#1", "THE GREAT PYRAMID", "GIZA, EGYPT", "frames_great_pyramid", 656.775, 659.90, 663.40, 725.95, [
    shot("pyr_01", 663.40, 670.90, TILT(0.3, 0.6, 1.0)),           # last of the Seven Wonders
    shot("pyr_06", 670.90, 676.80, IN(1.0, 1.08)),                 # every room inside? We don't.
    shot("pyr_05", 676.80, 683.80, IN(1.0, 1.12)),                 # 2017, muons from space
    shot("pyr_10", 683.80, 687.70, IN(1.0, 1.10)),                 # like an X-ray
    shot("pyr_02", 687.70, 695.40, IN(1.0, 1.12)),                 # above the Grand Gallery, the Big Void
    shot("pyr_07", 695.40, 700.00, IN(1.0, 1.08)),                 # nobody inside
    shot("pyr_03", 700.00, 708.70, IN(1.0, 1.12)),                 # 2023, north face corridor
    shot("pyr_11", 708.70, 716.00, IN(1.0, 1.10)),                 # a 6 mm camera
    shot("pyr_08", 716.00, 720.10, TILT(0.6, 0.35, 1.0)),          # sealed
    shot("pyr_12", 720.10, 727.55, OUT(1.1, 1.0)),                 # still keeping its secrets
], badge="NEVER ENTERED")

# ---------------- 11_outro ----------------
shots.append(shot("see_10", 727.55, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 728.1, "t1": DURATION, "fin": 1.2, "fout": 0.6})

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
