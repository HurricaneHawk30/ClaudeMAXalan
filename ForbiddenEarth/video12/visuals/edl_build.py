"""Edit decision list for video12 "10 Places No Human Has Ever Set Foot On" (10:53.3).
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 18 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 653.3

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

# ---------------- 00_hook (0:00-0:26.475) ----------------
shots += [
    shot("gan_03",  0.00,  3.60, IN(1.0, 1.08), 0.3, xin=0),     # we have climbed Everest
    shot("thw_03",  3.60,  8.00, IN(1.0, 1.10), 0.25),           # places no human has reached
    shot("mac_14",  8.00, 11.70, IN(1.0, 1.10), 0.25),           # a summit a king protected
    shot("taa_07", 11.70, 16.40, IN(1.0, 1.12), 0.25),           # a hole in the sea
    shot("gam_08", 16.40, 20.80, IN(1.0, 1.10), 0.25),           # a range as big as the Alps
    shot("dee_04", 20.80, 26.475, IN(1.0, 1.12), 0.3, xout=0.5), # number one
]
overlays.append({"type": "brand", "t0": 22.00, "t1": 26.20, "fin": 0.9, "fout": 0.5})

# ---------------- 01_hranice ----------------
place("#10", "HRANICE ABYSS", "CZECH REPUBLIC", "frames_hranice", 26.475, 29.60, 33.10, 95.275, [
    shot("hra_08", 33.10, 37.10, TILT(0.3, 0.6, 1.05)),            # a crack in the limestone
    shot("hra_11", 37.10, 42.00, IN(1.0, 1.12)),                   # a green lake 70 m down
    shot("hra_02", 42.00, 47.10, IN(1.0, 1.10)),                   # deepest flooded cave
    shot("hra_13", 47.10, 53.00, TILT(0.3, 0.65, 1.05)),           # divers went down
    shot("hra_03", 53.00, 58.00, IN(1.0, 1.10)),                   # Starnawski, 200 m
    shot("hra_07", 58.00, 63.00, PAN(0.35, 0.65, 1.1)),
    shot("hra_09", 63.00, 65.90, IN(1.0, 1.08)),                   # robots (gas warning in the cave)
    shot("hra_04", 65.90, 70.80, TILT(0.6, 0.3, 1.05)),            # 2016, 400 m
    shot("hra_06", 70.80, 75.60, IN(1.0, 1.10)),
    shot("hra_12", 75.60, 81.80, IN(1.0, 1.12)),                   # 2022, 450 m
    shot("hra_05", 81.80, 85.80, TILT(0.3, 0.6, 1.0)),             # no bottom
    shot("hra_10", 85.80, 90.20, IN(1.0, 1.08)),                   # maybe a kilometer
    shot("hra_01", 90.20, 96.075, OUT(1.1, 1.0)),                  # nobody knows, no end
], badge="NO BOTTOM FOUND")

# ---------------- 02_machapuchare ----------------
place("#9", "MACHAPUCHARE", "NEPAL", "frames_machapuchare", 96.075, 99.20, 102.70, 155.775, [
    shot("mac_12", 102.70, 107.40, PAN(0.35, 0.65, 1.1)),          # above Pokhara, the fish tail
    shot("mac_08", 107.40, 111.30, IN(1.0, 1.10)),                 # nearly 7,000 m
    shot("mac_06", 111.30, 115.60, IN(1.0, 1.10)),                 # sacred to Shiva
    shot("mac_11", 115.60, 120.40, IN(1.0, 1.08)),                 # 1957, a British team
    shot("mac_03", 120.40, 123.50, IN(1.0, 1.10)),                 # the king's condition
    shot("mac_13", 123.50, 128.60, PAN(0.6, 0.75, 1.15)),          # not step on the summit
    shot("mac_02", 128.60, 137.00, IN(1.0, 1.15, (0.5, 0.35))),    # 50 m below the top
    shot("mac_09", 137.00, 141.70, IN(1.0, 1.08)),                 # turned around
    shot("mac_10", 141.70, 144.40, IN(1.0, 1.08)),                 # Nepal closed the mountain
    shot("mac_04", 144.40, 147.90, IN(1.0, 1.08)),                 # no permits
    shot("mac_15", 147.90, 152.70, PAN(0.35, 0.6, 1.1)),           # trekkers look at it
    shot("mac_01", 152.70, 156.575, OUT(1.1, 1.0)),                # no human on the summit
], badge="NEVER SUMMITED")

# ---------------- 03_taam_ja ----------------
place("#8", "TAAM JA' BLUE HOLE", "MEXICO", "frames_taam_ja", 156.575, 159.70, 163.20, 216.35, [
    shot("taa_01", 163.20, 166.80, IN(1.0, 1.15)),                 # a bay near Belize
    shot("taa_02", 166.80, 173.00, IN(1.0, 1.25, (0.5, 0.5), (0.75, 0.45))),  # a dark circle
    shot("taa_06", 173.00, 176.40, IN(1.0, 1.08)),                 # an understatement
    shot("taa_03", 176.40, 184.80, IN(1.0, 1.12)),                 # 2021 sonar, 275 m
    inset("taa_04b", 184.80, 188.40),                              # swallowed the echoes
    shot("taa_10", 188.40, 193.30, IN(1.0, 1.08)),                 # December 2023, a cable
    inset("taa_09", 193.30, 196.70),                               # 500 m, ran out
    inset("taa_04e", 196.70, 200.50),                              # 420 m, no bottom
    shot("taa_05", 200.50, 204.50, PAN(0.35, 0.65, 1.1)),
    shot("taa_07", 204.50, 208.60, IN(1.0, 1.12)),                 # the deepest blue hole
    shot("taa_08", 208.60, 217.15, OUT(1.12, 1.0)),                # caves, a maze; no one has seen
], badge="420 M — STILL NO BOTTOM")

# ---------------- 04_thwaites ----------------
place("#7", "THWAITES GLACIER", "ANTARCTICA", "frames_thwaites", 217.15, 220.275, 223.775, 277.60, [
    shot("thw_02", 223.775, 227.10, IN(1.0, 1.10)),                # the size of Florida
    shot("thw_07", 227.10, 232.40, IN(1.0, 1.10)),                 # the Doomsday Glacier
    shot("thw_08", 232.40, 237.00, IN(1.0, 1.08)),                 # sea levels
    shot("thw_04", 237.00, 241.20, PAN(0.35, 0.65, 1.1)),          # a place no one can visit
    inset("thw_10", 241.20, 249.10),                               # the grounding line
    shot("thw_11", 249.10, 259.40, PAN(0.3, 0.7, 1.12)),           # 2020, a 600 m hole, Icefin
    shot("thw_05", 259.40, 264.10, IN(1.0, 1.10)),                 # first pictures
    inset("thw_06", 264.10, 269.90),                               # a staircase
    shot("thw_09", 269.90, 273.30, IN(1.0, 1.10)),                 # cracks
    shot("thw_01", 273.30, 278.40, OUT(1.12, 1.0)),                # only a robot
], badge="ONLY A ROBOT HAS BEEN HERE")

# ---------------- 05_kawagarbo ----------------
place("#6", "KAWAGARBO", "CHINA", "frames_kawagarbo", 278.40, 281.525, 285.025, 336.30, [
    shot("kaw_07", 285.025, 289.00, IN(1.0, 1.10)),                # Yunnan, Tibet
    shot("kaw_01", 289.00, 297.40, PAN(0.35, 0.65, 1.12)),         # 6,740 m, sacred
    shot("kaw_05", 297.40, 300.10, IN(1.0, 1.08)),                 # a warrior god (stupa)
    shot("kaw_03", 300.10, 306.80, IN(1.0, 1.12)),                 # late 1980s, climbers
    shot("kaw_11", 306.80, 310.00, IN(1.0, 1.08)),                 # local people protested
    shot("kaw_04", 310.00, 317.20, TILT(0.3, 0.7, 1.05)),          # January 1991, an avalanche
    shot("kaw_08", 317.20, 321.10, IN(1.0, 1.08)),                 # 17 lost
    shot("kaw_02", 321.10, 325.60, IN(1.0, 1.10)),                 # the mountain's anger
    shot("kaw_09", 325.60, 331.60, IN(1.0, 1.08)),                 # 2001, a ban
    shot("kaw_06", 331.60, 337.10, OUT(1.12, 1.0)),                # never reached
], badge="FORBIDDEN SUMMIT")

# ---------------- 06_denman ----------------
place("#5", "DENMAN CANYON", "ANTARCTICA", "frames_denman", 337.10, 340.225, 343.725, 388.90, [
    shot("den_02", 343.725, 345.90, IN(1.0, 1.08)),                # the Dead Sea shore
    shot("den_06", 345.90, 349.00, IN(1.0, 1.08)),                 # 400 m below sea level
    shot("den_09", 349.00, 352.30, IN(1.0, 1.08)),                 # not the lowest
    shot("den_07", 352.30, 359.40, IN(1.0, 1.12)),                 # 2019, a new map
    shot("den_01", 359.40, 368.60, PAN(0.3, 0.6, 1.12)),           # a canyon 3,500 m below
    shot("den_dia", 368.60, 372.70, IN(1.0, 1.05)),                # eight times deeper
    inset("den_03", 372.70, 378.10),                               # deepest point on land
    shot("den_05", 378.10, 382.90, IN(1.0, 1.10)),                 # filled with ice
    inset("den_08", 382.90, 386.00),                               # radar, satellites
    shot("den_04", 386.00, 389.70, OUT(1.1, 1.0)),
], badge="3,500 M BELOW SEA LEVEL")

# ---------------- 07_zacaton ----------------
place("#4", "EL ZACATÓN", "MEXICO", "frames_zacaton", 389.70, 392.825, 396.325, 451.125, [
    shot("zac_02", 396.325, 403.30, PAN(0.3, 0.6, 1.1)),           # a round pool on a ranch, sulfur
    shot("zac_01", 403.30, 412.30, TILT(0.25, 0.6, 1.0)),          # one of the deepest sinkholes; divers
    shot("zac_dia", 412.30, 425.60, IN(1.0, 1.10)),                # 1994; Bowden, 282 m
    shot("zac_01b", 425.60, 429.80, IN(1.0, 1.10)),                # Exley never came back
    inset("zac_03", 429.80, 434.10),                               # 2007, a NASA robot
    inset("zac_04", 434.10, 440.80),                               # Europa
    inset("zac_02b", 440.80, 447.60),                              # the bottom, 318 m
    shot("zac_03b", 447.60, 451.925, OUT(1.1, 1.0)),               # only a machine touched it
], badge="ROBOT ONLY")

# ---------------- 08_gamburtsev ----------------
place("#3", "GAMBURTSEV MOUNTAINS", "ANTARCTICA", "frames_gamburtsev", 451.925, 455.05, 458.55, 512.325, [
    shot("gam_02", 458.55, 462.90, IN(1.0, 1.08)),                 # 1958, Soviet scientists
    shot("gam_10", 462.90, 469.20, IN(1.0, 1.10)),                 # explosions, echoes
    shot("gam_07", 469.20, 471.60, IN(1.0, 1.08)),                 # something wrong
    shot("gam_08", 471.60, 475.10, IN(1.0, 1.10)),                 # mountains
    shot("gam_05", 475.10, 481.40, IN(1.0, 1.10)),                 # radar aircraft
    inset("gam_03", 481.40, 485.50),                               # 1,000 km
    shot("gam_09", 485.50, 490.10, IN(1.0, 1.08)),                 # peaks 3 km
    shot("gam_04", 490.10, 494.00, PAN(0.35, 0.65, 1.1)),          # the size of the Alps
    inset("gam_11", 494.00, 499.10),                               # buried
    inset("gam_01", 499.10, 503.00),                               # peaks under the ice
    shot("den_07", 503.00, 509.30, IN(1.0, 1.12, (0.5, 0.5), (0.6, 0.45))),  # valleys
    inset("den_08", 509.30, 513.125),                              # known only from echoes
], badge="MOUNTAINS NO ONE HAS SEEN")

# ---------------- 09_gangkhar ----------------
place("#2", "GANGKHAR PUENSUM", "BHUTAN", "frames_gangkhar", 513.125, 516.25, 519.75, 574.075, [
    shot("gan_07", 519.75, 523.90, IN(1.0, 1.12)),                 # the highest unclimbed mountain
    shot("gan_01", 523.90, 529.00, TILT(0.25, 0.55, 1.05)),        # 7,570 m
    inset("gan_10", 529.00, 533.90),                               # the name
    inset("gan_08", 533.90, 538.50),                               # Bhutan opened its mountains
    shot("gan_03", 538.50, 543.80, IN(1.0, 1.10)),                 # mid-1980s, four expeditions
    shot("gan_09", 543.80, 549.80, PAN(0.3, 0.6, 1.12)),           # storms, wrong maps
    shot("gan_05", 549.80, 556.00, IN(1.0, 1.08)),                 # peaks above 6,000 m closed
    shot("gan_04", 556.00, 560.70, IN(1.0, 1.10, (0.6, 0.4))),     # 1994
    shot("gan_11", 560.70, 565.50, IN(1.0, 1.08)),                 # 2003, a total ban
    inset("gan_09b", 565.50, 569.40),                              # Everest has queues
    shot("gan_02", 569.40, 574.875, OUT(1.12, 1.0)),               # never a footstep
], badge="HIGHEST UNCLIMBED PEAK")

# ---------------- 10_deep_seafloor ----------------
place("#1", "THE DEEP SEAFLOOR", "EARTH'S OCEANS", "frames_deep_seafloor", 574.875, 578.00, 581.50, 636.65, [
    shot("dee_20", 581.50, 587.30, IN(1.0, 1.12)),                 # not a mountain; most of the planet
    shot("dee_dia1", 587.30, 592.60, IN(1.0, 1.05)),               # below 200 m sunlight fades
    shot("dee_07", 592.60, 596.40, IN(1.0, 1.08)),                 # two-thirds of the surface
    shot("dee_04", 596.40, 599.80, IN(1.0, 1.10)),                 # bigger than the continents
    shot("dee_05", 599.80, 605.50, IN(1.0, 1.10)),                 # 2025, dives counted
    shot("dee_06", 605.50, 611.70, IN(1.0, 1.10)),                 # 40,000 since 1958
    shot("dee_dia2", 611.70, 626.70, IN(1.0, 1.25)),               # 0.001 percent, Rhode Island
    inset("dee_08", 626.70, 632.30),                               # mountains, vents, creatures
    shot("dee_04b", 632.30, 637.45, OUT(1.1, 1.0)),                # waiting in the dark
], badge="0.001% SEEN")

# ---------------- 11_outro ----------------
shots.append(shot("mac_01", 637.45, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 638.0, "t1": DURATION, "fin": 1.2, "fout": 0.6})

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
