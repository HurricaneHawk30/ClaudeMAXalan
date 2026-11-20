"""Edit decision list for video15 "10 Volcanoes That Could Erupt Any Day" (12:51.95).
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 21 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 771.95

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

# ---------------- 00_hook (0:00-0:27.65) ----------------
shots += [
    shot("sak_05",  0.00,  4.90, IN(1.0, 1.08), 0.3, xin=0),     # most volcanoes sleep / these ten don't
    shot("pop_11", 4.90,  9.00, IN(1.0, 1.10), 0.25),          # ash on one of the biggest cities
    shot("nyi_01",  9.00, 12.00, IN(1.0, 1.10), 0.25),           # drained a lake of lava
    shot("rex_01", 12.00, 16.80, IN(1.0, 1.10), 0.25),           # split a town in two
    shot("cam_17", 16.80, 27.65, IN(1.0, 1.12), 0.3, xout=0.5),  # half a million live inside it
]
overlays.append({"type": "brand", "t0": 22.40, "t1": 27.30, "fin": 0.9, "fout": 0.5})

# ---------------- 01_fuji ----------------
place("#10", "MOUNT FUJI", "JAPAN", "frames_fuji", 27.65, 30.775, 34.275, 103.0, [
    shot("fuj_12", 34.275, 40.10, IN(1.0, 1.10)),                  # almost perfect cone
    {"frames": "maps/frames_fuji", "t0": 40.10, "t1": 43.60, "f0": 104, "xin": 0.6, "xout": 0.6},  # Fuji -> Tokyo, 100 km
    shot("fuj_14", 43.60, 49.90, PAN(0.35, 0.65, 1.12)),           # visible from Tokyo, active volcano
    shot("fuj_03", 49.90, 54.50, IN(1.0, 1.10)),                   # last erupted 1707 (Hoei crater)
    shot("fuj_19", 54.50, 58.70, IN(1.0, 1.08)),                   # 49 days after the earthquake
    shot("fuj_09", 58.70, 63.50, IN(1.0, 1.08)),                   # ash fell on Edo
    shot("fuj_01", 63.50, 67.80, IN(1.0, 1.10)),                   # the city we now call Tokyo
    shot("fuj_06", 67.80, 71.60, IN(1.0, 1.10)),                   # 37 million people
    shot("fuj_08", 71.60, 76.00, PAN(0.6, 0.4, 1.12)),             # stop trains
    shot("fuj_n1", 76.00, 80.50, IN(1.0, 1.10)),                   # cut power
    shot("fuj_16", 80.50, 84.60, IN(1.0, 1.08)),                   # block roads
    shot("fuj_02", 84.60, 89.50, IN(1.0, 1.10)),                   # 490 million cubic metres of ash
    shot("fuj_07", 89.50, 94.20, PAN(0.3, 0.7, 1.12)),
    shot("fuj_n2", 94.20, 98.90, IN(1.0, 1.10)),                   # erupted far more often
    shot("fuj_20", 98.90, 103.80, OUT(1.12, 1.0)),                 # long silence
], badge="LAST ERUPTION: 1707")

# ---------------- 02_rainier ----------------
place("#9", "MOUNT RAINIER", "USA", "frames_rainier", 103.8, 106.925, 110.425, 176.125, [
    shot("rai_06", 110.425, 115.00, IN(1.0, 1.10)),                # towers over Seattle
    shot("rai_10", 115.00, 119.40, IN(1.0, 1.08)),                 # more glacier ice
    shot("rai_07", 119.40, 122.40, TILT(0.3, 0.6, 1.1)),           # that ice is the problem
    shot("rai_17", 122.40, 126.00, IN(1.0, 1.10)),                 # melt its glaciers fast
    shot("rai_20", 126.00, 130.00, IN(1.0, 1.10)),                 # weak, rotten rock
    shot("rai_05", 130.00, 135.50, IN(1.0, 1.12, (0.55, 0.55))),   # lahar (USGS hazard map)
    shot("rai_02", 135.50, 139.80, IN(1.0, 1.08)),                 # tens of km in an hour
    shot("rai_18", 139.80, 144.50, IN(1.0, 1.10)),                 # Electron mudflow, Orting
    shot("rai_09", 144.50, 149.30, IN(1.0, 1.08)),
    shot("rai_n1", 149.30, 153.50, IN(1.0, 1.10)),                 # USGS 2018
    shot("rai_12", 153.50, 157.40, PAN(0.4, 0.6, 1.12)),           # third most dangerous
    shot("rai_11", 157.40, 161.80, PAN(0.3, 0.7, 1.2)),            # 80,000 people
    shot("rai_13", 161.80, 165.90, IN(1.0, 1.08)),                 # sensors watching the valleys
    shot("rai_14", 165.90, 170.00, IN(1.0, 1.08)),                 # sirens tested, schoolchildren
    shot("rai_19", 170.00, 172.70, IN(1.0, 1.06)),
    shot("rai_16", 172.70, 176.925, OUT(1.12, 1.0)),               # less than an hour
], badge="80,000 IN LAHAR ZONES")

# ---------------- 03_taal ----------------
place("#8", "TAAL VOLCANO", "PHILIPPINES", "frames_taal", 176.925, 180.05, 183.55, 243.075, [
    shot("tal_01", 183.55, 188.00, IN(1.0, 1.10)),                 # island in a lake, Luzon
    shot("tal_10", 188.00, 192.40, PAN(0.35, 0.65, 1.12)),         # 60 km south of Manila
    shot("tal_03", 192.40, 198.60, IN(1.0, 1.10)),                 # most active, deadliest
    shot("tal_17", 198.60, 204.00, IN(1.0, 1.08)),                 # 1911
    shot("tal_02", 204.00, 208.50, IN(1.0, 1.10)),                 # January 2020, ash 15 km
    shot("tal_11", 208.50, 212.20, IN(1.0, 1.08)),
    shot("tal_05", 212.20, 216.50, IN(1.0, 1.10)),                 # ash fell on Manila
    shot("tal_18", 216.50, 220.50, IN(1.0, 1.08)),                 # people had to leave
    shot("tal_08", 220.50, 226.70, PAN(0.3, 0.7, 1.12)),           # permanent danger zone
    shot("tal_13", 226.70, 232.00, IN(1.0, 1.08)),                 # hasn't calmed down
    shot("tal_07", 232.00, 238.50, IN(1.0, 1.10)),                 # October 2026 ash column
    shot("tal_04", 238.50, 243.875, OUT(1.12, 1.0)),               # crowded region
], badge="15 KM ASH CLOUD")

# ---------------- 04_etna ----------------
place("#7", "MOUNT ETNA", "ITALY", "frames_etna", 243.875, 247.0, 250.5, 306.425, [
    shot("etn_04", 250.50, 255.30, IN(1.0, 1.10)),                 # Europe's most active
    shot("etn_10", 255.30, 260.50, PAN(0.3, 0.6, 1.12)),           # Catania at its foot
    shot("etn_13", 260.50, 266.10, IN(1.0, 1.08)),                 # sweep black ash
    shot("etn_08", 266.10, 272.30, IN(1.0, 1.12, (0.55, 0.5))),    # August 2026, Voragine
    shot("etn_19", 272.30, 276.00, IN(1.0, 1.08)),                 # airport closed
    shot("etn_14", 276.00, 279.00, IN(1.0, 1.08)),
    shot("etn_05", 279.00, 283.50, PAN(0.35, 0.65, 1.12)),         # 700 flights cancelled
    shot("etn_17", 283.50, 287.20, IN(1.0, 1.10)),
    shot("etn_01", 287.20, 291.40, TILT(0.3, 0.7, 1.15)),          # ash drifted to Malta, Libya
    shot("etn_n1", 291.40, 295.50, IN(1.0, 1.10)),                 # erupted again in September
    shot("etn_12", 295.50, 298.90, IN(1.0, 1.08)),                 # never quiet for long
    shot("etn_18", 298.90, 303.00, IN(1.0, 1.08)),                 # watched every hour
    shot("etn_15", 303.00, 307.225, OUT(1.12, 1.0)),               # towns on its slopes
], badge="~700 FLIGHTS CANCELLED")

# ---------------- 05_nyiragongo ----------------
place("#6", "NYIRAGONGO", "DR CONGO", "frames_nyiragongo", 307.225, 310.35, 313.85, 374.125, [
    shot("nyi_14", 313.85, 319.00, IN(1.0, 1.10)),                 # one of the largest lava lakes
    shot("nyi_15", 319.00, 324.50, IN(1.0, 1.10)),                 # boiling pool of molten rock
    shot("nyi_18", 324.50, 328.80, IN(1.0, 1.08)),                 # runny like water
    shot("nyi_10", 328.80, 332.00, IN(1.0, 1.08)),                 # 1977 walls cracked
    shot("nyi_02", 332.00, 335.30, IN(1.0, 1.08)),                 # drained in less than an hour
    shot("nyi_n1", 335.30, 339.00, IN(1.0, 1.10)),                 # 60 km an hour
    shot("nyi_11", 339.00, 342.40, IN(1.0, 1.08)),
    shot("nyi_03", 342.40, 347.50, IN(1.0, 1.08)),                 # 2002: lava into Goma
    {"frames": "maps/frames_nyiragongo", "t0": 347.50, "t1": 351.50, "f0": 104, "xin": 0.6, "xout": 0.6},  # Nyiragongo + Goma
    shot("nyi_12", 351.50, 355.80, IN(1.0, 1.10)),                 # May 2021
    shot("nyi_05", 355.80, 360.00, IN(1.0, 1.06)),                 # stopped short of the city
    shot("nyi_09", 360.00, 363.80, PAN(0.35, 0.65, 1.12)),         # hundreds of thousands fled
    shot("nyi_08", 363.80, 367.50, IN(1.0, 1.10)),                 # Goma, 15 km from the crater
    shot("nyi_17", 367.50, 370.80, IN(1.0, 1.08)),
    shot("nyi_16", 370.80, 374.925, OUT(1.12, 1.0)),               # race against time
], badge="LAVA AT 60 KM/H")

# ---------------- 06_sakurajima ----------------
place("#5", "SAKURAJIMA", "JAPAN", "frames_sakurajima", 374.925, 378.05, 381.55, 439.875, [
    shot("sak_06", 381.55, 387.80, IN(1.0, 1.10)),                 # across the bay from Kagoshima
    shot("sak_14", 387.80, 392.00, IN(1.0, 1.10)),                 # small explosions
    shot("skx_03", 392.00, 396.30, IN(1.35, 1.45, (0.55, 0.78))),                  # ash high over the water
    shot("sak_17", 396.30, 401.50, IN(1.0, 1.08)),                 # people live with it
    shot("sak_10", 401.50, 406.10, IN(1.0, 1.08)),                 # ash bags, weather reports
    shot("sak_08", 406.10, 411.70, IN(1.0, 1.08)),                 # helmets on the way to school (shelter)
    shot("sak_02", 411.70, 414.80, IN(1.0, 1.08)),                 # not always small
    shot("sak_13", 414.80, 420.70, TILT(0.3, 0.6, 1.1)),           # 1914
    shot("sak_n1", 420.70, 425.10, IN(1.0, 1.10)),                 # joined to the mainland
    shot("sak_16", 425.10, 429.00, IN(1.0, 1.08)),                 # 58 people died
    shot("sak_09", 429.00, 434.50, PAN(0.35, 0.65, 1.12)),         # alert level 3
    shot("sak_11", 434.50, 440.675, OUT(1.12, 1.0)),                # magma building under the bay
], badge="ALERT LEVEL 3")

# ---------------- 07_reykjanes ----------------
place("#4", "REYKJANES PENINSULA", "ICELAND", "frames_reykjanes", 440.675, 443.8, 447.3, 517.75, [
    shot("rey_01", 447.30, 450.70, IN(1.0, 1.10)),                 # quiet for 800 years
    shot("rey_n2", 450.70, 453.50, IN(1.0, 1.08)),                 # 2021 they woke up
    shot("rex_03", 453.50, 458.50, IN(1.0, 1.10)),                 # Nov 2023, ground split under Grindavik
    shot("rex_04", 458.50, 464.50, PAN(0.35, 0.65, 1.12)),         # streets cracked
    shot("rex_02", 464.50, 470.80, IN(1.0, 1.08)),                 # evacuated in a single night
    shot("rey_n1", 470.80, 475.50, IN(1.0, 1.08)),                 # crater row erupted again and again (thermal)
    shot("rey_04", 475.50, 480.60, IN(1.0, 1.08)),                 # nine times (lava flow map)
    shot("rex_05", 480.60, 486.30, IN(1.0, 1.10)),                 # lava crossed the defences
    shot("rey_09", 486.30, 491.60, IN(1.0, 1.08)),                 # Blue Lagoon evacuated
    shot("rex_06", 491.60, 495.50, PAN(0.3, 0.7, 1.12)),           # earth walls
    shot("rey_02", 495.50, 499.20, IN(1.0, 1.08)),                 # Svartsengi power plant
    shot("rey_06", 499.20, 503.00, IN(1.0, 1.08)),                 # magma flowing back
    shot("rey_11", 503.00, 506.80, IN(1.0, 1.08)),
    shot("rey_17", 506.80, 510.50, IN(1.0, 1.06)),                 # less than an hour's warning
    shot("rey_14", 510.50, 514.00, IN(1.0, 1.08)),
    shot("rey_16", 514.00, 518.55, OUT(1.12, 1.0)),                # haven't moved back
], badge="9 ERUPTIONS")

# ---------------- 08_merapi ----------------
place("#3", "MOUNT MERAPI", "INDONESIA", "frames_merapi", 518.55, 521.675, 525.175, 585.8, [
    shot("mer_20", 525.175, 531.00, IN(1.0, 1.10)),                # mountain of fire
    shot("mer_03", 531.00, 535.60, IN(1.0, 1.08)),                 # most active in Indonesia
    shot("mer_01", 535.60, 540.00, IN(1.0, 1.08)),                 # millions within sight
    shot("mer_09", 540.00, 544.30, PAN(0.35, 0.65, 1.12)),         # Yogyakarta, 30 km
    shot("mer_07", 544.30, 550.50, IN(1.0, 1.10)),                 # pyroclastic flow
    shot("mer_16", 550.50, 556.60, IN(1.0, 1.10)),                 # well over 100 km/h
    shot("mer_11", 556.60, 559.20, IN(1.0, 1.08)),                 # nothing outruns it
    shot("mer_02", 559.20, 564.40, IN(1.0, 1.10)),                 # 2010, biggest in a century
    shot("mer_10", 564.40, 570.00, IN(1.0, 1.08)),                 # flows swept the valleys
    shot("mer_12", 570.00, 574.00, IN(1.0, 1.08)),                 # 350,000 evacuated
    shot("mer_n1", 574.00, 579.30, IN(1.0, 1.08)),                 # alert level three
    shot("mer_18", 579.30, 583.00, IN(1.0, 1.08)),                 # lava dome keeps growing
    shot("mer_19", 583.00, 586.60, OUT(1.12, 1.0)),                # hot avalanches
], badge='"MOUNTAIN OF FIRE"')

# ---------------- 09_popocatepetl ----------------
place("#2", "POPOCATÉPETL", "MEXICO", "frames_popocatepetl", 586.6, 589.725, 593.225, 654.625, [
    shot("pop_02", 593.225, 598.20, IN(1.0, 1.10)),                # smoking mountain, El Popo
    shot("pop_03", 598.20, 602.50, PAN(0.35, 0.65, 1.12)),         # 5,400 m
    {"frames": "maps/frames_popocatepetl", "t0": 602.50, "t1": 608.00, "f0": 104, "xin": 0.6, "xout": 0.6},  # 70 km from Mexico City
    shot("pop_18", 608.00, 614.00, IN(1.0, 1.08)),                 # 25 million people
    shot("pop_11", 614.00, 619.00, IN(1.0, 1.10)),                 # woke up in 1994
    shot("pop_12", 619.00, 622.50, IN(1.0, 1.10)),                 # steam, gas and ash
    shot("pop_15", 622.50, 625.90, IN(1.0, 1.08)),
    shot("pop_10", 625.90, 630.50, IN(1.0, 1.08)),                 # 2023: airports shut
    shot("pop_17", 630.50, 635.20, IN(1.0, 1.08)),                 # schools closed
    shot("pop_n2", 635.20, 641.10, IN(1.0, 1.10)),                 # February 2026 ash on Mexico City
    shot("pop_09", 641.10, 646.30, IN(1.0, 1.08)),                 # yellow alert, 12 km
    shot("pop_13", 646.30, 650.50, IN(1.0, 1.08)),                 # watched around the clock
    shot("pop_19", 650.50, 655.425, OUT(1.12, 1.0)),               # noisy to violent
], badge="25 MILLION NEARBY")

# ---------------- 10_campi_flegrei ----------------
place("#1", "CAMPI FLEGREI", "ITALY", "frames_campi_flegrei", 655.425, 658.55, 662.05, 757.525, [
    shot("cam_15", 662.05, 666.00, IN(1.0, 1.08)),                 # west of Naples
    shot("cam_n1", 666.00, 670.30, IN(1.0, 1.10)),                 # bigger, harder to see
    shot("cam_01", 670.30, 674.10, IN(1.0, 1.08)),                 # the burning fields
    shot("cam_dia", 674.10, 683.90, IN(1.0, 1.08, (0.45, 0.5))),   # caldera 15 km wide (own diagram)
    shot("cam_19", 683.90, 687.50, IN(1.0, 1.10)),                 # 39,000 years ago
    shot("cam_14", 687.50, 691.00, IN(1.0, 1.08)),
    shot("cam_20", 691.00, 698.50, IN(1.0, 1.10)),                 # last eruption much smaller, 1538
    shot("cam_02", 698.50, 704.30, IN(1.0, 1.08)),                 # a new hill in a week
    shot("cam_17", 704.30, 709.40, PAN(0.35, 0.6, 1.12)),          # Monte Nuovo
    shot("cam_08", 709.40, 713.50, IN(1.0, 1.08)),                 # the ground is rising
    shot("cam_03", 713.50, 717.00, IN(1.0, 1.08)),                 # nearly 1.5 m since 2005
    shot("cam_13", 717.00, 719.90, IN(1.0, 1.08)),
    shot("cam_06", 719.90, 725.00, IN(1.0, 1.10)),                 # earthquakes more often
    shot("cam_11", 725.00, 731.00, IN(1.0, 1.08)),                 # July 31, 2026
    shot("cam_07", 731.00, 735.50, IN(1.0, 1.08)),                 # half a million in the red zone
    shot("cam_18", 735.50, 739.80, TILT(0.3, 0.6, 1.1)),
    shot("cam_16", 739.80, 745.50, IN(1.0, 1.08)),                 # not certain or soon
    {"frames": "maps/frames_campi_flegrei", "t0": 745.50, "t1": 750.50, "f0": 104, "xin": 0.6, "xout": 0.6},  # watched most closely
    shot("cam_12", 750.50, 758.325, OUT(1.12, 1.0)),               # under a city
], badge="500,000 IN RED ZONE")

# ---------------- 11_outro ----------------
shots.append(shot("fuj_05", 758.325, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 758.825, "t1": DURATION, "fin": 1.2, "fout": 0.6})
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
