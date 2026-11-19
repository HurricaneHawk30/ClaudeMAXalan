"""Edit decision list for video14 "10 Ancient Places Scientists Still Can't Explain" (11:16.8).
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 20 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 676.8

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

PLA_CRATER = "pla_17" if "pla_17" in FILES else "pla_04"

# ---------------- 00_hook (0:00-0:26.775) ----------------
shots += [
    shot("sac_05",  0.00,  2.30, IN(1.0, 1.08), 0.3, xin=0),     # somebody built these places
    shot("naz_06",  2.30,  5.20, IN(1.0, 1.10), 0.25),           # we don't know how or why
    shot("lon_11",  5.20,  9.10, IN(1.0, 1.10), 0.25),           # giant caves carved by hand
    shot("baa_09",  9.10, 13.50, IN(1.0, 1.10), 0.25),           # a block as heavy as four jumbo jets
    shot("sto_10", 13.50, 17.50, IN(1.0, 1.10), 0.25),           # moved across Britain
    shot("gob_12", 17.50, 26.775, IN(1.0, 1.12), 0.3, xout=0.5), # number one: older than farming
]
overlays.append({"type": "brand", "t0": 22.20, "t1": 26.45, "fin": 0.9, "fout": 0.5})

# ---------------- 01_longyou ----------------
place("#10", "LONGYOU CAVES", "CHINA", "frames_longyou", 26.775, 29.90, 33.40, 91.625, [
    shot("lon_08", 33.40, 38.00, IN(1.0, 1.10)),                   # a village in eastern China
    shot("lon_09", 38.00, 43.30, IN(1.0, 1.10)),                   # ponds with no bottom
    shot("lon_14", 43.30, 48.20, IN(1.0, 1.08)),                   # they drained one
    shot("lon_10", 48.20, 51.30, IN(1.0, 1.10)),                   # no bottom of mud
    shot("lon_01", 51.30, 56.50, IN(1.0, 1.12)),                   # a huge hall in sandstone
    shot("lon_02", 56.50, 59.30, IN(1.0, 1.08)),                   # sloping ceilings, pillars
    shot("lon_03", 59.30, 62.20, IN(1.0, 1.08)),                   # drained more ponds
    shot("lon_12", 62.20, 64.00, IN(1.0, 1.06)),                   # 24 caves
    shot("lon_13", 64.00, 67.70, IN(1.0, 1.10)),                   # more than 30 m across
    shot("lon_04", 67.70, 72.00, IN(1.0, 1.12)),                   # parallel chisel marks
    shot("lon_16", 72.00, 76.40, TILT(0.3, 0.6, 1.1)),             # one careful hand
    shot("lon_07", 76.40, 81.50, IN(1.0, 1.10)),                   # more than 2,000 years old
    shot("lon_15", 81.50, 85.00, IN(1.0, 1.08)),                   # China kept records
    shot("lon_05", 85.00, 87.80, IN(1.0, 1.08)),                   # not one mentions them
    shot("lon_06", 87.80, 92.425, OUT(1.12, 1.0)),                 # still unknown
], badge="NO RECORDS")

# ---------------- 02_carnac ----------------
place("#9", "CARNAC STONES", "FRANCE", "frames_carnac", 92.425, 95.55, 99.05, 154.125, [
    shot("car_05", 99.05, 104.60, PAN(0.3, 0.7, 1.15)),            # 3,000 standing stones
    shot("car_09", 104.60, 109.30, IN(1.0, 1.10)),                 # rows over a kilometre
    shot("car_04", 109.30, 112.40, IN(1.0, 1.08)),                 # Neolithic people
    shot("car_17", 112.40, 117.00, IN(1.0, 1.10)),                 # 4800-3500 BC
    shot("car_13", 117.00, 119.40, IN(1.0, 1.08)),                 # before Stonehenge
    shot("car_15", 119.40, 122.10, IN(1.0, 1.10)),                 # taller than a person
    shot("car_03", 122.10, 126.00, IN(1.0, 1.08)),                 # cut from granite
    shot("car_07", 126.00, 129.50, IN(1.0, 1.10)),                 # no metal tools or wheel
    shot("car_02", 129.50, 133.30, IN(1.0, 1.10)),                 # a Roman army turned to stone
    shot("car_14", 133.30, 136.50, PAN(0.35, 0.65, 1.1)),          # other ideas
    shot("car_10", 136.50, 141.40, IN(1.0, 1.10)),                 # calendar, ritual, the dead
    shot("car_11", 141.40, 143.20, IN(1.0, 1.06)),                 # nobody knows
    shot("car_06", 143.20, 150.80, IN(1.0, 1.12)),                 # UNESCO, July 2025
    shot("car_08", 150.80, 154.925, OUT(1.12, 1.0)),               # still open
], badge="3,000+ STONES")

# ---------------- 03_sacsayhuaman ----------------
place("#8", "SACSAYHUAMÁN", "PERU", "frames_sacsayhuaman", 154.925, 158.05, 161.55, 212.575, [
    shot("sac_04", 161.55, 164.50, IN(1.0, 1.08)),                 # above Cusco
    shot("sac_03", 164.50, 167.70, IN(1.0, 1.10)),                 # three zigzag walls
    shot("sac_01", 167.70, 170.60, IN(1.0, 1.10)),                 # more than 100 tons
    shot("sac_09", 170.60, 174.60, TILT(0.6, 0.35, 1.1)),          # 8 m tall
    shot("sac_17", 174.60, 178.80, IN(1.0, 1.10)),                 # not just the size
    shot("sac_13", 178.80, 183.00, IN(1.0, 1.12)),                 # many angles
    shot("sac_02", 183.00, 187.10, IN(1.0, 1.10)),                 # no mortar
    shot("sac_12", 187.10, 193.10, IN(1.0, 1.12)),                 # not even a sheet of paper
    shot("sac_15", 193.10, 197.20, IN(1.0, 1.08)),                 # the Inca, 15th century
    shot("sac_16", 197.20, 200.10, IN(1.0, 1.08)),                 # no wheels, no horses
    shot("sac_07", 200.10, 202.50, IN(1.0, 1.08)),                 # stone hammers
    shot("sac_11", 202.50, 206.10, IN(1.0, 1.08)),                 # ramps, ropes, teams
    shot("sac_08", 206.10, 209.50, IN(1.0, 1.08)),                 # exactly how
    shot("sac_14", 209.50, 213.375, OUT(1.12, 1.0)),               # still debated
], badge="NO MORTAR")

# ---------------- 04_plain_of_jars ----------------
place("#7", "PLAIN OF JARS", "LAOS", "frames_plain_of_jars", 213.375, 216.50, 220.00, 273.725, [
    shot("pla_06", 220.00, 224.50, PAN(0.3, 0.7, 1.15)),           # thousands of jars
    shot("pla_11", 224.50, 226.40, IN(1.0, 1.06)),                 # some stand alone
    shot("pla_01", 226.40, 228.70, IN(1.0, 1.08)),                 # groups of hundreds
    shot("pla_05", 228.70, 234.20, IN(1.0, 1.12)),                 # 3 m tall, up to 20 tons
    shot("pla_07", 234.20, 237.70, IN(1.0, 1.08)),                 # no one could say how old
    shot("pla_08", 237.70, 241.80, IN(1.0, 1.10)),                 # 2021, soil beneath
    shot("pla_15", 241.80, 247.70, IN(1.0, 1.10)),                 # 1240-660 BC
    shot("pla_13", 247.70, 252.90, IN(1.0, 1.10)),                 # to do with the dead
    shot("pla_03", 252.90, 255.50, IN(1.0, 1.08)),                 # how carved
    shot("pla_09", 255.50, 260.50, IN(1.0, 1.10)),                 # what they held
    shot("pla_16", 260.50, 262.50, IN(1.0, 1.06)),                 # another danger
    shot("pla_10", 262.50, 265.90, IN(1.0, 1.08)),                 # Vietnam War, bombed
    shot(PLA_CRATER, 265.90, 270.30, IN(1.0, 1.08)),               # unexploded bombs (crater, general view)
    shot("pla_02", 270.30, 274.525, OUT(1.12, 1.0)),               # cleared paths
], badge="UP TO 20 TONS")

# ---------------- 05_yonaguni ----------------
place("#6", "YONAGUNI MONUMENT", "JAPAN", "frames_yonaguni", 274.525, 277.65, 281.15, 335.10, [
    shot("yon_12", 281.15, 284.70, IN(1.0, 1.08)),                 # 1986, hammerhead sharks
    shot("yon_11", 284.70, 287.20, IN(1.0, 1.10)),                 # westernmost islands
    shot("yon_01", 287.20, 289.50, IN(1.0, 1.08)),                 # something strange
    shot("yon_07", 289.50, 294.20, IN(1.0, 1.12)),                 # terraces, right angles, steps
    shot("yon_05", 294.20, 297.50, IN(1.0, 1.10)),                 # underwater pyramid
    shot("yon_02", 297.50, 301.50, TILT(0.35, 0.65, 1.1)),         # a marine geologist
    shot("yon_10", 301.50, 305.70, IN(1.0, 1.10)),                 # built by people
    shot("yon_14", 305.70, 309.50, IN(1.0, 1.08)),                 # the sea was lower
    shot("yon_09", 309.50, 313.90, IN(1.0, 1.10)),                 # rewrite the history
    shot("yon_08", 313.90, 317.00, IN(1.0, 1.08)),                 # most geologists disagree
    shot("yon_13", 317.00, 321.00, IN(1.0, 1.10)),                 # rock splits along lines
    shot("yon_03", 321.00, 324.40, IN(1.0, 1.08)),                 # waves and earthquakes
    shot("yon_16", 324.40, 328.40, IN(1.0, 1.08)),                 # no tools or pottery
    shot("yon_15", 328.40, 332.80, IN(1.0, 1.10)),                 # lost monument or illusion?
    shot("yon_04", 332.80, 335.90, OUT(1.1, 1.0)),                 # divers still argue
], badge="NATURE OR HUMANS?")

# ---------------- 06_nan_madol ----------------
place("#5", "NAN MADOL", "MICRONESIA", "frames_nan_madol", 335.90, 339.025, 342.525, 399.075, [
    shot("nan_14", 342.525, 345.00, IN(1.0, 1.08)),                # Pohnpei, western Pacific
    shot("nan_15", 345.00, 349.10, IN(1.0, 1.08)),                 # a hundred artificial islands
    shot("nan_12", 349.10, 351.20, IN(1.0, 1.08)),                 # canals
    shot("nan_06", 351.20, 355.00, IN(1.0, 1.10)),                 # columns of basalt
    shot("nan_11", 355.00, 358.40, TILT(0.3, 0.6, 1.1)),           # stacked like logs
    shot("nan_03", 358.40, 362.00, IN(1.0, 1.10)),                 # centre of power
    shot("nan_07", 362.00, 366.00, IN(1.0, 1.08)),                 # Saudeleur dynasty
    shot("nan_09", 366.00, 372.20, IN(1.0, 1.12)),                 # 1200-1500 AD
    shot("nan_01", 372.20, 377.50, IN(1.0, 1.10)),                 # 750,000 tons
    shot("nan_08", 377.50, 382.40, IN(1.0, 1.10)),                 # single columns 50 tons
    shot("nan_17", 382.40, 386.20, IN(1.0, 1.08)),                 # quarries across the island
    shot("nan_05", 386.20, 390.90, IN(1.0, 1.08)),                 # moved across water
    shot("nan_10", 390.90, 394.20, IN(1.0, 1.08)),                 # no one knows
    shot("nan_02", 394.20, 399.875, OUT(1.12, 1.0)),               # sorcerers made them fly
], badge="750,000 TONS OF STONE")

# ---------------- 07_nazca ----------------
place("#4", "NAZCA LINES", "PERU", "frames_nazca", 399.875, 403.00, 406.50, 463.00, [
    shot("naz_07", 406.50, 408.60, IN(1.0, 1.06), 0.4),            # desert of southern Peru
    shot("naz_01", 408.60, 409.70, IN(1.0, 1.04), 0.3),            # a hummingbird
    shot("naz_03", 409.70, 410.70, IN(1.0, 1.04), 0.3),            # a monkey
    shot("naz_02", 410.70, 412.10, IN(1.0, 1.04), 0.3),            # a spider, a whale
    shot("naz_06", 412.10, 414.50, IN(1.0, 1.08), 0.4),            # straight lines for km
    shot("naz_08", 414.50, 418.90, IN(1.0, 1.10)),                 # only from the air
    shot("naz_04", 418.90, 422.90, IN(1.0, 1.10)),                 # the Nazca people
    shot("naz_16", 422.90, 429.50, IN(1.0, 1.12)),                 # moving dark stones aside
    shot("naz_09", 429.50, 435.00, IN(1.0, 1.10)),                 # dry, windless desert
    shot("naz_14", 435.00, 436.90, IN(1.0, 1.06)),                 # still finding them
    shot("naz_05", 436.90, 442.00, TILT(0.3, 0.6, 1.1)),           # AI, 2024
    shot("naz_12", 442.00, 447.90, IN(1.0, 1.12)),                 # 303 new figures
    shot("naz_10", 447.90, 451.50, IN(1.0, 1.08)),                 # why the Nazca
    shot("naz_15", 451.50, 455.80, IN(1.0, 1.08)),                 # great questions
    shot("naz_17", 455.80, 459.20, IN(1.0, 1.08)),                 # paths, messages
    shot("naz_11", 459.20, 463.80, OUT(1.12, 1.0)),                # still debating
], badge="303 NEW FIGURES")

# ---------------- 08_baalbek ----------------
place("#3", "BAALBEK", "LEBANON", "frames_baalbek", 463.80, 466.925, 470.425, 530.275, [
    shot("baa_04", 470.425, 473.90, IN(1.0, 1.08)),                # Bekaa Valley ruins
    shot("baa_01", 473.90, 475.60, IN(1.0, 1.06)),                 # temple of Jupiter
    shot("baa_05", 475.60, 480.60, IN(1.0, 1.10)),                 # the Trilithon
    shot("baa_06", 480.60, 484.50, PAN(0.3, 0.7, 1.12)),           # 800 tons each
    shot("baa_07", 484.50, 488.90, IN(1.0, 1.08)),                 # lifted into a wall
    shot("baa_13", 488.90, 494.00, IN(1.0, 1.10)),                 # the ancient quarry
    shot("baa_10", 494.00, 498.30, IN(1.0, 1.10)),                 # stone of the pregnant woman
    shot("baa_08", 498.30, 504.80, IN(1.0, 1.12)),                 # 2014, block underneath
    shot("baa_11", 504.80, 510.20, IN(1.0, 1.10)),                 # 1,650 tons
    shot("baa_14", 510.20, 515.00, IN(1.0, 1.08)),                 # four jumbo jets
    shot("baa_15", 515.00, 519.20, IN(1.0, 1.08)),                 # largest block ever carved
    shot("baa_02", 519.20, 523.90, IN(1.0, 1.08)),                 # too big to move
    shot("baa_12", 523.90, 527.50, IN(1.0, 1.06)),                 # how the Romans moved them
    shot("baa_03", 527.50, 531.075, OUT(1.12, 1.0)),               # not fully understood
], badge="1,650 TONS")

# ---------------- 09_stonehenge ----------------
place("#2", "STONEHENGE", "ENGLAND", "frames_stonehenge", 531.075, 534.20, 537.70, 592.125, [
    shot("sto_01", 537.70, 540.50, IN(1.0, 1.08)),                 # Salisbury Plain
    shot("sto_09", 540.50, 544.00, IN(1.0, 1.10)),                 # 5,000 years ago
    shot("sto_05", 544.00, 548.50, IN(1.0, 1.10)),                 # the stranger it gets
    shot("sto_02", 548.50, 553.30, PAN(0.35, 0.65, 1.1)),          # sarsens, 25 km
    shot("sto_15", 553.30, 557.30, IN(1.0, 1.08)),                 # hills of west Wales
    shot("sto_14", 557.30, 559.90, IN(1.0, 1.06)),                 # 200 km away
    shot("sto_04", 559.90, 565.30, IN(1.0, 1.10)),                 # 2024 discovery
    shot("sto_13", 565.30, 569.40, IN(1.0, 1.10)),                 # the Altar Stone at the heart
    {"frames": "maps/frames_stonehenge", "t0": 569.40, "t1": 575.70, "xin": 0.6, "xout": 0.6},  # Scotland -> Stonehenge
    shot("sto_16", 575.70, 579.50, IN(1.0, 1.08)),                 # how Stone Age people moved it
    shot("sto_18", 579.50, 582.80, IN(1.0, 1.08)),                 # over mountains, by sea
    shot("sto_07", 582.80, 587.30, IN(1.0, 1.08)),                 # why that stone
    shot("sto_06", 587.30, 592.925, OUT(1.12, 1.0)),               # keeping its secrets
], badge="700 KM")

# ---------------- 10_gobekli_tepe ----------------
place("#1", "GÖBEKLI TEPE", "TURKEY", "frames_gobekli_tepe", 592.925, 596.05, 599.55, 661.375, [
    shot("gob_01", 599.55, 604.10, IN(1.0, 1.10)),                 # circles of T-shaped pillars
    shot("gob_13", 604.10, 607.10, TILT(0.3, 0.6, 1.1)),           # taller than five metres
    shot("gob_17", 607.10, 609.90, IN(1.0, 1.08)),                 # foxes, boars
    shot("gob_15", 609.90, 613.60, TILT(0.35, 0.6, 1.1)),          # snakes, scorpions, vultures
    shot("gob_03", 613.60, 619.80, PAN(0.3, 0.7, 1.15)),           # 11,600 years ago
    shot("gob_06", 619.80, 627.00, IN(1.0, 1.10)),                 # before the Great Pyramid
    shot("gob_14", 627.00, 631.00, IN(1.0, 1.08)),                 # before farming, writing
    shot("gob_16", 631.00, 634.30, IN(1.0, 1.08)),                 # before the wheel
    shot("gob_07", 634.30, 641.00, IN(1.0, 1.10)),                 # settle down, become farmers
    shot("gob_08", 641.00, 644.30, IN(1.0, 1.08)),                 # upside down
    shot("gob_09", 644.30, 649.10, IN(1.0, 1.08)),                 # hunter-gatherers, 1995
    shot("gob_05", 649.10, 651.90, IN(1.0, 1.04)),                 # new questions
    shot("gob_27", 651.90, 654.80, IN(1.0, 1.08)),                 # what was it for
    shot("gob_18", 654.80, 659.00, TILT(0.3, 0.6, 1.08)),          # who were the people
    shot("gob_04", 659.00, 662.175, OUT(1.1, 1.0)),                # still can't explain
], badge="11,600 YEARS OLD")

# ---------------- 11_outro ----------------
shots.append(shot("sto_17", 662.175, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 662.675, "t1": DURATION, "fin": 1.2, "fout": 0.6})

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
