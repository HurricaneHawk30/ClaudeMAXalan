"""Edit decision list for video09 "Beautiful Places That Can Kill You" (11:25.95).
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 15 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 685.95

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

# ---------------- 00_hook (0:00-0:30.35) ----------------
shots += [
    shot("han_04",   0.00,  4.30, IN(1.0, 1.08), 0.3, xin=0),     # so beautiful that people forget to be afraid
    shot("han_01",   4.30,  7.70, IN(1.0, 1.12, (0.47, 0.6)), 0.25), # a sign that counts the dead
    shot("dev_03",   7.70, 11.60, IN(1.0, 1.10), 0.25), # a pool on the edge of a waterfall
    shot("man_14",  11.60, 14.40, IN(1.0, 1.08), 0.25),           # a tree that seems to grow apples
    shot("yel_01",  14.40, 17.70, IN(1.0, 1.10), 0.25),           # visitors from all over the world
    shot("ice_01",  17.70, 20.40, IN(1.0, 1.08), 0.25),           # a way to kill you
    shot("blu_01",  20.40, 23.80, IN(1.0, 1.10), 0.25),           # a blue hole in the Red Sea
    shot("blu_04",  23.80, 30.35, IN(1.0, 1.10), 0.3, xout=0.5),  # an underwater arch
]
overlays.append({"type": "brand", "t0": 26.40, "t1": 30.05, "fin": 0.9, "fout": 0.5})

# ---------------- 01_manchineel ----------------
place("#10", "MANCHINEEL TREE", "THE CARIBBEAN", "frames_manchineel", 30.35, 33.475, 36.975, 95.475, [
    shot("man_10", 36.975, 41.50, IN(1.0, 1.10)),                  # a tree on the beach
    shot("man_09", 41.50, 45.00, IN(1.0, 1.08)),                   # wide green leaves, shade
    shot("man_01", 45.00, 48.50, IN(1.0, 1.12)),                   # fruit like green apples
    shot("man_07", 48.50, 52.50, PAN(0.4, 0.6, 1.1)),              # the little apple of death
    shot("man_05", 52.50, 55.30, IN(1.0, 1.08)),                   # every part is poisonous
    shot("man_02", 55.30, 62.90, PAN(0.35, 0.65, 1.12)),           # sap, rain under the tree
    shot("man_08", 62.90, 66.10, IN(1.0, 1.08)),                   # burn its wood
    shot("man_06", 66.10, 72.70, TILT(0.35, 0.6, 1.0)),            # 1999, one bite of the fruit
    shot("man_04", 72.70, 78.60, IN(1.0, 1.10)),                   # barely swallow
    shot("man_11", 78.60, 88.00, IN(1.0, 1.15, (0.5, 0.45))),      # Ponce de Leon, 1521 (old plate)
    shot("man_03", 88.00, 93.20, IN(1.0, 1.12)),                   # a red mark on the trunk
    shot("man_13", 93.20, 96.275, OUT(1.1, 1.0)),                  # don't even sit here
], badge="LITTLE APPLE OF DEATH")

# ---------------- 02_natron ----------------
place("#9", "LAKE NATRON", "TANZANIA", "frames_natron", 96.275, 99.40, 102.90, 152.35, [
    shot("nat_02", 102.90, 108.10, TILT(0.35, 0.6, 1.0)),          # a lake that can turn blood red
    shot("nat_13", 108.10, 113.60, IN(1.0, 1.10)),                 # salt-loving microbes
    shot("nat_05", 113.60, 117.80, IN(1.0, 1.10)),                 # hot springs, volcano
    shot("nat_07", 117.80, 124.70, PAN(0.4, 0.6, 1.1)),            # caustic water, the shallows
    shot("nat_10", 124.70, 129.40, IN(1.0, 1.08)),                 # burns skin and eyes
    shot("nat_03", 129.40, 133.20, IN(1.0, 1.10)),                 # birds and bats don't rot
    shot("nat_08", 133.20, 140.60, IN(1.0, 1.12)),                 # turned to stone (from orbit)
    shot("nat_15", 140.60, 143.90, IN(1.0, 1.08)),                 # also a nursery
    shot("nat_06", 143.90, 148.20, PAN(0.4, 0.6, 1.1)),            # three quarters of lesser flamingos
    shot("nat_11", 148.20, 153.15, OUT(1.1, 1.0)),                 # predators can't follow
], badge="AS CAUSTIC AS AMMONIA")

# ---------------- 03_hanakapiai ----------------
place("#8", "HANAKAPIAI BEACH", "KAUAI, HAWAII", "frames_hanakapiai", 153.15, 156.275, 159.775, 214.425, [
    shot("han_08", 159.775, 162.60, IN(1.0, 1.08)),                # the Na Pali Coast
    shot("han_14", 162.60, 166.20, PAN(0.4, 0.6, 1.1)),            # cliffs into the Pacific
    shot("han_06", 166.20, 171.00, TILT(0.6, 0.4, 1.0)),           # two miles of mud and jungle
    shot("han_03", 171.00, 175.80, IN(1.0, 1.10)),                 # no road, no lifeguard
    shot("han_02", 175.80, 180.60, IN(1.0, 1.10, (0.47, 0.55))),   # the sign
    shot("han_01", 180.60, 190.00, IN(1.0, 1.45, (0.47, 0.55), (0.46, 0.66))),  # tally marks
    shot("han_11", 190.00, 193.30, IN(1.0, 1.08)),                 # by 2014, more than eighty
    shot("han_07", 193.30, 198.50, IN(1.0, 1.10)),                 # researchers count fewer
    shot("han_13", 198.50, 201.00, IN(1.0, 1.08)),                 # thirty since 1970
    shot("han_09", 201.00, 203.00, IN(1.0, 1.08)),                 # the danger is real
    shot("han_05", 203.00, 207.00, IN(1.0, 1.10)),                 # no reef to break the waves
    shot("han_10", 207.00, 211.50, PAN(0.4, 0.6, 1.1)),            # a rip current
    shot("han_12", 211.50, 215.225, OUT(1.1, 1.0)),                # miles away
], badge="80+ TALLY MARKS")

# ---------------- 04_hua ----------------
place("#7", "MOUNT HUA", "SHAANXI, CHINA", "frames_hua", 215.225, 218.35, 221.85, 278.875, [
    shot("hua_05", 221.85, 223.50, IN(1.0, 1.08)),                 # five sacred mountains
    shot("hua_09", 223.50, 226.40, IN(1.0, 1.08)),                 # Taoist temples
    shot("hua_17", 226.40, 229.20, IN(1.0, 1.08)),                 # twisted pines, granite peaks
    shot("hua_03", 229.20, 234.50, TILT(0.35, 0.6, 1.0)),          # out of the clouds
    shot("hua_14", 234.50, 237.60, IN(1.0, 1.08)),                 # the Plank Walk
    shot("hua_06", 237.60, 240.90, IN(1.0, 1.08)),                 # the South Peak
    shot("hua_04", 240.90, 245.60, TILT(0.3, 0.7, 1.0)),           # boards pinned to a sheer cliff
    shot("hua_01", 245.60, 249.80, PAN(0.4, 0.6, 1.1)),            # thirty centimetres wide
    shot("hua_11", 249.80, 253.20, IN(1.0, 1.10)),                 # nothing but air
    shot("hua_10", 253.20, 257.70, IN(1.0, 1.08)),                 # built 700 years ago
    shot("hua_18", 257.70, 262.20, IN(1.0, 1.10)),                 # to meditate far from the world
    shot("hua_07", 262.20, 267.70, PAN(0.4, 0.6, 1.1)),            # a harness clipped to a chain
    shot("hua_16", 267.70, 272.20, TILT(0.3, 0.6, 1.0)),           # faces to the stone
    shot("hua_02", 272.20, 276.60, IN(1.0, 1.08)),                 # rumours
    shot("hua_12", 276.60, 279.675, OUT(1.1, 1.0)),                # no official numbers
], badge="30 CM WIDE")

# ---------------- 05_devils_pool ----------------
place("#6", "DEVIL'S POOL", "VICTORIA FALLS, ZAMBIA", "frames_devils_pool", 279.675, 282.80, 286.30, 344.825, [
    shot("dev_09", 286.30, 291.90, IN(1.0, 1.10)),                 # one of the largest waterfalls
    shot("dev_06", 291.90, 298.50, PAN(0.4, 0.6, 1.1)),            # the rainy season
    shot("dev_08", 298.50, 304.60, TILT(0.6, 0.35, 1.0)),          # the smoke that thunders
    shot("dev_07", 304.60, 310.80, IN(1.0, 1.10)),                 # the Zambezi runs low
    shot("dev_11", 310.80, 314.20, IN(1.0, 1.10)),                 # next to Livingstone Island
    shot("dev_03", 314.20, 317.20, IN(1.0, 1.10)),                 # a natural rock pool at the lip
    shot("dev_10", 317.20, 323.00, IN(1.0, 1.10)),                 # a drop of more than 100 m
    shot("dev_14", 323.00, 328.20, IN(1.0, 1.08)),                 # an underwater rock wall
    shot("dev_15", 328.20, 333.20, IN(1.0, 1.10)),                 # guides hold swimmers
    shot("dev_13", 333.20, 338.90, IN(1.0, 1.10)),                 # only when the water is low
    shot("dev_05", 338.90, 345.625, OUT(1.1, 1.0)),                # the whole Zambezi goes over
], badge="100+ M DROP")

# ---------------- 06_ice_caves ----------------
place("#5", "ICE CAVES", "VATNAJÖKULL, ICELAND", "frames_ice_caves", 345.625, 348.75, 352.25, 414.90, [
    shot("ice_08", 352.25, 358.20, IN(1.0, 1.10)),                 # meltwater carves tunnels
    shot("ice_01", 358.20, 362.60, IN(1.0, 1.10)),                 # every shade of blue
    shot("ice_09", 362.60, 367.10, PAN(0.4, 0.6, 1.1)),            # air bubbles, hundreds of years
    shot("ice_03", 367.10, 369.50, IN(1.0, 1.08)),                 # not permanent
    shot("ice_11", 369.50, 373.10, IN(1.0, 1.08)),                 # some vanish completely
    shot("ice_04", 373.10, 376.30, IN(1.0, 1.08)),                 # winter, hard and stable
    shot("ice_13", 376.30, 382.40, IN(1.0, 1.10)),                 # summer, melting
    shot("ice_02", 382.40, 389.10, IN(1.0, 1.10)),                 # 2017, very high risk
    shot("ice_06", 389.10, 396.60, PAN(0.4, 0.6, 1.1)),            # August 2024, southeastern Iceland
    shot("ice_12", 396.60, 403.80, IN(1.0, 1.08)),                 # an ice arch collapsed
    shot("ice_14", 403.80, 410.90, IN(1.0, 1.10)),                 # stricter rules
    shot("ice_05", 410.90, 415.70, OUT(1.1, 1.0)),                 # still beautiful, still melting
], badge="MELTS EVERY SUMMER")

# ---------------- 07_antelope ----------------
place("#4", "ANTELOPE CANYON", "PAGE, ARIZONA", "frames_antelope", 415.70, 418.825, 422.325, 479.275, [
    shot("ant_03", 422.325, 423.90, IN(1.0, 1.08)),                # Navajo land near Page
    shot("ant_12", 423.90, 427.50, IN(1.0, 1.08)),                 # cracks in the desert
    shot("ant_01", 427.50, 431.00, IN(1.0, 1.10)),                 # red sandstone curves
    shot("ant_08", 431.00, 434.40, TILT(0.6, 0.4, 1.0)),           # waves frozen in stone
    shot("ant_02", 434.40, 440.50, IN(1.0, 1.10)),                 # beams of sunlight
    shot("ant_05", 440.50, 442.90, IN(1.0, 1.08)),                 # carved by water
    shot("ant_10", 442.90, 449.60, IN(1.0, 1.10)),                 # flash floods
    shot("ant_07", 449.60, 455.10, IN(1.0, 1.10)),                 # August 12, 1997, the sky looked calm
    shot("ant_06", 455.10, 460.10, IN(1.0, 1.10)),                 # a thunderstorm upstream
    shot("ant_11", 460.10, 463.30, IN(1.0, 1.08)),                 # a wall of water
    shot("ant_13", 463.30, 468.50, IN(1.0, 1.08)),                 # eleven tourists
    shot("ant_09", 468.50, 473.80, IN(1.0, 1.10)),                 # Navajo-licensed guide
    shot("ant_14", 473.80, 480.075, OUT(1.1, 1.0)),                # metal stairs
], badge="FLASH FLOOD, 1997")

# ---------------- 08_jacobs_well ----------------
place("#3", "JACOB'S WELL", "WIMBERLEY, TEXAS", "frames_jacobs_well", 480.075, 483.20, 486.70, 543.35, [
    shot("jac_02", 486.70, 491.70, PAN(0.4, 0.6, 1.1)),            # a creek over flat limestone
    shot("jac_04", 491.70, 500.70, IN(1.0, 1.15, (0.5, 0.55))),    # a round hole, a window into the earth
    shot("jac_03", 500.70, 506.50, TILT(0.3, 0.6, 1.0)),           # a well from Bible times
    shot("jac_05", 506.50, 512.30, IN(1.0, 1.10)),                 # swimmers jump in
    shot("jac_06", 512.30, 521.00, TILT(0.3, 0.75, 1.0)),          # nine metres down, chambers
    shot("jac_07", 521.00, 532.00, IN(1.0, 1.15, (0.5, 0.55))),    # eight divers; 1980 grate
    shot("jac_04c", 532.00, 544.15, IN(1.0, 1.12)),                # only trained cave divers (detail)
], badge="8+ DIVERS LOST")

# ---------------- 09_yellowstone ----------------
place("#2", "YELLOWSTONE", "WYOMING, USA", "frames_yellowstone", 544.15, 547.275, 550.775, 601.425, [
    shot("yel_06", 550.775, 557.40, IN(1.0, 1.10)),                # a supervolcano, geysers
    shot("yel_03", 557.40, 563.10, TILT(0.35, 0.6, 1.0)),          # Grand Prismatic
    shot("yel_09", 563.10, 567.90, IN(1.0, 1.10)),                 # deep blue centre
    shot("yel_14", 567.90, 572.70, PAN(0.4, 0.6, 1.1)),            # green, yellow, orange
    shot("yel_05", 572.70, 576.10, IN(1.0, 1.08)),                 # you can't swim in it
    shot("yel_07", 576.10, 579.50, IN(1.0, 1.10)),                 # close to boiling
    shot("yel_13", 579.50, 583.70, IN(1.0, 1.08)),                 # a thin crust
    shot("yel_02", 583.70, 587.40, PAN(0.4, 0.6, 1.1)),            # the boardwalk
    shot("yel_08", 587.40, 593.60, IN(1.0, 1.10)),                 # bears get the headlines
    shot("yel_15", 593.60, 600.40, PAN(0.4, 0.6, 1.1)),            # hot springs killed more; the first rule
    shot("yel_10", 600.40, 602.225, OUT(1.1, 1.0)),                # stay on the boardwalk
], badge="DEADLIER THAN BEARS")

# ---------------- 10_blue_hole ----------------
place("#1", "BLUE HOLE", "DAHAB, EGYPT", "frames_blue_hole", 602.225, 605.35, 608.85, 670.55, [
    shot("blu_07", 608.85, 614.70, PAN(0.35, 0.65, 1.12)),         # coast near Dahab
    shot("blu_02", 614.70, 619.10, IN(1.0, 1.10)),                 # a sinkhole over 100 m deep
    shot("blu_03", 619.10, 622.20, IN(1.0, 1.08)),                 # coral and fish
    shot("blu_09", 622.20, 625.90, IN(1.0, 1.08)),                 # snorkelers float over the edge
    shot("blu_06", 625.90, 629.00, IN(1.0, 1.08)),                 # hidden far below
    shot("blu_14", 629.00, 636.00, IN(1.0, 1.10)),                 # the Arch
    shot("blu_10", 636.00, 640.50, IN(1.0, 1.08)),                 # looks closer
    shot("blu_15", 640.50, 644.10, IN(1.0, 1.08)),                 # 26 metres long
    shot("blu_12", 644.10, 649.20, IN(1.0, 1.10)),                 # nitrogen narcosis
    shot("blu_08", 649.20, 654.60, IN(1.0, 1.10)),                 # fatal mistakes
    shot("blu_13", 654.60, 658.40, IN(1.0, 1.08)),                 # around forty deaths
    shot("blu_04", 658.40, 661.60, IN(1.0, 1.08)),                 # estimates run higher
    shot("blu_05b", 661.60, 665.50, OUT(1.06, 1.0)),               # memorial plaques (blurred)
    shot("blu_01", 665.50, 672.15, OUT(1.1, 1.0)),                 # still looking for the Arch
], badge="THE DIVERS' CEMETERY")

# ---------------- 11_outro ----------------
shots.append(shot("yel_04", 672.15, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 672.7, "t1": DURATION, "fin": 1.2, "fout": 0.6})

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
