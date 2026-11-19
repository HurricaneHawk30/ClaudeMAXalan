"""Edit decision list for video13 "10 Most Dangerous Roads on Earth" (10:24.0).
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 19 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 623.975

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

# ---------------- 00_hook (0:00-0:27.525) ----------------
shots += [
    shot("dal_01",  0.00,  2.60, IN(1.0, 1.08), 0.3, xin=0),     # some roads take you somewhere
    shot("zoj_06",  2.60,  5.10, IN(1.0, 1.10), 0.25),           # might not let you come back
    shot("ice_13",  5.10,  9.70, IN(1.0, 1.10), 0.25),           # a highway across frozen lakes
    shot("guo_05",  9.70, 14.00, IN(1.0, 1.10), 0.25),           # a tunnel carved through a cliff
    shot("kol_16", 14.00, 18.00, IN(1.0, 1.10), 0.25),           # the Road of Bones
    shot("yun_11", 18.00, 27.525, IN(1.0, 1.12), 0.3, xout=0.5), # number one: the Andes
]
overlays.append({"type": "brand", "t0": 23.00, "t1": 27.20, "fin": 0.9, "fout": 0.5})

# ---------------- 01_caracoles ----------------
place("#10", "LOS CARACOLES", "CHILE", "frames_caracoles", 27.525, 30.65, 34.15, 86.00, [
    shot("car_13", 34.15, 37.80, IN(1.0, 1.10)),                   # main road Santiago - Mendoza
    shot("car_04", 37.80, 41.70, IN(1.0, 1.12)),                   # folds back and forth
    shot("car_01", 41.70, 46.90, PAN(0.35, 0.65, 1.1)),            # twenty-nine hairpin bends
    shot("car_05", 46.90, 52.10, IN(1.0, 1.12)),                   # the shell of a snail
    shot("car_02", 52.10, 55.10, IN(1.0, 1.08)),                   # the Snails
    shot("car_03", 55.10, 62.50, IN(1.0, 1.12)),                   # trucks crawl up, 3,200 m
    shot("car_06", 62.50, 65.00, IN(1.0, 1.08)),                   # well kept
    shot("car_14", 65.00, 70.00, IN(1.0, 1.10)),                   # the danger is the weather
    shot("car_11", 70.00, 74.60, IN(1.0, 1.08)),                   # snow and falling rocks
    shot("car_10", 74.60, 80.00, IN(1.0, 1.12)),                   # September 2013, a snowstorm
    shot("car_08", 80.00, 86.80, OUT(1.12, 1.0)),                  # stranded at the border
], badge="29 HAIRPIN BENDS")

# ---------------- 02_ice_road ----------------
place("#9", "TIBBITT TO CONTWOYTO", "CANADA", "frames_ice_road", 86.80, 89.925, 93.425, 146.875, [
    shot("ice_04", 93.425, 98.30, IN(1.0, 1.10)),                  # only two months a year
    shot("ice_14", 98.30, 103.40, IN(1.0, 1.08)),                  # every January, north of Yellowknife
    shot("ice_07", 103.40, 109.20, IN(1.0, 1.12)),                 # 85% over frozen lakes
    shot("ice_06", 109.20, 112.90, IN(1.0, 1.08)),                 # longest heavy-haul ice road
    shot("ice_08", 112.90, 117.90, IN(1.0, 1.10)),                 # 400 to 600 km
    shot("ice_10", 117.90, 122.40, IN(1.0, 1.12)),                 # diamond mines of the Arctic
    shot("ice_02", 122.40, 125.20, IN(1.0, 1.08)),                 # the ice melts
    shot("ice_15", 125.20, 128.70, IN(1.0, 1.08)),                 # the road disappears
    shot("ice_03", 128.70, 135.00, IN(1.0, 1.10)),                 # the rules are strict
    shot("ice_09", 135.00, 141.10, IN(1.0, 1.15)),                 # 25 km/h, 500 m apart
    shot("ice_01", 141.10, 147.675, OUT(1.12, 1.0)),               # black, freezing water
], badge="ROAD MADE OF ICE")

# ---------------- 03_sani_pass ----------------
place("#8", "SANI PASS", "SOUTH AFRICA / LESOTHO", "frames_sani_pass", 147.675, 150.80, 154.30, 199.20, [
    shot("san_07", 154.30, 160.60, PAN(0.35, 0.65, 1.1)),          # the Drakensberg, toward Lesotho
    shot("san_06", 160.60, 163.00, IN(1.0, 1.08)),                 # nine kilometers
    shot("san_05", 163.00, 166.00, IN(1.0, 1.10)),                 # 1,300 m up
    shot("san_01", 166.00, 170.40, IN(1.0, 1.12)),                 # tight hairpin bends
    shot("san_12", 170.40, 175.00, IN(1.0, 1.08)),                 # from 1,500 m
    shot("san_15", 175.00, 179.60, IN(1.0, 1.08)),                 # the Lesotho border post
    shot("san_13", 179.60, 184.20, IN(1.0, 1.10)),                 # four-by-four only
    shot("san_10", 184.20, 186.30, IN(1.0, 1.08)),                 # rain, mud
    shot("san_02", 186.30, 190.40, IN(1.0, 1.08)),                 # winter, snow and ice
    shot("san_08", 190.40, 194.20, IN(1.0, 1.08)),                 # at the very top
    shot("san_14", 194.20, 200.00, OUT(1.1, 1.0)),                 # the highest pub in Africa
], badge="4x4 ONLY")

# ---------------- 04_dalton ----------------
place("#7", "DALTON HIGHWAY", "ALASKA, USA", "frames_dalton", 200.00, 203.125, 206.625, 261.35, [
    shot("dal_09", 206.625, 210.00, IN(1.0, 1.10)),                # 414 miles
    shot("dal_05", 210.00, 215.50, IN(1.0, 1.10)),                 # forests near Fairbanks
    shot("dal_11", 215.50, 220.60, IN(1.0, 1.08)),                 # to Prudhoe Bay
    shot("dal_04", 220.60, 227.70, PAN(0.3, 0.6, 1.1)),            # 1974, haul road for the pipeline
    shot("dal_08", 227.70, 229.70, IN(1.0, 1.08)),                 # still gravel
    shot("dal_02", 229.70, 233.30, IN(1.0, 1.08)),                 # Atigun Pass
    shot("dal_14", 233.30, 238.90, IN(1.0, 1.10)),                 # 1,400 m, the tundra
    shot("dal_10", 238.90, 241.00, IN(1.0, 1.08)),                 # the emptiness
    shot("dal_07", 241.00, 243.80, IN(1.0, 1.08)),                 # the truck stop at Coldfoot
    shot("dal_15", 243.80, 247.70, IN(1.0, 1.10)),                 # no services for 240 miles
    shot("dal_06", 247.70, 250.00, IN(1.0, 1.08)),                 # almost 400 km
    shot("dal_13", 250.00, 254.10, IN(1.0, 1.08)),                 # no gas, no signal
    shot("dal_03", 254.10, 258.30, IN(1.0, 1.10)),                 # minus forty
    shot("dal_16", 258.30, 262.15, OUT(1.1, 1.0)),                 # on your own
], badge="NO SERVICES FOR 240 MILES")

# ---------------- 05_skippers ----------------
place("#6", "SKIPPERS CANYON ROAD", "NEW ZEALAND", "frames_skippers", 262.15, 265.275, 268.775, 312.725, [
    shot("ski_06", 268.775, 274.20, PAN(0.3, 0.6, 1.1)),           # a narrow dirt road on a canyon wall
    shot("ski_13", 274.20, 279.00, TILT(0.3, 0.7, 1.0)),           # the richest river in the world
    shot("ski_17", 279.00, 284.50, PAN(0.35, 0.65, 1.1)),          # 1883-1890, the gold diggings
    shot("ski_05", 284.50, 288.60, IN(1.0, 1.10)),                 # cut straight into the rock
    shot("ski_04", 288.60, 292.90, IN(1.0, 1.08)),                 # barely wide enough
    shot("ski_07", 292.90, 296.40, IN(1.0, 1.08)),                 # a wall of rock
    shot("ski_09", 296.40, 300.50, IN(1.0, 1.10)),                 # a drop of hundreds of meters
    shot("ski_02", 300.50, 304.00, IN(1.0, 1.08)),                 # rental car companies
    shot("ski_11", 304.00, 307.00, IN(1.0, 1.08)),
    inset("ski_03", 307.00, 309.40),                               # Skippers Canyon (bridge)
    shot("ski_01", 309.40, 313.525, OUT(1.1, 1.0)),                # a local guide
], badge="NO RENTAL CARS")

# ---------------- 06_zoji_la ----------------
place("#5", "ZOJI LA", "INDIA", "frames_zoji_la", 313.525, 316.65, 320.15, 369.425, [
    shot("zoj_01", 320.15, 325.30, IN(1.0, 1.10)),                 # Kashmir and Ladakh
    shot("zoj_16", 325.30, 328.70, IN(1.0, 1.08)),                 # a lifeline
    shot("zoj_07", 328.70, 332.90, IN(1.0, 1.10)),                 # most frightening drives in Asia
    shot("zoj_08", 332.90, 336.20, IN(1.0, 1.08)),                 # narrow, unpaved
    shot("zoj_12", 336.20, 338.60, IN(1.0, 1.08)),                 # sheer drops, no barriers
    shot("zoj_11", 338.60, 342.40, IN(1.0, 1.08)),                 # convoys, trucks
    shot("zoj_10", 342.40, 345.20, IN(1.0, 1.08)),                 # snow buries the pass
    shot("zoj_03", 345.20, 350.80, IN(1.0, 1.12)),                 # deeper than a truck is tall
    shot("zoj_14", 350.80, 354.10, IN(1.0, 1.08)),                 # avalanches
    shot("zoj_15", 354.10, 356.30, IN(1.0, 1.08)),                 # that may finally change
    shot("zoj_04", 356.30, 363.90, IN(1.0, 1.12)),                 # June 2026, a 13 km tunnel
    shot("zoj_02", 363.90, 370.225, OUT(1.12, 1.0)),               # fifteen minutes
], badge="CLOSED FOR MONTHS")

# ---------------- 07_guoliang ----------------
place("#4", "GUOLIANG TUNNEL", "CHINA", "frames_guoliang", 370.225, 373.35, 376.85, 432.05, [
    shot("guo_03", 376.85, 380.30, PAN(0.3, 0.6, 1.1)),            # a village on top of a cliff
    shot("guo_11", 380.30, 382.10, IN(1.0, 1.08)),                 # cut off from the world
    shot("guo_06", 382.10, 387.10, TILT(0.25, 0.65, 1.0)),         # a steep stairway in the rock
    shot("guo_15", 387.10, 392.10, IN(1.0, 1.08)),                 # 1972, the villagers decided
    shot("guo_07", 392.10, 395.20, IN(1.0, 1.08)),                 # sold their livestock
    shot("guo_01", 395.20, 398.20, IN(1.0, 1.10)),                 # thirteen men, ropes on the cliff
    shot("guo_04", 398.20, 402.90, IN(1.0, 1.10)),                 # cutting into the rock by hand
    shot("guo_02", 402.90, 408.10, IN(1.0, 1.12)),                 # one meter every three days
    shot("guo_05", 408.10, 413.20, IN(1.0, 1.10)),                 # May 1, 1977, the tunnel opened
    shot("guo_14", 413.20, 418.90, IN(1.0, 1.08)),                 # 1.2 km, 5 x 4 m
    shot("guo_09", 418.90, 422.60, IN(1.0, 1.08)),                 # thirty openings like windows
    shot("guo_10", 422.60, 426.30, IN(1.0, 1.08)),                 # one builder died
    shot("guo_13", 426.30, 432.85, OUT(1.1, 1.0)),                 # tour buses today
], badge="CARVED BY HAND")

# ---------------- 08_kolyma ----------------
place("#3", "KOLYMA HIGHWAY", "RUSSIA", "frames_kolyma", 432.85, 435.975, 439.475, 486.175, [
    shot("kol_12", 439.475, 444.90, IN(1.0, 1.10)),                # from the port of Magadan
    shot("kol_16", 444.90, 447.70, IN(1.0, 1.08)),                 # one of the coldest cities
    shot("kol_05", 447.70, 449.30, IN(1.0, 1.06)),                 # the Road of Bones
    shot("kol_07", 449.30, 457.20, IN(1.0, 1.12)),                 # built 1932-1953 by prisoners
    shot("kol_23", 457.20, 459.70, IN(1.0, 1.08)),                 # brutal cold
    shot("kol_22", 459.70, 465.60, IN(1.0, 1.10)),                 # many died (camp ruins, far)
    shot("kol_02", 465.60, 469.10, IN(1.0, 1.08)),                 # mostly gravel
    shot("kol_09", 469.10, 474.40, IN(1.0, 1.08)),                 # ice, minus fifty
    shot("kol_03", 474.40, 477.80, IN(1.0, 1.08)),                 # mud in summer
    shot("kol_19", 477.80, 481.20, IN(1.0, 1.08)),                 # abandoned villages
    shot("kol_11", 481.20, 483.60, IN(1.0, 1.08)),                 # the few drivers
    shot("kol_21", 483.60, 486.975, OUT(1.1, 1.0)),                # four or five days
], badge="ROAD OF BONES")

# ---------------- 09_fairy_meadows ----------------
place("#2", "FAIRY MEADOWS ROAD", "PAKISTAN", "frames_fairy_meadows", 486.975, 490.10, 493.60, 541.10, [
    shot("fai_13", 493.60, 498.20, IN(1.0, 1.10)),                 # Nanga Parbat
    shot("fai_11", 498.20, 506.30, PAN(0.3, 0.6, 1.1)),            # Raikot Bridge, up to Tato
    shot("fai_07", 506.30, 509.30, IN(1.0, 1.08)),                 # sixteen kilometers
    shot("fai_10", 509.30, 511.30, IN(1.0, 1.08)),                 # built by villagers
    shot("fai_06", 511.30, 513.30, IN(1.0, 1.08)),                 # as wide as a jeep
    shot("fai_04", 513.30, 515.50, IN(1.0, 1.08)),                 # no guardrails
    shot("fai_05", 515.50, 517.60, IN(1.0, 1.08)),                 # the mountain
    shot("fai_08", 517.60, 521.90, TILT(0.3, 0.7, 1.05)),          # a drop into the valley
    shot("fai_17", 521.90, 525.20, IN(1.0, 1.08)),                 # visitors can't drive
    shot("fai_09", 525.20, 527.90, IN(1.0, 1.10)),                 # old jeeps
    shot("fai_01", 527.90, 531.70, IN(1.0, 1.10)),                 # inches from the edge
    shot("fai_14", 531.70, 535.10, IN(1.0, 1.08)),                 # the adventure isn't over
    shot("fai_15", 535.10, 541.90, OUT(1.1, 1.0)),                 # the meadows below Nanga Parbat
], badge="NO GUARDRAILS")

# ---------------- 10_yungas ----------------
place("#1", "YUNGAS ROAD", "BOLIVIA", "frames_yungas", 541.90, 545.025, 548.525, 610.475, [
    shot("yun_09", 548.525, 554.60, IN(1.0, 1.10)),                # Paraguayan prisoners, near La Paz
    shot("yun_02", 554.60, 560.70, IN(1.0, 1.10)),                 # down to the Yungas
    shot("yun_04", 560.70, 564.40, IN(1.0, 1.10)),                 # drops 3,500 m
    shot("yun_05", 564.40, 571.40, TILT(0.3, 0.65, 1.05)),         # less than 3 m wide
    shot("yun_08", 571.40, 574.30, PAN(0.3, 0.6, 1.1)),            # the main route north
    shot("yun_03", 574.30, 577.30, IN(1.0, 1.08)),                 # trucks, crowded buses
    shot("yun_10", 577.30, 580.20, IN(1.0, 1.08)),                 # fog, rain, mud, waterfalls
    shot("yun_13", 580.20, 586.70, IN(1.0, 1.10)),                 # 200-300 people a year
    shot("yun_06", 586.70, 593.10, IN(1.0, 1.12)),                 # 1995, most dangerous road
    shot("yun_01", 593.10, 595.60, IN(1.0, 1.08)),                 # Death Road
    shot("yun_20", 595.60, 599.30, IN(1.0, 1.08)),                 # the new road
    shot("yun_19", 599.30, 601.50, IN(1.0, 1.08)),                 # traffic moved
    shot("yun_12", 601.50, 603.80, IN(1.0, 1.08)),                 # the old road is still open
    shot("yun_15", 603.80, 607.70, IN(1.0, 1.08)),                 # tourists on mountain bikes
    shot("yun_17", 607.70, 611.275, OUT(1.1, 1.0)),                # past the crosses
], badge="DEATH ROAD")

# ---------------- 11_outro ----------------
shots.append(shot("yun_16", 611.275, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 611.8, "t1": DURATION, "fin": 1.2, "fout": 0.6})

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
