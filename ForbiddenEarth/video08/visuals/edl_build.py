"""Edit decision list for video08 "Hidden Wonders Tourists Never See" (10:45.3).
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 14 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 645.3

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

# ---------------- 00_hook (0:00-0:30.6) ----------------
shots += [
    shot("hid_03",   0.00,  3.30, IN(1.0, 1.08), 0.3, xin=0),     # famous wonders are crowded
    shot("mar_09",   3.30,  6.60, IN(1.0, 1.10), 0.3),            # some of the most beautiful places are almost empty
    shot("kel_14",   6.60,  9.90, IN(1.0, 1.10), 0.3),
    shot("jel_18",   9.90, 12.10, IN(1.0, 1.08), 0.25),           # too far away, too hard to reach
    shot("hid_08",  12.10, 16.00, IN(1.0, 1.10), 0.3),            # protected by strict rules
    shot("hil_03",  16.00, 17.60, IN(1.0, 1.08), 0.25),           # a pink lake
    shot("can_03",  17.60, 19.20, IN(1.0, 1.08), 0.25),           # a river of five colors
    shot("mos_15",  19.20, 21.40, IN(1.0, 1.08), 0.25),           # a bay that glows in the dark
    shot("son_02",  21.40, 25.70, IN(1.0, 1.10), 0.3),            # a cave with its own jungle
    shot("son_05",  25.70, 30.60, IN(1.0, 1.10, (0.5, 0.45)), 0.3, xout=0.5),  # lost for almost 20 years
]
overlays.append({"type": "brand", "t0": 26.60, "t1": 30.30, "fin": 0.9, "fout": 0.5})

# ---------------- 01_crooked ----------------
place("#10", "CROOKED FOREST", "GRYFINO, POLAND", "frames_crooked", 30.60, 33.725, 37.225, 89.225, [
    shot("cro_02", 37.225, 41.80, IN(1.0, 1.10)),                  # a pine forest where something went wrong
    shot("cro_01", 41.80, 44.60, IN(1.0, 1.08)),                   # around 400 trees
    shot("cro_06", 44.60, 51.20, PAN(0.4, 0.6, 1.1)),              # bend sharply sideways
    shot("cro_07", 51.20, 54.50, IN(1.0, 1.08)),                   # all bend north
    shot("cro_10", 54.50, 59.20, IN(1.0, 1.10)),                   # other pines grow straight
    shot("cro_09", 59.20, 65.10, TILT(0.6, 0.4, 1.1)),             # planted around 1930
    shot("cro_11", 65.10, 67.60, IN(1.0, 1.08)),                   # heavy snow
    shot("cro_12", 67.60, 71.50, IN(1.0, 1.10)),                   # tanks
    shot("cro_03", 71.50, 76.20, PAN(0.4, 0.6, 1.1)),              # foresters bent them on purpose
    shot("cro_04", 76.20, 79.40, IN(1.0, 1.08)),                   # curved wood for furniture or boats
    shot("cro_08", 79.40, 84.90, IN(1.0, 1.10)),                   # the war came
    shot("cro_13", 84.90, 90.025, OUT(1.1, 1.0)),                  # keeping its secret
], badge="400 BENT TREES")

# ---------------- 02_fingal ----------------
place("#9", "FINGAL'S CAVE", "STAFFA, SCOTLAND", "frames_fingal", 90.025, 93.15, 96.65, 154.00, [
    shot("fin_13", 96.65, 100.80, PAN(0.4, 0.6, 1.1)),             # Staffa, no people
    shot("fin_15", 100.80, 104.40, IN(1.0, 1.10)),                 # cliffs look built
    shot("fin_04", 104.40, 107.20, IN(1.0, 1.10)),                 # six-sided columns, honeycomb
    shot("fin_03", 107.20, 109.90, TILT(0.6, 0.4, 1.1)),
    shot("fin_10", 109.90, 117.20, PAN(0.35, 0.65, 1.12)),         # basalt, lava cooled slowly
    shot("fin_12", 117.20, 121.80, IN(1.0, 1.10)),                 # the sea hollowed out a cave
    shot("fin_05", 121.80, 124.90, TILT(0.6, 0.35, 1.0)),          # tall like a cathedral
    shot("fin_02", 124.90, 127.50, IN(1.0, 1.08)),                 # booms and echoes
    shot("fin_06", 127.50, 133.20, IN(1.0, 1.12)),                 # 1772, Joseph Banks (1832 engraving)
    shot("fin_08", 133.20, 139.40, IN(1.0, 1.10)),                 # 1829, Mendelssohn by boat (Gude sketch)
    shot("fin_07", 139.40, 146.70, IN(1.0, 1.12)),                 # Hebrides overture (1900 photochrom)
    shot("fin_09", 146.70, 150.60, PAN(0.4, 0.6, 1.1)),            # small boats bring visitors
    shot("fin_01", 150.60, 154.80, OUT(1.1, 1.0)),                 # the weather is wild
], badge="INSPIRED A SYMPHONY")

# ---------------- 03_hillier ----------------
place("#8", "LAKE HILLIER", "WESTERN AUSTRALIA", "frames_hillier", 154.80, 157.925, 161.425, 213.65, [
    shot("hil_01", 161.425, 168.10, IN(1.0, 1.12)),                # bright pink
    shot("hil_03", 168.10, 177.40, PAN(0.6, 0.4, 1.12)),           # strawberry milk, thin strip
    shot("hil_11", 177.40, 182.00, IN(1.0, 1.10)),                 # explorers' chart, 1792
    shot("hil_08", 182.00, 185.20, IN(1.0, 1.08)),                 # climbing the highest hill
    shot("hil_09", 185.20, 191.00, IN(1.0, 1.10)),                 # Dunaliella salina bloom
    shot("hil_10", 191.00, 196.00, PAN(0.4, 0.6, 1.12)),           # red pigment (another pink lake, WA)
    shot("hil_05", 196.00, 201.10, IN(1.0, 1.10)),                 # no roads
    shot("hil_07", 201.10, 204.00, IN(1.0, 1.08)),                 # no hotels, no ferry
    shot("hil_12", 204.00, 208.60, IN(1.0, 1.10)),                 # a scenic flight
    shot("hil_02", 208.60, 211.90, PAN(0.4, 0.6, 1.1)),            # from the shore, a softer pink
    shot("hil_04", 211.90, 214.45, OUT(1.1, 1.0)),                 # from the sky, unreal
], badge="PINK FROM ABOVE")

# ---------------- 04_kelimutu ----------------
place("#7", "KELIMUTU", "FLORES, INDONESIA", "frames_kelimutu", 214.45, 217.575, 221.075, 268.425, [
    shot("kel_02", 221.075, 225.60, IN(1.0, 1.10)),                # three crater lakes side by side
    shot("kel_09", 225.60, 228.00, IN(1.0, 1.08)),                 # they don't stay the same colour
    shot("kel_04", 228.00, 230.60, IN(1.0, 1.08)),                 # turquoise
    shot("kel_05", 230.60, 234.00, IN(1.0, 1.08)),                 # green, red, brown, black
    shot("kel_12", 234.00, 238.80, PAN(0.4, 0.6, 1.1)),            # one lake changes
    shot("kel_06", 238.80, 243.00, IN(1.0, 1.10)),                 # chemistry
    shot("kel_15", 243.00, 247.30, IN(1.0, 1.10)),                 # gas and minerals
    shot("kel_10", 247.30, 251.10, IN(1.0, 1.08)),                 # the Lio people
    shot("kel_08", 251.10, 255.50, PAN(0.4, 0.6, 1.1)),            # resting place of souls
    shot("kel_11", 255.50, 260.40, IN(1.0, 1.10)),
    shot("kel_14", 260.40, 265.00, IN(1.0, 1.10)),                 # climb before dawn
    shot("kel_03", 265.00, 269.225, OUT(1.1, 1.0)),                # the lakes appear
], badge="3 LAKES, CHANGING COLORS")

# ---------------- 05_marble ----------------
place("#6", "MARBLE CAVES", "PATAGONIA, CHILE", "frames_marble", 269.225, 272.35, 275.85, 325.025, [
    shot("mar_n_2", 275.85, 278.80, IN(1.0, 1.10)),                # General Carrera from space
    shot("mar_09", 278.80, 281.20, IN(1.0, 1.08)),                 # caves made of marble
    shot("mar_01", 281.20, 286.20, IN(1.0, 1.10)),                 # 6,000 years of waves
    shot("mar_07", 286.20, 288.80, IN(1.0, 1.08)),                 # arches and pillars
    shot("mar_05", 288.80, 291.20, PAN(0.4, 0.6, 1.1)),            # streaked white, grey, blue
    shot("mar_06", 291.20, 294.40, IN(1.0, 1.08)),
    shot("mar_03", 294.40, 297.60, IN(1.0, 1.08)),                 # colour changes with the seasons
    shot("mar_14", 297.60, 302.80, IN(1.0, 1.10)),                 # only by small boat
    shot("mar_04", 302.80, 306.00, IN(1.0, 1.10)),                 # light off turquoise water
    shot("mar_08", 306.00, 309.30, IN(1.0, 1.08)),
    shot("mar_13", 309.30, 311.70, IN(1.0, 1.08)),                 # a journey of its own
    shot("mar_12", 311.70, 316.50, PAN(0.4, 0.6, 1.1)),            # long drive through Patagonia
    shot("mar_11", 316.50, 321.50, IN(1.0, 1.10)),                 # the lake is so big
    shot("mar_10", 321.50, 325.825, OUT(1.1, 1.0)),                # never this far south
], badge="6,000 YEARS OF WAVES")

# ---------------- 06_jellyfish ----------------
place("#5", "JELLYFISH LAKE", "PALAU", "frames_jellyfish", 325.825, 328.95, 332.45, 384.40, [
    shot("jel_14", 332.45, 334.50, IN(1.0, 1.08)),                 # jungle-covered islands
    shot("jel_01", 334.50, 336.80, IN(1.0, 1.08)),                 # a lake full of jellyfish
    shot("jel_03", 336.80, 341.70, IN(1.0, 1.12)),                 # millions, golden jellyfish
    shot("jel_13", 341.70, 346.60, IN(1.0, 1.10)),                 # people swim among them
    shot("jel_06", 346.60, 349.70, IN(1.0, 1.10)),                 # algae inside their bodies
    shot("jel_07", 349.70, 352.90, IN(1.0, 1.08)),                 # sunlight into food
    shot("jel_02", 352.90, 358.20, PAN(0.4, 0.6, 1.1)),            # the swarm follows the sun
    shot("jel_17", 358.20, 363.70, IN(1.0, 1.10)),                 # 2016 drought, El Nino
    shot("jel_09", 363.70, 368.70, IN(1.0, 1.08)),                 # the jellyfish vanished
    shot("jel_12", 368.70, 370.70, IN(1.0, 1.08)),                 # scientists watched
    shot("jel_08", 370.70, 374.20, IN(1.0, 1.10)),                 # the jellyfish returned
    shot("jel_05", 374.20, 377.50, IN(1.0, 1.10)),                 # millions once more
    shot("jel_04", 377.50, 381.50, IN(1.0, 1.08)),                 # snorkels only
    shot("jel_18", 381.50, 385.20, OUT(1.1, 1.0)),
], badge="MILLIONS OF JELLYFISH")

# ---------------- 07_hidden_beach ----------------
place("#4", "HIDDEN BEACH", "MARIETA ISLANDS, MEXICO", "frames_hidden_beach", 385.20, 388.325, 391.825, 441.575, [
    shot("hid_12", 391.825, 394.60, PAN(0.4, 0.6, 1.1)),           # the Marieta Islands
    shot("hid_09", 394.60, 397.60, IN(1.0, 1.08)),                 # empty in the early 1900s
    shot("hid_10", 397.60, 402.60, IN(1.0, 1.10)),                 # target practice
    shot("hid_11", 402.60, 406.10, IN(1.0, 1.10)),                 # bombs tore at the rock
    shot("hid_02", 406.10, 410.90, IN(1.0, 1.10)),                 # one of the strangest beaches
    shot("hid_08", 410.90, 416.00, TILT(0.35, 0.6, 1.1)),          # a round hole, a beach at the bottom
    shot("hid_01", 416.00, 418.00, IN(1.0, 1.08)),                 # open to the sky
    shot("hid_04", 418.00, 420.70, IN(1.0, 1.08)),                 # nobody knows how it formed
    shot("hid_14", 420.70, 423.60, IN(1.0, 1.08)),                 # from the open sea
    shot("hid_13", 423.60, 426.50, IN(1.0, 1.10)),                 # a short tunnel
    shot("hid_03", 426.50, 429.50, IN(1.0, 1.08)),                 # too many tourists
    shot("hid_06", 429.50, 433.60, IN(1.0, 1.10)),                 # closed in 2016
    shot("hid_07", 433.60, 438.40, IN(1.0, 1.10)),                 # about a hundred a day
    shot("hid_05", 438.40, 442.375, OUT(1.1, 1.0)),                # permit, guide, good lungs
], badge="~100 VISITORS A DAY")

# ---------------- 08_mosquito_bay ----------------
place("#3", "MOSQUITO BAY", "VIEQUES, PUERTO RICO", "frames_mosquito_bay", 442.375, 445.50, 449.00, 501.80, [
    shot("mos_03", 449.00, 451.40, IN(1.0, 1.08)),                 # a bay that glows
    shot("mos_12", 451.40, 455.60, PAN(0.4, 0.6, 1.1)),            # lights up blue and green
    shot("mos_13", 455.60, 458.70, IN(1.0, 1.10)),                 # a paddle, a fish, a raindrop
    shot("mos_02", 458.70, 464.50, IN(1.0, 1.10)),                 # the brightest bioluminescent bay
    shot("mos_15", 464.50, 471.00, PAN(0.4, 0.6, 1.12)),           # 700,000 organisms per gallon
    shot("mos_08", 471.00, 477.40, IN(1.0, 1.12)),                 # Vieques
    shot("mos_10", 477.40, 483.90, PAN(0.4, 0.6, 1.1)),            # bombing stopped in 2003
    shot("mos_01", 483.90, 490.40, IN(1.0, 1.10)),                 # a protected nature reserve
    shot("mos_04", 490.40, 496.00, IN(1.0, 1.12)),                 # kayak or electric boat
    shot("mos_14", 496.00, 498.20, IN(1.0, 1.08)),                 # the moon
    shot("mos_05c", 498.20, 502.60, OUT(1.1, 1.0)),                # dip your hand, it lights up
], badge="BRIGHTEST GLOWING BAY")

# ---------------- 09_cano_cristales ----------------
place("#2", "CAÑO CRISTALES", "META, COLOMBIA", "frames_cano_cristales", 502.60, 505.725, 509.225, 559.525, [
    shot("can_03", 509.225, 514.60, IN(1.0, 1.10)),                # a river that turns into a rainbow
    shot("can_01", 514.60, 518.50, IN(1.0, 1.10)),                 # red, yellow, green, blue, black
    shot("can_09", 518.50, 523.50, PAN(0.4, 0.6, 1.1)),            # river of five colours
    shot("can_05", 523.50, 527.30, IN(1.0, 1.10)),                 # a water plant on the riverbed
    shot("can_07", 527.30, 531.00, IN(1.0, 1.08)),                 # deep, vivid red
    shot("can_02", 531.00, 534.20, IN(1.0, 1.08)),
    shot("can_14", 534.20, 539.20, IN(1.0, 1.10)),                 # yellow sand, green algae, black rock
    shot("can_12", 539.20, 542.70, IN(1.0, 1.08)),                 # almost nobody could see it
    shot("can_13", 542.70, 548.20, IN(1.0, 1.10)),                 # armed conflict
    shot("can_10", 548.20, 552.00, IN(1.0, 1.10)),                 # reopened in the late 2000s
    shot("can_11", 552.00, 556.70, PAN(0.4, 0.6, 1.1)),            # by small plane
    shot("can_16", 556.70, 560.325, OUT(1.1, 1.0)),                # visitors controlled
], badge="RIVER OF FIVE COLORS")

# ---------------- 10_son_doong ----------------
place("#1", "HANG SON DOONG", "QUANG BINH, VIETNAM", "frames_son_doong", 560.325, 563.45, 566.95, 629.375, [
    shot("son_15", 566.95, 569.50, IN(1.0, 1.10)),                 # the jungle of central Vietnam (park map)
    shot("son_09", 569.50, 575.20, IN(1.0, 1.10)),                 # he found the entrance
    shot("son_08", 575.20, 580.10, PAN(0.4, 0.6, 1.1)),            # a river roaring inside
    shot("son_04", 580.10, 584.90, IN(1.0, 1.08)),                 # he couldn't find it again
    shot("son_12", 584.90, 587.50, IN(1.0, 1.08)),                 # lost for almost 20 years
    shot("son_07", 587.50, 592.50, IN(1.0, 1.10)),                 # 2008, the entrance once more
    shot("son_10", 592.50, 597.90, IN(1.0, 1.10)),                 # 2009 expedition (camp)
    shot("son_03", 597.90, 603.50, IN(1.0, 1.10)),                 # one of the largest passages
    shot("son_06", 603.50, 606.60, IN(1.0, 1.08)),                 # fits a skyscraper
    shot("son_05", 606.60, 611.20, IN(1.0, 1.10, (0.5, 0.45))),    # sunlight pours in
    shot("son_02", 611.20, 618.20, TILT(0.35, 0.6, 1.1)),          # a jungle inside the cave
    shot("son_01", 618.20, 630.975, IN(1.0, 1.18, (0.5, 0.5), (0.45, 0.4))),  # a whole hidden world
], badge="JUNGLE INSIDE A CAVE")

# ---------------- 11_outro ----------------
shots.append(shot("hil_01", 630.975, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 631.5, "t1": DURATION, "fin": 1.2, "fout": 0.6})

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
