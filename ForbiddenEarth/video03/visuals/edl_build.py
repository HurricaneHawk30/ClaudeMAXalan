"""Edit decision list for video03 "10 Beautiful Places You're Not Allowed to Visit" (10:57.6).
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 6 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 657.6

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

def place(num, name, sub, frames, t_card, t_map, t_lower, t_end, items, lower=None):
    shots.append({"card": True, "bg_map": f"maps/{frames}", "num": num, "name": name, "sub": sub,
                  "t0": t_card, "t1": t_map, "xin": 0.5, "xout": 0.5})
    shots.append({"frames": f"maps/{frames}", "t0": t_map, "t1": t_lower, "xin": 0.5, "xout": 0.6})
    shots.extend(items)
    overlays.append({"type": "lower", "num": num, "text": lower or f"{name}, {sub}", "t0": t_lower + 0.1, "t1": t_end})

# ---------------- 00_hook (0:00-0:21.2) ----------------
shots += [
    shot("fly_01",   0.00,  3.90, IN(1.0, 1.12), 0.3, xin=0),       # the most beautiful places are off-limits
    shot("wave_03",  3.90,  5.80, PAN(0.4, 0.6, 1.12), 0.25),        # guarded by a lottery
    shot("lasc_03",  5.80,  7.30, IN(1.0, 1.10), 0.25),              # some by law
    shot("kai_02",   7.30,  9.00, IN(1.0, 1.10), 0.25),              # some by the gods
    shot("snk_07",   9.00, 11.70, IN(1.0, 1.12), 0.25),              # thousands of venomous snakes
    shot("qin_14",  11.70, 17.20, OUT(1.15, 1.0), 0.3),              # no one alive has seen inside it
    shot("kai_10",  17.20, 22.00, IN(1.0, 1.08), 0.3, xout=0.5),     # ten beautiful places
]
overlays.append({"type": "brand", "t0": 18.60, "t1": 21.90, "fin": 0.9, "fout": 0.5})

# ---------------- 01_the_wave ----------------
place("#10", "THE WAVE", "ARIZONA, USA", "frames_wave", 22.00, 25.15, 28.65, 74.675, [
    shot("wave_05",  28.65, 32.60, IN(1.0, 1.10)),                   # the rock looks like it's moving
    shot("wave_10",  32.60, 36.40, PAN(0.4, 0.6, 1.12)),             # ripple like frozen water
    shot("wave_09",  36.40, 41.00, IN(1.0, 1.10)),                   # you can't just walk in
    shot("wave_01",  41.00, 47.60, PAN(0.6, 0.4, 1.12)),             # thin, fragile ridges; BLM
    shot("wave_11",  47.60, 54.80, PAN(0.25, 0.75, 1.0)),            # 64 people a day, lottery
    shot("wave_13",  54.80, 61.70, IN(1.0, 1.10)),                   # drawn online / daily draw
    shot("wave_14",  61.70, 69.10, PAN(0.4, 0.6, 1.1)),              # 200,000 entered the lottery
    shot("wave_02",  69.10, 75.475, OUT(1.12, 1.0)),                 # you just have to be lucky
])

# ---------------- 02_fly_geyser ----------------
place("#9", "FLY GEYSER", "NEVADA, USA", "frames_flygeyser", 75.475, 78.60, 82.10, 131.80, [
    shot("fly_02",   82.10,  88.00, IN(1.0, 1.10)),                  # made by accident; 1964 well
    shot("fly_03",   88.00,  94.50, IN(1.0, 1.12, (0.5, 0.45))),     # scalding water, flowing since
    shot("fly_06",   94.50, 102.50, PAN(0.4, 0.6, 1.12)),            # multicoloured cones
    shot("fly_08",  102.50, 108.70, IN(1.0, 1.10)),                  # still growing; private land
    shot("fly_12",  108.70, 114.30, PAN(0.4, 0.6, 1.1)),             # Fly Ranch, closed 20 years
    shot("fly_11",  114.30, 119.00, PAN(0.3, 0.7, 1.0)),             # Burning Man Project
    shot("fly_13",  119.00, 123.50, IN(1.0, 1.10)),                  # festival in the nearby desert
    shot("fly_09",  123.50, 128.00, IN(1.0, 1.12)),                  # small guided walk
    shot("fly_10",  128.00, 132.60, OUT(1.12, 1.0)),                 # pools close to boiling
])

# ---------------- 03_niihau ----------------
place("#8", "NIIHAU", "HAWAII, USA", "frames_niihau", 132.60, 135.75, 139.25, 190.275, [
    shot("nii_05",   139.25, 143.70, IN(1.0, 1.10)),                 # 17 miles off Kauai
    inset("nii_10",  143.70, 151.60, max_up=1.2),                    # bought in 1864 (map of 1833)
    shot("nii_04",   151.60, 158.60, PAN(0.6, 0.4, 1.12)),           # the Robinson family decides
    shot("nii_01",   158.60, 166.50, IN(1.0, 1.12)),                 # about 70 people live there
    shot("nii_09",   166.50, 171.50, IN(1.0, 1.10)),                 # the Forbidden Isle
    shot("nii_03",   171.50, 176.70, PAN(0.4, 0.6, 1.1)),            # outsiders kept away
    shot("nii_helios5", 176.70, 184.10, IN(1.0, 1.08)),              # helicopter tours, dives
    shot("nii_06",   184.10, 191.075, OUT(1.12, 1.0)),               # owned for 160 years
])

# ---------------- 04_surtsey ----------------
place("#7", "SURTSEY", "ICELAND", "frames_surtsey", 191.075, 194.20, 197.70, 258.675, [
    inset("surt_11", 197.70, 202.30, max_up=1.2),                    # an eruption broke the surface
    shot("surt_10",  202.30, 206.80, IN(1.0, 1.12)),                 # a ridge of new rock
    shot("surt_04",  206.80, 211.10, IN(1.0, 1.10)),                 # a brand-new island
    shot("surt_01",  211.10, 218.20, PAN(0.4, 0.6, 1.1)),            # named after Surtr
    shot("surt_06",  218.20, 222.50, IN(1.0, 1.10)),                 # watch life arrive
    shot("surt_03",  222.50, 226.70, PAN(0.6, 0.4, 1.1)),            # bare, sterile land
    shot("surt_02",  226.70, 231.10, PAN(0.35, 0.65, 1.0)),          # protected since 1965
    shot("surt_05",  231.10, 235.80, IN(1.0, 1.10)),                 # off-limits except researchers
    shot("surt_09",  235.80, 242.00, IN(1.0, 1.10)),                 # not a single seed
    shot("surt_07",  242.00, 248.30, PAN(0.3, 0.7, 1.0)),            # first plant; birds
    shot("surt_14",  248.30, 255.00, PAN(0.4, 0.6, 1.1)),            # seals and 90 bird species
    shot("surt_08",  255.00, 259.475, OUT(1.12, 1.0)),               # the sea wears it away
])

# ---------------- 05_lascaux ----------------
place("#6", "LASCAUX CAVE", "FRANCE", "frames_lascaux", 259.475, 262.60, 266.10, 320.80, [
    shot("lasc_13",  266.10, 270.90, IN(1.0, 1.10)),                 # followed their dog into a hole
    shot("lasc_01",  270.90, 275.50, IN(1.0, 1.12)),                 # paintings of horses
    shot("lasc_05",  275.50, 279.90, PAN(0.4, 0.6, 1.1)),            # bulls and deer
    shot("lasc_06",  279.90, 285.60, IN(1.0, 1.10)),                 # greatest discovery
    shot("lasc_11",  285.60, 289.80, PAN(0.3, 0.7, 1.0)),            # opened in 1948
    shot("lasc_10",  289.80, 296.10, IN(1.0, 1.10)),                 # 1,500 people a day
    shot("lasc_07",  296.10, 303.40, TILT(0.4, 0.6, 1.1)),           # microbes, green mould
    shot("lasc_14",  303.40, 310.70, IN(1.0, 1.10)),                 # closed in 1963
    shot("lasc_02",  310.70, 317.00, IN(1.0, 1.10)),                 # researchers in sterile overalls
    shot("lasc_09",  317.00, 321.60, OUT(1.12, 1.0)),                # a full-size replica nearby
])

# ---------------- 06_ise ----------------
place("#5", "ISE GRAND SHRINE", "JAPAN", "frames_ise", 321.60, 324.75, 328.25, 388.475, [
    shot("ise_10",   328.25, 334.00, IN(1.0, 1.10)),                 # deep in a forest
    shot("ise_11",   334.00, 338.40, TILT(0.4, 0.6, 1.1)),           # Naiku, Amaterasu
    shot("ise_01",   338.40, 344.20, IN(1.0, 1.10)),                 # millions of pilgrims
    shot("ise_02",   344.20, 348.00, IN(1.0, 1.10)),                 # stop at the outer fences
    shot("ise_03",   348.00, 352.40, PAN(0.4, 0.6, 1.1)),            # only priests beyond
    shot("ise_12",   352.40, 359.40, IN(1.0, 1.12)),                 # rebuilt every 20 years (1953 aerial)
    shot("ise_13",   359.40, 365.90, IN(1.0, 1.10)),                 # 125 buildings, fresh cypress
    shot("ise_14",   365.90, 373.70, PAN(0.35, 0.65, 1.05)),         # a plot next to the old one
    shot("ise_06",   373.70, 378.10, IN(1.0, 1.10)),                 # first rebuilding in 690
    shot("ise_07",   378.10, 382.00, IN(1.0, 1.10)),                 # rebuilding underway
    shot("ise_15",   382.00, 386.00, PAN(0.4, 0.6, 1.1)),            # 2033
    shot("ise_08",   386.00, 389.275, OUT(1.12, 1.0)),               # the cycle begins again
])

# ---------------- 07_snake_island ----------------
place("#4", "SNAKE ISLAND", "BRAZIL", "frames_snake", 389.275, 392.40, 395.90, 447.60, [
    shot("snk_02",   395.90, 402.70, IN(1.0, 1.10)),                 # a lush green island
    shot("snk_03",   402.70, 408.00, PAN(0.4, 0.6, 1.1)),            # paradise; Snake Island
    shot("snk_06",   408.00, 413.70, IN(1.0, 1.12)),                 # golden lancehead
    shot("snk_13",   413.70, 420.70, IN(1.0, 1.10)),                 # hunting birds
    shot("snk_09",   420.70, 426.70, IN(1.0, 1.12)),                 # venom five times stronger
    shot("snk_05",   426.70, 432.70, IN(1.0, 1.10)),                 # 43 hectares
    shot("snk_10",   432.70, 438.60, PAN(0.4, 0.6, 1.1)),            # critically endangered
    shot("snk_04",   438.60, 444.00, TILT(0.55, 0.4, 1.1)),          # only the navy and scientists
    shot("snk_01",   444.00, 448.40, OUT(1.12, 1.0)),                # admire it from a boat
])

# ---------------- 08_naica ----------------
place("#3", "CAVE OF THE CRYSTALS", "MEXICO", "frames_naica", 448.40, 451.55, 455.05, 514.075, [
    inset("nai_10",  455.05, 459.40, max_up=1.0),                    # the Naica mine
    shot("nai_13",   459.40, 463.30, IN(1.0, 1.10)),                 # a hidden chamber
    shot("nai_01",   463.30, 471.60, IN(1.0, 1.15, (0.5, 0.5), (0.45, 0.55))), # giant beams of gypsum
    shot("nai_11",   471.60, 479.80, PAN(0.4, 0.6, 1.1)),            # Sistine Chapel of crystals
    shot("nai_16",   479.80, 486.20, IN(1.0, 1.10)),                 # grew slowly
    shot("nai_19",   486.20, 492.80, PAN(0.4, 0.6, 1.1)),            # 58 °C, 90 % humidity
    inset("nai_14",  492.80, 501.50, max_up=1.2),                    # cooling suits, short shifts
    shot("nai_17",   501.50, 508.00, IN(1.0, 1.10)),                 # the mine shut down
    shot("nai_15",   508.00, 512.00, IN(1.0, 1.08)),                 # flooded again
    shot("nai_20",   512.00, 514.875, OUT(1.1, 1.0)),                # no one can go in
])

# ---------------- 09_kailash ----------------
place("#2", "MOUNT KAILASH", "TIBET", "frames_kailash", 514.875, 518.00, 521.50, 572.55, [
    shot("kai_06",   521.50, 525.90, IN(1.0, 1.10)),                 # shaped like a pyramid
    shot("kai_01",   525.90, 533.50, PAN(0.4, 0.6, 1.1)),            # 6,638 metres
    shot("kai_07",   533.50, 541.20, IN(1.0, 1.10)),                 # nobody has climbed it
    shot("kai_11",   541.20, 548.10, PAN(0.4, 0.6, 1.1)),            # sacred to four religions
    shot("kai_03",   548.10, 555.90, TILT(0.4, 0.55, 1.08)),         # Shiva; Mount Meru
    shot("kai_pia",  555.90, 562.90, IN(1.0, 1.10)),                 # permits not granted
    shot("kai_14",   562.90, 567.90, IN(1.0, 1.06)),                 # pilgrims walk around it
    shot("kai_13",   567.90, 573.35, OUT(1.1, 1.0)),                 # bowing every few steps
])

# ---------------- 10_qin ----------------
place("#1", "TOMB OF QIN SHI HUANG", "CHINA", "frames_qin", 573.35, 576.50, 580.00, 643.875, [
    shot("qin_pia",  580.00, 584.60, IN(1.0, 1.10)),                 # near Xi'an, 1974
    shot("qin_04",   584.60, 589.00, PAN(0.4, 0.6, 1.1)),            # the Terracotta Army
    shot("qin_01",   589.00, 593.30, IN(1.0, 1.10)),                 # 8,000 figures
    shot("qin_03",   593.30, 599.00, IN(1.0, 1.10, (0.5, 0.4))),     # the first emperor, 210 BC
    shot("qin_09",   599.00, 604.90, PAN(0.3, 0.7, 1.0)),            # a huge mound nearby
    shot("qin_08",   604.90, 610.00, IN(1.0, 1.10)),                 # never been opened
    shot("qin_11",   610.00, 614.50, IN(1.0, 1.10)),                 # 700,000 workers
    shot("qin_12",   614.50, 618.50, PAN(0.4, 0.6, 1.1)),            # rivers of mercury
    shot("qin_14",   618.50, 622.50, IN(1.0, 1.10)),                 # it sounded like legend
    shot("qin_10",   622.50, 626.60, IN(1.0, 1.08)),                 # tested the soil
    shot("qin_05",   626.60, 633.50, IN(1.0, 1.10)),                 # far more mercury
    shot("qin_06",   633.50, 638.10, PAN(0.4, 0.6, 1.1)),            # any breach could destroy it
    shot("qin_02",   638.10, 644.675, OUT(1.12, 1.0)),               # stays sealed
])

# ---------------- 11_outro ----------------
shots.append(shot("wave_15", 644.675, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 645.2, "t1": DURATION, "fin": 1.2, "fout": 0.6})

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
