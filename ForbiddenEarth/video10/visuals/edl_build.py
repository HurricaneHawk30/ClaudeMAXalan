"""Edit decision list for video10 "Islands No One Is Allowed to Live On" (11:22.1).
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 16 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 682.1

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

# ---------------- 00_hook (0:00-0:29.175) ----------------
shots += [
    shot("ske_05",   0.00,  4.00, IN(1.0, 1.08), 0.3, xin=0),     # islands empty because nobody wants them
    shot("bou_03",   4.00,  6.70, IN(1.0, 1.08), 0.25),           # nobody is allowed
    shot("bal_01",   6.70, 10.80, IN(1.0, 1.10), 0.25),           # a rock where a giant insect hid
    shot("hen_12",  10.80, 16.00, IN(1.0, 1.10), 0.25),           # buried under plastic
    shot("hea_09",  16.00, 21.30, IN(1.0, 1.10), 0.25),           # only penguins live there
    shot("nse_01",  21.30, 29.175, IN(1.0, 1.12), 0.3, xout=0.5), # stay away
]
overlays.append({"type": "brand", "t0": 25.20, "t1": 28.90, "fin": 0.9, "fout": 0.5})

# ---------------- 01_skellig ----------------
place("#10", "SKELLIG MICHAEL", "COUNTY KERRY, IRELAND", "frames_skellig", 29.175, 32.30, 35.80, 84.35, [
    shot("ske_01", 35.80, 41.10, IN(1.0, 1.10)),                   # a jagged peak out of the Atlantic
    shot("ske_13", 41.10, 46.90, IN(1.0, 1.10)),                   # monks climbed it
    shot("ske_10", 46.90, 50.20, IN(1.0, 1.08)),                   # as far from the world as possible
    shot("ske_04", 50.20, 54.40, TILT(0.3, 0.7, 1.0)),             # 618 stone steps
    shot("ske_09", 54.40, 58.60, IN(1.0, 1.08)),                   # huts without mortar
    shot("ske_08", 58.60, 60.70, IN(1.0, 1.08)),                   # still standing
    shot("ske_02", 60.70, 64.60, IN(1.0, 1.10)),                   # twelve monks and an abbot
    shot("ske_15", 64.60, 68.60, PAN(0.4, 0.6, 1.1)),              # moved to the mainland
    shot("ske_11", 68.60, 73.80, IN(1.0, 1.10)),                   # World Heritage Site
    shot("ske_12", 73.80, 78.50, IN(1.0, 1.08)),                   # only when the sea allows
    shot("ske_03", 78.50, 82.20, IN(1.0, 1.08)),                   # nobody stays the night
    shot("ske_14", 82.20, 85.15, OUT(1.1, 1.0)),                   # the puffins
], badge="618 STONE STEPS")

# ---------------- 02_henderson ----------------
place("#9", "HENDERSON ISLAND", "PITCAIRN ISLANDS", "frames_henderson", 85.15, 88.275, 91.775, 147.50, [
    shot("hen_14", 91.775, 93.10, IN(1.0, 1.08)),                  # middle of the South Pacific
    shot("hen_04", 93.10, 99.80, TILT(0.35, 0.65, 1.0)),           # a raised coral island
    shot("hen_03", 99.80, 104.00, PAN(0.4, 0.6, 1.1)),             # Polynesians once lived here
    shot("hen_05", 104.00, 107.20, IN(1.0, 1.08)),                 # no people for 600 years
    shot("hen_15", 107.20, 111.90, IN(1.0, 1.10)),                 # untouched wildlife
    shot("hen_06", 111.90, 116.90, IN(1.0, 1.10)),                 # visited by scientists
    shot("hen_09", 116.90, 121.50, IN(1.0, 1.08)),                 # 2015
    shot("hen_01", 121.50, 127.80, IN(1.0, 1.15, (0.5, 0.6))),     # covered in plastic
    shot("hen_08", 127.80, 133.50, IN(1.0, 1.10)),                 # nearly 38 million pieces (Midway Atoll)
    shot("hen_07", 133.50, 138.00, IN(1.0, 1.08)),                 # washing up every day
    shot("hen_11", 138.00, 143.80, PAN(0.4, 0.6, 1.1)),            # ocean currents
    shot("hen_13", 143.80, 148.30, OUT(1.1, 1.0)),                 # everybody's trash
], badge="38 MILLION PIECES OF PLASTIC")

# ---------------- 03_balls_pyramid ----------------
place("#8", "BALL'S PYRAMID", "LORD HOWE ISLAND, AUSTRALIA", "frames_balls_pyramid", 148.30, 151.425, 154.925, 214.15, [
    shot("bal_09", 154.925, 161.70, IN(1.0, 1.10)),                # a blade of volcanic rock
    shot("bal_04", 161.70, 165.30, IN(1.0, 1.08)),                 # the tallest sea stack
    shot("bal_02", 165.30, 170.80, IN(1.0, 1.10)),                 # nowhere to stand
    shot("bal_03", 170.80, 177.00, IN(1.0, 1.10)),                 # as long as a human hand
    shot("bal_10", 177.00, 179.30, IN(1.0, 1.08)),                 # the tree lobster
    shot("bal_13", 179.30, 185.20, IN(1.0, 1.12)),                 # 1918, rats on Lord Howe (1889 map)
    shot("bal_05", 185.20, 189.00, IN(1.0, 1.08)),                 # the insect was gone
    shot("bal_12", 189.00, 191.70, IN(1.0, 1.08)),                 # declared extinct
    shot("bal_14", 191.70, 197.00, IN(1.0, 1.10)),                 # 2001, climbed at night
    shot("bal_06", 197.00, 203.60, PAN(0.4, 0.6, 1.1)),            # twenty-four still alive
    shot("bal_08", 203.60, 210.30, IN(1.0, 1.10)),                 # climbing banned in 1982
    shot("bal_01", 210.30, 214.95, OUT(1.1, 1.0)),                 # the last wild tree lobsters
], badge="24 INSECTS ON A ROCK")

# ---------------- 04_poveglia ----------------
place("#7", "POVEGLIA", "VENETIAN LAGOON, ITALY", "frames_poveglia", 214.95, 218.075, 221.575, 279.925, [
    shot("pov_03", 221.575, 225.80, PAN(0.3, 0.7, 1.0)),           # seen from the beaches of Venice
    shot("pov_01", 225.80, 227.40, IN(1.0, 1.08)),                 # that's Poveglia
    shot("pov_08", 227.40, 231.70, IN(1.0, 1.10)),                 # nobody since 1968
    shot("pov_06", 231.70, 236.40, IN(1.0, 1.10)),                 # 1776, quarantine station (18th-c. painting)
    shot("pov_11", 236.40, 242.80, IN(1.0, 1.12)),                 # plague (1793 inscription)
    shot("pov_02", 242.80, 246.30, IN(1.0, 1.08)),                 # a hospital
    shot("pov_05", 246.30, 251.70, TILT(0.35, 0.6, 1.0)),          # left to the trees
    shot("pov_10", 251.70, 256.30, IN(1.0, 1.08)),                 # legends
    shot("pov_12", 256.30, 261.50, TILT(0.35, 0.6, 1.0)),          # the stories stuck
    shot("pov_13", 261.50, 266.80, IN(1.0, 1.10)),                 # most haunted
    shot("pov_09", 266.80, 269.60, IN(1.0, 1.08)),                 # still closed
    shot("pov_07", 269.60, 274.70, IN(1.0, 1.10)),                 # 2014 auction
    shot("pov_14", 274.70, 280.725, OUT(1.1, 1.0)),                # a public park (plan)
], badge="QUARANTINE ISLAND")

# ---------------- 05_farallon ----------------
place("#6", "FARALLON ISLANDS", "SAN FRANCISCO, USA", "frames_farallon", 280.725, 283.85, 287.35, 337.325, [
    shot("far_02", 287.35, 294.90, IN(1.0, 1.12)),                 # a ring of granite islands
    shot("far_05", 294.90, 300.90, IN(1.0, 1.10)),                 # part of San Francisco
    shot("far_07", 300.90, 304.90, IN(1.0, 1.08)),                 # closed since 1969
    shot("far_12", 304.90, 307.60, IN(1.0, 1.08)),                 # a few researchers
    shot("far_03", 307.60, 311.00, IN(1.0, 1.08)),                 # seabirds
    shot("far_04", 311.00, 314.90, IN(1.0, 1.08)),                 # seals and sea lions
    shot("far_14", 314.90, 320.40, PAN(0.4, 0.6, 1.1)),            # white sharks hunt them
    shot("far_06", 320.40, 323.30, IN(1.0, 1.08)),                 # a darker secret
    shot("far_09", 323.30, 328.00, IN(1.0, 1.10)),                 # barrels on the seafloor
    shot("far_11", 328.00, 333.00, IN(1.0, 1.08)),                 # low-level radioactive waste
    shot("far_08", 333.00, 336.30, IN(1.0, 1.08)),                 # mapped (Bierstadt, 1872)
    shot("far_01", 336.30, 338.125, OUT(1.1, 1.0)),                # still down there
], badge="~48,000 BARRELS")

# ---------------- 06_heard ----------------
place("#5", "HEARD ISLAND", "AUSTRALIA", "frames_heard", 338.125, 341.25, 344.75, 397.275, [
    shot("hea_08", 344.75, 349.60, IN(1.0, 1.10)),                 # the stormy Southern Ocean
    shot("hea_03", 349.60, 353.30, IN(1.0, 1.08)),                 # two weeks from Perth
    shot("hea_07", 353.30, 359.40, PAN(0.4, 0.6, 1.1)),            # glaciers, black sand
    shot("hea_01", 359.40, 364.60, IN(1.0, 1.10)),                 # Big Ben
    shot("hea_12", 364.60, 366.80, IN(1.0, 1.08)),                 # no one lives here
    shot("hea_05", 366.80, 369.20, IN(1.0, 1.08)),                 # no buildings, no roads
    shot("hea_11", 369.20, 372.10, IN(1.0, 1.08)),                 # a permit to land
    shot("hea_02", 372.10, 377.10, IN(1.0, 1.10)),                 # penguins, seals, seabirds
    shot("hea_04", 377.10, 381.50, IN(1.0, 1.08)),                 # April 2025, the tariff list
    shot("hea_06", 381.50, 386.70, IN(1.0, 1.10)),
    shot("hea_10", 386.70, 390.20, IN(1.0, 1.08)),                 # ten percent
    shot("hea_13", 390.20, 392.60, IN(1.0, 1.08)),                 # no shops, no factories
    shot("hea_15", 392.60, 395.90, IN(1.0, 1.08)),                 # tariffs on penguins
    shot("hea_09", 395.90, 398.075, OUT(1.1, 1.0)),                # no comment
], badge="PENGUINS ONLY")

# ---------------- 07_bouvet ----------------
place("#4", "BOUVET ISLAND", "NORWAY", "frames_bouvet", 398.075, 401.20, 404.70, 459.25, [
    shot("bou_05", 404.70, 412.50, PAN(0.3, 0.7, 1.0)),            # the most remote island on Earth
    shot("bou_02", 412.50, 414.80, IN(1.0, 1.08)),                 # nobody lives there either
    shot("bou_01", 414.80, 421.80, IN(1.0, 1.10)),                 # covered by a glacier
    shot("bou_04", 421.80, 426.00, IN(1.0, 1.12)),                 # discovered 1739 (map)
    shot("bou_10", 426.00, 432.60, IN(1.0, 1.12)),                 # James Cook gave up (1754 map)
    shot("bou_06", 432.60, 438.90, IN(1.0, 1.10)),                 # 1964, by helicopter
    shot("bou_09", 438.90, 442.60, IN(1.0, 1.08)),                 # an abandoned lifeboat
    shot("bou_11", 442.60, 445.40, IN(1.0, 1.08)),                 # oars and supplies
    shot("bou_07", 445.40, 450.40, IN(1.0, 1.10)),                 # no name on the boat
    shot("bou_08", 450.40, 460.05, OUT(1.12, 1.0)),                # a nature reserve
], badge="1,700 KM TO ANYWHERE")

# ---------------- 08_clipperton ----------------
place("#3", "CLIPPERTON ISLAND", "FRANCE", "frames_clipperton", 460.05, 463.175, 466.675, 530.50, [
    shot("cli_01", 466.675, 475.00, IN(1.0, 1.20)),                # a ring of coral (from orbit)
    shot("cli_05", 475.00, 484.20, IN(1.0, 1.12)),                 # a pirate's hideout (1849 chart)
    shot("cli_02", 484.20, 493.30, PAN(0.35, 0.65, 1.1)),          # the early 1900s (1899 drawing)
    shot("cli_04", 493.30, 503.50, IN(1.0, 1.10)),                 # the ships stopped coming
    shot("cli_03", 503.50, 514.00, IN(1.0, 1.12)),                 # the lighthouse keeper
    shot("cli_06", 514.00, 523.10, IN(1.0, 1.12)),                 # eleven survivors
    shot("cli_07", 523.10, 531.30, OUT(1.15, 1.0)),                # nobody since
], badge="ABANDONED SINCE 1917")

# ---------------- 09_vozrozhdeniya ----------------
place("#2", "VOZROZHDENIYA", "ARAL SEA", "frames_vozrozhdeniya", 531.30, 534.425, 537.925, 592.20, [
    shot("voz_13", 537.925, 540.20, IN(1.0, 1.08)),                # Rebirth Island
    shot("voz_02", 540.20, 548.40, IN(1.0, 1.12)),                 # the Aral Sea (1964)
    shot("voz_09", 548.40, 552.00, IN(1.0, 1.10)),                 # a secret
    shot("voz_03", 552.00, 558.00, IN(1.0, 1.10)),                 # testing ground (1997)
    shot("voz_11", 558.00, 562.70, IN(1.0, 1.08)),                 # a closed town
    shot("voz_14", 562.70, 569.00, PAN(0.4, 0.6, 1.1)),            # left almost overnight
    shot("voz_15", 569.00, 573.90, IN(1.0, 1.08)),                 # buried in pits
    shot("voz_04", 573.90, 580.20, IN(1.0, 1.10)),                 # 2002 clean-up (2011)
    shot("voz_08", 580.20, 585.50, IN(1.0, 1.10)),                 # the Aral Sea was dying
    shot("voz_06", 585.50, 589.00, IN(1.0, 1.08)),                 # the water dried up (2017)
    shot("voz_01", 589.00, 593.00, OUT(1.1, 1.0)),                 # no longer an island (1989/2008)
], badge="THE ISLAND THAT VANISHED")

# ---------------- 10_north_sentinel ----------------
place("#1", "NORTH SENTINEL", "ANDAMAN ISLANDS, INDIA", "frames_north_sentinel", 593.00, 596.125, 599.625, 666.325, [
    shot("nse_10", 599.625, 601.80, IN(1.0, 1.08)),                # the Andaman Islands
    shot("nse_01", 601.80, 608.70, IN(1.0, 1.12)),                 # ringed by reefs, covered in forest
    shot("nse_09", 608.70, 617.70, IN(1.0, 1.10)),                 # the Sentinelese
    shot("nse_07", 617.70, 624.50, IN(1.0, 1.12)),                 # nine kilometres
    shot("nse_14", 624.50, 626.70, IN(1.0, 1.08)),                 # disease
    shot("nse_03", 626.70, 634.30, PAN(0.4, 0.6, 1.1)),            # no immunity
    shot("nse_12", 634.30, 636.90, IN(1.0, 1.08)),                 # wishes clear
    shot("nse_05", 636.90, 642.10, TILT(0.35, 0.65, 1.0)),         # 2004 tsunami
    shot("nse_04", 642.10, 645.10, IN(1.0, 1.08)),                 # an arrow
    shot("nse_08", 645.10, 652.10, IN(1.0, 1.10)),                 # outsiders killed
    shot("nse_02", 652.10, 658.30, IN(1.0, 1.10)),                 # 2025
    shot("nse_06", 658.30, 663.20, IN(1.0, 1.08)),                 # thousands of years
    shot("nse_13", 663.20, 667.925, OUT(1.1, 1.0)),                # leave it alone
], badge="DO NOT APPROACH")

# ---------------- 11_outro ----------------
shots.append(shot("bal_04", 667.925, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 668.5, "t1": DURATION, "fin": 1.2, "fout": 0.6})

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
