"""Edit decision list for video04 "The Most Extreme Places on Earth" (11:07.6).
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 8 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 667.6

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

# ---------------- 00_hook (0:00-0:25.1) ----------------
shots += [
    shot("dv_n_valley", 0.00,  1.25, IN(1.0, 1.08), 0.25, xin=0),    # the hottest
    shot("oym_03",   1.25,  2.35, IN(1.0, 1.08), 0.25),              # the coldest
    shot("cat_03",   2.35,  3.45, IN(1.0, 1.08), 0.25),              # the wettest (storm)
    shot("kol_06",   3.45,  4.60, IN(1.0, 1.10), 0.25),              # the deepest
    shot("cat_01",   4.60,  8.30, IN(1.0, 1.12), 0.3),               # numbers stop making sense
    shot("rin_02",   8.30, 10.60, PAN(0.4, 0.6, 1.12), 0.3),         # people living in them
    shot("tri_01",  10.60, 14.50, IN(1.0, 1.10), 0.3),               # so remote
    shot("maw_10",  14.50, 18.10, PAN(0.4, 0.6, 1.12), 0.3),         # 12 metres of rain
    shot("nem_n_sunrise", 18.10, 21.90, IN(1.0, 1.10), 0.3),         # closest humans are in space
    shot("cat_04",  21.90, 25.925, IN(1.0, 1.08), 0.3, xout=0.5),    # most extreme places on Earth
]
overlays.append({"type": "brand", "t0": 22.20, "t1": 25.70, "fin": 0.9, "fout": 0.5})

# ---------------- 01_mawsynram ----------------
place("#10", "MAWSYNRAM", "INDIA", "frames_mawsynram", 25.925, 29.05, 32.55, 88.60, [
    shot("maw_09",  32.55, 39.50, PAN(0.4, 0.6, 1.12)),              # hills of Meghalaya
    shot("maw_01",  39.50, 47.70, IN(1.0, 1.12)),                    # 11,873 mm a year (NASA)
    shot("maw_03",  47.70, 53.90, TILT(0.4, 0.6, 1.12)),             # almost 12 metres of water
    shot("maw_02",  53.90, 60.20, IN(1.0, 1.10)),                    # a metre of rain in a day
    shot("maw_11",  60.20, 67.00, IN(1.0, 1.10)),                    # monsoon; life built around rain
    inset("maw_04", 67.00, 73.30, max_up=1.2),                       # stock up on food
    shot("maw_05",  73.30, 77.90, IN(1.0, 1.12)),                    # living root bridges
    shot("maw_06",  77.90, 85.90, PAN(0.35, 0.65, 1.12)),            # the knup
    shot("maw_07",  85.90, 89.40, OUT(1.12, 1.0)),                   # both hands free
])

# ---------------- 02_catatumbo ----------------
place("#9", "LAKE MARACAIBO", "VENEZUELA", "frames_catatumbo", 89.40, 92.525, 96.025, 150.10, [
    shot("cat_02",  96.025, 101.60, IN(1.0, 1.10)),                  # the sky almost never dark
    shot("cat_11", 101.60, 107.00, IN(1.8, 1.95, (0.56, 0.5))),                   # where the Catatumbo flows in
    inset("cat_10", 107.00, 116.70, max_up=1.4),                     # 16 years of lightning data
    shot("cat_07", 116.70, 122.60, PAN(0.4, 0.6, 1.12)),             # 233 flashes per km2
    shot("cat_12", 122.60, 129.40, IN(1.0, 1.10)),                   # warm lake, Andes around it
    shot("cat_05", 129.40, 135.20, IN(1.0, 1.10)),                   # cool breezes slide down
    shot("cat_09", 135.20, 141.40, PAN(0.4, 0.6, 1.12)),             # storms explode
    shot("cat_08", 141.40, 147.10, IN(1.0, 1.10)),                   # sailors used them
    shot("cat_06", 147.10, 150.90, OUT(1.12, 1.0)),                  # Lighthouse of Maracaibo
])

# ---------------- 03_death_valley ----------------
place("#8", "DEATH VALLEY", "CALIFORNIA, USA", "frames_deathvalley", 150.90, 154.025, 157.525, 214.45, [
    shot("dv_01",  157.525, 163.80, IN(1.0, 1.10)),                  # Furnace Creek, 1913
    shot("dv_03",  163.80, 167.20, IN(1.0, 1.12)),                   # 134 F / 57 C
    shot("dv_05",  167.20, 174.10, PAN(0.4, 0.6, 1.12)),             # still the official record
    inset("dv_n_pia25482", 174.10, 180.00, max_up=1.2),              # the ground itself: 201 F
    shot("dv_09",  180.00, 183.80, IN(1.0, 1.10)),                   # near boiling water
    shot("dv_n_badwater", 183.80, 188.50, IN(1.0, 1.12)),            # a long, narrow basin
    shot("dv_04",  188.50, 192.50, IN(1.0, 1.10)),                   # 86 m below sea level
    shot("dv_06",  192.50, 197.10, PAN(0.4, 0.6, 1.12)),             # sun heats bare rock
    shot("dv_10",  197.10, 203.00, IN(1.0, 1.12)),                   # hot air sinks and compresses
    shot("dv_07",  203.00, 209.30, PAN(0.6, 0.4, 1.12)),             # summer 2001
    shot("dv_12",  209.30, 215.25, OUT(1.12, 1.0)),                  # 154 days in a row
])

# ---------------- 04_atacama ----------------
place("#7", "ATACAMA DESERT", "CHILE", "frames_atacama", 215.25, 218.375, 221.875, 274.525, [
    shot("ata_02", 221.875, 225.80, IN(1.0, 1.10)),                  # driest desert
    shot("ata_01", 225.80, 231.40, PAN(0.4, 0.6, 1.12)),             # 1 mm a year
    shot("ata_04", 231.40, 235.80, IN(1.0, 1.10)),                   # never a single drop
    shot("ata_n_coast", 235.80, 243.30, IN(1.0, 1.12)),              # two ranges block moisture
    shot("ata_11", 243.30, 250.30, IN(1.0, 1.10)),                   # NASA tests instruments
    shot("ata_03", 250.30, 253.60, PAN(0.4, 0.6, 1.12)),             # one huge advantage
    shot("ata_08", 253.60, 259.70, IN(1.0, 1.10)),                   # clear skies, no light pollution
    shot("ata_07", 259.70, 264.20, IN(1.0, 1.10)),                   # study the universe
    shot("ata_05", 264.20, 270.00, PAN(0.35, 0.6, 1.1)),             # ALMA, 66 antennas
    shot("ata_10", 270.00, 275.325, OUT(1.12, 1.0)),                 # plateau 5,000 m
])

# ---------------- 05_la_rinconada ----------------
place("#6", "LA RINCONADA", "PERU", "frames_rinconada", 275.325, 278.45, 281.95, 333.90, [
    shot("rin_02", 281.95, 287.30, IN(1.0, 1.10)),                   # highest settlement
    shot("rin_iss65", 287.30, 292.50, TILT(0.35, 0.6, 1.0)),         # half the oxygen (Andes from ISS)
    shot("rin_01", 292.50, 299.00, TILT(0.6, 0.35, 1.15)),           # La Bella Durmiente glacier
    shot("rin_07", 299.00, 306.10, IN(1.9, 2.0, (0.5, 0.27))),       # they came for gold (nugget only, no label)
    shot("rin_05", 306.10, 311.70, IN(1.6, 1.7, (0.68, 0.74))),      # no running water (detail of the tin houses)
    inset("rin_03", 311.70, 315.00, max_up=1.0),                     # electricity in the 2000s
    shot("rin_06", 315.00, 320.00, IN(1.45, 1.55, (0.45, 0.76))),    # cachorreo (detail of the rooftops)
    shot("rin_iss29", 320.00, 324.70, IN(1.0, 1.10)),                # one day to keep the ore (Titicaca region from ISS)
    shot("rin_10", 324.70, 329.20, IN(1.0, 1.10)),                   # very little gold
    inset("rin_08", 329.20, 334.70, max_up=1.4),                     # hardest places to live
])

# ---------------- 06_oymyakon ----------------
place("#5", "OYMYAKON", "RUSSIA", "frames_oymyakon", 334.70, 337.825, 341.325, 388.80, [
    shot("oym_03", 341.325, 348.90, PAN(0.4, 0.6, 1.12)),            # minus 68 C, 1933
    shot("oym_01", 348.90, 358.50, IN(1.0, 1.12)),                   # coldest inhabited place
    shot("oym_06", 358.50, 361.80, IN(1.0, 1.10)),                   # a few hundred people
    shot("oym_02", 361.80, 369.70, IN(1.0, 1.12)),                   # the school closes at -52
    shot("oym_09", 369.70, 374.10, IN(1.0, 1.10)),                   # glasses freeze to the face
    shot("oym_11", 374.10, 379.50, IN(1.0, 1.08, (0.5, 0.45))),      # road to Yakutsk
    shot("oym_10", 379.50, 389.60, OUT(1.12, 1.0)),                  # engines running all day
])

# ---------------- 07_tristan ----------------
place("#4", "TRISTAN DA CUNHA", "SOUTH ATLANTIC", "frames_tristan", 389.60, 392.725, 396.225, 448.525, [
    shot("tri_07", 396.225, 399.30, IN(1.0, 1.10)),                  # volcano with a village
    shot("tri_n_iss34", 399.30, 403.10, IN(1.0, 1.15)),              # most remote inhabited island
    shot("tri_01", 403.10, 411.80, IN(1.0, 1.10)),                   # St Helena 2,400 km
    shot("tri_09", 411.80, 418.70, PAN(0.4, 0.6, 1.12)),             # Cape Town 2,800 km
    shot("tri_06", 418.70, 424.30, IN(1.0, 1.10)),                   # Edinburgh of the Seven Seas
    shot("tri_05", 424.30, 426.80, IN(1.0, 1.10)),                   # no harbour for big ships
    inset("tri_02", 426.80, 434.10, max_up=1.0),                     # only by sea
    inset("tri_n_pia", 434.10, 438.00, max_up=1.2),                  # 1961 eruption
    shot("tri_10", 438.00, 443.20, PAN(0.4, 0.6, 1.12)),             # fled in fishing boats
    shot("tri_04", 443.20, 449.325, OUT(1.12, 1.0)),                 # came back home
])

# ---------------- 08_kola ----------------
place("#3", "KOLA SUPERDEEP BOREHOLE", "RUSSIA", "frames_kola", 449.325, 452.45, 455.95, 516.35, [
    inset("kol_03", 455.95, 462.10, max_up=2.0),                     # drilling straight down, 1970
    shot("kol_01", 462.10, 464.90, IN(1.0, 1.10)),                   # nearly 20 years
    shot("depth_kola", 464.90, 480.60, IN(1.0, 1.04, (0.6, 0.45))), # 12,262 m vs Everest and trench
    shot("kol_06", 480.60, 484.30, IN(1.0, 1.10)),                   # only 23 cm wide
    shot("kol_07", 484.30, 495.20, PAN(0.4, 0.6, 1.12)),             # 180 C, rock like plastic
    inset("kol_04", 495.20, 506.10, max_up=1.0),                     # microfossils (geological section)
    shot("kol_10", 506.10, 512.60, PAN(0.4, 0.6, 1.12)),             # a third through the crust
    shot("kol_05", 512.60, 517.15, OUT(1.12, 1.0)),                  # sealed under a metal cap
])

# ---------------- 09_challenger_deep ----------------
place("#2", "CHALLENGER DEEP", "PACIFIC OCEAN", "frames_challenger", 517.15, 520.275, 523.775, 581.325, [
    inset("cha_06", 523.775, 527.70, max_up=1.2),                    # southern end of the trench
    shot("cha_n_iss30", 527.70, 532.10, IN(1.0, 1.10)),              # about 10,935 m deep
    shot("depth_challenger", 532.10, 539.10, IN(1.0, 1.04, (0.5, 0.45))), # Everest would vanish
    shot("cha_08", 539.10, 545.30, IN(1.0, 1.10)),                   # 1,000 times the pressure
    shot("cha_02", 545.30, 550.00, IN(1.0, 1.10)),                   # 23 January 1960
    shot("cha_01", 550.00, 555.40, IN(1.0, 1.10)),                   # the bathyscaphe Trieste
    shot("cha_04", 555.40, 560.70, IN(1.0, 1.10)),                   # a window cracked
    shot("cha_03", 560.70, 566.20, IN(1.0, 1.10)),                   # 20 minutes at the bottom
    shot("cha_n_vent", 566.20, 574.70, IN(1.0, 1.12)),               # life at the very bottom (NOAA vent)
    shot("cha_05", 574.70, 582.125, OUT(1.12, 1.0)),                 # nobody went back until 2012
])

# ---------------- 10_point_nemo ----------------
place("#1", "POINT NEMO", "SOUTH PACIFIC", "frames_nemo", 582.125, 585.25, 588.75, 653.225, [
    shot("nem_05", 588.75, 591.60, IN(1.0, 1.10)),                   # farthest from any land
    inset("nem_01", 591.60, 597.20, max_up=1.2),                     # calculated in 1992
    inset("nem_10", 597.20, 601.40, max_up=1.2),                     # Captain Nemo, Jules Verne
    shot("nem_09", 601.40, 604.30, IN(1.0, 1.10)),                   # nemo means no one
    shot("nem_06", 604.30, 609.00, IN(1.0, 1.12)),                   # 2,688 km: three tiny islands
    shot("nem_07", 609.00, 613.40, IN(1.0, 1.10)),                   # none inhabited
    shot("nem_08", 613.40, 618.20, IN(1.0, 1.10)),                   # the ISS passes overhead
    shot("nem_n_issoverpac", 618.20, 624.10, IN(1.0, 1.10)),         # astronauts are the closest
    shot("nem_02", 624.10, 630.80, PAN(0.4, 0.6, 1.12)),             # graveyard for spacecraft
    shot("nem_n_atvreentry", 630.80, 638.10, IN(1.0, 1.10)),         # burn up in the atmosphere
    shot("nem_n_mir", 638.10, 644.00, IN(1.0, 1.10)),                # Mir came down here, 2001
    shot("nem_n_atvundock", 644.00, 650.60, IN(1.12, 1.2)),        # (zoom hides the caption strip)          # the ISS itself, early 2030s
    shot("nem_04", 650.60, 654.025, OUT(1.12, 1.0)),                 # the loneliest place on Earth
])

# ---------------- 11_outro ----------------
shots.append(shot("ata_06", 654.025, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 654.6, "t1": DURATION, "fin": 1.2, "fout": 0.6})

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
